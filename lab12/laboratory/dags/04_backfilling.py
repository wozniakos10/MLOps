import os
from datetime import datetime, timedelta

import pandas as pd
import requests
from airflow.sdk import dag, task


@dag(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    schedule=timedelta(days=7),
    catchup=True,
    tags=["example"],
)
def exercise_2_pipeline():
    @task
    def get_data(**kwargs) -> dict:
        print("Fetching data from API")
        logical_date = kwargs["logical_date"]
        print(f"Executing for date: {logical_date}")

        start_date = logical_date
        end_date = start_date + timedelta(days=6)

        # Clamp to Jan 31st to strictly follow the requirement
        limit_date = start_date.replace(year=2025, month=1, day=31)

        if end_date > limit_date:
            end_date = limit_date

        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # New York daily forecast validation for the next week (7 days inclusive)
        # Using Historical Forecast API as requested
        url = (
            "https://historical-forecast-api.open-meteo.com/v1/forecast?"
            "latitude=40.7143&longitude=-74.006&"
            f"start_date={start_date_str}&end_date={end_date_str}&"
            "daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        )

        # Add timeout to prevent hanging
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        return {
            "time": data["daily"]["time"],
            "max_temp": data["daily"]["temperature_2m_max"],
            "min_temp": data["daily"]["temperature_2m_min"],
        }

    @task
    def transform(data: dict) -> pd.DataFrame:
        df = pd.DataFrame(data)
        return df

    @task
    def save_data(df: pd.DataFrame) -> None:
        print("Saving the data")
        file_path = "data_04.csv"
        # Append to file, write header only if file does not exist
        header = not os.path.exists(file_path)
        df.to_csv(file_path, mode="a", header=header, index=False)

    api_data_pipeline = get_data()
    transformed_data = transform(api_data_pipeline)  # type: ignore
    save_data(transformed_data)  # type: ignore


exercise_2_pipeline()
