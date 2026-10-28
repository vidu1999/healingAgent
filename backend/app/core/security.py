"""Cryptographic helpers: password hashing, session tokens, CSRF.

Passwords are hashed with Argon2id via argon2-cffi (modern, memory-hard).
Session tokens are random and stored hashed in the database. Raw secrets are
never written to logs or AI prompts.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHash

from app.core.config import settings

_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerificationError, InvalidHash, ValueError):
        return False


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for storage (we never store raw tokens)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def expires_in(seconds: int) -> datetime:
    return utc_now() + timedelta(seconds=seconds)
