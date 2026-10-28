"""Incident endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_db, get_current_user
from app.models.all import Incident
from app.schemas.incidents import IncidentCreate, IncidentOut, IncidentUpdate, IncidentEventOut
from app.services.incident_service import list_incidents, get_incident, create_incident
from app.services.audit_service import record_audit

router = APIRouter()


@router.get("", response_model=list[IncidentOut])
def list_incidents_endpoint(
    repository_id: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: object = Depends(get_current_user),
    db=Depends(get_db),
):
    items, _ = list_incidents(db, repository_id=repository_id, severity=severity, status=status, limit=limit, offset=offset)
    return items


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident_endpoint(incident_id: str, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    inc = get_incident(db, incident_id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return inc


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident_endpoint(payload: IncidentCreate, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    actor = current_user if hasattr(current_user, "id") else None
    inc = create_incident(
        db,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=payload.status,
        source_type=payload.source_type,
        source_ref=payload.source_ref,
        trace_id=payload.trace_id,
        repository_id=payload.repository_id,
        workflow_run_id=payload.workflow_run_id,
        actor_user=actor,
    )
    return inc
