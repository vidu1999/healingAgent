"""Central policy engine.

Defines which actions require approval, which roles may perform read-only
operations, and risk classification. Repository content can never change
permissions or approval rules.
"""

from __future__ import annotations

# Actions that ALWAYS require explicit human approval (external mutations).
APPROVAL_REQUIRED_ACTIONS = {
    "github.push_branch",
    "github.create_pull_request",
    "github.update_pull_request",
    "github.post_comment",
    "github.rerun_workflow",
    "github.change_repository_config",
    "github.merge_pull_request",
    "github.trigger_deployment",
    "service.restart",
    "service.isolate",
    "firewall.change",
    "infrastructure.change",
    "notification.send_incident",
}

# Read-only actions that may run automatically within access boundaries.
READ_ONLY_ACTIONS = {
    "github.list_repositories",
    "github.list_workflow_runs",
    "logs.ingest",
    "incidents.list",
    "investigations.read",
    "audit.read",
}


def requires_approval(action_type: str) -> bool:
    return action_type in APPROVAL_REQUIRED_ACTIONS


def risk_classification(action_type: str) -> str:
    high = {
        "github.merge_pull_request",
        "github.trigger_deployment",
        "firewall.change",
        "infrastructure.change",
        "service.isolate",
    }
    return "high" if action_type in high else "medium"
