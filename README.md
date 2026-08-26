# pm-workflow-automation

A small, real, tested Python workflow-automation tool for a Product
Management intake queue: pull feature requests/bugs → score with RICE
→ build a live Excel KPI dashboard → notify a webhook for anything
critical. The shape is identical to a low-code automation flow
(trigger → transform → branch → act) that a tool like n8n, Power
Automate, or Copilot Studio would build visually — this project
demonstrates the same underlying skills (workflow orchestration, real
HTTP API integration, KPI dashboarding, structured decision logic) in
code that can be run, tested, and inspected.

## Why this project exists

I don't have direct, verifiable experience with n8n, Power Automate,
or Copilot Studio specifically — those are hosted SaaS platforms I
can't install or run inside this build environment, and I didn't want
to claim experience with named tools I can't actually demonstrate.
Rather than leave that gap unaddressed, I built and fully tested the
equivalent automation logic in Python: real scoring rules, a real
generated Excel file with live formulas (not screenshots or
pre-baked values), and a real HTTP webhook call verified against a
mocked server. It's an honest substitute for tool-specific experience,
not a claim of having used those platforms.

## What it actually does

1. **`src/feature_requests.py`** — a synthetic PM intake queue (7
   feature requests/bugs) modeled loosely on a KPI-tracking / asset-
   monitoring product, similar in shape to KINEXON's real-time
   location and asset-monitoring domain. **This is synthetic sample
   data I wrote, not real KINEXON data** — I have no access to
   KINEXON's actual product backlog.
2. **`src/prioritization.py`** — scores every request with
   [RICE](https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/)
   (`reach × impact × confidence / effort`), a real, widely-used PM
   framework, not something invented for this project. Adds one
   explicit business rule on top: a bug affecting enterprise accounts
   is always tier "critical" regardless of its raw RICE score — this
   escalation rule is disclosed as a design choice on top of RICE, not
   part of RICE itself.
3. **`src/excel_dashboard.py`** — builds a real two-sheet `.xlsx`
   workbook with `openpyxl`: a "Prioritized Queue" sheet where the
   RICE Score column is a **live spreadsheet formula**
   (`=ROUND((reach*impact*(confidence/100))/effort, 2)`) rather than a
   value computed in Python and pasted in, plus conditional formatting
   that highlights critical/high rows, and a "Summary" sheet with a
   real bar chart.
4. **`src/notifier.py`** — fires a real `requests.post()` webhook call
   for every critical-tier request, with per-request success/failure
   reporting (not one opaque flag), and handles connection failures
   without crashing the run.
5. **`src/workflow.py`** — orchestrates all of the above into one
   `run_pm_workflow()` call. Notifications are skipped entirely (not
   silently sent to a placeholder) when no webhook URL is given.

## An honest, disclosed limitation of the RICE math

Run the demo and look at `REQ-107` ("fix a typo in a PDF header"): it
scores **500.0** — the single highest score in the whole queue, ahead
of every substantive feature or bug. That's correct arithmetic
(`200 reach × 0.25 impact × 100% confidence / 0.1 person-weeks effort
= 500`), not a bug in this code. It's a known, real limitation of
naive RICE scoring: trivial-effort, high-reach items can dominate the
ranking even when they're clearly not the actual priority. This
project doesn't hide that — `test_small_effort_with_high_reach_produces_a_very_high_score`
in `tests/test_prioritization.py` documents it as expected behavior, and
a real system built on this would need a human sanity-check step or an
effort floor before acting on the raw ranking automatically.

## Verified output (real run, not illustrative)

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

Note the two enterprise bugs (REQ-105, REQ-102) rank above REQ-107
despite REQ-107's higher raw RICE score — the critical-bug-escalation
rule takes priority over raw score, as intended.

To also exercise the webhook step against your own endpoint:

```
python run_demo.py --webhook-url https://your-endpoint.example.com/hook
```

## Testing

23 tests, all passing, covering RICE math, the critical-bug-escalation
rule, queue ordering, the Excel workbook's structure, and — the
strongest check — that the **live spreadsheet formulas actually
evaluate to the correct numbers**. That last check doesn't just read
back the formula string from openpyxl (which would pass even if the
formula were wrong); it converts the generated `.xlsx` to CSV with a
real LibreOffice headless process and asserts the *evaluated* values
match what `compute_rice_score()` computes in Python.

The webhook notifier is tested against a real mocked HTTP server via
`requests_mock`, covering success, non-2xx responses, and connection
errors — not a stub that always returns `True`.

```
pip install -r requirements.txt --break-system-packages
pytest -v
```

```
============================== 23 passed in ~2s ==============================
```

### Regression-test discipline

During development, the RICE-score Excel formula was deliberately
broken (effort and reach columns swapped in the formula string) to
confirm `test_rice_formulas_evaluate_to_the_same_values_python_computed`
actually catches a wrong formula rather than trivially passing —
LibreOffice recomputed clearly wrong values (e.g. `0.24` instead of
`8.55`), the test failed as expected, the fix was restored, and the
full 23-test suite was re-confirmed passing.

## Project structure

```
pm-workflow-automation/
├── src/
│   ├── feature_requests.py   # synthetic intake queue
│   ├── prioritization.py     # RICE scoring + critical-bug rule
│   ├── excel_dashboard.py    # openpyxl workbook w/ live formulas + chart
│   ├── notifier.py           # real webhook POST via requests
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

## What this project is not

- Not a real n8n/Power Automate/Copilot Studio deployment — those are
  hosted low-code platforms this build environment can't access.
- Not built on real KINEXON product data — the intake queue is
  synthetic, written to resemble the domain, and clearly labeled as
  such throughout.
- The RICE scoring, as noted above, has a known naive-math limitation
  around trivial-effort items that a production version would need to
  guard against.
