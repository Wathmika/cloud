from decimal import Decimal
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException

from app.database import create_promotions_table, create_table, get_products_table, get_promotions_table
from app import schemas
from app.dependencies import require_role

app = FastAPI(title="Product Catalogue Service")

from fastapi.middleware.cors import CORSMiddleware

def apply_discount(item: dict) -> dict:
    discount = get_active_discount(item["product_id"])
    if discount:
        item["original_price"] = item["price"]
        item["price"] = round(float(item["price"]) * (1 - discount / 100), 2)
        item["discount_percentage"] = discount
    return item

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_table()
    create_promotions_table()

@app.get("/api/v1/products", response_model=list[schemas.ProductResponse])
def list_products():
    table = get_products_table()
    items = table.scan().get("Items", [])
    return [apply_discount(dict(item)) for item in items]

@app.get("/api/v1/products/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: str):
    table = get_products_table()
    item = table.get_item(Key={"product_id": product_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return apply_discount(dict(item))

@app.post("/api/v1/products", response_model=schemas.ProductResponse,
          dependencies=[Depends(require_role("admin"))])
def create_product(product: schemas.ProductCreate):
    table = get_products_table()
    item = {
        "product_id": str(uuid.uuid4()),
        "name": product.name,
        "description": product.description,
        "price": Decimal(str(product.price)),
        "category": product.category,
        "image_url": product.image_url,
    }
    table.put_item(Item=item)
    return item

@app.put("/api/v1/products/{product_id}", response_model=schemas.ProductResponse,
         dependencies=[Depends(require_role("admin"))])
def update_product(product_id: str, product: schemas.ProductCreate):
    table = get_products_table()
    if not table.get_item(Key={"product_id": product_id}).get("Item"):
        raise HTTPException(status_code=404, detail="Product not found")
    item = {
        "product_id": product_id,
        "name": product.name,
        "description": product.description,
        "price": Decimal(str(product.price)),
        "category": product.category,
        "image_url": product.image_url,
    }
    table.put_item(Item=item)
    return item

@app.delete("/api/v1/products/{product_id}", dependencies=[Depends(require_role("admin"))])
def delete_product(product_id: str):
    get_products_table().delete_item(Key={"product_id": product_id})
    return {"detail": "Product deleted"}

def get_active_discount(product_id: str) -> float | None:
    table = get_promotions_table()
    item = table.get_item(Key={"product_id": product_id}).get("Item")
    if not item:
        return None
    now = datetime.utcnow()
    start = datetime.fromisoformat(item["start_time"])
    end = datetime.fromisoformat(item["end_time"])
    # Normalize to naive UTC regardless of whether the stored string had timezone info
    if start.tzinfo is not None:
        start = start.replace(tzinfo=None)
    if end.tzinfo is not None:
        end = end.replace(tzinfo=None)
    if start <= now <= end:
        return float(item["discount_percentage"])
    return None

@app.post("/api/v1/products/{product_id}/promotions", dependencies=[Depends(require_role("admin"))])
def create_promotion(product_id: str, promo: schemas.PromotionCreate):
    table = get_promotions_table()
    table.put_item(Item={
        "product_id": product_id,
        "discount_percentage": Decimal(str(promo.discount_percentage)),
        "start_time": promo.start_time.isoformat(),
        "end_time": promo.end_time.isoformat(),
    })
    return {"detail": "Promotion created"}