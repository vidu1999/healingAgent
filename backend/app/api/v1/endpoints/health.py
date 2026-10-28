"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/live")
def live():
    return {"status": "alive"}


@router.get("/ready")
def ready():
    return {"status": "ready"}
