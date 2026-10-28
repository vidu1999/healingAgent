"""System endpoints: Ollama status."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.config import settings
from app.schemas.incidents import OllamaStatus
from app.services.ollama_adapter import OllamaAdapter

router = APIRouter()


@router.get("/ollama-status", response_model=OllamaStatus)
def ollama_status(current_user: object = Depends(get_current_user)):
    adapter = OllamaAdapter()
    try:
        st = adapter.status()
    finally:
        adapter.close()
    return OllamaStatus(
        reachable=st.get("reachable", False),
        model_available=st.get("model_available", False),
        model=st.get("model", settings.OLLAMA_MODEL),
        error=st.get("error"),
        mode=st.get("mode", "unavailable"),
    )
