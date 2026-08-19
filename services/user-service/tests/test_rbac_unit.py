"""
Unit tests for app/dependencies.py — the RBAC layer (require_role,
get_current_user). Dependency functions are called directly, bypassing
FastAPI's injection — no database, no network, no HTTP layer.

Run: pytest tests/test_rbac_unit.py -v
"""
import pytest
from fastapi import HTTPException


def test_require_role_allows_a_matching_role():
    from app.dependencies import require_role

    checker = require_role("admin")
    result = checker(user={"sub": "1", "role": "admin"})
    assert result["role"] == "admin"


def test_require_role_blocks_the_wrong_role_with_403():
    """This is the actual proof RBAC blocks, not just allows — a valid but
    insufficiently-privileged user must get 403, not a silent pass-through."""
    from app.dependencies import require_role

    checker = require_role("admin")
    with pytest.raises(HTTPException) as exc_info:
        checker(user={"sub": "2", "role": "customer"})
    assert exc_info.value.status_code == 403


def test_require_role_accepts_any_of_several_allowed_roles():
    from app.dependencies import require_role

    checker = require_role("admin", "staff")
    result = checker(user={"sub": "3", "role": "staff"})
    assert result["role"] == "staff"


def test_get_current_user_rejects_a_garbage_token_with_401():
    from app.dependencies import get_current_user

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="not-a-real-jwt")
    assert exc_info.value.status_code == 401


def test_get_current_user_accepts_a_validly_issued_token():
    from app.auth import create_access_token
    from app.dependencies import get_current_user

    token = create_access_token(user_id=7, role="customer", email="bob@example.com")
    payload = get_current_user(token=token)
    assert payload["sub"] == "7"
    assert payload["role"] == "customer"
    assert payload["email"] == "bob@example.com"
