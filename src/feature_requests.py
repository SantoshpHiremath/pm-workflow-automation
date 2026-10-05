"""
feature_requests.py
---------------------

Synthetic product feature-request/bug-report data, modeled on what a
Product Management team's intake queue actually looks like (a ticket
title, description, requesting customer segment, estimated reach,
confidence, and effort). The data here is synthetic. This is the
"system" this project's workflow automation reads from, analogous to
what an n8n/Power Automate flow would pull from a tool like Jira, a
form, or a spreadsheet.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureRequest:
    request_id: str
    title: str
    description: str
    customer_segment: str  # "enterprise" | "mid_market" | "smb"
    reach_per_quarter: int  # estimated number of users/accounts affected
    impact: float  # 0.25 (minimal) .. 3.0 (massive) -- RICE impact scale
    confidence_pct: int  # 0-100
    effort_person_weeks: float
    is_bug: bool = False


SAMPLE_REQUESTS: list[FeatureRequest] = [
    FeatureRequest(
        request_id="REQ-101",
        title="Bulk-export asset locations to CSV",
        description="Enterprise customers want a one-click export of all real-time asset positions for offline reporting.",
        customer_segment="enterprise",
        reach_per_quarter=42,
        impact=1.0,
        confidence_pct=90,
        effort_person_weeks=1.5,
    ),
    FeatureRequest(
        request_id="REQ-102",
        title="Dashboard fails to load for accounts with >500 sensors",
        description="Timeout error on the KPI dashboard when an account has more than 500 active sensors.",
        customer_segment="enterprise",
        reach_per_quarter=8,
        impact=2.0,
        confidence_pct=100,
        effort_person_weeks=2.0,
        is_bug=True,
    ),
    FeatureRequest(
        request_id="REQ-103",
        title="Add dark mode to the web dashboard",
        description="Multiple smaller accounts have requested a dark theme for extended monitoring sessions.",
        customer_segment="smb",
        reach_per_quarter=120,
        impact=0.5,
        confidence_pct=70,
        effort_person_weeks=1.0,
    ),
    FeatureRequest(
        request_id="REQ-104",
        title="Real-time alert webhook for zone-breach events",
        description="Mid-market customers want a webhook fired the moment an asset breaches a defined safety zone, for integration with their own alerting.",
        customer_segment="mid_market",
        reach_per_quarter=25,
        impact=2.5,
        confidence_pct=85,
        effort_person_weeks=3.0,
    ),
    FeatureRequest(
        request_id="REQ-105",
        title="Sensor firmware update fails silently on reconnect",
        description="After a network drop, sensors sometimes fail to receive a pending firmware update with no error surfaced to the user.",
        customer_segment="enterprise",
        reach_per_quarter=15,
        impact=1.5,
        confidence_pct=95,
        effort_person_weeks=2.5,
        is_bug=True,
    ),
    FeatureRequest(
        request_id="REQ-106",
        title="Custom KPI widget builder",
        description="Let Product Managers on customer accounts build their own KPI widgets without engineering involvement.",
        customer_segment="enterprise",
        reach_per_quarter=18,
        impact=2.0,
        confidence_pct=60,
        effort_person_weeks=6.0,
    ),
    FeatureRequest(
        request_id="REQ-107",
        title="Minor typo in weekly report PDF header",
        description="'Utilizaton' should be 'Utilization' in the auto-generated weekly PDF report.",
        customer_segment="smb",
        reach_per_quarter=200,
        impact=0.25,
        confidence_pct=100,
        effort_person_weeks=0.1,
        is_bug=True,
    ),
]
