from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    env: str = "local"
    database_url: str = "postgresql+psycopg://zenith:zenith@localhost:5432/zenith"
    redis_url: str = "redis://localhost:6379/0"

settings = Settings()
