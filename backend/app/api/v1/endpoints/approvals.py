"""Approval endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_db, get_current_user
from app.models.all import ApprovalRequest, User
from app.schemas.incidents import ApprovalRequestOut, ApprovalAction
from app.services.approval_service import (
    create_approval_request,
    get_approval,
    list_approvals,
    decide_approval,
    consume_approval,
    record_external_action,
    complete_external_action,
)
from app.services.audit_service import record_audit, content_hash_for
from app.core.config import settings

router = APIRouter()


def _actor(current_user: object) -> Optional[User]:
    return current_user if hasattr(current_user, "id") else None


@router.get("", response_model=list[ApprovalRequestOut])
def list_approvals_endpoint(status: Optional[str] = None, limit: int = 50, offset: int = 0, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    items, _ = list_approvals(db, status=status, limit=limit, offset=offset)
    return items


@router.get("/{approval_id}", response_model=ApprovalRequestOut)
def get_approval_endpoint(approval_id: str, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    req = get_approval(db, approval_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    return req


@router.post("/{approval_id}/approve", response_model=ApprovalRequestOut)
def approve_approval(approval_id: str, action: ApprovalAction, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    actor = _actor(current_user)
    if not actor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    req = decide_approval(db, approval_id, "approve", actor, reason=action.reason)
    return req


@router.post("/{approval_id}/reject", response_model=ApprovalRequestOut)
def reject_approval(approval_id: str, action: ApprovalAction, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    actor = _actor(current_user)
    if not actor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    req = decide_approval(db, approval_id, "reject", actor, reason=action.reason)
    return req


@router.post("/{approval_id}/revoke", response_model=ApprovalRequestOut)
def revoke_approval(approval_id: str, action: ApprovalAction, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    actor = _actor(current_user)
    if not actor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    req = decide_approval(db, approval_id, "revoke", actor, reason=action.reason)
    return req
