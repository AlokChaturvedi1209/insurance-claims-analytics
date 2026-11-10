# Insurance Claims Operations Analytics: Business Insights

## Executive Summary

This report analyzes the verified synthetic snapshot of 50,000 claims as of
`2026-10-31 23:59:59`. It is an operational prioritization analysis, not an
insurer performance assessment. The data supports three immediate management
signals:

1. The open backlog is the most urgent exposure: 7,744 of 9,111 open claims
   (85.00%) are older than 72 hours.
2. Verification has the highest stage breach rate, while Assessment has the
   longest completed-stage duration. These are distinct bottleneck signals.
3. Health produces the largest absolute breach volume and the longest closed
   turnaround; Home has the highest normalized overall breach rate. Category
   comparisons should be investigated before operational policy changes.

The overall stage SLA rate is 67,901 / 185,527 = **36.60%**. The completed-only
rate is 59,722 / 176,416 = **33.85%**. The 8,179 active-stage breaches are
included only in the overall operational-exposure measure. They represent
12.05% of all overall breaches and create a 2.75 percentage-point difference
between the two rates.

## Scope And Method

- Source: existing PostgreSQL tables and verified Python reports only.
- Dataset: synthetic claims, policies, customers, teams, events, and SLA rules.
- Snapshot: `2026-10-31 23:59:59`.
- Closed claim: status `Approved` or `Rejected`.
- Open claim: status `Pending` or `In Review`.
- SLA breach: elapsed time strictly greater than the effective rule's
  `allowed_hours`.
- Completed event elapsed time: `exited_at - entered_at`.
- Active event elapsed time: snapshot timestamp minus `entered_at`.
- Region means the assigned team's region; no claimant geographic region is
  available in the claim fact.

The calculations use the existing joins in `sql/002_operational_queries.sql`,
the effective-rule join in `sql/003_powerbi_star_schema.sql`, and the Python
logic in `src/insurance_analytics/analysis.py`. All event denominators below
are effective-rule-matched events.

## Verified Baseline

| KPI | Numerator | Denominator | Result |
| --- | ---: | ---: | ---: |
| Closed approval rate | 32,912 approved | 40,889 closed | 80.49% |
| Closed rejection rate | 7,977 rejected | 40,889 closed | 19.51% |
| Open claims over 72 hours | 7,744 | 9,111 open | 85.00% |
| Overall stage SLA breach rate | 67,901 breaches | 185,527 events | 36.60% |
| Completed-stage SLA breach rate | 59,722 breaches | 176,416 completed events | 33.85% |
| Active-stage SLA breach rate | 8,179 breaches | 9,111 active events | 89.77% |
| Average closed turnaround | — | 40,889 closed claims | 125.16 hours |

The average-turnaround numerator is not a meaningful additive count and is
therefore shown as an aggregate duration rather than a fabricated sum. The
unrounded PostgreSQL average is 125.162342 hours.

## Findings And Recommendations

### 1. The open backlog is predominantly aged beyond the 72-hour threshold

**Evidence:** 7,744 / 9,111 open claims are older than 72 hours (**85.00%**).
Open claims have a median age of **240 hours** and an average age of **245.21
hours** at the snapshot. The overall open population is 9,111 claims.

**Business impact:** A large share of active work is already outside the
portfolio's 72-hour monitoring threshold. This is a current workload exposure,
not merely a completed-case quality issue.

**Recommendation:** Establish an aging-based daily queue review. Prioritize
open claims by age, current stage, and claim value, and track both the count and
share older than 72 hours. Do not infer that age alone identifies the cause of
delay; case complexity and required documents are not modeled here.

### 2. Active-stage exposure materially changes the SLA story

**Evidence:** Overall SLA breaches are **67,901 / 185,527 = 36.60%**. The
completed-only result is **59,722 / 176,416 = 33.85%**. Active stages contribute
**8,179 / 9,111 = 89.77%** active-stage breaches and **12.05%** of all overall
breaches. The difference between the two rates is **2.75 percentage points**.

**Business impact:** Reporting only completed work would omit current active
exposure. Reporting only the overall rate would mix completed performance with
in-progress risk.

**Recommendation:** Keep two clearly labeled operational KPIs: completed-stage
breach rate for finished-work quality and overall-stage breach rate plus active
overdue count for current exposure. Always display numerator and denominator
with the card or tooltip.

