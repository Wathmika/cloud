from decimal import Decimal
import boto3
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
from fastapi.security import HTTPAuthorizationCredentials
from app.dependencies import get_current_user, bearer_scheme

from app.database import get_db, create_tables
from app import models, schemas
from app.dependencies import get_current_user, require_role
from app.config import settings


app = FastAPI(title="Order Processing Service")
from fastapi.middleware.cors import CORSMiddleware

import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

inventory_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30)
payment_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30)

@inventory_breaker
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
       retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
       reraise=True)

def call_reserve_stock(product_id, quantity, token):
    resp = httpx.post(
        f"{settings.inventory_service_url}/api/v1/inventory/{product_id}/reserve",
        json={"quantity": quantity},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    if resp.status_code >= 500:
        resp.raise_for_status()
    return resp

@payment_breaker
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
       retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
       reraise=True)
def call_charge_payment(order_id, amount, token):
    resp = httpx.post(
        f"{settings.payment_service_url}/api/v1/payments",
        json={"order_id": order_id, "amount": amount, "currency": "LKR"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    if resp.status_code >= 500:
        resp.raise_for_status()
    return resp

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

    # Create the order first, as "pending" — gives it a real ID before
    # Payment is called, so payments can trace back to the correct order.
    new_order = models.Order(
        user_id=current_user["sub"],
        product_id=order.product_id,
        quantity=order.quantity,
        total_amount=total,
        status="pending",
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    try:
        admin_resp = httpx.get(f"{settings.user_service_url}/api/v1/users/admin-ids", timeout=5)
        if admin_resp.status_code == 200:
            for admin in admin_resp.json():
                db.add(models.Notification(
                    user_id=str(admin["id"]),
                    message=f"New order #{new_order.id} placed — needs processing.",
                ))
            db.commit()
    except httpx.RequestError as e:
        print(f"[WARNING] Could not notify admins for order {new_order.id}: {e}")

    try:
        reserve_resp = call_reserve_stock(order.product_id, order.quantity, credentials.credentials)
    except pybreaker.CircuitBreakerError:
        new_order.status = "cancelled"; db.commit()
        raise HTTPException(status_code=503, detail="Inventory service temporarily unavailable — too many recent failures")
    except (httpx.RequestError, httpx.HTTPStatusError):
        new_order.status = "cancelled"; db.commit()
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

    if reserve_resp.status_code == 409:
        new_order.status = "cancelled"; db.commit()
        raise HTTPException(status_code=409, detail="Insufficient stock")
    if reserve_resp.status_code != 200:
        new_order.status = "cancelled"; db.commit()
        raise HTTPException(status_code=502, detail="Inventory service error")

    try:
        payment_resp = call_charge_payment(str(new_order.id), float(total), credentials.credentials)
    except pybreaker.CircuitBreakerError:
        httpx.post(f"{settings.inventory_service_url}/api/v1/inventory/{order.product_id}/release",
                    json={"quantity": order.quantity},
                    headers={"Authorization": f"Bearer {credentials.credentials}"})
        new_order.status = "cancelled"; db.commit()
        raise HTTPException(status_code=503, detail="Payment service temporarily unavailable — too many recent failures")
    except (httpx.RequestError, httpx.HTTPStatusError):
        httpx.post(f"{settings.inventory_service_url}/api/v1/inventory/{order.product_id}/release",
                    json={"quantity": order.quantity},
                    headers={"Authorization": f"Bearer {credentials.credentials}"})
        new_order.status = "cancelled"; db.commit()
        raise HTTPException(status_code=503, detail="Payment service unavailable")

    if payment_resp.status_code != 200:
        httpx.post(f"{settings.inventory_service_url}/api/v1/inventory/{order.product_id}/release",
                    json={"quantity": order.quantity},
                    headers={"Authorization": f"Bearer {credentials.credentials}"})
        new_order.status = "cancelled"; db.commit()
        raise HTTPException(status_code=402, detail="Payment failed")

    payment_token = payment_resp.json()["payment_token"]
    new_order.status = "confirmed"
    new_order.payment_token = payment_token
    db.commit()
    db.refresh(new_order)

    try:
        sns = boto3.client("sns", region_name="ap-south-1")
        sns.publish(
            TopicArn="arn:aws:sns:ap-south-1:961776040849:smartretailx-order-events",
            Message=f'{{"order_id": "{new_order.id}", "customer_email": "{current_user["email"]}"}}',
        )
    except Exception as e:
        # Local dev has no AWS credentials, so SNS publish fails by design here —
        # fall back to calling Notification directly over the docker-compose network.
        print(f"[INFO] SNS publish unavailable ({e}), falling back to direct call")
        try:
            httpx.post(
                f"{settings.notification_service_url}/api/v1/notifications/order-placed",
                json={"order_id": str(new_order.id), "customer_email": current_user["email"]},
                timeout=5,
            )
        except httpx.RequestError as fallback_error:
            print(f"[WARNING] Notification fallback also failed: {fallback_error}")

    return new_order

@app.get("/api/v1/debug/breaker-status")
def breaker_status():
    return {
        "payment_breaker_state": str(payment_breaker.current_state),
        "payment_breaker_fail_counter": payment_breaker.fail_counter,
        "inventory_breaker_state": str(inventory_breaker.current_state),
        "inventory_breaker_fail_counter": inventory_breaker.fail_counter,
    }

@app.get("/api/v1/orders", response_model=list[schemas.OrderResponse])
def list_my_orders(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return db.query(models.Order).filter(models.Order.user_id == current_user["sub"]).all()

VALID_STATUSES = ["confirmed", "packed", "shipped", "delivered", "cancelled"]

@app.get("/api/v1/orders/all", response_model=list[schemas.OrderResponse])
def list_all_orders(db: Session = Depends(get_db), current_user: dict = Depends(require_role("admin"))):
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()

@app.get("/api/v1/orders/{order_id}", response_model=schemas.OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user["sub"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this order")
    return order


@app.patch("/api/v1/orders/{order_id}/status", response_model=schemas.OrderResponse)
def update_order_status(order_id: int, update: schemas.StatusUpdate, db: Session = Depends(get_db),
                         current_user: dict = Depends(require_role("admin"))):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if update.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    order.status = update.status
    if update.status == "shipped" and not order.tracking_number:
        import uuid
        order.tracking_number = f"TRK-{uuid.uuid4().hex[:10].upper()}"
    db.commit()
    db.refresh(order)

    new_notif = models.Notification(
        user_id=order.user_id,
        message=f"Your order #{order.id} is now {update.status}.",
    )
    db.add(new_notif)
    db.commit()

    return order

@app.get("/api/v1/notifications", response_model=list[schemas.NotificationOut])
def get_my_notifications(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return db.query(models.Notification).filter(
        models.Notification.user_id == current_user["sub"]
    ).order_by(models.Notification.created_at.desc()).all()

@app.patch("/api/v1/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    notif = db.query(models.Notification).filter(
        models.Notification.id == notif_id, models.Notification.user_id == current_user["sub"]
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"detail": "Marked as read"}
    