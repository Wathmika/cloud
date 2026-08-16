from pydantic import BaseModel, Field
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float = Field(gt=0)
    category: str

class ProductResponse(BaseModel):
    product_id: str
    name: str
    description: str
    price: float
    category: str
    original_price: float | None = None
    discount_percentage: float | None = None

class PromotionCreate(BaseModel):
    discount_percentage: float = Field(gt=0, le=100)
    start_time: datetime
    end_time: datetime