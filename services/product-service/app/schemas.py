from pydantic import BaseModel, Field

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