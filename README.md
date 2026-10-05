# pm-workflow-automation

A tested Python workflow-automation tool for a Product Management intake
queue: pull feature requests and bugs → score with RICE → build a live Excel
KPI dashboard → notify a webhook for anything critical. The shape is the same
as a low-code automation flow (trigger → transform → branch → act) of the kind
n8n, Power Automate, or Copilot Studio build visually. I implemented it in
code so the logic can be run, tested, and inspected: workflow orchestration,
real HTTP API integration, KPI dashboarding, and structured decision logic.

## What it does

1. **`src/feature_requests.py`** — a synthetic PM intake queue (7
   feature requests/bugs) modeled loosely on a KPI-tracking / asset-monitoring
   product. The data is synthetic sample data I wrote; the workflow is built so
   a real backlog source can replace it.
2. **`src/prioritization.py`** — scores every request with
   [RICE](https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/)
   (`reach × impact × confidence / effort`), a widely used PM
   framework. I added one explicit business rule on top: a bug affecting
   enterprise accounts is always tier "critical" regardless of its raw RICE
   score. This escalation rule is a design choice layered on RICE, not part
   of RICE itself.
3. **`src/excel_dashboard.py`** — builds a two-sheet `.xlsx`
   workbook with `openpyxl`: a "Prioritized Queue" sheet where the
   RICE Score column is a **live spreadsheet formula**
   (`=ROUND((reach*impact*(confidence/100))/effort, 2)`) rather than a
   value computed in Python and pasted in, plus conditional formatting
   that highlights critical/high rows, and a "Summary" sheet with a
   bar chart.
4. **`src/notifier.py`** — fires a `requests.post()` webhook call
   for every critical-tier request, with per-request success/failure
   reporting (not one opaque flag), and handles connection failures
   without crashing the run.
5. **`src/workflow.py`** — orchestrates all of the above into one
   `run_pm_workflow()` call. Notifications are skipped entirely (not
   silently sent to a placeholder) when no webhook URL is given.

## Results

Output of a real run:

```
$ python run_demo.py
Scored 7 requests from the intake queue.

ID        Tier      RICE    Title
----------------------------------------------------------------------
REQ-105   critical  8.55    Sensor firmware update fails silently on reconnect
REQ-102   critical  8.0     Dashboard fails to load for accounts with >500 sensors
REQ-107   high      500.0   Minor typo in weekly report PDF header
REQ-103   high      42.0    Add dark mode to the web dashboard
REQ-101   medium    25.2    Bulk-export asset locations to CSV
REQ-104   medium    17.71   Real-time alert webhook for zone-breach events
REQ-106   low       3.6     Custom KPI widget builder

Dashboard written to: /home/claude/pm-workflow-automation/dashboard.xlsx

No --webhook-url given -- notification step skipped (not sent to a placeholder).
```

The two enterprise bugs (REQ-105, REQ-102) rank above REQ-107 despite
REQ-107's higher raw RICE score, because the critical-bug-escalation rule
takes priority over raw score, as intended.

To also exercise the webhook step against your own endpoint:

```
python run_demo.py --webhook-url https://your-endpoint.example.com/hook
```

## Tests

23 tests, all passing, covering RICE math, the critical-bug-escalation
rule, queue ordering, the Excel workbook's structure, and, as the
strongest check, that the **live spreadsheet formulas evaluate to the
correct numbers**. That check doesn't just read back the formula string from
openpyxl; it converts the generated `.xlsx` to CSV with a LibreOffice
headless process and asserts the *evaluated* values match what
`compute_rice_score()` computes in Python.

The webhook notifier is tested against a mocked HTTP server via
`requests_mock`, covering success, non-2xx responses, and connection errors.

```
pip install -r requirements.txt --break-system-packages
pytest -v
```

```
============================== 23 passed in ~2s ==============================
```

### Regression-test discipline

During development I deliberately broke the RICE-score Excel formula (effort
and reach columns swapped in the formula string) to confirm
`test_rice_formulas_evaluate_to_the_same_values_python_computed` catches a
wrong formula rather than trivially passing. LibreOffice recomputed clearly
wrong values (e.g. `0.24` instead of `8.55`), the test failed as expected, I
restored the formula, and the full 23-test suite passed again.

## Project structure

```
pm-workflow-automation/
├── src/
│   ├── feature_requests.py   # synthetic intake queue
│   ├── prioritization.py     # RICE scoring + critical-bug rule
│   ├── excel_dashboard.py    # openpyxl workbook w/ live formulas + chart
│   ├── notifier.py           # webhook POST via requests
│   └── workflow.py           # orchestration
├── tests/
│   ├── test_prioritization.py
│   ├── test_excel_dashboard.py
│   ├── test_notifier.py
│   └── test_workflow.py
├── run_demo.py
├── requirements.txt
├── pytest.ini
└── .github/workflows/ci.yml
```

## Notes

- RICE behavior on trivial-effort items: `REQ-107` ("fix a typo in a PDF
  header") scores **500.0**, the highest in the queue. The arithmetic is
  correct (`200 reach × 0.25 impact × 100% confidence / 0.1 person-weeks
  effort = 500`) and reflects how naive RICE ranks trivial-effort,
  high-reach items. `test_small_effort_with_high_reach_produces_a_very_high_score`
  in `tests/test_prioritization.py` documents it as expected behavior.
- The tool runs the automation logic in Python; the intake queue is
  synthetic and the webhook step is optional.

## Possible extensions

- Add an effort floor or a human review step before acting on the raw RICE
  ranking automatically.
- Pull the queue from a live source such as Jira or a form instead of the
  synthetic list.
- Export the same flow as a visual n8n or Power Automate workflow.
