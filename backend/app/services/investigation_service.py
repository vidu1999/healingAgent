"""Investigation state machine.

States (section 6):
DETECTED -> TRIAGED -> INVESTIGATING -> FIX_CANDIDATE_READY -> TEST_GENERATION ->
SANDBOX_VALIDATION -> PATCH_VERIFIED -> AWAITING_EXTERNAL_ACTION_APPROVAL ->
APPROVED -> EXTERNAL_ACTION_EXECUTING -> AWAITING_RESULT -> COMPLETED

Failure states: INVESTIGATION_FAILED, TEST_GENERATION_FAILED, SANDBOX_FAILED,
PATCH_REJECTED, APPROVAL_REJECTED, APPROVAL_EXPIRED, ACTION_FAILED, CANCELLED,
MANUAL_REVIEW_REQUIRED.

Every transition is persisted transactionally.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import utc_now
from app.models.all import Investigation, Investigation as InvestigationModel
from app.models.all import Incident, IncidentEvent, EvidenceItem
from app.services.audit_service import record_audit, content_hash_for


# ------------------------------------------------------------------ state machine
STATES = {
    "DETECTED",
    "TRIAGED",
    "INVESTIGATING",
    "FIX_CANDIDATE_READY",
    "TEST_GENERATION",
    "SANDBOX_VALIDATION",
    "PATCH_VERIFIED",
    "AWAITING_EXTERNAL_ACTION_APPROVAL",
    "APPROVED",
    "EXTERNAL_ACTION_EXECUTING",
    "AWAITING_RESULT",
    "COMPLETED",
}

FAILURE_STATES = {
    "INVESTIGATION_FAILED",
    "TEST_GENERATION_FAILED",
    "SANDBOX_FAILED",
    "PATCH_REJECTED",
    "APPROVAL_REJECTED",
    "APPROVAL_EXPIRED",
    "ACTION_FAILED",
    "CANCELLED",
    "MANUAL_REVIEW_REQUIRED",
}

# Allowed transitions (current -> set of next)
TRANSITIONS = {
    "DETECTED": {"TRIAGED", "INVESTIGATION_FAILED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "TRIAGED": {"INVESTIGATING", "INVESTIGATION_FAILED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "INVESTIGATING": {"FIX_CANDIDATE_READY", "INVESTIGATION_FAILED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "FIX_CANDIDATE_READY": {"TEST_GENERATION", "PATCH_REJECTED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "TEST_GENERATION": {"SANDBOX_VALIDATION", "TEST_GENERATION_FAILED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "SANDBOX_VALIDATION": {"PATCH_VERIFIED", "SANDBOX_FAILED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "PATCH_VERIFIED": {"AWAITING_EXTERNAL_ACTION_APPROVAL", "PATCH_REJECTED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "AWAITING_EXTERNAL_ACTION_APPROVAL": {"APPROVED", "APPROVAL_REJECTED", "APPROVAL_EXPIRED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "APPROVED": {"EXTERNAL_ACTION_EXECUTING", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "EXTERNAL_ACTION_EXECUTING": {"AWAITING_RESULT", "ACTION_FAILED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "AWAITING_RESULT": {"COMPLETED", "ACTION_FAILED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    # Terminal-ish
    "COMPLETED": set(),
    "INVESTIGATION_FAILED": {"DETECTED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "TEST_GENERATION_FAILED": {"INVESTIGATING", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "SANDBOX_FAILED": {"FIX_CANDIDATE_READY", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "PATCH_REJECTED": {"FIX_CANDIDATE_READY", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "APPROVAL_REJECTED": {"PATCH_VERIFIED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "APPROVAL_EXPIRED": {"PATCH_VERIFIED", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "ACTION_FAILED": {"EXTERNAL_ACTION_EXECUTING", "CANCELLED", "MANUAL_REVIEW_REQUIRED"},
    "CANCELLED": set(),
    "MANUAL_REVIEW_REQUIRED": {"INVESTIGATING", "CANCELLED"},
}


def is_terminal(state: str) -> bool:
    return state in ("COMPLETED", "CANCELLED") or state in FAILURE_STATES


def can_transition(current: str, target: str) -> bool:
    if target not in STATES and target not in FAILURE_STATES:
        return False
    return target in TRANSITIONS.get(current, set())


# ------------------------------------------------------------------ service
def create_investigation(db: Session, incident_id: str, model: Optional[str] = None) -> Investigation:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError(f"Incident {incident_id} not found")
    inv = Investigation(incident_id=incident_id, state="DETECTED", model=model, retry_count=0)
    db.add(inv)
    db.flush()
    db.add(IncidentEvent(incident_id=incident_id, event_type="investigation.created", message="Investigation DETECTED"))
    record_audit(
        db,
        action="investigation.create",
        resource=f"investigation:{inv.id}",
        decision="success",
        result="created",
        correlation_id=incident.trace_id,
    )
    return inv


def get_investigation(db: Session, investigation_id: str) -> Optional[Investigation]:
    return db.query(Investigation).filter(Investigation.id == investigation_id).first()


def transition(
    db: Session,
    investigation_id: str,
    target: str,
    *,
    actor_user=None,
    output: Optional[str] = None,
    confidence: Optional[str] = None,
    error: Optional[str] = None,
) -> Investigation:
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise ValueError(f"Investigation {investigation_id} not found")
    current = inv.state
    if not can_transition(current, target):
        raise ValueError(f"Invalid transition {current} -> {target}")
    inv.state = target
    if output is not None:
        inv.output = output
    if confidence is not None:
        inv.confidence = confidence
    if error is not None:
        inv.error = error
    inv.retry_count += 1 if target in FAILURE_STATES else 0
    db.add(inv)
    db.flush()
    db.add(IncidentEvent(incident_id=inv.incident_id, event_type="state.transition", message=f"{current} -> {target}"))
    record_audit(
        db,
        action="investigation.transition",
        resource=f"investigation:{inv.id}",
        decision="success",
        result=target,
        actor_user=actor_user,
        content_hash=content_hash_for(f"{current}->{target}"),
    )
    return inv


def add_evidence(db: Session, investigation_id: str, type: str, ref: str, description: Optional[str] = None, content_hash: Optional[str] = None) -> EvidenceItem:
    item = EvidenceItem(investigation_id=investigation_id, type=type, ref=ref, description=description, content_hash=content_hash)
    db.add(item)
    db.flush()
    return item
