# Technical Validation

Validation was run against the existing project and PostgreSQL database. No
dataset was regenerated, Docker configuration was changed, or Power BI asset
was modified.

## Commands Run

```powershell
# DATABASE_URL is read from the ignored local .env file.
$env:RUN_POSTGRES_INTEGRATION='1'
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe scripts\validate_data.py
.\.venv\Scripts\python.exe scripts\validate_powerbi_assets.py
```

## Automated Results

- PostgreSQL-enabled pytest: **16 passed** in 152.41 seconds.
- Ruff: **passed**.
- `scripts/validate_data.py`: **passed**.
- `scripts/validate_powerbi_assets.py`: **passed**.
- PostgreSQL integration verified idempotent schema/load behavior, table
  counts, foreign keys, policy windows, timestamps, stage ordering, star-schema
  views, and both SLA definitions.

## Database Validation

| Table | Rows | Result |
| --- | ---: | --- |
| `customers` | 16,667 | passed |
| `teams` | 4 | passed |
| `policies` | 25,000 | passed |
| `claims` | 50,000 | passed |
| `claim_events` | 185,527 | passed |
| `sla_rules` | 16 | passed |

Foreign-key orphan counts were zero for policies-to-customers,
claims-to-policies, claims-to-teams, events-to-claims, and events-to-teams.
Duplicate primary/business keys were zero. Policy-window violations,
negative amounts, future closures, event timestamp violations, stage-order
violations, and duplicate open stages were all zero.

The fixed reporting timestamp is `2026-10-31 23:59:59`. All generated event
timestamps and closures are at or before that timestamp. Stage transitions are
contiguous, and each claim has at most one active stage.

## KPI Reconciliation

Direct PostgreSQL results and the Python `calculate_metrics` output matched:

| KPI | PostgreSQL/Python result |
| --- | ---: |
| Total claims | 50,000 |
| Approved claims | 32,912 |
| Rejected claims | 7,977 |
| Open claims | 9,111 |
| Closed claims | 40,889 |
| Closed approval rate | 80.49% |
| Closed rejection rate | 19.51% |
| Average closed turnaround | 125.162342 hours, displayed as 125.16 |
| Open claims over 72 hours | 7,744 |

## SLA Validation

All 185,527 events matched exactly one effective SLA rule. The comparison is
strictly greater than `allowed_hours`; completed events use `exited_at`, while
active events use the reporting timestamp.

| Measure | Numerator | Denominator | Rate |
| --- | ---: | ---: | ---: |
| Completed-stage SLA | 59,722 | 176,416 | 33.85% |
| Overall-stage SLA | 67,901 | 185,527 | 36.60% |
| Active-stage component | 8,179 | 9,111 | 89.77% |

The overall numerator reconciles as `59,722 + 8,179 = 67,901`. The two rates
are valid, different definitions: completed-stage SLA excludes active events;
overall-stage SLA includes active events evaluated at the snapshot.

## SQL, Python, and Power BI Asset Checks

- `sql/001_schema.sql` defines the six validated tables and constraints.
- `sql/003_powerbi_star_schema.sql` produced claim and event views with row
  counts of 50,000 and 185,527 respectively.
- Python reports contain the reconciled overall and completed-stage metrics.
- The DAX definitions explicitly distinguish overall and completed-stage SLA
  measures and use the same fixed timestamp and strict comparison.
- Existing fallback CSV exports passed row-count, schema, uniqueness, and KPI
  checks.

## Power BI Files

- `powerbi/claims_operations.pbix` exists and is non-empty: **6,432,822 bytes**.
- `powerbi/claims_operations_final.pbix.pbip` exists: **200 bytes**.
- Its referenced `claims_operations_final.pbix.Report` directory exists and
  contains the report definition, page metadata, three page directories, and
  visual JSON assets.
- `pages.json` contains three page IDs.

These are file and definition checks only. Power BI Desktop was not opened by
this validation, so visual rendering, refresh behavior, slicer interactions,
relationships as materialized in Desktop, and card formatting remain manual
checks.

## Unresolved Issues / Blockers

No automated data, SQL, Python, or lint blockers remain. The only unresolved
items are manual Power BI Desktop checks: open the saved PBIX, refresh against
PostgreSQL on port 5435, confirm all three pages render, and verify the cards
and slicers against the metrics above. This report does not claim those visual
checks were performed.
