"""Audit events endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_db, get_current_user, require_roles
from app.models.all import AuditEvent
from app.schemas.incidents import AuditEventOut

router = APIRouter()


@router.get("", response_model=list[AuditEventOut])
def list_audit_events(
    limit: int = 100,
    offset: int = 0,
    current_user: object = Depends(require_roles("admin", "operator")),
    db=Depends(get_db),
):
    return db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit).all()
