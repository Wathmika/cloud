"""
Seeds SmartRetailX with realistic test data by calling the real APIs —
not direct database inserts. Run this once after all services are up.

Usage:
    python seed_data.py
"""

import subprocess
import sys

import requests

USER_API = "http://localhost:8001"
PRODUCT_API = "http://localhost:8002"
INVENTORY_API = "http://localhost:8003"

ADMIN_EMAIL = "admin@smartretailx.com"
ADMIN_PASSWORD = "AdminPass123"
CUSTOMER_EMAIL = "customer@smartretailx.com"
CUSTOMER_PASSWORD = "CustomerPass123"

PRODUCTS = [
    {"name": "Wireless Mouse", "description": "Ergonomic wireless mouse", "price": 25.99, "category": "Electronics"},
    {"name": "Mechanical Keyboard", "description": "RGB backlit mechanical keyboard", "price": 79.99, "category": "Electronics"},
    {"name": "USB-C Hub", "description": "7-in-1 USB-C hub adapter", "price": 34.50, "category": "Electronics"},
    {"name": "Running Shoes", "description": "Lightweight running shoes, size 9", "price": 64.99, "category": "Footwear"},
    {"name": "Yoga Mat", "description": "Non-slip 6mm yoga mat", "price": 22.00, "category": "Fitness"},
    {"name": "Ceramic Mug", "description": "350ml ceramic coffee mug", "price": 9.99, "category": "Homeware"},
]


def register(email, password, full_name):
    resp = requests.post(f"{USER_API}/api/v1/users/register", json={
        "email": email, "password": password, "full_name": full_name,
    })
    if resp.status_code == 200:
        print(f"  Registered {email}")
    elif resp.status_code == 400:
        print(f"  {email} already exists — skipping")
    else:
        print(f"  Unexpected response registering {email}: {resp.status_code} {resp.text}")
        sys.exit(1)


def promote_to_admin(email):
    print(f"  Promoting {email} to admin...")
    subprocess.run([
        "docker", "exec", "user-db", "psql", "-U", "user_service", "-d", "user_db",
        "-c", f"UPDATE users SET role='admin' WHERE email='{email}';",
    ], check=True)


def login(email, password):
    resp = requests.post(
        f"{USER_API}/api/v1/users/login",
        data={"username": email, "password": password},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def main():
    print("1. Registering admin and customer accounts...")
    register(ADMIN_EMAIL, ADMIN_PASSWORD, "Admin User")
    register(CUSTOMER_EMAIL, CUSTOMER_PASSWORD, "Test Customer")

    print("\n2. Promoting admin account...")
    promote_to_admin(ADMIN_EMAIL)

    print("\n3. Logging in as admin...")
    admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    headers = {"Authorization": f"Bearer {admin_token}"}

    print("\n4. Creating products and inventory...")
    created = []
    for p in PRODUCTS:
        resp = requests.post(f"{PRODUCT_API}/api/v1/products", json=p, headers=headers)
        resp.raise_for_status()
        product = resp.json()
        created.append(product)

        stock = 50
        requests.post(
            f"{INVENTORY_API}/api/v1/inventory",
            json={"product_id": product["product_id"], "quantity_available": stock},
            headers=headers,
        ).raise_for_status()

        print(f"  {product['name']:<22} £{product['price']:<8} stock={stock}  id={product['product_id']}")

    print("\nDone. Reference data:")
    print(f"  Admin login:    {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  Customer login: {CUSTOMER_EMAIL} / {CUSTOMER_PASSWORD}")
    print(f"  {len(created)} products created, each with 50 units in stock")


if __name__ == "__main__":
    main()
