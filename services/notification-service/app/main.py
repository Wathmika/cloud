from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx as httpx_client

from fastapi import HTTPException

from app import schemas

app = FastAPI(title="Notification Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/notifications/order-placed")
async def notify_order_placed(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or empty JSON body")

    if body.get("Type") == "SubscriptionConfirmation":
        confirm_url = body.get("SubscribeURL")
        httpx_client.get(confirm_url)
        return {"detail": "Subscription confirmed"}

    if body.get("Type") == "Notification":
        event = schemas.OrderPlacedEvent.model_validate_json(body["Message"])
    else:
        event = schemas.OrderPlacedEvent(**body)

    print(f"[NOTIFICATION] Order {event.order_id} confirmed — email sent to {event.customer_email}")
    return {"detail": "Notification sent", "channel": "email", "order_id": event.order_id}