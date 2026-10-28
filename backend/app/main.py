"""FastAPI application factory.

Config validation and production secret checks run at startup. Routers are
mounted under /api/v1. Error handling is generic so internal traces never leak
to clients.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine, init_db

__all__ = ["app"]


def create_app() -> FastAPI:
    app = FastAPI(
        title="SentinelOps AI",
        description="Locally AI-powered, security-first DevOps monitoring and repair platform.",
        version="0.1.0",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
    )

    # ------------------------------------------------------------------ CORS
    # In production, origins must be explicitly configured. Default: loopback only.
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------ routes
    app.include_router(api_router, prefix="/api/v1")

    # ------------------------------------------------------------------ startup
    @app.on_event("startup")
    def _startup() -> None:
        settings.require_production_secrets()
        # Dev/demo convenience: create tables. Production relies on Alembic.
        if not settings.is_production:
            init_db()

    # ------------------------------------------------------------------ health-ish root
    @app.get("/health/live", tags=["health"])
    def live():
        return {"status": "alive", "env": settings.APP_ENV, "demo": settings.is_demo}

    @app.get("/health/ready", tags=["health"])
    def ready():
        try:
            with engine().connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ready", "database": "connected"}
        except Exception as exc:  # pragma: no cover - infrastructure dependent
            return JSONResponse(
                status_code=503,
                content={"status": "not ready", "database": "disconnected", "error": str(exc)},
            )

    # ------------------------------------------------------------------ generic error handler
    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        # Never leak internal exception traces to clients.
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
