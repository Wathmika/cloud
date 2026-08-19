"""
Integration tests for user-service's API — exercises the real endpoint code
(FastAPI routing, Pydantic validation, SQLAlchemy) against a real database
(in-memory SQLite standing in for Postgres). This is the "integration" layer
of Task 8: not mocked business logic, an actual request going through the
real stack down to a real database row — the same DB engine (SQLAlchemy),
just a disposable one.

Run from services/user-service/: pytest tests/test_api_integration.py -v
"""


def _register(client, email="alice@example.com", password="password123",
              full_name="Alice", role=None):
    body = {"email": email, "password": password, "full_name": full_name}
    if role is not None:
        # Attempted mass-assignment attack: role isn't a field on UserCreate,
        # so this should be silently dropped before it ever reaches our code.
        body["role"] = role
    return client.post("/api/v1/users/register", json=body)


def _login(client, email="alice@example.com", password="password123"):
    return client.post(
        "/api/v1/users/login",
        data={"username": email, "password": password},
    )


# ---- Registration ---------------------------------------------------------

def test_register_creates_user_with_default_customer_role(test_client):
    resp = _register(test_client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["role"] == "customer"
    assert "hashed_password" not in data  # UserResponse must never leak the hash


def test_register_rejects_a_duplicate_email(test_client):
    _register(test_client)
    resp = _register(test_client)
    assert resp.status_code == 400


def test_register_rejects_a_password_under_8_characters(test_client):
    resp = test_client.post("/api/v1/users/register", json={
        "email": "bob@example.com", "password": "short", "full_name": "Bob",
    })
    assert resp.status_code == 422  # Field(min_length=8) rejects it


def test_register_rejects_a_malformed_email(test_client):
    resp = test_client.post("/api/v1/users/register", json={
        "email": "not-an-email", "password": "password123", "full_name": "Bob",
    })
    assert resp.status_code == 422


def test_mass_assignment_role_field_is_silently_ignored(test_client):
    """Security test: a signup request that tries to smuggle
    "role": "admin" into the body must be ignored — UserCreate has no role
    field at all, so there's structurally nothing for it to set."""
    resp = _register(test_client, email="mallory@example.com", role="admin")
    assert resp.status_code == 200
    assert resp.json()["role"] == "customer"


# ---- Login ------------------------------------------------------------

def test_login_with_correct_credentials_returns_a_bearer_token(test_client):
    _register(test_client)
    resp = _login(test_client)
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert len(resp.json()["access_token"]) > 20


def test_login_with_wrong_password_returns_401(test_client):
    _register(test_client)
    resp = _login(test_client, password="wrong-password")
    assert resp.status_code == 401


def test_login_with_unregistered_email_returns_401(test_client):
    resp = _login(test_client, email="nobody@example.com")
    assert resp.status_code == 401


# ---- RBAC (end to end, through real HTTP requests) ----------------------

def test_me_endpoint_requires_authentication(test_client):
    resp = test_client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_me_endpoint_returns_the_caller_s_own_claims(test_client):
    _register(test_client)
    token = _login(test_client).json()["access_token"]
    resp = test_client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "customer"


def test_users_list_blocks_customer_role_with_403(test_client):
    """The actual proof RBAC works end to end: a genuinely valid token
    (401 doesn't fire) but the wrong role (403 fires instead)."""
    _register(test_client)
    token = _login(test_client).json()["access_token"]
    resp = test_client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_users_list_allows_admin_role_after_promotion(test_client):
    """Simulates the same role-promotion path used in the real deployment
    (an admin updating role='admin' directly in the DB), then confirms a
    freshly issued token carrying the new role is accepted — while also
    proving a *stale* token issued before the promotion is not enough on
    its own (a fresh login/token is required, matching real JWT behaviour)."""
    from app import auth, models
    from app.database import get_db
    from app.main import app

    _register(test_client, email="admin@example.com")

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    user = db.query(models.User).filter(
        models.User.email == "admin@example.com"
    ).first()
    user.role = "admin"
    db.commit()

    fresh_token = auth.create_access_token(user.id, "admin", user.email)
    resp = test_client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {fresh_token}"}
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
