# Power BI Design Specification

## Model Grain And Relationships

The recommended model imports the PostgreSQL views in `sql/003_powerbi_star_schema.sql`.

| From | To | Cardinality | Cross-filter | Key |
| --- | --- | --- | --- | --- |
| `vw_dim_customer` | `vw_dim_policy` | 1:* | Single | `customer_id` |
| `vw_dim_policy` | `vw_fact_claim` | 1:* | Single | `policy_id` |
| `vw_dim_team` | `vw_fact_claim` | 1:* | Single | `team_id` to `assigned_team_id` |
| `vw_fact_claim` | `vw_fact_claim_event` | 1:* | Single | `claim_id` |
| `vw_dim_team` | `vw_fact_claim_event` | 1:* | Single | `team_id` |
| `vw_dim_sla_rule` | `vw_fact_claim_event` | No direct relationship | None | Match is resolved in the view |
| `Calendar` | `vw_fact_claim` | 1:* | Single | `Date` to `Submitted Date` |

Do not create a direct relationship between `vw_fact_claim` and `vw_fact_claim_event` plus a second bidirectional path through policy or team. The claim-to-event relationship is used for drill-through and event detail; `DISTINCTCOUNT(claim_id)` protects claim KPIs from event fan-out.

## Visual Language

- Canvas: 16:9, white `#FFFFFF`, page padding 24 px, visual spacing 16 px.
- Primary navy: `#12304A`; teal accent: `#007C83`; blue secondary: `#2F6B9A`.
- Positive/approved: `#238636`; warning/open: `#D97706`; breach/rejected: `#C2413B`.
- Text: Segoe UI, 11 pt body, 12 pt labels, 18 pt visual titles, 28 pt KPI values, 32 pt page title.
- Use dark text on white and never rely on color alone; include labels or icons for status.
- Format rates as percentages with two decimals, hours with one or two decimals, amounts with local currency formatting only if the report owner selects a currency convention.
- KPI cards use navy labels, dark values, and a small muted denominator subtitle.

## Page A: Executive Overview

- Header: `Claims Operations | Executive Overview` and subtitle `Synthetic data | As of 31 Oct 2026 23:59:59`.
- KPI cards: Total Claims, Closed Approval Rate, Open Claims, Avg Closed Turnaround Hours, Open Claims Older Than 72 Hours.
- Stacked column chart: `Calendar[Month]` by `vw_fact_claim[current_status]`, value `Claims Submitted`; title `Claims Submitted By Month And Status`.
- Clustered bar chart: `vw_fact_claim[insurance_type]` with Total Claims and Closed Approval Rate; title `Portfolio Mix And Closed Approval`.
- Line chart: `Calendar[Month]` with Claims Submitted and Claims Submitted Previous Month; tooltip Claims Submitted MoM %.
- Slicers: submission month, insurance type, customer segment, assigned team.
- Drill-through: claim detail page using `claim_id`, policy, status, amount, dates, and team.
- Interpretation: show volume and service outcomes together. Approval rate is among closed claims only; it is not an approval rate over all claims.

## Page B: SLA And Bottleneck Analysis

- Header: `Claims Operations | SLA And Bottlenecks`.
- KPI cards: Stage SLA Breach Rate, Stage SLA Breaches, Completed Stage SLA Breaches, Overdue Open Stages, Average Completed Stage Hours.
- Bar chart: `vw_fact_claim_event[stage]` with Stage SLA Breach Rate and Stage Events; title `SLA Breach Rate By Stage`.
- Bar chart: `vw_dim_team[team_name]` with Stage SLA Breach Rate and Stage Events; title `SLA Breach Rate By Assigned Team`.
- Scatter chart: stage event volume versus Average Completed Stage Hours, legend stage, size Stage SLA Breaches.
- Table: claim ID, stage, team, entered time, allowed hours, elapsed hours, and breach flag. Filter to open overdue stages for the exception view.
- Slicers: stage, team, insurance type, current status, submission month.
- Drill-through: claim ID to the event sequence; retain one row per stage event.
- Interpretation: prioritize high breach rate and meaningful volume for investigation. These simulated associations do not establish operational causality.

## Page C: Rejection And Root Cause Analysis

- Header: `Claims Operations | Rejection Patterns`.
- KPI cards: Rejected Claims, Rejected Claims % of Closed, Total Claim Amount for selected claims, Average Claim Amount.
- Bar chart: `vw_fact_claim[rejection_reason]` with Rejected Claims; title `Rejected Claims By Recorded Reason`.
- 100% stacked bar: insurance type by rejection reason, value Rejected Claims; title `Reason Mix Within Insurance Type`.
- Matrix: team by rejection reason with Rejected Claims and Rejected Claims % of Closed.
- Table: claim ID, policy ID, insurance type, team, amount, submitted date, rejection reason.
- Slicers: rejection reason, insurance type, team, customer segment, submission month.
- Tooltips: closed denominator, selected claim count, and synthetic-data disclaimer.
- Interpretation: rank recorded reasons as investigation candidates. Do not label them root causes without additional evidence.
