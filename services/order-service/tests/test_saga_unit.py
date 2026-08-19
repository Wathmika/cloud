"""
Unit/integration tests for order-service's Saga orchestration logic in
app/main.py::create_order.

This is the most important file in the whole test suite: create_order IS
the Saga-pattern implementation for the system (reserve stock -> charge
payment -> confirm, with compensating actions if a later step fails) —
and, until now, it had zero test coverage anywhere in the project.

External calls (Product Catalogue lookup, Inventory reserve/release, Payment
charge, Notification) are mocked. This deliberately tests the ORCHESTRATION
LOGIC — what create_order does in response to each possible outcome — not
whether the network calls themselves succeed (that's what the k6 concurrent-
orders test and the Postman collection already prove against the real,
deployed services). Auth is stubbed via FastAPI's dependency_overrides
rather than needing a real JWT, since token verification itself is already
covered by user-service's own tests.

Place this file at services/order-service/tests/test_saga_unit.py and run
from services/order-service/: pytest tests/test_saga_unit.py -v
"""
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FAKE_USER = {"sub": "1", "role": "customer", "email": "alice@example.com"}
FAKE_CREDENTIALS = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")


def _resp(status_code, json_body=None):
    """Minimal stand-in for an httpx.Response — just the two attributes
    create_order actually reads (status_code, json())."""
    return SimpleNamespace(status_code=status_code, json=lambda: json_body or {})


def _fake_product():
    return _resp(200, {"id": "prod-1", "price": 25.50})


def _httpx_get_router(admin_ids_response=None):
    """create_order makes TWO different httpx.get calls now: the product
    lookup, and (right after creating the order) a lookup of admin user IDs
    to notify. A single return_value can't serve both — this routes by URL
    instead. Admin-ids defaults to an empty list (200, []) so the
    admin-notification block is a deterministic no-op in tests that aren't
    specifically about it."""
    admin_resp = admin_ids_response if admin_ids_response is not None else _resp(200, [])

    def _get(url, *args, **kwargs):
        if "/admin-ids" in url:
            return admin_resp
        return _fake_product()

    return _get


def _order_payload():
    return {"product_id": "prod-1", "quantity": 2}


def _release_calls(mock_post):
    return [c for c in mock_post.call_args_list if "release" in c.args[0]]


@pytest.fixture(autouse=True)
def _no_real_aws_sns():
    """create_order's final step tries real boto3 SNS publish, then falls
    back to a direct httpx.post to notification-service on failure (exactly
    the local-dev fallback pattern documented in the code). Forcing that
    failure deterministically here means the notification path always
    exercises the httpx.post mock instead of depending on whether AWS
    credentials happen to be configured on whatever machine runs this."""
    with patch("app.main.boto3.client", side_effect=Exception("no AWS credentials in tests")):
        yield


@pytest.fixture
def client():
    from app import models  # noqa: F401 (registers Order on Base)
    from app.database import Base, get_db
    from app.dependencies import bearer_scheme, get_current_user
    from app.main import app

    # StaticPool: see the comment in user-service's conftest.py — without it
    # each request gets a fresh, empty in-memory database.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    app.dependency_overrides[bearer_scheme] = lambda: FAKE_CREDENTIALS

    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ---- Happy path -------------------------------------------------------

def test_successful_order_confirms_and_stores_payment_token(client):
    with patch("app.main.httpx.get", side_effect=_httpx_get_router()), \
         patch("app.main.call_reserve_stock", return_value=_resp(200)), \
         patch("app.main.call_charge_payment",
               return_value=_resp(200, {"payment_token": "tok_abc123"})), \
         patch("app.main.httpx.post", return_value=_resp(200)) as mock_post:
        resp = client.post("/api/v1/orders", json=_order_payload())

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "confirmed"
    assert body["payment_token"] == "tok_abc123"
    # Nothing failed, so no compensating stock release should have fired.
    assert _release_calls(mock_post) == []


# ---- Product lookup failure --------------------------------------------

