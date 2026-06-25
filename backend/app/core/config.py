from functools import lru_cache

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "InterviewLoop-v2"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: PostgresDsn = "postgresql+psycopg://interviewloop:interviewloop@postgres:5432/interviewloop"
    redis_url: RedisDsn = "redis://redis:6379/0"
    ollama_base_url: str = "http://ollama:11434"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
