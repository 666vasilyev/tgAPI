from pydantic import BaseSettings
from pathlib import Path


class Config(BaseSettings):

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    SESSIONS_DIR: Path = "accounts"
    MEDIA_DIR: str = "media/"

    API_ID: int = 1506593
    API_HASH: str = "74b07d38a04337651c59ca46bb3e9ec6"

    LOG_LEVEL: str = "INFO"

    SYNC_DB_URL: str = "sqlite:///database.db"

    def broker(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    def backend(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"