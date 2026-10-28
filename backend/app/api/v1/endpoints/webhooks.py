"""GitHub webhook ingestion endpoint (HMAC-verified, replay-protected)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.core.deps import get_db, get_current_user
from app.core.config import settings
from app.services.github_adapter import verify_webhook_signature, GitHubAdapter
from app.services.incident_service import create_incident
from app.services.audit_service import record_audit

router = APIRouter()


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    current_user: object = Depends(get_current_user),
    db=Depends(get_db),
):
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook secret not configured")
    body = await request.body()
    if not verify_webhook_signature(body, x_hub_signature_256, secret):
        record_audit(db, action="webhook.github", resource="webhook", decision="failure", result="invalid_signature", actor_user=current_user if hasattr(current_user, 'id') else None)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    adapter = GitHubAdapter()
    try:
        accepted = adapter.webhook_event(x_github_event or "unknown", x_github_delivery or "", {}, secret)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    finally:
        adapter.close()
    # On failed workflow runs, create an incident (read-only reaction).
    try:
        import json
        payload = json.loads(body) if body else {}
    except Exception:
        payload = {}
    if payload.get("workflow_run", {}).get("conclusion") == "failure":
        wr = payload["workflow_run"]
        create_incident(
            db,
            title=f"GitHub workflow failure: {wr.get('name')}",
            description=f"Run {wr.get('run_id')} on {wr.get('branch')} concluded with failure.",
            severity="error",
            source_type="github",
            source_ref=str(wr.get("run_id")),
            trace_id=str(wr.get("head_sha", "")),
            actor_user=current_user if hasattr(current_user, "id") else None,
        )
    return {"accepted": True, "delivery_id": x_github_delivery}
