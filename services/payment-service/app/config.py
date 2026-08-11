from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql://payment_service:devpassword@localhost:5434/payment_db"
    jwt_public_key_path: str = "keys/public.pem"
    jwt_algorithm: str = "RS256"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()