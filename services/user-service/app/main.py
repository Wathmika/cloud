from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db, create_tables
from app import models, schemas, auth
from app.dependencies import get_current_user, require_role

app = FastAPI(title="User Management Service")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_tables()

@app.post("/api/v1/users/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        email=user.email,
        hashed_password=auth.hash_password(user.password),
        full_name=user.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/v1/users/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = auth.create_access_token(user.id, user.role, user.email)
    return schemas.Token(access_token=token)

@app.get("/api/v1/users/me")
def read_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/api/v1/users", dependencies=[Depends(require_role("admin"))])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.patch("/api/v1/users/{user_id}/role", dependencies=[Depends(require_role("admin"))])
def update_user_role(user_id: int, role: str, db: Session = Depends(get_db)):
    if role not in ("customer", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'customer' or 'admin'")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    return {"detail": f"User {user_id} role set to {role}"}

@app.get("/api/v1/users/admin-ids")
def get_admin_ids(db: Session = Depends(get_db)):
    admins = db.query(models.User).filter(models.User.role == "admin").all()
    return [{"id": a.id} for a in admins]