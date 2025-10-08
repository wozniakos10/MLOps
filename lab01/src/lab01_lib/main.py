import argparse
import os
from dotenv import load_dotenv
from lab01_lib.settings import Settings
from yaml import safe_load


def export_envs(environment: str = "dev") -> None:
    load_dotenv(f".env.{environment}")

    with open("secrets.yaml", "r") as file:
        config = safe_load(file)

    os.environ["API_KEY"] = config.get("app").get(environment).get("API_KEY")
    os.environ["DB_PASSWORD"] = config.get("app").get(environment).get("DB_PASSWORD")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load environment variables from specified.env file.")
    parser.add_argument("--environment", type=str, default="dev", help="The environment to load (dev, test, prod)")
    args = parser.parse_args()

    export_envs(args.environment)

    settings = Settings()

    print("APP_NAME: ", settings.APP_NAME)
    print("ENVIRONMENT: ", settings.ENVIRONMENT)
    print("API_KEY: ", settings.API_KEY)
    print("DB_PASSWORD: ", settings.DB_PASSWORD)
