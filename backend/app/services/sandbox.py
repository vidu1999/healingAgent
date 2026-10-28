"""Sandbox worker interface (section 7.5).

Runs verification checks in a disposable Docker worker image with non-root
user, dropped capabilities, resource limits, read-only rootfs, no network,
no Docker socket, no credential mounts, no production secrets.

Docker is not available in this sandbox, so the interface reports the actual
state ("not available") instead of faking a successful verification. The real
Docker worker execution lives in worker/runner and is wired in via config.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass
class SandboxResult:
    exit_code: int
    duration_ms: int
    output: str  # sanitized
    status: str  # passed | failed | error | not_available


class NotAvailableError(RuntimeError):
    pass


class SandboxWorker:
    """Interface to the Docker-based verification worker."""

    def __init__(self) -> None:
        self.available = shutil.which("docker") is not None

    def run_check(
        self,
        *,
        command: list[str],
        checkout_path: str,
        timeout: int,
        image: str,
    ) -> SandboxResult:
        if not self.available:
            return SandboxResult(
                exit_code=-1,
                duration_ms=0,
                output="Docker is not available in this environment; sandbox verification could not run.",
                status="not_available",
            )
        raise NotImplementedError(
            "Real Docker worker execution is implemented in worker/runner and wired via config."
        )

    def close(self) -> None:
        pass
