from datetime import datetime
from pydantic import BaseModel, Field

class OrderCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)

class OrderResponse(BaseModel):
    id: int
    user_id: str
    product_id: str
    quantity: int
    total_amount: float
    payment_token: str | None
    status: str
    created_at: datetime
    tracking_number: str | None

    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: str

class NotificationOut(BaseModel):
    id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True