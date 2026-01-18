import pickle
from airflow.sdk import dag, task, ObjectStoragePath
from pendulum import datetime

# S3 Bucket and Paths
BUCKET_NAME = "homework-data-bucket"
PREPROCESSED_DATA_PATH = "preprocessed_data"
MODELS_CANDIDATES_PATH = "models/candidates"
BEST_MODEL_PATH = "models/best_model.pkl"


@dag(
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["homework", "lab12", "ml"],
)
def model_training_pipeline():
    @task
    def get_aws_credentials() -> dict:
        from airflow.providers.amazon.aws.hooks.s3 import S3Hook

        hook = S3Hook(aws_conn_id="aws_default")
        creds = hook.get_credentials()
        return {
            "key": creds.access_key,
            "secret": creds.secret_key,
            "endpoint_url": hook.conn_config.endpoint_url,
        }

    @task.virtualenv(
        requirements=["pandas", "s3fs", "pyarrow"],
        serializer="cloudpickle",
        system_site_packages=False,
    )
    def fetch_and_split(
        aws_creds: dict, bucket_name: str, preprocessed_path: str
    ) -> dict:
        import pandas as pd
        import s3fs

        fs = s3fs.S3FileSystem(
            key=aws_creds["key"],
            secret=aws_creds["secret"],
            endpoint_url=aws_creds["endpoint_url"],
        )

        files = fs.glob(f"s3://{bucket_name}/{preprocessed_path}/*.parquet")
        if not files:
            raise ValueError("No preprocessed data found.")

        dfs = []
        for file in files:
            with fs.open(file, "rb") as f:
                dfs.append(pd.read_parquet(f))

        full_df = pd.concat(dfs)
        full_df["date"] = pd.to_datetime(full_df["date"])
        full_df = full_df.sort_values("date")

        max_date = full_df["date"].max()
        cutoff_date = max_date.replace(day=1)

        train_df = full_df[full_df["date"] < cutoff_date]
        test_df = full_df[full_df["date"] >= cutoff_date]

        def create_features(df):
            df = df.copy()
            df["day_of_week"] = df["date"].dt.dayofweek
            df["day_of_month"] = df["date"].dt.day
            return df[["day_of_week", "day_of_month"]], df["count"]

        X_train, y_train = create_features(train_df)
        X_test, y_test = create_features(test_df)

        split_path = f"s3://{bucket_name}/split_data"

        def save_to_s3(df, name):
            path = f"{split_path}/{name}.parquet"
            with fs.open(path, "wb") as f:
                df.to_parquet(f)
            return path

        paths = {
            "X_train": save_to_s3(X_train, "X_train"),
            "y_train": save_to_s3(pd.DataFrame(y_train), "y_train"),
            "X_test": save_to_s3(X_test, "X_test"),
            "y_test": save_to_s3(pd.DataFrame(y_test), "y_test"),
            "training_set_size": len(X_train),
        }
        return paths

    @task.virtualenv(
        requirements=["pandas", "scikit-learn", "s3fs", "pyarrow"],
        serializer="cloudpickle",
        system_site_packages=False,
    )
    def train_model(
        model_type: str,
        data_paths: dict,
        aws_creds: dict,
        bucket_name: str,
        candidates_path: str,
    ) -> dict:
        import pandas as pd
        import s3fs
        from sklearn.linear_model import Ridge
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.svm import SVR
        from sklearn.model_selection import GridSearchCV
        from sklearn.metrics import mean_absolute_error

        fs = s3fs.S3FileSystem(
            key=aws_creds["key"],
            secret=aws_creds["secret"],
            endpoint_url=aws_creds["endpoint_url"],
        )

        def load_from_s3(path):
            with fs.open(path, "rb") as f:
                return pd.read_parquet(f)

        X_train = load_from_s3(data_paths["X_train"])
        y_train = load_from_s3(data_paths["y_train"]).values.ravel()
        X_test = load_from_s3(data_paths["X_test"])
        y_test = load_from_s3(data_paths["y_test"]).values.ravel()

        model = None
        params = {}

        if model_type == "Ridge":
            model = Ridge()
            params = {"alpha": [0.1, 1.0, 10.0]}
        elif model_type == "RandomForest":
            model = RandomForestRegressor(random_state=42)
            params = {"n_estimators": [50, 100], "max_depth": [5, 10, None]}
        elif model_type == "SVR":
            model = SVR()
            params = {"C": [0.1, 1, 10], "kernel": ["linear", "rbf"]}

        search = GridSearchCV(model, params, cv=3, scoring="neg_mean_absolute_error")
        search.fit(X_train, y_train)
        best_model = search.best_estimator_

        predictions = best_model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)

        model_filename = f"{model_type}_candidate.pkl"
        s3_key = f"{candidates_path}/{model_filename}"
        s3_path = f"s3://{bucket_name}/{s3_key}"

        with fs.open(s3_path, "wb") as f:
            pickle.dump(best_model, f)

        return {
            "model_name": model_type,
            "mae": mae,
            "s3_key": s3_key,
            "training_set_size": data_paths["training_set_size"],
        }

    @task
    def select_best_model(results: list) -> str:
        best_result = min(results, key=lambda x: x["mae"])
        print(f"Best model: {best_result['model_name']} with MAE: {best_result['mae']}")

        base = ObjectStoragePath(f"s3://{BUCKET_NAME}/", conn_id="aws_default")
        source_path = base / best_result["s3_key"]
        dest_path = base / BEST_MODEL_PATH

        # Copy
        source_path.copy(dest_path)

        # Cleanup
        for res in results:
            path = base / res["s3_key"]
            path.unlink(missing_ok=True)

        return best_result["model_name"]

    @task
    def log_performance(results: list) -> None:
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        conn_id = "postgres_storage"

        rows = []
        for res in results:
            rows.append(
                (res["s3_key"], res["model_name"], res["mae"], res["training_set_size"])
            )

        pg_hook = PostgresHook(postgres_conn_id=conn_id)
        pg_hook.insert_rows(
            table="trained_models_stats",
            rows=rows,
            target_fields=["s3_key", "model_name", "mae", "training_set_size"],
        )

    creds = get_aws_credentials()
    data_paths = fetch_and_split(
        aws_creds=creds,
        bucket_name=BUCKET_NAME,
        preprocessed_path=PREPROCESSED_DATA_PATH,
    )

    model_types = ["Ridge", "RandomForest", "SVR"]
    results = []
    for model_type in model_types:
        res = train_model(
            model_type=model_type,
            data_paths=data_paths,
            aws_creds=creds,
            bucket_name=BUCKET_NAME,
            candidates_path=MODELS_CANDIDATES_PATH,
        )
        results.append(res)

    select_best_model(results)
    log_performance(results)


model_training_pipeline()
