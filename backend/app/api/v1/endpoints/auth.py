"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import utc_now, expires_in, hash_token
from app.models.all import User, Session as SessionModel, Role, UserRole
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse
from app.services.auth_service import authenticate_user, create_session, destroy_session, get_user_roles
from app.services.audit_service import record_audit

router = APIRouter()


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        path="/",
        max_age=settings.SESSION_TTL_SECONDS,
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.email, req.password)
    if not user:
        record_audit(db, action="auth.login", resource=f"user:{req.email}", decision="failure", result="invalid_credentials")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_session(db, user, ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    _set_session_cookie(response, token)
    roles = get_user_roles(db, user)
    record_audit(db, action="auth.login", resource=f"user:{user.id}", decision="success", result="authenticated", actor_user=user)
    return LoginResponse(message="Logged in", user={"id": user.id, "email": user.email, "username": user.username, "roles": roles})


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    destroyed = destroy_session(db, token, current_user)
    _clear_session_cookie(response)
    return {"message": "Logged out", "destroyed": destroyed}


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = get_user_roles(db, current_user)
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        roles=roles,
    )


@router.post("/refresh", response_model=dict)
def refresh(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # sliding refresh handled by get_current_user; just confirm session alive
    return {"message": "Session refreshed"}