### 3. Verification is the highest-rate overall stage bottleneck

| Stage | Events | Completed | Active | Overall breaches | Overall rate | Completed breaches | Completed rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Intake | 50,000 | 47,632 | 2,368 | 18,128 | 36.26% | 15,836 | 33.25% |
| Verification | 47,632 | 45,115 | 2,517 | 17,564 | **36.87%** | 15,366 | 34.06% |
| Assessment | 45,115 | 42,780 | 2,335 | 16,482 | 36.53% | 14,564 | 34.04% |
| Decision | 42,780 | 40,889 | 1,891 | 15,727 | 36.76% | 13,956 | **34.13%** |

**Business impact:** Verification is the highest-rate stage under the overall
definition, with 17,564 overall breaches and 2,198 overdue active stages.
Decision has the highest completed-only rate at 34.13%, only 0.07 percentage
points above Verification's 34.06%.

**Recommendation:** Review Verification work queues, handoffs, document checks,
and rework loops. Use stage entry and exit timestamps to measure queue age and
repeat handling before changing staffing or SLA policy. The dataset does not
contain workflow reason codes, so it cannot prove why Verification breaches are
higher.

### 4. Assessment is the longest completed stage despite not having the highest breach rate

**Evidence:** Assessment has the highest average completed-stage duration at
**55.10 hours** across 42,780 completed events. Intake averages 13.98 hours,
Verification 27.70 hours, and Decision 27.82 hours. Assessment has 16,482
overall breaches (36.53%), while Verification has a slightly higher rate.

**Business impact:** A stage can be the slowest in elapsed time without having
the highest breach rate because SLA thresholds and stage populations differ.
This separates capacity/throughput investigation from threshold compliance.

**Recommendation:** Monitor Assessment median and p95 duration alongside breach
rate and volume. Investigate case complexity, specialist dependencies, and
handoff waiting time using operational case samples; do not treat the average
alone as proof of a process defect.

### 5. Health is the largest breach-volume and turnaround priority; Home has the highest rate

| Category | Claims | Stage events | Overall breaches | Overall rate | Completed breaches / events | Completed rate | Avg closed hours |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Health | 19,614 | 72,677 | **26,725** | 36.77% | 23,540 / 69,094 | 34.07% | **142.78** |
| Motor | 17,579 | 65,391 | 23,634 | 36.14% | 20,792 / 62,244 | 33.40% | 113.82 |
| Travel | 7,735 | 28,713 | 10,554 | 36.76% | 9,270 / 27,287 | 33.97% | 114.01 |
| Home | 5,072 | 18,746 | 6,988 | **37.28%** | 6,120 / 17,791 | **34.40%** | 113.38 |

Health contributes **26,725 / 67,901 = 39.36%** of all overall breaches and
has a closed average 29.40 hours higher than Home (142.78 versus 113.38).
Home's rate is highest, but its volume is much smaller. Health also has a
95th-percentile closed turnaround of **289 hours**, compared with 228 hours for
Home, based on a direct PostgreSQL percentile calculation using the verified
closed-duration definition.

**Business impact:** Health is the most important volume and turnaround signal;
Home is the highest normalized-rate signal. They should not receive the same
intervention automatically.

**Recommendation:** Segment the next investigation by category and stage.
Review Health's long-tail cases and Home's breach composition, while checking
whether category-specific SLA thresholds, case mix, or documentation needs
explain the observed difference. The synthetic data does not establish a
category cause.

### 6. Team and region differences are narrow, so there is no clear team-level outlier

| Team / region | Claims | Open over 72h | Stage events | Overall breaches | Breach rate | Avg closed hours |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| South Claims / South | 12,518 | **2,014** | 46,398 | **17,039** | **36.72%** | 124.98 |
| West Claims / West | 12,522 | 1,957 | 46,429 | 17,016 | 36.65% | **126.07** |
| Central Claims / Central | 12,536 | 1,966 | 46,470 | 17,012 | 36.61% | 125.16 |
| North Claims / North | 12,424 | 1,807 | 46,230 | 16,834 | **36.41%** | 124.44 |

The team breach-rate spread is only **0.31 percentage points** (36.72% versus
36.41%). South has the most absolute breaches and aged open claims, but also
has similar volume to the other teams. West has the highest average closed
turnaround, only 1.63 hours above North.

