from pydantic_settings import BaseSettings
from pathlib import Path

class Config(BaseSettings):

    REDIS_HOST: str
    REDIS_PORT: int 

    SESSIONS_DIR: Path
    MEDIA_DIR: str

    API_ID: int
    API_HASH: str 

    LOG_LEVEL: str 

    SYNC_DB_URL: str

    @property
    def broker(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    @property
    def backend(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"
    
    class Config:
        env_file = ".env"

config = Config()