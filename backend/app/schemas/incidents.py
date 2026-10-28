"""Incident, log, investigation, repair, verification schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------- incidents ----------
class IncidentBase(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    description: str | None = None
    severity: str = Field(default="error")  # debug|info|warning|error|critical
    status: str = Field(default="open")
    source_type: str = Field(default="manual")
    source_ref: str | None = None
    trace_id: str | None = None


class IncidentCreate(IncidentBase):
    repository_id: str | None = None
    workflow_run_id: str | None = None


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    status: str | None = None


class IncidentOut(IncidentBase):
    id: str
    repository_id: str | None = None
    workflow_run_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentEventOut(BaseModel):
    id: str
    incident_id: str
    event_type: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- log ingestion ----------
class LogIngestItem(BaseModel):
    timestamp: str | None = None
    level: str = Field(default="INFO")
    service: str | None = None
    environment: str | None = None
    message: str
    trace_id: str | None = None
    exception: str | None = None


class LogIngestRequest(BaseModel):
    source_id: str
    events: list[LogIngestItem]


class LogIngestResponse(BaseModel):
    ingested: int
    incidents_created: int


# ---------- investigations ----------
class InvestigationCreate(BaseModel):
    incident_id: str


class InvestigationOut(BaseModel):
    id: str
    incident_id: str
    state: str
    model: str | None = None
    confidence: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationDetail(InvestigationOut):
    output: str | None = None
    error: str | None = None


# ---------- repair ----------
class RepairCreate(BaseModel):
    investigation_id: str


class RepairAttemptOut(BaseModel):
    id: str
    investigation_id: str
    status: str
    base_commit_sha: str | None = None
    patch_hash: str | None = None
    branch_name: str | None = None
    pr_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiffOut(BaseModel):
    repair_attempt_id: str
    patch_hash: str
    explanation: str | None = None
    files_changed: list[str] = []
    diff: str


class VerificationCheckOut(BaseModel):
    id: str
    name: str
    tool: str
    tool_version: str | None = None
    exit_code: int | None = None
    duration_ms: int | None = None
    command: str | None = None
    output: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class VerificationRunOut(BaseModel):
    id: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    worker_id: str | None = None
    checks: list[VerificationCheckOut] = []

    model_config = ConfigDict(from_attributes=True)


# ---------- approvals ----------
class ApprovalRequestOut(BaseModel):
    id: str
    requesting_user_id: str | None = None
    requesting_role: str | None = None
    repository_id: str | None = None
    environment: str | None = None
    resource: str
    action_type: str
    parameters: str
    base_commit_sha: str | None = None
    patch_sha256: str | None = None
    payload_hash: str | None = None
    impact_summary: str
    risk_classification: str
    status: str
    created_at: datetime
    expires_at: datetime
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    revoked_at: datetime | None = None
    approver_id: str | None = None
    audit_correlation_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalAction(BaseModel):
    reason: str | None = None


# ---------- audit ----------
class AuditEventOut(BaseModel):
    event_id: str
    actor_user_id: str | None = None
    actor_role: str | None = None
    action: str
    resource: str
    decision: str
    reason_code: str | None = None
    approval_reference: str | None = None
    correlation_id: str | None = None
    result: str
    duration_ms: int | None = None
    content_hash: str | None = None
    sanitized_error: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- repositories ----------
class RepositoryBase(BaseModel):
    name: str
    full_name: str
    owner: str
    default_branch: str = "main"
    html_url: str | None = None
    clone_url: str | None = None
    allow_write: bool = False


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryOut(RepositoryBase):
    id: str
    is_active: bool
    github_installation_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- workflow runs ----------
class WorkflowRunOut(BaseModel):
    id: str
    repository_id: str
    run_id: str
    name: str
    branch: str
    sha: str
    trigger: str | None = None
    status: str
    conclusion: str | None = None
    url: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int
    last_successful_run_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------- dashboard ----------
class DashboardSummary(BaseModel):
    active_incidents: int
    critical_errors: int
    failed_workflows: int
    recent_repair_attempts: int
    pending_approvals: int
    verification_rate: str
    integrations: list[dict]


# ---------- system ----------
class OllamaStatus(BaseModel):
    reachable: bool
    model_available: bool
    model: str
    error: str | None = None
    mode: str  # live | unavailable | demo
