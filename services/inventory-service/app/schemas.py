from pydantic import BaseModel, Field

class InventoryCreate(BaseModel):
    product_id: str
    quantity_available: int = Field(ge=0)

class InventoryUpdate(BaseModel):
    quantity_available: int = Field(ge=0)

class InventoryResponse(BaseModel):
    product_id: str
    quantity_available: int

class ReserveStockRequest(BaseModel):
    quantity: int = Field(gt=0)