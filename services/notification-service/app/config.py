from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    service_name: str = "notification-service"
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()