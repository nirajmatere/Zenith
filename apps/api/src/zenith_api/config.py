from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    env: str = "local"
    database_url: str = Field(
        default="postgresql+psycopg://zenith:zenith@localhost:5432/zenith",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0", 
        validation_alias="REDIS_URL"
    )
    
    jwt_secret: str = Field(
        default="dev-change-me", 
        validation_alias="JWT_SECRET"
    )
    jwt_access_minutes: int = 30
    jwt_refresh_days: int = 30

settings = Settings()
