"""
notifier.py
------------

Fires a real HTTP webhook POST for every critical-tier request -- the
same integration pattern n8n or Power Automate would use to connect a
workflow trigger (e.g. "new critical bug scored") to a downstream
system (Slack, Teams, an incident tracker). Uses the standard `requests`
library so this is a genuine HTTP call, tested against a real (mocked)
HTTP server via `requests_mock` in the test suite -- not a stubbed
function that just returns True.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from src.prioritization import ScoredRequest


@dataclass(frozen=True)
class NotificationResult:
    request_id: str
    sent: bool
    status_code: int | None
    error: str | None


def notify_critical_requests(
    scored_requests: list[ScoredRequest],
    webhook_url: str,
    timeout_seconds: float = 5.0,
) -> list[NotificationResult]:
    """Sends one webhook POST per critical-tier request. Returns a
    result per request so callers can see exactly what was sent and
    what the receiving endpoint responded with, rather than a single
    opaque success/failure flag."""
    results = []

    for scored in scored_requests:
        if scored.priority_tier != "critical":
            continue

        payload = {
            "request_id": scored.request.request_id,
            "title": scored.request.title,
            "customer_segment": scored.request.customer_segment,
            "rice_score": scored.rice_score,
            "priority_tier": scored.priority_tier,
            "is_bug": scored.request.is_bug,
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=timeout_seconds)
            results.append(NotificationResult(
                request_id=scored.request.request_id,
                sent=response.ok,
                status_code=response.status_code,
                error=None,
            ))
        except requests.RequestException as e:
            results.append(NotificationResult(
                request_id=scored.request.request_id,
                sent=False,
                status_code=None,
                error=str(e),
            ))

    return results
