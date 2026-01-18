import pandas as pd
import requests
from airflow.sdk import dag, task, ObjectStoragePath
import pendulum

base = ObjectStoragePath("s3://weather-data/", conn_id="aws_default")


@dag(
    schedule=None,
    catchup=False,
    tags=["exercise_4"],
)
def exercise_4_pipeline():
    @task
    def get_data() -> dict:
        print("Fetching data from API")

        # New York temperature in 2025
        url = "https://archive-api.open-meteo.com/v1/archive?latitude=40.7143&longitude=-74.006&start_date=2025-01-01&end_date=2025-12-31&hourly=temperature_2m&timezone=auto"

        resp = requests.get(url)
        resp.raise_for_status()

        data = resp.json()
        data = {
            "time": data["hourly"]["time"],
            "temperature": data["hourly"]["temperature_2m"],
        }
        return data

    @task
    def transform(data: dict) -> pd.DataFrame:
        df = pd.DataFrame(data)
        df["temperature"] = df["temperature"].clip(lower=-20, upper=50)
        return df

    @task
    def save_data(df: pd.DataFrame, logical_date: pendulum.DateTime) -> None:
        print("Saving the data")

        # ensure the bucket exists
        base.mkdir(exist_ok=True)

        formatted_date = logical_date.format("YYYYMMDD")
        path = base / f"new_york_temperature_{formatted_date}.csv"

        with path.open("wb") as file:
            df.to_csv(file)

    api_data_pipeline = get_data()
    transformed_data = transform(api_data_pipeline)
    save_data(transformed_data, logical_date="{{ logical_date }}")


exercise_4_pipeline()
