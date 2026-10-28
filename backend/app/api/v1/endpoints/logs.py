"""Log ingestion endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_db, get_current_user
from app.models.all import MonitoredSource
from app.schemas.incidents import LogIngestRequest, LogIngestResponse
from app.services.log_ingestion import ingest_event, is_path_allowed
from app.services.incident_service import create_incident

router = APIRouter()


@router.post("/ingest", response_model=LogIngestResponse)
def ingest_logs(payload: LogIngestRequest, current_user: object = Depends(get_current_user), db=Depends(get_db)):
    actor = current_user if hasattr(current_user, "id") else None
    source = db.query(MonitoredSource).filter(MonitoredSource.id == payload.source_id).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitored source not found")
    count = 0
    for ev in payload.events:
        ingest_event(db, payload.source_id, ev.model_dump(), actor_user=actor)
        count += 1
    db.flush()
    return LogIngestResponse(ingested=count, incidents_created=0)