def test_missing_product_returns_404(client):
    with patch("app.main.httpx.get", return_value=_resp(404)):
        resp = client.post("/api/v1/orders", json=_order_payload())
    assert resp.status_code == 404


# ---- Inventory failure --------------------------------------------------

def test_insufficient_stock_cancels_order_with_no_release_needed(client):
    """409 from Inventory means nothing was ever reserved in the first
    place, so there's nothing to compensate — no release call should fire."""
    with patch("app.main.httpx.get", side_effect=_httpx_get_router()), \
         patch("app.main.call_reserve_stock", return_value=_resp(409)), \
         patch("app.main.httpx.post") as mock_post:
        resp = client.post("/api/v1/orders", json=_order_payload())

    assert resp.status_code == 409
    mock_post.assert_not_called()


def test_inventory_circuit_breaker_open_returns_503(client):
    import pybreaker

    with patch("app.main.httpx.get", side_effect=_httpx_get_router()), \
         patch("app.main.call_reserve_stock",
               side_effect=pybreaker.CircuitBreakerError("open")):
        resp = client.post("/api/v1/orders", json=_order_payload())

    assert resp.status_code == 503
    assert "too many recent failures" in resp.json()["detail"]


# ---- Payment failure triggers Saga compensation --------------------------
# These three tests are the actual Saga proof: once stock has genuinely been
# reserved, ANY failure from Payment onward must release that stock back —
# not just the obvious "payment declined" case.

def test_payment_declined_releases_stock_and_cancels_order(client):
    with patch("app.main.httpx.get", side_effect=_httpx_get_router()), \
         patch("app.main.call_reserve_stock", return_value=_resp(200)), \
         patch("app.main.call_charge_payment", return_value=_resp(402)), \
         patch("app.main.httpx.post", return_value=_resp(200)) as mock_post:
        resp = client.post("/api/v1/orders", json=_order_payload())

    assert resp.status_code == 402
    releases = _release_calls(mock_post)
    assert len(releases) == 1
    assert releases[0].kwargs["json"] == {"quantity": 2}


def test_payment_service_unreachable_releases_stock(client):
    import httpx

    with patch("app.main.httpx.get", side_effect=_httpx_get_router()), \
         patch("app.main.call_reserve_stock", return_value=_resp(200)), \
         patch("app.main.call_charge_payment",
               side_effect=httpx.ConnectError("connection refused")), \
         patch("app.main.httpx.post", return_value=_resp(200)) as mock_post:
        resp = client.post("/api/v1/orders", json=_order_payload())

    assert resp.status_code == 503
    assert len(_release_calls(mock_post)) == 1


def test_payment_circuit_breaker_open_releases_stock(client):
    import pybreaker

    with patch("app.main.httpx.get", side_effect=_httpx_get_router()), \
         patch("app.main.call_reserve_stock", return_value=_resp(200)), \
         patch("app.main.call_charge_payment",
               side_effect=pybreaker.CircuitBreakerError("open")), \
         patch("app.main.httpx.post", return_value=_resp(200)) as mock_post:
        resp = client.post("/api/v1/orders", json=_order_payload())

    assert resp.status_code == 503
    assert "too many recent failures" in resp.json()["detail"]
    assert len(_release_calls(mock_post)) == 1


# ---- Notification failure must never block the order --------------------

def test_order_still_confirms_if_notification_call_fails(client):
    """Order -> Notification is deliberately fire-and-forget (matches the
    real system's try/except around that call). A notification outage must
    never fail or roll back an otherwise-successful order."""
    import httpx

    with patch("app.main.httpx.get", side_effect=_httpx_get_router()), \
         patch("app.main.call_reserve_stock", return_value=_resp(200)), \
         patch("app.main.call_charge_payment",
               return_value=_resp(200, {"payment_token": "tok_xyz"})), \
         patch("app.main.httpx.post",
               side_effect=httpx.ConnectError("notification unreachable")):
        resp = client.post("/api/v1/orders", json=_order_payload())

    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"
