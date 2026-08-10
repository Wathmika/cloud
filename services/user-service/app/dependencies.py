from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose.exceptions import JWTError

from app import auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return auth.decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_role(*allowed_roles):
    def checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker