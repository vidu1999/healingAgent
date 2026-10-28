"""Approval lifecycle: expiry, invalidation, atomic consume."""

from datetime import timedelta

from app.services.approval_service import (
    create_approval_request,
    decide_approval,
    consume_approval,
    list_approvals,
    _is_valid,
)
from app.core.security import utc_now, expires_in


def test_approval_expires(seed, db):
    req = create_approval_request(
        db,
        requesting_user=seed["admin"],
        requesting_role="admin",
        repository_id=None,
        environment="prod",
        resource="github:owner/repo",
        action_type="github.create_pull_request",
        parameters="{}",
        impact_summary="test",
        risk_classification="medium",
    )
    assert req.status == "pending"
    assert _is_valid(req)
    # force expiry
    req.expires_at = utc_now() - timedelta(seconds=1)
    db.add(req)
    db.flush()
    assert not _is_valid(req)


def test_approve_reject_revoke(seed, db):
    req = create_approval_request(
        db,
        requesting_user=seed["admin"],
        requesting_role="admin",
        repository_id=None,
        environment="prod",
        resource="github:owner/repo",
        action_type="github.create_pull_request",
        parameters="{}",
        impact_summary="test",
        risk_classification="medium",
    )
    decided = decide_approval(db, req.id, "approve", seed["admin"], reason="looks good")
    assert decided.status == "approved"
    assert decided.approved_at is not None

    # cannot re-decide an approved one as pending
    try:
        decide_approval(db, req.id, "reject", seed["admin"], reason="no")
        raise AssertionError("should have raised")
    except ValueError:
        pass

    items, _ = list_approvals(db, status="approved")
    assert any(i.id == req.id for i in items)


def test_consume_atomic(seed, db):
    req = create_approval_request(
        db,
        requesting_user=seed["admin"],
        requesting_role="admin",
        repository_id=None,
        environment="prod",
        resource="github:owner/repo",
        action_type="github.create_pull_request",
        parameters="{}",
        impact_summary="test",
        risk_classification="medium",
    )
    decided = decide_approval(db, req.id, "approve", seed["admin"])
    first = consume_approval(db, req.id)
    assert first.status == "consumed"
    try:
        consume_approval(db, req.id)
        raise AssertionError("second consume should fail")
    except ValueError:
        pass
