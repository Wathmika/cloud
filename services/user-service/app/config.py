from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql://user_service:devpassword@localhost:5432/user_db"
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"
    jwt_algorithm: str = "RS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()