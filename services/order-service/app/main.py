from decimal import Decimal

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
from fastapi.security import HTTPAuthorizationCredentials
from app.dependencies import get_current_user, bearer_scheme

from app.database import get_db, create_tables
from app import models, schemas
from app.dependencies import get_current_user
from app.config import settings

app = FastAPI(title="Order Processing Service")

@app.on_event("startup")
def on_startup():
    create_tables()


@app.post("/api/v1/orders", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user),
                  credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):

    product_resp = httpx.get(f"{settings.product_service_url}/api/v1/products/{order.product_id}")
    if product_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Product not found")
    product = product_resp.json()

    total = Decimal(str(product["price"])) * order.quantity

    try:
        reserve_resp = httpx.post(
            f"{settings.inventory_service_url}/api/v1/inventory/{order.product_id}/reserve",
            json={"quantity": order.quantity},
            headers={"Authorization": f"Bearer {credentials.credentials}"},
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

    try:
        payment_resp = httpx.post(
            f"{settings.payment_service_url}/api/v1/payments",
            json={"order_id": "pending", "amount": float(total), "currency": "GBP"},
            headers={"Authorization": f"Bearer {credentials.credentials}"},
        )
    except httpx.RequestError:
        httpx.post(
            f"{settings.inventory_service_url}/api/v1/inventory/{order.product_id}/release",
            json={"quantity": order.quantity},
            headers={"Authorization": f"Bearer {credentials.credentials}"},
        )
        raise HTTPException(status_code=503, detail="Payment service unavailable")

    if payment_resp.status_code != 200:
        httpx.post(
            f"{settings.inventory_service_url}/api/v1/inventory/{order.product_id}/release",
            json={"quantity": order.quantity},
            headers={"Authorization": f"Bearer {credentials.credentials}"},
        )
        raise HTTPException(status_code=402, detail="Payment failed")

    payment_token = payment_resp.json()["payment_token"]

    if reserve_resp.status_code == 409:
        raise HTTPException(status_code=409, detail="Insufficient stock")
    if reserve_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Inventory service error")

    
    new_order = models.Order(
        user_id=current_user["sub"],
        product_id=order.product_id,
        quantity=order.quantity,
        total_amount=total,
        payment_token=payment_token,
        status="confirmed",
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    try:
        httpx.post(
            f"{settings.notification_service_url}/api/v1/notifications/order-placed",
            json={"order_id": str(new_order.id), "customer_email": current_user["email"]},
        )
    except httpx.RequestError:
        pass  # best-effort — order already succeeded, notification failure shouldn't block the response

    return new_order

    