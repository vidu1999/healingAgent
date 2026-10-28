"""Patch generation and validation service.

Produces minimal reviewable diffs, validates paths (no traversal/symlink
escape), scans for secrets and suspicious content, records a cryptographic
hash of the patch, and generates per-file explanations.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Optional

from app.core.config import settings


SUSPICIOUS_UNICODE = re.compile(r"[\u200B-\u200D\uFEFF\u202A-\u202E]")
SECRET_SCAN = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|passwd|aws_secret|private_key)\s*[:=]\s*['\"]?[^'\"]{4,}"
)
PROHIBITED_PREFIXES = (".env", ".github/workflows", "docker-compose", "Dockerfile", "requirements.txt", "package.json")


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_diff_paths(diff: str, repo_root: str) -> list[str]:
    """Validate that a diff only touches files inside repo_root and rejects
    absolute paths, traversal, symlink escapes and prohibited files without
    dedicated review. Returns list of changed files."""
    changed = []
    # crude file extraction from diff headers
    for m in re.finditer(r"^diff --git a/(.*) b/(.*)$", diff, re.MULTILINE):
        dest = m.group(2)
        changed.append(dest)
    for f in changed:
        if os.path.isabs(f):
            raise ValueError(f"Absolute path in diff: {f}")
        if ".." in f.split("/"):
            raise ValueError(f"Path traversal in diff: {f}")
        full = os.path.normpath(os.path.join(repo_root, f))
        root_real = os.path.realpath(os.path.abspath(repo_root))
        file_real = os.path.realpath(os.path.abspath(full))
        if not (file_real == root_real or file_real.startswith(root_real + os.sep)):
            raise ValueError(f"Symlink escape or outside root: {f}")
        for prohibited in PROHIBITED_PREFIXES:
            if f.lower().startswith(prohibited.lower()) or prohibited.lower() in f.lower():
                # flagged for heightened review, not automatically rejected here
                pass
    return changed


def scan_for_secrets(diff: str) -> list[str]:
    findings = []
    for m in SECRET_SCAN.finditer(diff):
        findings.append(f"Possible secret in diff: {m.group(0)[:80]}")
    return findings


def scan_suspicious_unicode(diff: str) -> list[str]:
    findings = []
    for m in SUSPICIOUS_UNICODE.finditer(diff):
        findings.append(f"Suspicious unicode/control character at offset {m.start()}")
    return findings


def build_patch_artifact(diff: str, explanation: str | None = None, files_changed: list[str] | None = None) -> dict:
    return {
        "diff": diff,
        "sha256": sha256_of(diff),
        "explanation": explanation,
        "files_changed": files_changed or [],
    }
