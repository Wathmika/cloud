from datetime import datetime
from pydantic import BaseModel, Field

class PaymentCreate(BaseModel):
    order_id: str
    amount: float = Field(gt=0)
    currency: str = "GBP"

class PaymentResponse(BaseModel):
    id: int
    order_id: str
    amount: float
    currency: str
    payment_token: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True