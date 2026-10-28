"""Dashboard summary endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_db
from app.models.all import Incident, ApprovalRequest, VerificationRun, VerificationCheck, WorkflowRun
from sqlalchemy import func

router = APIRouter()


@router.get("/summary")
def summary(current_user: object = Depends(get_current_user), db=Depends(get_db)):
    active = db.query(Incident).filter(Incident.status != "resolved").count()
    critical = db.query(Incident).filter(Incident.severity == "critical").count()
    failed_workflows = db.query(WorkflowRun).filter(WorkflowRun.conclusion == "failure").count()
    recent_repairs = db.query(VerificationRun).count()
    pending_approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").count()
    total = db.query(VerificationCheck).count() or 1
    passed = db.query(VerificationCheck).filter(VerificationCheck.status == "passed").count()
    return {
        "active_incidents": active,
        "critical_errors": critical,
        "failed_workflows": failed_workflows,
        "recent_repair_attempts": recent_repairs,
        "pending_approvals": pending_approvals,
        "verification_rate": f"{(passed/total*100):.0f}%",
        "integrations": [
            {"name": "github", "status": "configured" if __import__("app.core.config", fromlist=["settings"]).settings.GITHUB_TOKEN else "not configured"},
            {"name": "ollama", "status": "not checked"},
            {"name": "sandbox", "status": "not available"},
        ],
    }
