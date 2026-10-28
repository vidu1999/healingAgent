"""Log ingestion, redaction, path validation tests."""

from app.services.log_ingestion import redact, is_path_allowed
from app.core.config import settings


def test_redaction_hides_secrets():
    text = 'api_key=sk-1234567890abcdef Authorization: Bearer eyJhbGci password=hunter2'
    out = redact(text)
    assert "sk-1234567890abcdef" not in out
    assert "eyJhbGci" not in out
    assert "hunter2" not in out
    assert "[REDACTED]" in out


def test_redaction_preserves_message_shape():
    assert redact("hello world") == "hello world"


def test_is_path_allowed_rejects_when_no_roots(monkeypatch):
    settings.LOG_MONITORING_ROOTS = ""
    assert is_path_allowed("/some/path") is False


def test_is_path_allowed_traversal_rejected(monkeypatch, tmp_path):
    root = tmp_path / "logs"
    root.mkdir()
    settings.LOG_MONITORING_ROOTS = str(root)
    # traversal outside root
    assert is_path_allowed(str(root / ".." / "secret")) is False


def test_ingest_creates_incident_for_critical(client, seed, db):
    from app.models.all import MonitoredSource, Incident
    from app.services.log_ingestion import ingest_event
    from app.services.incident_service import get_incident

    source = MonitoredSource(name="app", source_type="file", path="/var/log/app.log")
    db.add(source)
    db.flush()
    event = {
        "timestamp": "2026-10-27T10:00:00+00:00",
        "level": "CRITICAL",
        "service": "api",
        "environment": "prod",
        "message": "database connection failed api_key=secret123",
        "trace_id": "trace-1",
    }
    actor = seed["admin"]
    log = ingest_event(db, source.id, event, actor_user=actor)
    assert log.level == "CRITICAL"
    assert "secret123" not in log.message
    assert "[REDACTED]" in log.message
    inc = db.query(Incident).filter(Incident.trace_id == "trace-1").first()
    assert inc is not None
    assert inc.severity == "critical"
