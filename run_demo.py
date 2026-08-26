"""
run_demo.py
-------------

Entry point that runs the full automation against the synthetic sample
intake queue and prints a summary, so the workflow can be exercised
end-to-end without pytest. Notification step is demoed against a local
httpbin-style echo endpoint by default (webhook.site-style), but is
skipped (webhook_url=None) unless one is supplied, since this script
should not fire real HTTP requests at an arbitrary URL on every run.

Usage:
    python run_demo.py
    python run_demo.py --webhook-url https://your-webhook-endpoint
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.feature_requests import SAMPLE_REQUESTS
from src.workflow import run_pm_workflow


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--webhook-url", default=None, help="Optional webhook URL to notify for critical-tier requests.")
    parser.add_argument("--output", default="dashboard.xlsx", help="Path to write the Excel KPI dashboard to.")
    args = parser.parse_args()

    output_path = Path(args.output)
    result = run_pm_workflow(
        SAMPLE_REQUESTS,
        dashboard_output_path=output_path,
        webhook_url=args.webhook_url,
    )

    print(f"Scored {len(result.scored_requests)} requests from the intake queue.\n")
    print(f"{'ID':<10}{'Tier':<10}{'RICE':<8}{'Title'}")
    print("-" * 70)
    for scored in result.scored_requests:
        print(f"{scored.request.request_id:<10}{scored.priority_tier:<10}{scored.rice_score:<8}{scored.request.title}")

    print(f"\nDashboard written to: {output_path.resolve()}")

    if args.webhook_url:
        print(f"\nNotifications sent to {args.webhook_url}:")
        for n in result.notifications:
            status = f"HTTP {n.status_code}" if n.status_code else f"error: {n.error}"
            print(f"  {n.request_id}: sent={n.sent} ({status})")
    else:
        print("\nNo --webhook-url given -- notification step skipped (not sent to a placeholder).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
