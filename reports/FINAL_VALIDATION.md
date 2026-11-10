# Final Validation

Validation was performed against the existing PostgreSQL database at
`localhost:5435`, database `claims_analytics`, using the fixed reporting timestamp
`2026-10-31 23:59:59`. The existing 50,000-claim dataset was preserved.

## SLA Reconciliation

All 185,527 claim-stage events matched exactly one SLA rule by insurance type,
stage, and effective entry date. There were no missing rules, duplicate rule
joins, or future event timestamps.

| Definition | Numerator | Denominator | Rate |
| --- | ---: | ---: | ---: |
| Overall stage SLA breaches | 67,901 | 185,527 eligible events | 36.60% |
| Completed-stage SLA breaches | 59,722 | 176,416 completed events | 33.85% |
| Active-stage SLA breaches | 8,179 | 9,111 active events | 89.77% |

The overall numerator reconciles exactly: `59,722 + 8,179 = 67,901`.

An event is breached when elapsed time is **strictly greater** than its
effective `allowed_hours`. Completed events use `exited_at`; active events use
the reporting timestamp as their end time. The SQL, Python, star-schema view,
and DAX definitions use the same rule selection and comparison. The generated
dataset has 16 effective rules, one for each insurance-type/stage combination.

### Why Power BI Shows 33.85%

Power BI's `Completed Stage SLA Breach Rate` measure filters out events with a
blank `exited_at`. It therefore calculates `59,722 / 176,416 = 33.85%`.

Power BI's `Stage SLA Breach Rate` measure includes both completed and active
events, using the fixed snapshot for active events. It calculates
`67,901 / 185,527 = 36.60%`. These are different valid KPI definitions, not a
calculation error. The completed-only rate is appropriate for completed work
quality; the overall rate is appropriate when current active-stage exposure is
part of operational monitoring.

## Other KPI Reconciliation

| KPI | Verified result | Definition |
| --- | ---: | --- |
| Total claims | 50,000 | Distinct claim IDs |
| Approved claims | 32,912 | Current status `Approved` |
| Rejected claims | 7,977 | Current status `Rejected` |
| Open claims | 9,111 | Current status `Pending` or `In Review` |
| Closed claims | 40,889 | Current status `Approved` or `Rejected` |
| Closed approval rate | 80.49% | 32,912 / 40,889 |
| Closed rejection rate | 19.51% | 7,977 / 40,889 |
| Average closed turnaround | 125.16 hours | `closed_at - submitted_at` |
| Open claims over 72 hours | 7,744 | Open claims submitted more than 72 hours before snapshot |

The status counts reconcile to 50,000. Closed claims have non-null closure
timestamps and open claims have null closure timestamps. No claim or event
violates the snapshot or chronology checks.

## Changes

- Added completed-event count, completed breach count, and completed breach rate
  to the Python KPI summary and fallback export.
- Added reconciliation assertions for completed and overall SLA definitions to
  the Python and PostgreSQL integration tests.
- Updated Power BI implementation documentation and DAX comments to label the
  two definitions explicitly.
- Fixed the existing pytest import-path/package setup so the full suite can
  collect the Power BI fallback test.

No dashboard metric was changed to force agreement with an expected value.

## Verification Results

- `python scripts/validate_data.py`: passed.
- `python scripts/validate_powerbi_assets.py`: passed.
- `RUN_POSTGRES_INTEGRATION=1 pytest -q`: **16 passed** in 121.50 seconds.
- `ruff check .`: passed.
- PostgreSQL integration checks: passed, including repeat-load integrity,
  50,000 claims, 185,527 events, effective-rule joins, and both SLA KPI
  definitions.

## Remaining Manual Power BI Checks

Open the existing `powerbi/claims_operations.pbix` in Power BI Desktop with
the PostgreSQL source available, refresh, and confirm that all three existing
pages remain present and render. With no slicers selected, compare cards to
the metrics above, especially both 36.60% overall and 33.85% completed-only
rates. Also check that date/type/team slicers affect the intended fact table
without multiplying claim counts. These visual and interaction checks require
Power BI Desktop and were not claimed as visually verified here.
