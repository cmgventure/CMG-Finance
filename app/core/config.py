from hypercorn import Config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_host: str
    app_port: int

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: str

    counter: int = 10

    squarespace_api_key: str
    stripe_api_key: str

    # tags = [
    #     "revenue", "gross", "profit", "ratio", "income", "net", "eps", "diluted",
    #     "dividends", "stock", "cash", "assets", "liabilities", "equity", "debt"
    # ]

    tags: list = []

    APSCHEDULER_JOB_TRIGGER: str = "date"
    APSCHEDULER_PROCESSING_TASK_TRIGGER_PARAMS: dict = {}

    @property
    def postgres_url(self):
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()

hypercorn_config = Config()
hypercorn_config.bind = [f"{settings.app_host}:{settings.app_port}"]
