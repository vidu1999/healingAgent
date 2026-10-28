"""Investigation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_db, get_current_user
from app.models.all import Investigation
from app.schemas.incidents import InvestigationCreate, InvestigationOut, InvestigationDetail
from app.services.investigation_service import create_investigation, get_investigation, transition, add_evidence, can_transition
from app.services.audit_service import record_audit

router = APIRouter()


@router.post("", response_model=InvestigationOut, status_code=status.HTTP_201_CREATED)
def create_investigation_endpoint(payload: InvestigationCreate, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    actor = current_user if hasattr(current_user, "id") else None
    inv = create_investigation(db, payload.incident_id, model=None)
    return inv


@router.get("/{investigation_id}", response_model=InvestigationDetail)
def get_investigation_endpoint(investigation_id: str, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")
    return inv


@router.post("/{investigation_id}/transition", response_model=InvestigationOut)
def transition_investigation(
    investigation_id: str,
    target_state: str,
    current_user: object = Depends(get_current_user),
    db=Depends(get_db),
):
    actor = current_user if hasattr(current_user, "id") else None
    if not can_transition(get_investigation(db, investigation_id).state, target_state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid transition")
    inv = transition(db, investigation_id, target_state, actor_user=actor)
    return inv
