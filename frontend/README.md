# SmartRetailX Frontend

React (Vite) frontend for the SmartRetailX microservices backend.

## Prerequisites — do these on the backend first

1. **CORS** must be enabled on all 6 backend services (`allow_origins=["http://localhost:5173"]`).
2. **Order Processing** needs `GET /api/v1/orders` and `GET /api/v1/orders/{id}` added (list/view own orders).
3. All 6 backend services must be running (Docker or locally) on their usual ports:
   `8001` user, `8002` product, `8003` inventory, `8005` order.

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Opens at `http://localhost:5173`.

## Pages

| Route | Access | Purpose |
|---|---|---|
| `/products` | Public | Browse catalogue |
| `/products/:id` | Public | Product detail, add to cart |
| `/login`, `/register` | Public | Auth |
| `/cart` | Logged in | Review cart, checkout (places one order per item) |
| `/orders` | Logged in | Order history |
| `/admin/products` | Admin only | Create/edit/delete products |
| `/admin/inventory` | Admin only | View stock, create records, restock |

## Notes

- JWT is stored in `localStorage` and decoded client-side to read `role`/`email` for UI routing — the backend still independently verifies every token on every request, this is only used for showing/hiding UI elements.
- Checkout loops through cart items and places one order per product, since Order Processing's API accepts a single product per order.
- Admin-only pages are hidden in the UI for non-admins, but the real enforcement is server-side (`require_role("admin")`) — the frontend guard is a UX convenience, not the security boundary.
