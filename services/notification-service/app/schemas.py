from pydantic import BaseModel, EmailStr

class OrderPlacedEvent(BaseModel):
    order_id: str
    customer_email: EmailStr
    status: str = "placed"

class NotificationResponse(BaseModel):
    detail: str
    channel: str
    order_id: str