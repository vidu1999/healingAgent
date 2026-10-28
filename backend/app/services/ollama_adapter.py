"""Ollama local inference adapter.

Talks to the local Ollama HTTP API only. Never falls back to a cloud provider.
All model outputs are validated with Pydantic before use. Malformed/empty
responses, timeouts, context exhaustion and unavailable models are handled
explicitly and reported as unavailable/failed rather than fabricated.
"""

from __future__ import annotations

import json
import time
from typing import Optional

import httpx
import threading
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.security import utc_now


class OllamaError(Exception):
    def __init__(self, message: str, code: str = "ollama_error"):
        super().__init__(message)
        self.code = code


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatResponse(BaseModel):
    model: str
    created_at: str
    message: ChatMessage
    done: bool
    total_duration: Optional[int] = None
    eval_count: Optional[int] = None


class OllamaAdapter:
    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS
        self.max_concurrent = settings.OLLAMA_MAX_CONCURRENT_REQUESTS
        self._semaphore = threading.Semaphore(self.max_concurrent)
        self._client = httpx.Client(timeout=self.timeout)

    # ------------------------------------------------------------------ status
    def status(self) -> dict:
        """Return Ollama reachability + model availability without side effects
        beyond a lightweight /api/version and /api/tags call."""
        result: dict = {
            "reachable": False,
            "model_available": False,
            "model": self.model,
            "error": None,
            "mode": "demo" if settings.is_demo else "unavailable",
        }
        try:
            version = self._client.get(f"{self.base_url}/api/version", timeout=5)
            if version.status_code >= 400:
                result["error"] = f"Ollama HTTP {version.status_code}"
                return result
            result["reachable"] = True
            result["mode"] = "live"
        except Exception as exc:  # infrastructure unavailable
            result["error"] = f"Oollama unreachable: {exc}"
            return result

        # Verify the configured model is available before inference.
        try:
            tags = self._client.get(f"{self.base_url}/api/tags", timeout=5)
            if tags.status_code < 400:
                names = [g.get("name", "") for g in tags.json().get("models", [])]
                if self.model in names or any(n.startswith(self.model.split(":")[0] + ":") for n in names):
                    result["model_available"] = True
                else:
                    result["error"] = f"Model '{self.model}' not available. Installed: {names}"
        except Exception as exc:
            result["error"] = f"Could not list models: {exc}"
        return result

    # ---------------------------------------------------------------- inference
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        *,
        temperature: float = 0.2,
        num_predict: int = 1024,
    ) -> BaseModel:
        """Generate a JSON response validated against `schema`.

        Uses Ollama's `format: json` when the model supports structured output.
        Raises OllamaError on any failure - never fabricates data.
        """
        if settings.AI_CLOUD_FALLBACK:
            raise OllamaError("AI_CLOUD_FALLBACK is explicitly disabled", code="cloud_forbidden")

        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "num_ctx": settings.OLLAMA_CONTEXT_SIZE,
            },
        }

        start = utc_now()
        try:
            with self._semaphore:
                resp = self._client.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
        except Exception as exc:
            raise OllamaError(f"Inference request failed: {exc}", code="request_failed") from exc

        if resp.status_code >= 400:
            raise OllamaError(f"Ollama HTTP {resp.status_code}: {resp.text[:200]}", code="http_error")

        # Empty / malformed response handling.
        raw = resp.text.strip()
        if not raw:
            raise OllamaError("Empty response from Ollama", code="empty_response")

        try:
            parsed = resp.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise OllamaError(f"Malformed JSON from Ollama: {exc}", code="malformed_json") from exc

        try:
            chat = ChatResponse.model_validate(parsed)
        except ValidationError as exc:
            raise OllamaError(f"Response schema validation failed: {exc}", code="schema_validation") from exc

        content = chat.message.content.strip() if chat.message and chat.message.content else ""
        if not content:
            raise OllamaError("Empty content in model response", code="empty_content")

        # Validate against the caller's Pydantic schema.
        try:
            return schema.model_validate_json(content)
        except ValidationError as exc:
            raise OllamaError(f"Model output failed output validation: {exc}", code="output_validation") from exc

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass
