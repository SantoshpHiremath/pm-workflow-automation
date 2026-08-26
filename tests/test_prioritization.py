"""
tests/test_prioritization.py
-------------------------------

Tests RICE scoring math and the critical-bug-escalation business rule.
"""

from src.feature_requests import FeatureRequest
from src.prioritization import compute_rice_score, score_request, score_all


def _make_request(**overrides) -> FeatureRequest:
    defaults = dict(
        request_id="REQ-TEST", title="Test", description="Test",
        customer_segment="smb", reach_per_quarter=100, impact=1.0,
        confidence_pct=100, effort_person_weeks=1.0, is_bug=False,
    )
    defaults.update(overrides)
    return FeatureRequest(**defaults)


class TestRiceScoreMath:
    def test_basic_rice_calculation(self):
        req = _make_request(reach_per_quarter=100, impact=2.0, confidence_pct=50, effort_person_weeks=5.0)
        # (100 * 2.0 * 0.5) / 5.0 = 20.0
        assert compute_rice_score(req) == 20.0

    def test_full_confidence_and_unit_effort(self):
        req = _make_request(reach_per_quarter=10, impact=1.0, confidence_pct=100, effort_person_weeks=1.0)
        assert compute_rice_score(req) == 10.0

    def test_small_effort_with_high_reach_produces_a_very_high_score(self):
        """Documents a real, known limitation of naive RICE scoring:
        a trivial-effort, high-reach item can outscore substantive
        work. This is correct math, not a bug -- see README."""
        req = _make_request(reach_per_quarter=200, impact=0.25, confidence_pct=100, effort_person_weeks=0.1)
        assert compute_rice_score(req) == 500.0


class TestCriticalBugEscalation:
    def test_enterprise_bug_is_always_critical_regardless_of_rice_score(self):
        req = _make_request(customer_segment="enterprise", is_bug=True,
                             reach_per_quarter=1, impact=0.25, confidence_pct=10, effort_person_weeks=10.0)
        scored = score_request(req)
        assert scored.priority_tier == "critical"

    def test_smb_bug_is_not_automatically_critical(self):
        req = _make_request(customer_segment="smb", is_bug=True,
                             reach_per_quarter=1, impact=0.25, confidence_pct=10, effort_person_weeks=10.0)
        scored = score_request(req)
        assert scored.priority_tier != "critical"

    def test_non_bug_enterprise_request_is_not_automatically_critical(self):
        req = _make_request(customer_segment="enterprise", is_bug=False,
                             reach_per_quarter=1, impact=0.25, confidence_pct=10, effort_person_weeks=10.0)
        scored = score_request(req)
        assert scored.priority_tier != "critical"


class TestScoreAllOrdering:
    def test_critical_items_sort_before_all_others(self):
        low_score_critical = _make_request(
            request_id="A", customer_segment="enterprise", is_bug=True,
            reach_per_quarter=1, impact=0.25, confidence_pct=10, effort_person_weeks=10.0,
        )
        high_score_non_critical = _make_request(
            request_id="B", customer_segment="smb", is_bug=False,
            reach_per_quarter=1000, impact=3.0, confidence_pct=100, effort_person_weeks=0.5,
        )
        scored = score_all([high_score_non_critical, low_score_critical])
        assert scored[0].request.request_id == "A"  # critical wins despite lower raw score

    def test_within_a_tier_sorted_by_descending_rice_score(self):
        higher = _make_request(request_id="HIGH", reach_per_quarter=1000, impact=3.0, confidence_pct=100, effort_person_weeks=1.0)
        lower = _make_request(request_id="LOW", reach_per_quarter=10, impact=1.0, confidence_pct=50, effort_person_weeks=5.0)
        scored = score_all([lower, higher])
        ids_in_order = [s.request.request_id for s in scored]
        assert ids_in_order.index("HIGH") < ids_in_order.index("LOW")
