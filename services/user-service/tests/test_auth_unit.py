"""
Unit tests for app/auth.py — password hashing and JWT issuance/verification.
No database, no network, no HTTP layer. Run: pytest tests/test_auth_unit.py -v
"""
import pytest
from jose.exceptions import ExpiredSignatureError, JWTError


def test_hash_password_produces_a_bcrypt_hash_not_plaintext():
    from app.auth import hash_password

    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert hashed.startswith("$2b$")  # bcrypt hash format marker


def test_verify_password_accepts_the_correct_password():
    from app.auth import hash_password, verify_password

    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed) is True


def test_verify_password_rejects_the_wrong_password():
    from app.auth import hash_password, verify_password

    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False


def test_create_access_token_embeds_subject_role_and_email():
    from app.auth import create_access_token, decode_access_token

    token = create_access_token(user_id=42, role="admin", email="admin@example.com")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"
    assert payload["email"] == "admin@example.com"


def test_decode_access_token_rejects_a_tampered_signature():
    """Security test: flip one character of a validly-issued token and
    confirm the signature check actually catches it, rather than silently
    trusting the payload."""
    from app.auth import create_access_token, decode_access_token

    token = create_access_token(user_id=1, role="customer", email="alice@example.com")
    header, payload, signature = token.split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]
    tampered = f"{header}.{payload}.{flipped}"
    with pytest.raises(JWTError):
        decode_access_token(tampered)


def test_decode_access_token_rejects_an_expired_token(monkeypatch):
    """Security test: a token whose exp has already passed must be rejected
    even though it was validly signed with the right key."""
    from app import auth

    monkeypatch.setattr(auth.settings, "access_token_expire_minutes", -1)
    token = auth.create_access_token(user_id=1, role="customer", email="alice@example.com")
    with pytest.raises(ExpiredSignatureError):
        auth.decode_access_token(token)
