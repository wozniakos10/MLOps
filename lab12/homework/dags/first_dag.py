import os
import requests
from airflow.sdk import dag, task, ObjectStoragePath
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from pendulum import datetime
import pendulum

# S3 Bucket and Paths
BUCKET_NAME = "homework-data-bucket"
RAW_DATA_PATH = "raw_data"
PREPROCESSED_DATA_PATH = "preprocessed_data"


@dag(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    schedule="@monthly",
    catchup=True,
    tags=["homework", "lab12"],
)
def taxi_data_pipeline():
    @task
    def download_data(logical_date: str) -> ObjectStoragePath:
        date_obj = pendulum.parse(logical_date)
        year = date_obj.year
        month = date_obj.month

        file_name = f"yellow_tripdata_{year}-{month:02d}.parquet"
        url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{file_name}"

        print(f"Downloading {url}")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Use ObjectStoragePath
        base = ObjectStoragePath(f"s3://{BUCKET_NAME}/", conn_id="aws_default")
        path = base / RAW_DATA_PATH / file_name

        with path.open("wb") as f:
            f.write(response.content)

        print(f"Uploaded to {path}")
        # Return clean URI for downstream tasks using s3fs
        return f"s3://{BUCKET_NAME}/{RAW_DATA_PATH}/{file_name}"

    # Helper to get credentials for virtualenv tasks
    # can be done also in different way, without explicitly provide credentials
    @task
    def get_aws_credentials() -> dict:
        hook = S3Hook(aws_conn_id="aws_default")
        creds = hook.get_credentials()
        return {
            "key": creds.access_key,
            "secret": creds.secret_key,
            "endpoint_url": hook.conn_config.endpoint_url,
        }

    @task.virtualenv(
        requirements=["polars", "s3fs", "pendulum"],
        serializer="cloudpickle",
        system_site_packages=False,
    )
    def process_data(
        s3_key: ObjectStoragePath,
        aws_creds: dict,
        bucket_name: str,
        preprocessed_path: str,
    ) -> str:
        import s3fs
        import polars as pl

        # S3 filesystem with passed credentials
        fs = s3fs.S3FileSystem(
            key=aws_creds["key"],
            secret=aws_creds["secret"],
            endpoint_url=aws_creds["endpoint_url"],
        )

        # Input is full URI from ObjectStoragePath
        input_path = s3_key

        print(f"Processing {input_path}")

        with fs.open(input_path, mode="rb") as f:
            df = pl.read_parquet(f)

        # Transformations
        df = df.with_columns(
            [
                pl.col("tpep_pickup_datetime").dt.cast_time_unit("ms"),
                pl.col("tpep_dropoff_datetime").dt.cast_time_unit("ms"),
            ]
        )

        df = df.filter(pl.col("passenger_count") > 0)

        df = df.with_columns(
            pl.when(pl.col("passenger_count") > 6)
            .then(6)
            .otherwise(pl.col("passenger_count"))
            .alias("passenger_count")
        )

        duration_minutes = (
            pl.col("tpep_dropoff_datetime") - pl.col("tpep_pickup_datetime")
        ).dt.total_minutes()
        df = df.filter(duration_minutes <= 120)

        df_daily = (
            df.group_by(pl.col("tpep_pickup_datetime").dt.date().alias("date"))
            .agg(pl.len().alias("count"))
            .sort("date")
        )

        filename = os.path.basename(s3_key)
        output_key = f"{preprocessed_path}/{filename}"
        output_path = f"s3://{bucket_name}/{output_key}"

        with fs.open(output_path, mode="wb") as f:
            df_daily.write_parquet(f)

        return output_key

    creds = get_aws_credentials()
    # Pass logical_date via template
    raw_key = download_data(logical_date="{{ logical_date }}")
    process_data(
        raw_key,
        creds,
        bucket_name=BUCKET_NAME,
        preprocessed_path=PREPROCESSED_DATA_PATH,
    )


taxi_data_pipeline()
