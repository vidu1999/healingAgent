"""All SQLAlchemy domain models (single module for clarity).

Tables required by section 10: users, roles, user_roles, sessions,
repositories, repository_credentials_metadata, monitored_sources, log_events,
workflow_runs, incidents, incident_events, investigations, evidence_items,
repair_attempts, generated_tests, patch_artifacts, verification_runs,
verification_checks, approval_requests, approval_decisions, external_actions,
audit_events, notifications, system_settings, background_jobs.

All primary keys are UUID strings. Timestamps are stored in UTC. Deletion of a
user does not cascade to audit_events or incidents (security audit history is
preserved).
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UTCDateTime


class Role(Base):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    user: Mapped["User"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship(back_populates="user_roles")

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)


class Session(Base):
    __tablename__ = "sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True, unique=True)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")


class Repository(Base):
    __tablename__ = "repositories"
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    default_branch: Mapped[str] = mapped_column(String(255), default="main", nullable=False)
    html_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clone_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_write: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    github_installation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    credentials_metadata_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("repository_credentials_metadata.id", ondelete="SET NULL"), nullable=True, index=True
    )

    credentials_metadata: Mapped[Optional["RepositoryCredentialMetadata"]] = relationship(
        foreign_keys=[credentials_metadata_id]
    )
    workflow_runs: Mapped[list["WorkflowRun"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="repository", cascade="all, delete-orphan")


class RepositoryCredentialMetadata(Base):
    """Metadata only - never raw secrets. Encrypted reference points to a
    local secret store; the secret itself is never persisted here in plaintext."""

    __tablename__ = "repository_credentials_metadata"
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE", use_alter=True), nullable=False, index=True, unique=True
    )
    credential_type: Mapped[str] = mapped_column(String(64), nullable=False)  # github_app | fine_grained_pat
    encrypted_reference: Mapped[str] = mapped_column(Text, nullable=False)  # reference/identifier only
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    rotated_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class MonitoredSource(Base):
    __tablename__ = "monitored_sources"
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # file | github
    path: Mapped[str] = mapped_column(Text, nullable=False)  # root path / repo ref
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_ingested_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class LogEvent(Base):
    __tablename__ = "log_events"
    source_id: Mapped[Optional[str]] = mapped_column(ForeignKey("monitored_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    service: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    environment: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)  # redacted message
    trace_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    exception: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # redacted exception
    raw_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[Optional["MonitoredSource"]] = relationship()


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sha: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    trigger: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # queued|in_progress|completed
    conclusion: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # success|failure|cancelled...
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_successful_run_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    repository: Mapped["Repository"] = relationship(back_populates="workflow_runs")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="workflow_run")


class Incident(Base):
    __tablename__ = "incidents"
    repository_id: Mapped[Optional[str]] = mapped_column(ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # debug|info|warning|error|critical
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # open|investigating|resolved|closed
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # log|github|manual
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    repository: Mapped[Optional["Repository"]] = relationship(back_populates="incidents")
    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship(back_populates="incidents")
    events: Mapped[list["IncidentEvent"]] = relationship(back_populates="incident", cascade="all, delete-orphan")
    investigations: Mapped[list["Investigation"]] = relationship(back_populates="incident", cascade="all, delete-orphan")


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    incident: Mapped["Incident"] = relationship(back_populates="events")


class Investigation(Base):
    __tablename__ = "investigations"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(48), nullable=False, index=True)  # state machine state
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    prompt_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # structured investigation output (JSON)
    confidence: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    incident: Mapped["Incident"] = relationship(back_populates="investigations")
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(back_populates="investigation", cascade="all, delete-orphan")
    repair_attempts: Mapped[list["RepairAttempt"]] = relationship(back_populates="investigation", cascade="all, delete-orphan")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # log|file|commit|workflow
    ref: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    investigation: Mapped["Investigation"] = relationship(back_populates="evidence_items")


class RepairAttempt(Base):
    __tablename__ = "repair_attempts"
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(48), nullable=False, index=True)  # pending|generated|verified|rejected|applied|failed
    base_commit_sha: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    patch_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    branch_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pr_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    investigation: Mapped["Investigation"] = relationship(back_populates="repair_attempts")
    generated_tests: Mapped[list["GeneratedTest"]] = relationship(back_populates="repair_attempt", cascade="all, delete-orphan")
    patch_artifacts: Mapped[list["PatchArtifact"]] = relationship(back_populates="repair_attempt", cascade="all, delete-orphan")
    verification_runs: Mapped[list["VerificationRun"]] = relationship(back_populates="repair_attempt", cascade="all, delete-orphan")


class GeneratedTest(Base):
    __tablename__ = "generated_tests"
    repair_attempt_id: Mapped[str] = mapped_column(ForeignKey("repair_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    test_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    repair_attempt: Mapped["RepairAttempt"] = relationship(back_populates="generated_tests")


class PatchArtifact(Base):
    __tablename__ = "patch_artifacts"
    repair_attempt_id: Mapped[str] = mapped_column(ForeignKey("repair_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    diff: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    files_changed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list

    repair_attempt: Mapped["RepairAttempt"] = relationship(back_populates="patch_artifacts")


class VerificationRun(Base):
    __tablename__ = "verification_runs"
    repair_attempt_id: Mapped[str] = mapped_column(ForeignKey("repair_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # running|passed|failed|skipped
    started_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    worker_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    repair_attempt: Mapped["RepairAttempt"] = relationship(back_populates="verification_runs")
    checks: Mapped[list["VerificationCheck"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class VerificationCheck(Base):
    __tablename__ = "verification_checks"
    run_id: Mapped[str] = mapped_column(ForeignKey("verification_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    tool: Mapped[str] = mapped_column(String(128), nullable=False)
    tool_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # sanitized
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # passed|failed|error|skipped

    run: Mapped["VerificationRun"] = relationship(back_populates="checks")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    requesting_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    requesting_role: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    repository_id: Mapped[Optional[str]] = mapped_column(ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True, index=True)
    environment: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resource: Mapped[str] = mapped_column(String(512), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parameters: Mapped[str] = mapped_column(Text, nullable=False)  # JSON exact operation parameters
    base_commit_sha: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    patch_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    payload_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    impact_summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_classification: Mapped[str] = mapped_column(String(32), nullable=False)  # low|medium|high|critical
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # pending|approved|rejected|revoked|expired|consumed
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    approved_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approver_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    audit_correlation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"
    approval_request_id: Mapped[str] = mapped_column(ForeignKey("approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)  # approved|rejected|revoked
    decided_by: Mapped[str] = mapped_column(String(36), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExternalAction(Base):
    __tablename__ = "external_actions"
    approval_request_id: Mapped[str] = mapped_column(ForeignKey("approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # references approved content hash
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # pending|executed|failed|blocked
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # sanitized external result
    executed_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    event_id: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    actor_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(512), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approval_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sanitized_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_audit_events_created_at", "created_at"),
    )


class Notification(Base):
    __tablename__ = "notifications"
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BackgroundJob(Base):
    __tablename__ = "background_jobs"
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # queued|running|completed|failed|retry
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
