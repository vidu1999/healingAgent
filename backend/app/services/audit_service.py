"""Append-only audit event service.

Audit events are append-only: this service only inserts, never updates or
deletes. Raw secrets/prompts are never recorded.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import utc_now
from app.models.all import AuditEvent, User


def record_audit(
    db: Session,
    *,
    action: str,
    resource: str,
    decision: str,
    result: str,
    actor_user: Optional[User] = None,
    actor_role: Optional[str] = None,
    reason_code: Optional[str] = None,
    approval_reference: Optional[str] = None,
    correlation_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    content_hash: Optional[str] = None,
    sanitized_error: Optional[str] = None,
) -> AuditEvent:
    event_id = f"evt-{uuid.uuid4().hex}"
    if actor_role is None and actor_user is not None and actor_user.roles:
        actor_role = actor_user.roles[0].role.name
    event = AuditEvent(
        event_id=event_id,
        actor_user_id=actor_user.id if actor_user else None,
        actor_role=actor_role,
        action=action,
        resource=resource,
        decision=decision,
        reason_code=reason_code,
        approval_reference=approval_reference,
        correlation_id=correlation_id,
        result=result,
        duration_ms=duration_ms,
        content_hash=content_hash,
        sanitized_error=sanitized_error,
    )
    db.add(event)
    db.flush()
    return event


def content_hash_for(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
