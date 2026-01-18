import os
import pendulum
from airflow.decorators import dag, task
from dotenv import load_dotenv
import datetime

load_dotenv()


@dag(
    schedule=datetime.timedelta(minutes=1),
    catchup=False,
    tags=["exercise_5"],
)
def exercise_3_pipeline():
    # Define the task using the virtualenv decorator
    @task.virtualenv(
        requirements=["twelvedata", "pendulum", "lazy_object_proxy"],
        serializer="cloudpickle",
        system_site_packages=False,
    )
    def get_data(data_interval_start=None, api_key=None):
        from twelvedata import TDClient

        # Imports using dynamically installed libraries must be inside the function

        # Handle string input for data_interval_start if it comes from template
        if isinstance(data_interval_start, str):
            date_obj = pendulum.parse(data_interval_start)
        else:
            date_obj = data_interval_start

        print(f"Executing for data_interval_start: {date_obj}")

        td = TDClient(apikey=api_key)

        ts = td.exchange_rate(symbol="USD/EUR", date=date_obj.isoformat())
        data = ts.as_json()
        return data

    @task
    def save_data(data: dict) -> None:
        import json

        print("Saving the data")

        if not data:
            raise ValueError("No data received")

        with open("data_dag5.jsonl", "a+") as file:
            file.write(json.dumps(data))
            file.write("\n")

    # Retrieve API key from environment
    api_key = os.getenv("TWELVEDATA_API_KEY")

    # Calls the task, explicitly passing data_interval_start (as template)
    # and avoiding **kwargs to prevent context serialization issues
    api_data = get_data(
        data_interval_start="{{ data_interval_start }}", api_key=api_key
    )
    save_data(api_data)


dag = exercise_3_pipeline()
