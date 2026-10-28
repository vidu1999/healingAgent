"""Authentication service: login, logout, session management, rate-limit helpers.

Sessions are database-backed, token stored hashed, HttpOnly cookie transport.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_session_token, hash_token, verify_password, utc_now, expires_in
from app.models.all import Session as SessionModel, User, UserRole, Role
from app.services.audit_service import record_audit, content_hash_for


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.execute(
        __import__("sqlalchemy").select(User).where(User.email == email)
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: Session, user: User, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> str:
    token = generate_session_token()
    session = SessionModel(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=expires_in(settings.SESSION_TTL_SECONDS),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.flush()
    role_names = [r.role.name for r in user.roles] if hasattr(user, "roles") and user.roles else []
    record_audit(
        db,
        action="session.create",
        resource=f"user:{user.id}",
        decision="success",
        result="authenticated",
        actor_user=user,
        content_hash=content_hash_for(token[:8]),
    )
    return token


def get_user_roles(db: Session, user: User) -> list[str]:
    rows = db.execute(
        __import__("sqlalchemy").select(Role)
        .join(UserRole, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user.id)
    ).scalars()
    return [r.name for r in rows]


def destroy_session(db: Session, token: Optional[str], actor_user: Optional[User]) -> bool:
    if not token:
        return False
    token_hash = hash_token(token)
    session = db.execute(
        __import__("sqlalchemy").select(SessionModel).where(SessionModel.token_hash == token_hash)
    ).scalar_one_or_none()
    if session:
        db.delete(session)
        db.flush()
        if actor_user:
            record_audit(
                db,
                action="session.destroy",
                resource=f"session:{session.id}",
                decision="success",
                result="logged_out",
                actor_user=actor_user,
            )
        return True
    return False
