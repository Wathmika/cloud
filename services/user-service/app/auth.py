from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

from app.config import settings
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def _load_key(path: str, env_var: str) -> str:
    content = os.environ.get(env_var)
    if content:
        return content
    with open(path, "r") as f:
        return f.read()

def create_access_token(user_id: int, role: str, email: str) -> str:
    private_key = _load_key(settings.jwt_private_key_path, "JWT_PRIVATE_KEY")
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "email": email, "exp": expire}
    return jwt.encode(payload, private_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    public_key = _load_key(settings.jwt_public_key_path, "JWT_PUBLIC_KEY")
    return jwt.decode(token, public_key, algorithms=[settings.jwt_algorithm])