**Business impact:** The data does not support labeling one team or region as a
major performance outlier. A team-wide intervention could misallocate effort.

**Recommendation:** Use team-stage and category-adjusted views before changing
team staffing or targets. Start with South's aged queue and West's turnaround
tail as investigation queues, not as causal findings.

### 7. Rejection reasons are nearly evenly distributed; no single root cause is established

| Rejection reason | Rejected claims | Share of 7,977 rejected |
| --- | ---: | ---: |
| Missing documents | **2,018** | **25.30%** |
| Coverage exclusion | 2,001 | 25.08% |
| Duplicate claim | 1,982 | 24.85% |
| Invalid details | 1,976 | 24.77% |

The largest-to-smallest difference is only **42 claims** and **0.53 percentage
points**. Within-category reason shares are similarly close; for example,
Travel's leading reason is Coverage exclusion at 317 / 1,177 = 26.93%, while
Health's leading reason is Duplicate claim at 825 / 3,220 = 25.62%.

**Business impact:** `Missing documents` is the largest recorded reason, but
not by enough to support a single-cause conclusion. The rejection data may be
reflecting balanced synthetic generation rather than a real process pattern.

**Recommendation:** Track rejection reason by category and intake channel,
then sample rejected cases to confirm coding accuracy and document gaps. Add a
first-pass completeness check only after operational evidence confirms that
missing documents are preventable rather than an appropriate eligibility
outcome.

## Priority Actions

1. **Immediate queue control:** publish an aging worklist for the 7,744 open
   claims over 72 hours, with active stage, age, team, category, and next action.
2. **Stage investigation:** review Verification handoffs and Assessment elapsed
   time using event-level samples; measure waiting time separately from active
   handling time where possible.
3. **Category segmentation:** review Health long-tail turnaround and Home breach
   rate by stage before proposing policy or staffing changes.
4. **Measurement discipline:** keep completed and overall SLA metrics separate,
   with explicit numerators and denominators.
5. **Team fairness:** use category- and stage-adjusted comparisons before
   attributing performance differences to teams or regions.

## Recommended Operational KPIs

- Open claims over 72 hours: count and percentage of open claims.
- Active-stage overdue rate: overdue active events / active events, by stage.
- Overall stage SLA breach rate: all breached events / all eligible events.
- Completed-stage SLA breach rate: completed breached events / completed events.
- Stage throughput: completed events, median hours, p95 hours, and breach rate.
- Closed turnaround: median and p95 hours by category and team.
- Closed approval and rejection rates: each with the closed-claim denominator.
- Rejection reason mix: count and percentage by category, team, and intake
  channel when those fields become available.
- Queue aging buckets: 0-24, 24-72, 72-168, and over 168 hours for open work.

## Follow-up Investigations

- Validate whether the synthetic SLA thresholds and category mix make category
  comparisons operationally meaningful.
- Add or inspect case-complexity, document-completeness, rework, handoff, and
  intake-channel fields before making causal claims.
- Sample Verification and Assessment event histories to distinguish waiting,
  review, and rework time.
- Reconcile rejection reason coding against case records; the current dataset
  has labels but no evidence that a label is preventable.
- Monitor team-stage-category interactions over multiple snapshots. This single
  snapshot cannot establish persistence or seasonality.

## Limitations

- All records and performance values are synthetic and must not be presented as
  insurer or regulatory results.
- This is one fixed snapshot, not a time series or service-level trend.
- Correlations and group differences are descriptive associations, not proof of
  causality.
- No staffing, workload complexity, channel, rework, document completeness,
  customer geography, or monetary outcome fields support causal diagnosis.
- Region is assigned-team region, not claimant location.
- Average durations can be influenced by long-tail cases; medians and p95 values
  should be monitored together.

## Reproducibility

The headline results can be reproduced with:

- `sql/002_operational_queries.sql` for status, closed turnaround, active SLA,
  and rejection analysis.
- `src/insurance_analytics/analysis.py` and `python scripts/validate_data.py`
  for Python KPI and stage/team aggregation.
- PostgreSQL joins from `claim_events` to `claims`, `policies`, and the
  effective `sla_rules` on insurance type, stage, and entry date.
- Existing reports: `kpi_summary.csv`, `stage_performance.csv`,
  `team_performance.csv`, and `rejection_reasons.csv`.

No dataset, database schema, or Power BI asset was changed to produce this
report.
