from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  KEY:str
  SERPAPI_KEY:str

  model_config = SettingsConfigDict(
    env_file=".env",
    extra="ignore"
  )

Config = Settings()