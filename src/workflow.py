"""
workflow.py
-------------

The end-to-end automation this project exists to demonstrate: pull
requests from the intake queue -> score with RICE -> build the Excel
KPI dashboard -> notify on anything critical. This is the same shape
as a real n8n or Power Automate flow (trigger -> transform -> branch ->
act), built and tested in Python rather than in a low-code platform.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.feature_requests import FeatureRequest
from src.prioritization import score_all, ScoredRequest
from src.excel_dashboard import build_dashboard
from src.notifier import notify_critical_requests, NotificationResult


@dataclass(frozen=True)
class WorkflowResult:
    scored_requests: list[ScoredRequest]
    dashboard_path: Path
    notifications: list[NotificationResult]


def run_pm_workflow(
    requests: list[FeatureRequest],
    dashboard_output_path: str | Path,
    webhook_url: str | None = None,
) -> WorkflowResult:
    """Runs the full automation. If webhook_url is None, the
    notification step is skipped entirely (no requests sent) rather
    than sent to a placeholder URL -- an explicit choice, not a
    silent no-op that could be mistaken for "notifications sent"."""
    scored = score_all(requests)
    dashboard_path = build_dashboard(scored, dashboard_output_path)

    notifications: list[NotificationResult] = []
    if webhook_url is not None:
        notifications = notify_critical_requests(scored, webhook_url)

    return WorkflowResult(
        scored_requests=scored,
        dashboard_path=dashboard_path,
        notifications=notifications,
    )
