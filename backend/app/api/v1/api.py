"""Versioned API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    dashboard,
    health,
    incidents,
    logs,
    repositories,
    webhooks,
    investigations,
    repairs,
    approvals,
    audit,
    system,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["repositories"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(investigations.router, prefix="/investigations", tags=["investigations"])
api_router.include_router(repairs.router, prefix="/repair-attempts", tags=["repair-attempts"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(audit.router, prefix="/audit-events", tags=["audit-events"])

__all__ = ["api_router"]
