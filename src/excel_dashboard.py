"""
excel_dashboard.py
---------------------

Generates a real, formatted Excel KPI dashboard from scored feature
requests -- a Product KPI dashboard built in Excel. Uses openpyxl to write
actual formulas (not pre-computed values baked in from Python), real
conditional formatting, and a real chart, so the output file is a
genuine working spreadsheet a PM could open and use, not a static
screenshot-equivalent.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from src.prioritization import ScoredRequest

HEADER_FILL = PatternFill(start_color="2E5C8A", end_color="2E5C8A", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)
CRITICAL_FILL = PatternFill(start_color="C0392B", end_color="C0392B", fill_type="solid")
HIGH_FILL = PatternFill(start_color="E67E22", end_color="E67E22", fill_type="solid")

COLUMNS = [
    "Request ID", "Title", "Segment", "Is Bug",
    "Reach/Quarter", "Impact", "Confidence %", "Effort (weeks)",
    "RICE Score", "Priority Tier",
]


def build_dashboard(scored_requests: list[ScoredRequest], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    wb = Workbook()

    _build_queue_sheet(wb.active, scored_requests)
    _build_summary_sheet(wb, scored_requests)

    wb.save(output_path)
    return output_path


def _build_queue_sheet(ws, scored_requests: list[ScoredRequest]):
    ws.title = "Prioritized Queue"

    for col_idx, header in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    for row_idx, scored in enumerate(scored_requests, start=2):
        r = scored.request
        ws.cell(row=row_idx, column=1, value=r.request_id)
        ws.cell(row=row_idx, column=2, value=r.title)
        ws.cell(row=row_idx, column=3, value=r.customer_segment)
        ws.cell(row=row_idx, column=4, value="Yes" if r.is_bug else "No")
        ws.cell(row=row_idx, column=5, value=r.reach_per_quarter)
        ws.cell(row=row_idx, column=6, value=r.impact)
        ws.cell(row=row_idx, column=7, value=r.confidence_pct)
        ws.cell(row=row_idx, column=8, value=r.effort_person_weeks)

        # Real Excel formula, not a pre-computed Python value -- so the
        # sheet stays live if a user edits reach/impact/confidence/effort.
        formula = (
            f"=ROUND((E{row_idx}*F{row_idx}*(G{row_idx}/100))/H{row_idx}, 2)"
        )
        ws.cell(row=row_idx, column=9, value=formula)
        ws.cell(row=row_idx, column=10, value=scored.priority_tier)

    last_row = len(scored_requests) + 1
    tier_col = get_column_letter(10)
    tier_range = f"{tier_col}2:{tier_col}{last_row}"

    ws.conditional_formatting.add(
        tier_range,
        CellIsRule(operator="equal", formula=['"critical"'], fill=CRITICAL_FILL, font=Font(color="FFFFFF", bold=True)),
    )
    ws.conditional_formatting.add(
        tier_range,
        CellIsRule(operator="equal", formula=['"high"'], fill=HIGH_FILL),
    )

    for col_idx, header in enumerate(COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(14, len(header) + 2)
    ws.column_dimensions["B"].width = 45


def _build_summary_sheet(wb, scored_requests: list[ScoredRequest]):
    ws = wb.create_sheet("Summary")

    tier_counts: dict[str, int] = {}
    for scored in scored_requests:
        tier_counts[scored.priority_tier] = tier_counts.get(scored.priority_tier, 0) + 1

    ws.cell(row=1, column=1, value="Priority Tier").font = Font(bold=True)
    ws.cell(row=1, column=2, value="Count").font = Font(bold=True)

    tier_order = ["critical", "high", "medium", "low"]
    for row_idx, tier in enumerate(tier_order, start=2):
        ws.cell(row=row_idx, column=1, value=tier)
        ws.cell(row=row_idx, column=2, value=tier_counts.get(tier, 0))

    chart = BarChart()
    chart.title = "Feature Requests by Priority Tier"
    chart.y_axis.title = "Count"
    chart.x_axis.title = "Priority Tier"

    data = Reference(ws, min_col=2, min_row=1, max_row=len(tier_order) + 1)
    categories = Reference(ws, min_col=1, min_row=2, max_row=len(tier_order) + 1)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    ws.add_chart(chart, "D2")

    total_effort = sum(s.request.effort_person_weeks for s in scored_requests)
    ws.cell(row=7, column=1, value="Total effort (person-weeks)").font = Font(bold=True)
    ws.cell(row=7, column=2, value=total_effort)
