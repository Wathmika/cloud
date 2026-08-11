from jose import jwt

from app.config import settings

def decode_access_token(token: str) -> dict:
    with open(settings.jwt_public_key_path, "r") as f:
        public_key = f.read()
    return jwt.decode(token, public_key, algorithms=[settings.jwt_algorithm])