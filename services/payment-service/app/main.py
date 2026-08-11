import uuid

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import get_db, create_tables
from app import models, schemas
from app.dependencies import get_current_user

app = FastAPI(title="Payment Service")

@app.on_event("startup")
def on_startup():
    create_tables()

def simulate_gateway_charge(amount: float) -> str:
    return f"tok_{uuid.uuid4().hex[:16]}"

@app.post("/api/v1/payments", response_model=schemas.PaymentResponse)
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db),
                    current_user: dict = Depends(get_current_user)):
    token = simulate_gateway_charge(payment.amount)

    new_payment = models.Payment(
        order_id=payment.order_id,
        amount=payment.amount,
        currency=payment.currency,
        payment_token=token,
        status="completed",
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

@app.get("/api/v1/payments/{payment_id}", response_model=schemas.PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db),
                 current_user: dict = Depends(get_current_user)):
    return db.query(models.Payment).filter(models.Payment.id == payment_id).first()