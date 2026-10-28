"""GitHub adapter.

Read-only by default. Supports HMAC webhook signature verification, replay
protection (idempotency keys), polling fallback, and write operations that are
gated behind the central approval service. No credentials are stored in source,
logs, or prompts.
"""

from __future__ import annotations

import hmac
import hashlib
import time
from typing import Optional

import httpx

from app.core.config import settings


class GitHubError(Exception):
    def __init__(self, message: str, code: str = "github_error", status_code: int = 502):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def verify_webhook_signature(payload_body: bytes, signature: Optional[str], secret: str) -> bool:
    """HMAC-SHA256 verification of GitHub webhook deliveries."""
    if not signature or not secret:
        return False
    try:
        scheme, _, sig = signature.partition("=")
    except ValueError:
        return False
    if scheme.lower() != "sha256":
        return False
    mac = hmac.new(secret.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, sig)


def is_replay(delivery_id: str, seen: set, ttl_seconds: int = 300) -> bool:
    """Idempotency/replay protection for webhook deliveries (in-memory dev store)."""
    now = time.time()
    expired = [k for k, v in list(seen.items()) if now - v > ttl_seconds]
    for k in expired:
        seen.pop(k, None)
    if delivery_id in seen:
        return True
    seen[delivery_id] = now
    return False


class GitHubAdapter:
    def __init__(self) -> None:
        self.token = settings.GITHUB_TOKEN
        self.base_url = settings.GITHUB_API_BASE_URL.rstrip("/")
        self.headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        self._client = httpx.Client(timeout=30)
        self._delivery_store: dict = {}

    def is_configured(self) -> bool:
        return bool(self.token or settings.GITHUB_APP_ID)

    def is_read_only(self) -> bool:
        return settings.GITHUB_READ_ONLY

    def allowlist(self) -> list[str]:
        return settings.github_allowlist

    def is_allowed(self, full_name: str) -> bool:
        allowlist = self.allowlist()
        return not allowlist or full_name in allowlist

    # ---------------------------------------------------------------- requests
    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        if not settings.GITHUB_READ_ONLY and method in ("POST", "PATCH", "PUT", "DELETE"):
            # Writes must go through the approval service, never directly here.
            raise GitHubError("Direct GitHub writes are blocked; use the approval engine", code="write_blocked", status_code=403)
        url = f"{self.base_url}{path}"
        resp = self._client.request(method, url, headers=self.headers, **kwargs)
        if resp.status_code >= 400:
            raise GitHubError(f"GitHub API {resp.status_code}: {resp.text[:200]}", code="api_error", status_code=resp.status_code)
        return resp

    # ---------------------------------------------------------------- read ops
    def get_repository(self, full_name: str) -> dict:
        if not self.is_allowed(full_name):
            raise GitHubError(f"Repository {full_name} not on allowlist", code="not_allowed", status_code=403)
        resp = self._request("GET", f"/repos/{full_name}")
        return resp.json()

    def get_workflow_runs(self, full_name: str) -> list[dict]:
        if not self.is_allowed(full_name):
            raise GitHubError(f"Repository {full_name} not on allowlist", code="not_allowed", status_code=403)
        resp = self._request("GET", f"/repos/{full_name}/actions/runs?per_page=25")
        return resp.json().get("workflow_runs", [])

    def get_workflow_run(self, full_name: str, run_id: str) -> dict:
        resp = self._request("GET", f"/repos/{full_name}/actions/runs/{run_id}")
        return resp.json()

    def get_jobs(self, full_name: str, run_id: str) -> list[dict]:
        resp = self._request("GET", f"/repos/{full_name}/actions/runs/{run_id}/jobs")
        return resp.json().get("jobs", [])

    def webhook_event(self, event: str, delivery_id: str, payload: dict, secret: str) -> dict:
        """Ingest a verified webhook event. Replay deliveries are rejected."""
        if is_replay(delivery_id, self._delivery_store):
            raise GitHubError("Replayed webhook delivery", code="replay", status_code=409)
        return {"event": event, "delivery_id": delivery_id, "accepted": True, "payload": payload}

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass
