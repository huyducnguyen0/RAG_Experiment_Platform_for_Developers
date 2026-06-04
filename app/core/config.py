from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""

    APP_ENV: str = "development"
    DEBUG: bool = Field(default=True, validation_alias="APP_DEBUG")

    CHROMA_DIR: str = "./chroma_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
