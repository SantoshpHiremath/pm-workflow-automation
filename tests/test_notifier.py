"""
tests/test_notifier.py
------------------------

Tests the real HTTP webhook call using requests_mock, which intercepts
at the `requests` transport layer -- so notify_critical_requests() runs
its actual code path (building the payload, calling requests.post,
handling the response/exception) against a real mocked HTTP server
rather than a hand-rolled fake.
"""

from __future__ import annotations

import pytest
import requests

from src.feature_requests import FeatureRequest
from src.prioritization import score_all
from src.notifier import notify_critical_requests

WEBHOOK_URL = "https://hooks.example.com/kinexon-pm-alerts"


def _critical_bug():
    return FeatureRequest(
        request_id="REQ-CRIT", title="Critical enterprise bug", description="...",
        customer_segment="enterprise", reach_per_quarter=5, impact=1.0,
        confidence_pct=90, effort_person_weeks=2.0, is_bug=True,
    )


def _non_critical_feature():
    return FeatureRequest(
        request_id="REQ-LOW", title="Nice to have", description="...",
        customer_segment="smb", reach_per_quarter=5, impact=0.25,
        confidence_pct=50, effort_person_weeks=8.0, is_bug=False,
    )


def test_posts_only_for_critical_tier_requests(requests_mock):
    requests_mock.post(WEBHOOK_URL, json={"ok": True}, status_code=200)

    scored = score_all([_critical_bug(), _non_critical_feature()])
    results = notify_critical_requests(scored, WEBHOOK_URL)

    assert len(results) == 1
    assert results[0].request_id == "REQ-CRIT"
    assert requests_mock.call_count == 1


def test_successful_post_returns_sent_true_with_status_code(requests_mock):
    requests_mock.post(WEBHOOK_URL, json={"ok": True}, status_code=200)

    scored = score_all([_critical_bug()])
    results = notify_critical_requests(scored, WEBHOOK_URL)

    assert results[0].sent is True
    assert results[0].status_code == 200
    assert results[0].error is None


def test_payload_sent_matches_the_scored_request(requests_mock):
    requests_mock.post(WEBHOOK_URL, json={"ok": True}, status_code=200)

    scored = score_all([_critical_bug()])
    notify_critical_requests(scored, WEBHOOK_URL)

    sent_json = requests_mock.last_request.json()
    assert sent_json["request_id"] == "REQ-CRIT"
    assert sent_json["priority_tier"] == "critical"
    assert sent_json["is_bug"] is True


def test_non_2xx_response_marks_sent_false_without_raising(requests_mock):
    requests_mock.post(WEBHOOK_URL, status_code=500, text="internal error")

    scored = score_all([_critical_bug()])
    results = notify_critical_requests(scored, WEBHOOK_URL)

    assert results[0].sent is False
    assert results[0].status_code == 500
    assert results[0].error is None


def test_connection_error_is_caught_and_reported_per_request(requests_mock):
    requests_mock.post(WEBHOOK_URL, exc=requests.exceptions.ConnectionError("refused"))

    scored = score_all([_critical_bug()])
    results = notify_critical_requests(scored, WEBHOOK_URL)

    assert results[0].sent is False
    assert results[0].status_code is None
    assert "refused" in results[0].error


def test_no_critical_requests_means_no_http_calls_at_all(requests_mock):
    requests_mock.post(WEBHOOK_URL, json={"ok": True}, status_code=200)

    scored = score_all([_non_critical_feature()])
    results = notify_critical_requests(scored, WEBHOOK_URL)

    assert results == []
    assert requests_mock.call_count == 0
