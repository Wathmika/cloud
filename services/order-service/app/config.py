from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql://order_service:devpassword@localhost:5433/order_db"
    jwt_public_key_path: str = "keys/public.pem"
    jwt_algorithm: str = "RS256"

    user_service_url: str = "http://localhost:8001"
    product_service_url: str = "http://localhost:8002"
    inventory_service_url: str = "http://localhost:8003"
    payment_service_url: str = "http://localhost:8004"
    notification_service_url: str = "http://localhost:8006"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()