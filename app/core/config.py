import os
import sys

from dotenv import load_dotenv
from hypercorn import Config

load_dotenv()


class Settings:
    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = os.getenv("APP_PORT", "8080")

    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_db = os.getenv("POSTGRES_DB")
    postgres_host = os.getenv("POSTGRES_HOST")
    postgres_port = os.getenv("POSTGRES_PORT")

    postgres_url = (
        f"postgresql+asyncpg://{postgres_user}:{postgres_password}"
        f"@{postgres_host}:{postgres_port}/{postgres_db}"
    )

    counter = int(os.getenv("COUNTER", 10))

    squarespace_api_key = os.getenv("SQUARESPACE_API_KEY")
    stripe_api_key = os.getenv("STRIPE_API_KEY")

    # tags = [
    #     "revenue", "gross", "profit", "ratio", "income", "net", "eps", "diluted",
    #     "dividends", "stock", "cash", "assets", "liabilities", "equity", "debt"
    # ]

    tags = []


settings = Settings()

hypercorn_config = Config()
hypercorn_config.bind = [f"{settings.app_host}:{settings.app_port}"]
