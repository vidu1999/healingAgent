"""Incident management service."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import utc_now
from app.models.all import Incident, IncidentEvent, Repository, WorkflowRun
from app.services.audit_service import record_audit


def list_incidents(db: Session, repository_id: Optional[str] = None, severity: Optional[str] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0):
    q = db.query(Incident)
    if repository_id:
        q = q.filter(Incident.repository_id == repository_id)
    if severity:
        q = q.filter(Incident.severity == severity)
    if status:
        q = q.filter(Incident.status == status)
    total = q.count()
    items = q.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()
    return items, total


def get_incident(db: Session, incident_id: str) -> Optional[Incident]:
    return db.query(Incident).filter(Incident.id == incident_id).first()


def create_incident(
    db: Session,
    *,
    title: str,
    description: Optional[str] = None,
    severity: str = "error",
    status: str = "open",
    source_type: str = "manual",
    source_ref: Optional[str] = None,
    trace_id: Optional[str] = None,
    repository_id: Optional[str] = None,
    workflow_run_id: Optional[str] = None,
    actor_user=None,
) -> Incident:
    incident = Incident(
        title=title,
        description=description,
        severity=severity,
        status=status,
        source_type=source_type,
        source_ref=source_ref,
        trace_id=trace_id,
        repository_id=repository_id,
        workflow_run_id=workflow_run_id,
    )
    db.add(incident)
    db.flush()
    db.add(IncidentEvent(incident_id=incident.id, event_type="incident.created", message=title))
    record_audit(
        db,
        action="incident.create",
        resource=f"incident:{incident.id}",
        decision="success",
        result="created",
        actor_user=actor_user,
        correlation_id=trace_id,
    )
    return incident


def update_incident(db: Session, incident_id: str, **fields) -> Optional[Incident]:
    incident = get_incident(db, incident_id)
    if not incident:
        return None
    for k, v in fields.items():
        if hasattr(incident, k):
            setattr(incident, k, v)
    db.add(incident)
    db.flush()
    return incident
