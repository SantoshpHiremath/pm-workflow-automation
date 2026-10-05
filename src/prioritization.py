"""
prioritization.py
-------------------

Implements RICE scoring (Reach x Impact x Confidence / Effort), a real,
widely-used Product Management prioritization framework (popularized by
Intercom), not an invented scoring scheme. This is the "decision logic"
step a real workflow-automation tool (n8n, Power Automate) would apply
after pulling requests from a queue and before routing/reporting on
them.

RICE score = (reach * impact * confidence_fraction) / effort

Bugs get a priority-tier override: a bug affecting enterprise accounts
is escalated regardless of its raw RICE score, reflecting how PM teams
actually triage -- reliability issues for large accounts don't wait for
a quarterly roadmap score, even if the raw math says otherwise. This
override is a business-rule choice layered on top of RICE; RICE itself
does not define it.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.feature_requests import FeatureRequest

CRITICAL_BUG_SEGMENTS = frozenset({"enterprise"})


@dataclass(frozen=True)
class ScoredRequest:
    request: FeatureRequest
    rice_score: float
    priority_tier: str  # "critical" | "high" | "medium" | "low"


def compute_rice_score(request: FeatureRequest) -> float:
    confidence_fraction = request.confidence_pct / 100.0
    return round(
        (request.reach_per_quarter * request.impact * confidence_fraction)
        / request.effort_person_weeks,
        2,
    )


def _tier_from_score(score: float) -> str:
    if score >= 40:
        return "high"
    if score >= 15:
        return "medium"
    return "low"


def score_request(request: FeatureRequest) -> ScoredRequest:
    rice_score = compute_rice_score(request)

    if request.is_bug and request.customer_segment in CRITICAL_BUG_SEGMENTS:
        tier = "critical"
    else:
        tier = _tier_from_score(rice_score)

    return ScoredRequest(request=request, rice_score=rice_score, priority_tier=tier)


def score_all(requests: list[FeatureRequest]) -> list[ScoredRequest]:
    """Scores every request and returns them sorted: critical tier
    first, then by descending RICE score within each tier -- the order
    a PM would actually want to see a triage queue in."""
    scored = [score_request(r) for r in requests]
    tier_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    scored.sort(key=lambda s: (tier_order[s.priority_tier], -s.rice_score))
    return scored
