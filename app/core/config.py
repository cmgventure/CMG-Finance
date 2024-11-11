from hypercorn import Config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_HOST: str
    APP_PORT: int

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str

    COUNTER: int = 10

    SQUARESPACE_API_KEY: str
    STRIPE_API_KEY: str

    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"

    AWS_REGION: str
    AWSLOGS_GROUP: str
    AWSLOGS_STREAM: str

    # Operands can be words separated by spaces, hyphens, or underscores.
    # They can also be integers or floating-point numbers with a . symbol
    CUSTOM_FORMULA_OPERAND_PATTERN: str = r"(?:\b[a-zA-Z_]+(?:[\s_-][a-zA-Z_]+)*\b|\b\d+(?:\.\d+)?\b)"
    # Operators can be (+) or (-) symbols
    CUSTOM_FORMULA_OPERATOR_PATTERN: str = r"\(\+\)|\(\-\)"

    @property
    def postgres_url(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings(_env_file=".env")

hypercorn_config = Config()
hypercorn_config.bind = [f"{settings.APP_HOST}:{settings.APP_PORT}"]
