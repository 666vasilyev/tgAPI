from pathlib import Path
from typing import Literal

from pydantic import BaseSettings


class Config(BaseSettings):
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "telegram_comments"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: int = 123

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    SESSIONS_DIR: Path = "/accounts"

    API_ID: int = 26619802
    API_HASH: str = "962085a9248e992d28017919e4c01611"

    LOG_LEVEL: str = "INFO"

    def db_url(
            self,
            driver: Literal["db+postgresql", "postgresql+asyncpg", "postgresql+psycopg2"],
    ) -> str:
        return (
            f"{driver}://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    def broker(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    def backend(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
