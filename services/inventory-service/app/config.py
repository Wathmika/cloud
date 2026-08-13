from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    dynamodb_endpoint: str = "http://localhost:8000"
    aws_region: str = "ap-south-1"
    aws_access_key_id: str = "local"
    aws_secret_access_key: str = "local"
    inventory_table_name: str = "Inventory"
    jwt_public_key_path: str = "keys/public.pem"
    jwt_algorithm: str = "RS256"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()