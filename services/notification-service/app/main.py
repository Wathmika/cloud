from fastapi import FastAPI

from app import schemas

app = FastAPI(title="Notification Service")

@app.post("/api/v1/notifications/order-placed", response_model=schemas.NotificationResponse)
def notify_order_placed(event: schemas.OrderPlacedEvent):
    # Simulates sending an email/SMS confirmation.
    # In production, EventBridge triggers this as a Lambda — no direct HTTP call.
    print(f"[NOTIFICATION] Order {event.order_id} confirmed — email sent to {event.customer_email}")
    return schemas.NotificationResponse(
        detail="Notification sent",
        channel="email",
        order_id=event.order_id,
    )