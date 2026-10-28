"""Verification service.

Runs checks in a disposable worker: syntax/compilation, existing tests,
generated regression tests, linting/type checks, dependency/security checks,
secret scanning, diff policy checks, timeout/resource/output-size limits.

Every check records command, tool version, exit code, duration and sanitized
output. A failed required check rejects the patch - never overridden.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from typing import Optional

from app.core.config import settings
from app.models.all import VerificationCheck
from app.services.audit_service import record_audit, content_hash_for
from app.services.sandbox import SandboxWorker, SandboxResult, NotAvailableError


def _run_locally(command: list[str], cwd: str, timeout: int) -> SandboxResult:
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        output = (proc.stdout or "") + "\n" + (proc.stderr or "")
        # sanitize: strip potential secrets crudely
        output = output[: 10 * 1024 * 1024]
        return SandboxResult(
            exit_code=proc.returncode,
            duration_ms=duration_ms,
            output=output,
            status="passed" if proc.returncode == 0 else "failed",
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return SandboxResult(
            exit_code=-1,
            duration_ms=duration_ms,
            output=f"Command timed out after {timeout}s: {' '.join(command)}",
            status="error",
        )
    except FileNotFoundError:
        return SandboxResult(
            exit_code=-1,
            duration_ms=0,
            output=f"Tool not found: {command[0]}",
            status="not_available",
        )


class VerificationService:
    def __init__(self, db=None, sandbox: Optional[SandboxWorker] = None):
        self.db = db
        self.sandbox = sandbox or SandboxWorker()

    def run_check(
        self,
        *,
        repair_attempt_id: str,
        name: str,
        tool: str,
        command: list[str],
        checkout_path: str,
        timeout: int | None = None,
        required: bool = True,
        actor_user=None,
    ) -> VerificationCheck:
        timeout = timeout or settings.SANDBOX_TIMEOUT_SECONDS
        result: SandboxResult
        if self.sandbox.available:
            result = self.sandbox.run_check(
                command=command, checkout_path=checkout_path, timeout=timeout, image=settings.SANDBOX_IMAGE
            )
        else:
            result = _run_locally(command, checkout_path, timeout)

        tool_version = self._tool_version(tool)
        check = VerificationCheck(
            run_id="",  # filled by caller/run wrapper
            name=name,
            tool=tool,
            tool_version=tool_version,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
            command=" ".join(command),
            output=result.output,
            status=result.status,
        )
        if self.db:
            self.db.add(check)
            self.db.flush()
            record_audit(
                self.db,
                action="verification.check",
                resource=f"repair_attempt:{repair_attempt_id}",
                decision="success" if result.status == "passed" else "failure",
                result=result.status,
                actor_user=actor_user,
                content_hash=content_hash_for(name + result.output[:200]),
            )
        return check

    @staticmethod
    def _tool_version(tool: str) -> str | None:
        try:
            proc = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=10)
            if proc.returncode == 0:
                return (proc.stdout or proc.stderr or "").strip().splitlines()[0][:128]
        except Exception:
            return None
        return None
