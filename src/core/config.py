from pydantic_settings import BaseSettings
from pathlib import Path

class Config(BaseSettings):

    REDIS_HOST: str
    REDIS_PORT: int 

    SESSIONS_DIR: Path
    MEDIA_DIR: str

    API_ID: int
    API_HASH: str

    API_PORT: int

    LOG_LEVEL: str 

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    @property
    def broker(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    @property
    def backend(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"
    
    @property
    def DATABASE_URL(self):
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    
    class Config:
        env_file = ".env"
