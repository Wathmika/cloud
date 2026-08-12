from decimal import Decimal
import uuid

from fastapi import FastAPI, Depends, HTTPException

from app.database import create_table, get_products_table
from app import schemas
from app.dependencies import require_role

app = FastAPI(title="Product Catalogue Service")

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

@app.get("/api/v1/products", response_model=list[schemas.ProductResponse])
def list_products():
    table = get_products_table()
    return table.scan().get("Items", [])

@app.get("/api/v1/products/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: str):
    table = get_products_table()
    item = table.get_item(Key={"product_id": product_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return item

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
    }
    table.put_item(Item=item)
    return item

@app.delete("/api/v1/products/{product_id}", dependencies=[Depends(require_role("admin"))])
def delete_product(product_id: str):
    get_products_table().delete_item(Key={"product_id": product_id})
    return {"detail": "Product deleted"}