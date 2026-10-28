"""Repair attempt endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_db, get_current_user
from app.schemas.incidents import RepairCreate, RepairAttemptOut, DiffOut, VerificationRunOut
from app.models.all import RepairAttempt, PatchArtifact, VerificationRun, VerificationCheck, Investigation
from app.services.investigation_service import get_investigation
from app.services.audit_service import record_audit, content_hash_for

router = APIRouter()


@router.post("", response_model=RepairAttemptOut, status_code=status.HTTP_201_CREATED)
def create_repair_attempt(payload: RepairCreate, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    actor = current_user if hasattr(current_user, "id") else None
    inv = get_investigation(db, payload.investigation_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")
    attempt = RepairAttempt(investigation_id=payload.investigation_id, status="pending")
    db.add(attempt)
    db.flush()
    record_audit(db, action="repair.create", resource=f"repair_attempt:{attempt.id}", decision="success", result="created", actor_user=actor)
    return attempt


@router.get("/{repair_id}", response_model=RepairAttemptOut)
def get_repair_attempt(repair_id: str, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    attempt = db.query(RepairAttempt).filter(RepairAttempt.id == repair_id).first()
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair attempt not found")
    return attempt


@router.get("/{repair_id}/diff", response_model=DiffOut)
def get_repair_diff(repair_id: str, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    artifact = db.query(PatchArtifact).filter(PatchArtifact.repair_attempt_id == repair_id).first()
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No patch artifact for this repair attempt")
    return DiffOut(
        repair_attempt_id=repair_id,
        patch_hash=artifact.sha256,
        explanation=artifact.explanation,
        files_changed=[],
        diff=artifact.diff,
    )


@router.get("/{repair_id}/verification", response_model=VerificationRunOut)
def get_repair_verification(repair_id: str, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    run = db.query(VerificationRun).filter(VerificationRun.repair_attempt_id == repair_id).order_by(VerificationRun.created_at.desc()).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No verification run for this repair attempt")
    return run
