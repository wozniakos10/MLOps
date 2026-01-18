import pendulum
from airflow.decorators import dag, task
from airflow.models import Variable
import datetime
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(
    schedule=datetime.timedelta(minutes=1),
    catchup=False,
    tags=["exercise_5", "connections", "variables"],
)
def exercise_5_pipeline():
    # Define the task using the virtualenv decorator
    @task.virtualenv(
        requirements=["twelvedata", "pendulum", "lazy_object_proxy"],
        serializer="cloudpickle",
        system_site_packages=False,
    )
    def get_data(data_interval_start=None, api_key=None):
        from twelvedata import TDClient

        # Handle string input for data_interval_start
        if isinstance(data_interval_start, str):
            date_obj = pendulum.parse(data_interval_start)
        else:
            date_obj = data_interval_start

        print(f"Executing for data_interval_start: {date_obj}")

        td = TDClient(apikey=api_key)
        # Using the same logic as previous exercises
        ts = td.exchange_rate(symbol="USD/EUR", date=date_obj.isoformat())
        data = ts.as_json()
        return data

    @task
    def save_data(data: dict) -> None:
        print("Saving the data to Postgres")

        if not data:
            raise ValueError("No data received")

        # Prepare data for insertion
        symbol = data.get("symbol")
        rate = data.get("rate")

        if symbol is None or rate is None:
            raise ValueError(f"Incomplete data received: {data}")

        # Use PostgresHook to insert data
        pg_hook = PostgresHook(postgres_conn_id="postgres_storage")

        insert_sql = """
            INSERT INTO exchange_rates (symbol, rate)
            VALUES (%s, %s);
        """

        pg_hook.run(insert_sql, parameters=(symbol, rate))
        print(f"Saved rate {rate} for {symbol} to database.")

    # Retrieve API key from Airflow Variables
    api_key = Variable.get("TWELVEDATA_API_KEY")

    # Calls the task
    api_data = get_data(
        data_interval_start="{{ data_interval_start }}", api_key=api_key
    )
    save_data(api_data)


exercise_5_pipeline()
