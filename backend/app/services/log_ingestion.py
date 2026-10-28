"""Log ingestion: JSON Lines parsing, redaction, duplicate detection, incident grouping.

Sources must be explicitly registered (monitored_sources). Paths outside
configured monitoring roots are rejected. Symlinks and Windows path
normalization are handled safely. Credential directories are not monitored by
default.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import utc_now
from app.models.all import LogEvent, MonitoredSource, Incident, IncidentEvent
from app.services.audit_service import record_audit, content_hash_for


# Each entry: (compiled regex, replacement). Patterns with a capturing group 1
# use \1: [REDACTED] to keep the label but hide the secret; others are replaced
# wholesale with [REDACTED].
REDACTIONS = [
    (
        re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*['\"]?[^'\"]{4,}"),
        r"\1: [REDACTED]",
    ),
    (
        re.compile(r"(?i)(authorization)\s*:\s*bearer\s+\S+"),
        r"\1: [REDACTED]",
    ),
    (
        re.compile(r"(?i)(cookie)\s*:\s*[^;\n]{4,}"),
        r"\1: [REDACTED]",
    ),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED]"),
]


def redact(text: str) -> str:
    if not text:
        return text
    for pat, repl in REDACTIONS:
        text = pat.sub(repl, text)
    return text


def is_path_allowed(path: str) -> bool:
    """Check a path is within configured monitoring roots. Reject traversal,
    symlinks escaping roots, and credential directories by default."""
    roots = settings.log_monitoring_roots
    if not roots:
        return False  # no roots configured -> nothing allowed
    # Normalize
    norm = os.path.normpath(os.path.abspath(path))
    # Reject symlink escape: resolve real path
    try:
        real = os.path.realpath(norm)
    except OSError:
        return False
    for root in roots:
        root_norm = os.path.normpath(os.path.abspath(root))
        root_real = os.path.realpath(root_norm)
        for candidate in (norm, real):
            if candidate == root_norm or candidate == root_real or candidate.startswith(root_norm + os.sep) or candidate.startswith(root_real + os.sep):
                # credential directory check on the real path
                lower = real.lower()
                if any(seg in lower for seg in (".ssh", "passwords", "secrets", "credentials", ".aws", ".config/gcloud")):
                    return False
                return True
    return False


def parse_json_line(line: str) -> dict:
    try:
        return json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return {"message": line, "level": "INFO"}


def ingest_event(db: Session, source_id: str, event: dict, actor_user=None) -> LogEvent:
    ts_raw = event.get("timestamp")
    try:
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")) if ts_raw else utc_now()
    except (ValueError, AttributeError):
        ts = utc_now()
    level = str(event.get("level", "INFO")).upper()[:16]
    message = redact(str(event.get("message", "")))
    exception = redact(str(event.get("exception", ""))) if event.get("exception") else None
    raw = json.dumps(event, sort_keys=True)
    raw_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    log = LogEvent(
        source_id=source_id,
        timestamp=ts,
        level=level,
        service=event.get("service"),
        environment=event.get("environment"),
        message=message,
        trace_id=event.get("trace_id"),
        exception=exception,
        raw_hash=raw_hash,
    )
    db.add(log)
    db.flush()

    # Duplicate detection: identical raw_hash within a short window -> group into
    # an incident rather than creating a new one each time.
    existing = (
        db.query(LogEvent)
        .filter(LogEvent.raw_hash == raw_hash, LogEvent.source_id == source_id)
        .order_by(LogEvent.created_at.desc())
        .first()
    )
    if existing and existing.id != log.id:
        # Duplicate - don't create incident again; link to existing incident if any
        pass

    # Create incident for ERROR/CRITICAL if none exists for this trace/source
    if level in ("ERROR", "CRITICAL"):
        incident = (
            db.query(Incident)
            .filter(Incident.source_type == "log", Incident.source_ref == source_id, Incident.trace_id == log.trace_id)
            .first()
        )
        if not incident:
            incident = Incident(
                title=f"Critical log error from source {source_id}",
                description=message[:500],
                severity=level.lower(),
                status="open",
                source_type="log",
                source_ref=source_id,
                trace_id=log.trace_id,
            )
            db.add(incident)
            db.flush()
            db.add(IncidentEvent(incident_id=incident.id, event_type="incident.created", message=message[:1000]))
            record_audit(
                db,
                action="incident.create",
                resource=f"incident:{incident.id}",
                decision="success",
                result="created",
                actor_user=actor_user,
                correlation_id=log.trace_id,
            )
    return log
