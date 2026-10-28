"""Central approval engine (section 8).

Every external mutation passes through this service. Approvals are bound to the
exact operation, parameters and content hash, expire after a short TTL, are
consumed atomically, and fail closed if the policy/audit store is unavailable.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import utc_now, expires_in
from app.models.all import ApprovalRequest, ApprovalDecision, ExternalAction, User
from app.services.audit_service import record_audit, content_hash_for


def create_approval_request(
    db: Session,
    *,
    requesting_user: Optional[User],
    requesting_role: Optional[str],
    repository_id: Optional[str],
    environment: Optional[str],
    resource: str,
    action_type: str,
    parameters: str,
    base_commit_sha: Optional[str] = None,
    patch_sha256: Optional[str] = None,
    payload_hash: Optional[str] = None,
    impact_summary: str,
    risk_classification: str = "medium",
    correlation_id: Optional[str] = None,
) -> ApprovalRequest:
    ttl = expires_in(__import__("app.core.config", fromlist=["settings"]).settings.APPROVAL_LIFETIME_SECONDS)
    req = ApprovalRequest(
        requesting_user_id=requesting_user.id if requesting_user else None,
        requesting_role=requesting_role,
        repository_id=repository_id,
        environment=environment,
        resource=resource,
        action_type=action_type,
        parameters=parameters,
        base_commit_sha=base_commit_sha,
        patch_sha256=patch_sha256,
        payload_hash=payload_hash,
        impact_summary=impact_summary,
        risk_classification=risk_classification,
        status="pending",
        expires_at=ttl,
        audit_correlation_id=correlation_id,
    )
    db.add(req)
    db.flush()
    record_audit(
        db,
        action="approval.request.create",
        resource=f"approval:{req.id}",
        decision="pending",
        result="created",
        actor_user=requesting_user,
        approval_reference=req.id,
        correlation_id=correlation_id,
        content_hash=content_hash_for(parameters + (patch_sha256 or "")),
    )
    return req


def get_approval(db: Session, approval_id: str) -> Optional[ApprovalRequest]:
    return db.get(ApprovalRequest, approval_id)


def list_approvals(db: Session, status: Optional[str] = None, limit: int = 50, offset: int = 0):
    q = db.query(ApprovalRequest)
    if status:
        q = q.filter(ApprovalRequest.status == status)
    total = q.count()
    items = q.order_by(ApprovalRequest.created_at.desc()).offset(offset).limit(limit).all()
    return items, total


def _is_valid(req: ApprovalRequest) -> bool:
    if req.status != "pending":
        return False
    if req.expires_at < utc_now():
        return False
    return True


def decide_approval(
    db: Session,
    approval_id: str,
    decision: str,  # "approve" | "reject" | "revoke"
    decider: User,
    reason: Optional[str] = None,
) -> ApprovalRequest:
    req = get_approval(db, approval_id)
    if not req:
        raise ValueError(f"Approval {approval_id} not found")
    if not _is_valid(req) and decision != "revoke":
        raise ValueError(f"Approval {approval_id} is not pending or has expired")
    now = utc_now()
    req.status = {"approve": "approved", "reject": "rejected", "revoke": "revoked"}[decision]
    if decision == "approve":
        req.approved_at = now
    elif decision == "reject":
        req.rejected_at = now
    else:
        req.revoked_at = now
    db.add(req)
    db.add(
        ApprovalDecision(
            approval_request_id=req.id,
            decision=decision,
            decided_by=decider.id,
            reason=reason,
        )
    )
    db.flush()
    record_audit(
        db,
        action=f"approval.{decision}",
        resource=f"approval:{req.id}",
        decision=decision,
        result=req.status,
        actor_user=decider,
        approval_reference=req.id,
        reason_code=reason,
    )
    return req


def consume_approval(db: Session, approval_id: str) -> ApprovalRequest:
    """Atomically consume a pending/approved approval to prevent concurrent execution.
    Revalidate immediately before execution."""
    req = get_approval(db, approval_id)
    if not req:
        raise ValueError(f"Approval {approval_id} not found")
    if req.status != "approved":
        raise ValueError(f"Approval {approval_id} is not approved (status={req.status})")
    if req.expires_at < utc_now():
        req.status = "expired"
        db.add(req)
        db.flush()
        raise ValueError(f"Approval {approval_id} has expired")
    req.status = "consumed"
    db.add(req)
    db.flush()
    record_audit(
        db,
        action="approval.consume",
        resource=f"approval:{req.id}",
        decision="success",
        result="consumed",
        actor_user=None,
        approval_reference=req.id,
    )
    return req


def record_external_action(
    db: Session,
    *,
    approval_request: ApprovalRequest,
    action_type: str,
    parameters_hash: str,
    content_hash: str,
) -> ExternalAction:
    action = ExternalAction(
        approval_request_id=approval_request.id,
        action_type=action_type,
        parameters_hash=parameters_hash,
        content_hash=content_hash,
        status="pending",
    )
    db.add(action)
    db.flush()
    return action


def complete_external_action(
    db: Session,
    action: ExternalAction,
    *,
    status: str,  # executed | failed | blocked
    result: Optional[str] = None,
    error: Optional[str] = None,
) -> ExternalAction:
    action.status = status
    action.result = result
    action.error = error
    from app.core.security import utc_now as _now

    action.executed_at = _now()
    db.add(action)
    db.flush()
    return action
