# Power BI Desktop Implementation Guide

This guide documents the three-page report workflow from the verified
PostgreSQL database. The saved local report is `powerbi/claims_operations.pbix`;
visual refresh and interaction still require Power BI Desktop.

## 1. Prepare The Database

From Windows PowerShell in the project directory:

```powershell
claims-analytics init-db
claims-analytics load-db
python scripts/validate_data.py
$env:RUN_POSTGRES_INTEGRATION = '1'
pytest -q
```

The repository's configured `.env` supplies the connection for the CLI. Do not paste credentials into Power BI documentation, screenshots, or source files.

## 2. Create The Views

The loader creates base tables. Run `sql/003_powerbi_star_schema.sql` once using a PostgreSQL client if the views are absent. The integration suite also creates and queries them. The views are idempotent and do not copy source data.

## 3. Connect Power BI Desktop

1. Open Power BI Desktop.
2. Select **Get data > PostgreSQL database**.
3. Server: `localhost:5435`; database: `claims_analytics`.
4. Select **Import** for the verified portfolio snapshot. DirectQuery is optional but will query the local Docker database at report-open time.
5. Authenticate using the local database credentials already configured for the project. Do not store credentials in this repository.
6. Select schema `public` and import `vw_dim_customer`, `vw_dim_team`, `vw_dim_policy`, `vw_dim_sla_rule`, `vw_fact_claim`, and `vw_fact_claim_event`.
7. In Power Query, add `Submitted Date = Date.From([submitted_at])` to `vw_fact_claim` or use `powerbi/POWER_QUERY_M.pq`.
8. Create the `Calendar` table and mark it as a date table:

```dax
Calendar = CALENDAR(DATE(2026, 2, 1), DATE(2026, 10, 31))
Year = YEAR('Calendar'[Date])
Month Number = MONTH('Calendar'[Date])
Month = FORMAT('Calendar'[Date], "YYYY-MM")
```

9. Create the relationships in `powerbi/DESIGN_SPEC.md`, all single-direction.
10. Paste the measures from `powerbi/MEASURES.dax` into the model. Set rates to percentage format and hours to one or two decimal places.

## 4. Build The Pages

Use `powerbi/DESIGN_SPEC.md` for every visual's fields, title, slicers, tooltips, drill-through, and interpretation. Keep detail facts separate: never merge claim events into claim rows.

## 5. Validate Before Saving

With no slicers selected, compare the cards to `reports/kpi_summary.csv`: 50,000 claims, 32,912 approved, 7,977 rejected, 9,111 open, 80.49% closed approval, 125.16 average closed hours, 7,744 open claims over 72 hours, 67,901 overall stage breaches across 185,527 events (36.60%), and 59,722 completed-stage breaches across 176,416 completed events (33.85%). The overall rate includes 8,179 breaches from 9,111 active stages evaluated at the fixed snapshot; the completed-only rate excludes those active stages.

The fallback CSV inputs are the existing `reports/claims_enriched.csv`, `reports/events_enriched.csv`, `reports/kpi_summary.csv`, `reports/stage_performance.csv`, `reports/team_performance.csv`, `reports/monthly_claims.csv`, and `reports/rejection_reasons.csv`. Validate them with `python scripts/validate_powerbi_assets.py`.

## 6. Refresh And Save

Use **Home > Refresh** after the database is running and loaded. Save manually as `powerbi/claims_operations.pbix` only after the totals and relationship paths have been checked. Publishing, workspace permissions, scheduled refresh, and screenshots require human Power BI access.
