from fastapi import FastAPI, Depends, HTTPException

from app.database import create_table, get_inventory_table
from app import schemas
from app.dependencies import require_role
from botocore.exceptions import ClientError
from app.dependencies import require_role, get_current_user

app = FastAPI(title="Inventory Management Service")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_table()

@app.get("/api/v1/inventory", response_model=list[schemas.InventoryResponse],
         dependencies=[Depends(require_role("admin"))])
def list_inventory():
    table = get_inventory_table()
    return table.scan().get("Items", [])

@app.get("/api/v1/inventory/{product_id}", response_model=schemas.InventoryResponse,
         dependencies=[Depends(require_role("admin"))])
def get_inventory(product_id: str):
    table = get_inventory_table()
    item = table.get_item(Key={"product_id": product_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="No inventory record for this product")
    return item

@app.post("/api/v1/inventory", response_model=schemas.InventoryResponse,
          dependencies=[Depends(require_role("admin"))])
def create_inventory(item: schemas.InventoryCreate):
    table = get_inventory_table()
    table.put_item(Item=item.model_dump())
    return item

@app.put("/api/v1/inventory/{product_id}", response_model=schemas.InventoryResponse,
         dependencies=[Depends(require_role("admin"))])
def update_inventory(product_id: str, item: schemas.InventoryUpdate):
    table = get_inventory_table()
    if not table.get_item(Key={"product_id": product_id}).get("Item"):
        raise HTTPException(status_code=404, detail="No inventory record for this product")
    table.put_item(Item={"product_id": product_id, "quantity_available": item.quantity_available})
    return {"product_id": product_id, "quantity_available": item.quantity_available}

@app.post("/api/v1/inventory/{product_id}/reserve", response_model=schemas.InventoryResponse)
def reserve_stock(product_id: str, request: schemas.ReserveStockRequest,
                   current_user: dict = Depends(get_current_user)):
    table = get_inventory_table()
    try:
        result = table.update_item(
            Key={"product_id": product_id},
            UpdateExpression="SET quantity_available = quantity_available - :qty",
            ConditionExpression="quantity_available >= :qty",
            ExpressionAttributeValues={":qty": request.quantity},
            ReturnValues="ALL_NEW",
        )
        return result["Attributes"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=409, detail="Insufficient stock")
        raise

@app.post("/api/v1/inventory/{product_id}/release", response_model=schemas.InventoryResponse)
def release_stock(product_id: str, request: schemas.ReserveStockRequest,
                   current_user: dict = Depends(get_current_user)):
    table = get_inventory_table()
    result = table.update_item(
        Key={"product_id": product_id},
        UpdateExpression="SET quantity_available = quantity_available + :qty",
        ExpressionAttributeValues={":qty": request.quantity},
        ReturnValues="ALL_NEW",
    )
    return result["Attributes"]