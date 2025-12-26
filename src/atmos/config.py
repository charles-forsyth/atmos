from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GOOGLE_MAPS_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=[".env", str(Path.home() / ".config/atmos/.env")],
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
