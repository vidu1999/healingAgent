"""Pytest configuration: file SQLite test DB, TestClient, seeded users.

One file database for the test session. Each test gets its own Session; the
TestClient reuses that same Session for every request (one connection, no lock
contention). Sessions created by create_session() are committed so they remain
visible across requests. Uncommitted changes are rolled back at teardown.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_sentinelops.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-do-not-use-in-production")
os.environ.setdefault("AI_CLOUD_FALLBACK", "false")
os.environ.setdefault("DEMO_MODE", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.session import engine, session_factory, get_db  # noqa: E402
from app.db.base import Base  # noqa: E402
import app.models.all  # noqa: E402  (register models)
from app.main import create_app  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.all import Role, User, UserRole  # noqa: E402

_db_path = os.path.join(os.getcwd(), "test_sentinelops.db")


def pytest_configure():
    if os.path.exists(_db_path):
        os.remove(_db_path)
    Base.metadata.create_all(bind=engine())


@pytest.fixture(scope="session", autouse=True)
def _drop_schema_at_end():
    yield
    Base.metadata.drop_all(bind=engine())


@pytest.fixture()
def db():
    SessionLocal = session_factory()
    db = SessionLocal()
    db.rollback()
    yield db
    db.rollback()
    db.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _get_or_create_role(db, name, description):
    role = db.query(Role).filter(Role.name == name).first()
    if not role:
        role = Role(name=name, description=description)
        db.add(role)
        db.flush()
    return role


@pytest.fixture()
def seed(db):
    admin_role = _get_or_create_role(db, "admin", "Full access")
    op_role = _get_or_create_role(db, "operator", "Can investigate, repair, approve")
    _get_or_create_role(db, "viewer", "Read-only")

    admin = db.query(User).filter(User.email == "admin@test.example.com").first()
    if not admin:
        admin = User(
            email="admin@test.example.com",
            username="admin",
            password_hash=hash_password("password123"),
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        db.flush()
    operator = db.query(User).filter(User.email == "operator@test.example.com").first()
    if not operator:
        operator = User(
            email="operator@test.example.com",
            username="operator",
            password_hash=hash_password("password123"),
            is_active=True,
            is_superuser=False,
        )
        db.add(operator)
        db.flush()

    for user, role in [(admin, admin_role), (operator, op_role)]:
        if not db.query(UserRole).filter(
            UserRole.user_id == user.id, UserRole.role_id == role.id
        ).first():
            db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    return {
        "admin": admin,
        "operator": operator,
        "admin_role": admin_role,
        "operator_role": op_role,
    }
