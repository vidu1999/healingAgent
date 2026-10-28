"""Investigation state machine transition tests."""

from app.services.investigation_service import (
    create_investigation,
    transition,
    can_transition,
    is_terminal,
    STATES,
    FAILURE_STATES,
)


def test_state_machine_happy_path(seed, db):
    from app.models.all import Incident
    inc = Incident(title="t", severity="error", status="open", source_type="log", source_ref="s")
    db.add(inc)
    db.flush()
    inv = create_investigation(db, inc.id)
    assert inv.state == "DETECTED"

    inv = transition(db, inv.id, "TRIAGED", actor_user=seed["admin"])
    assert inv.state == "TRIAGED"
    inv = transition(db, inv.id, "INVESTIGATING", actor_user=seed["admin"])
    inv = transition(db, inv.id, "FIX_CANDIDATE_READY", actor_user=seed["admin"])
    inv = transition(db, inv.id, "TEST_GENERATION", actor_user=seed["admin"])
    inv = transition(db, inv.id, "SANDBOX_VALIDATION", actor_user=seed["admin"])
    inv = transition(db, inv.id, "PATCH_VERIFIED", actor_user=seed["admin"])
    inv = transition(db, inv.id, "AWAITING_EXTERNAL_ACTION_APPROVAL", actor_user=seed["admin"])
    inv = transition(db, inv.id, "APPROVED", actor_user=seed["admin"])
    inv = transition(db, inv.id, "EXTERNAL_ACTION_EXECUTING", actor_user=seed["admin"])
    inv = transition(db, inv.id, "AWAITING_RESULT", actor_user=seed["admin"])
    inv = transition(db, inv.id, "COMPLETED", actor_user=seed["admin"])
    assert inv.state == "COMPLETED"
    assert is_terminal("COMPLETED")


def test_invalid_transition_rejected(seed, db):
    from app.models.all import Incident
    inc = Incident(title="t", severity="error", status="open", source_type="log", source_ref="s")
    db.add(inc)
    db.flush()
    inv = create_investigation(db, inc.id)
    # DETECTED -> COMPLETED not allowed
    try:
        transition(db, inv.id, "COMPLETED", actor_user=seed["admin"])
        raise AssertionError("should reject")
    except ValueError:
        pass


def test_failure_states_are_terminalish():
    assert "INVESTIGATION_FAILED" in FAILURE_STATES
    assert "SANDBOX_FAILED" in FAILURE_STATES
    assert "APPROVAL_REJECTED" in FAILURE_STATES


def test_all_declared_states_have_transitions():
    for s in STATES:
        assert s in __import__("app.services.investigation_service", fromlist=["TRANSITIONS"]).TRANSITIONS
