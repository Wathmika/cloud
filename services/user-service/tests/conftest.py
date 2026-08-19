"""
Shared pytest fixtures for user-service tests.

Place this whole `tests/` folder at services/user-service/tests/ and run
from inside services/user-service/ (same working-directory assumption the
app itself already makes for keys/private.pem):

    cd services/user-service
    pip install -r requirements.txt -r tests/requirements-test.txt
    pytest tests/ -v
"""
import os
import sys

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Make "app" importable when pytest runs from services/user-service/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def rsa_keypair(tmp_path_factory):
    """A throwaway RS256 keypair for JWT tests, so tests never touch (or
    depend on) the real keys/private.pem used by the live deployment."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    d = tmp_path_factory.mktemp("keys")
    priv_path = d / "private.pem"
    pub_path = d / "public.pem"
    priv_path.write_bytes(priv_pem)
    pub_path.write_bytes(pub_pem)
    return str(priv_path), str(pub_path)


@pytest.fixture(autouse=True)
def _patch_key_paths(rsa_keypair, monkeypatch):
    """Point every test at the throwaway keypair instead of the real one.

    app/auth.py's _load_key() checks an env var (JWT_PRIVATE_KEY /
    JWT_PUBLIC_KEY) before falling back to the file path — so both are
    cleared here too, in case either is set in .env, to guarantee tests
    always use the disposable keypair above rather than real key material.
    """
    from app.config import settings

    priv, pub = rsa_keypair
    monkeypatch.setattr(settings, "jwt_private_key_path", priv)
    monkeypatch.setattr(settings, "jwt_public_key_path", pub)
    monkeypatch.delenv("JWT_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("JWT_PUBLIC_KEY", raising=False)
    yield


@pytest.fixture
def test_client():
    """A TestClient wired to an in-memory SQLite DB instead of the real
    Postgres user_db, via FastAPI's dependency_overrides. No live database,
    no network, needed to run this suite."""
    from app import models  # noqa: F401 (registers User on Base)
    from app.database import Base, get_db
    from app.main import app

    # StaticPool is required here: without it, SQLAlchemy opens a fresh
    # connection to sqlite:///:memory: per request, and each connection is a
    # brand-new, empty in-memory database (SQLite's memory DBs are
    # connection-scoped) — so tables created above would "vanish" on the
    # very next request. StaticPool keeps every session on the same single
    # connection for the lifetime of this engine.
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
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
