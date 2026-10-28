"""FastAPI dependencies: database session, current user, role checks.

Dependencies use `Depends(get_db)` so that (a) the application's real
request-scoped session is used in production and (b) test overrides of `get_db`
are honored. The `get_db` generator commits/rolls back and closes the session
after every request, so connections are never leaked.
"""

from __future__ import annotations

from datetime import timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_token, utc_now
from app.db.session import get_db
from app.models.all import Session as SessionModel, User, UserRole, Role

# OAuth2 bearer is kept for programmatic clients; browser sessions use cookies.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_request_id(request: Request) -> str:
    return request.headers.get("x-request-id", "")


# ---------------------------------------------------------------- auth


def get_session_token(request: Request) -> Optional[str]:
    """Read session token from HttpOnly cookie, falling back to bearer header."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        return token
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1]
    return None


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    token = get_session_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_hash = hash_token(token)
    session = db.execute(
        select(SessionModel).where(SessionModel.token_hash == token_hash)
    ).scalar_one_or_none()
    expires_at = session.expires_at if session else None
    if expires_at and expires_at.tzinfo is None:
        # SQLite returns naive datetimes; interpret as UTC.
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if session is None or (expires_at and expires_at < utc_now()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )
    user = db.execute(select(User).where(User.id == session.user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or not found",
        )
    # refresh sliding expiry (committed by get_db's finally after the request)
    session.expires_at = utc_now() + timedelta(seconds=settings.SESSION_TTL_SECONDS)
    db.add(session)
    return user


def require_roles(*allowed: str):
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        role_names = [
            r.name
            for r in db.execute(
                select(Role)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == current_user.id)
            ).scalars()
        ]
        if not any(r in allowed for r in role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return current_user

    return dependency


require_superuser = require_roles("admin")


__all__ = [
    "get_current_user",
    "require_roles",
    "require_superuser",
    "oauth2_scheme",
    "get_request_id",
    "get_db",
]
