# Power BI dashboard implementation guide

## Inputs
- Preferred source: PostgreSQL on `localhost:5435`, database `claims_analytics`, using the six views in `sql/003_powerbi_star_schema.sql`.
- Import `reports/claims_enriched.csv` and `reports/events_enriched.csv` for detail-page fallback prototypes.
- Import `reports/kpi_summary.csv`, `reports/stage_performance.csv`, `reports/team_performance.csv`, `reports/monthly_claims.csv`, and `reports/rejection_reasons.csv` for validated fallback prototypes.
- Run `python scripts/validate_powerbi_assets.py` before using the CSV fallback.
- When using both detail and summary outputs, avoid direct relationships that duplicate counts; use the documented star schema for the final report.

## Pages
1. Executive overview: total claims, approved among closed %, open backlog, mean completed turnaround; monthly stacked columns; category slicer.
2. SLA and bottlenecks: stage breach %, average completed stage duration, team breach %; active overdue list; team and stage slicers.
3. Rejections: rejection reason bar chart; types and teams; hypothesis/next-action notes.

## Measures And Definitions

The complete measure set is in `powerbi/MEASURES.dax`. It uses `DISTINCTCOUNT` for claim KPIs so event-level fan-out cannot inflate claim counts. The reporting timestamp is `2026-10-31 23:59:59`. Closed claims are Approved or Rejected; open claims are Pending or In Review. Stage breach rate uses all stage events in the denominator and treats an active event as ending at the reporting timestamp. Completed-stage averages and completed-stage breach measures exclude active events. All selected slicers remain in filter context unless a measure explicitly changes it.

## Desktop walkthrough

1. Run `claims-analytics generate --claims 50000 --seed 42`, then `claims-analytics analyze`.
2. In Power BI Desktop, choose **Get data > PostgreSQL database**, set server `localhost:5435` and database `claims_analytics`, and choose Import.
3. Execute `sql/003_powerbi_star_schema.sql` if the views are absent, then import the six `vw_dim_*` and `vw_fact_*` views.
4. For a CSV prototype, use `claims_enriched.csv` for claim-level visuals and `events_enriched.csv` for stage-level visuals. Do not relate these two detail tables directly because claim rows repeat across events.
5. Use `powerbi/DESIGN_SPEC.md` for the three page layouts and `powerbi/MEASURES.dax` for the measures.
6. Create one-to-many relationships from dimensions to facts with single-direction filtering as specified in `powerbi/DESIGN_SPEC.md`.
7. Validate totals against `reports/kpi_summary.csv`, save the report as `powerbi/claims_operations.pbix`, and capture screenshots if publishing is not available.

## Prepared Assets

- `MEASURES.dax`: complete KPI, SLA, time-comparison, and denominator definitions.
- `DESIGN_SPEC.md`: model relationships, visual specifications, accessibility, and interpretation guardrails.
- `POWER_QUERY_M.pq`: PostgreSQL source and date-column transformation pattern.
- `IMPLEMENTATION_GUIDE.md`: Windows Desktop setup, refresh, validation, and manual save steps.
- `scripts/validate_powerbi_assets.py`: automated fallback export schema, key, row-count, and KPI checks.

The local workspace contains the saved `powerbi/claims_operations.pbix` and a
Power BI project definition. The binary PBIX remains ignored because it is a
6.4 MB local artifact tied to a desktop refresh environment; the SQL views,
DAX, Power Query, PBIP definitions, validation scripts, and setup instructions
remain the reproducible project record. Opening, refreshing, and publishing
still require human interaction with Power BI Desktop.
