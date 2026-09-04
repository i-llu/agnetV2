from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    KEY: str
    SERPAPI_KEY: str

    model_config = SettingsConfigDict(env_file=ENV_PATH)

Config = Settings()