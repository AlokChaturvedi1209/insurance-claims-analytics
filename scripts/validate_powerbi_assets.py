"""Validate the existing CSV fallback exports used by Power BI."""
from pathlib import Path

import pandas as pd

REPORT_DIR = Path('reports')
EXPECTED_ROWS = {
    'claims_enriched': 50_000,
    'events_enriched': 185_527,
    'kpi_summary': 1,
    'stage_performance': 4,
    'team_performance': 4,
    'monthly_claims': 18,
    'rejection_reasons': 4,
}
EXPECTED_COLUMNS = {
    'claims_enriched': {'claim_id', 'policy_id', 'current_status', 'submitted_at', 'closed_at'},
    'events_enriched': {'event_id', 'claim_id', 'stage', 'entered_at', 'exited_at', 'allowed_hours'},
    'kpi_summary': {
        'as_of', 'total_claims', 'approved_claims', 'rejected_claims', 'open_claims',
        'approval_rate_closed_pct', 'avg_closed_turnaround_hours',
        'open_claims_older_than_72h', 'breached_stage_count', 'stage_sla_breach_rate_pct',
        'completed_stage_event_count', 'completed_stage_breach_count',
        'completed_stage_sla_breach_rate_pct',
    },
    'stage_performance': {'stage', 'event_count', 'sla_breaches', 'avg_completed_stage_hours'},
    'team_performance': {'team_name', 'stages', 'breaches', 'breach_rate_pct'},
    'monthly_claims': {'submission_month', 'current_status', 'claim_count'},
    'rejection_reasons': {'rejection_reason', 'claim_count'},
}


def validate_exports(report_dir: Path = REPORT_DIR) -> list[str]:
    errors: list[str] = []
    tables = {}
    for name, expected_rows in EXPECTED_ROWS.items():
        path = report_dir / f'{name}.csv'
        if not path.exists():
            errors.append(f'missing {path}')
            continue
        frame = pd.read_csv(path)
        tables[name] = frame
        missing = EXPECTED_COLUMNS[name] - set(frame.columns)
        if missing:
            errors.append(f'{name} missing columns: {sorted(missing)}')
        if len(frame) != expected_rows:
            errors.append(f'{name} expected {expected_rows} rows, found {len(frame)}')

    for name, key in [('claims_enriched', 'claim_id'), ('events_enriched', 'event_id')]:
        if name in tables and tables[name][key].duplicated().any():
            errors.append(f'{name}.{key} is not unique')

    if 'kpi_summary' in tables:
        kpi = tables['kpi_summary'].iloc[0]
        expected = {
            'total_claims': 50_000, 'approved_claims': 32_912, 'rejected_claims': 7_977,
            'open_claims': 9_111, 'approval_rate_closed_pct': 80.49,
            'avg_closed_turnaround_hours': 125.16, 'open_claims_older_than_72h': 7_744,
            'breached_stage_count': 67_901, 'stage_sla_breach_rate_pct': 36.60,
            'completed_stage_event_count': 176_416, 'completed_stage_breach_count': 59_722,
            'completed_stage_sla_breach_rate_pct': 33.85,
        }
        for field, value in expected.items():
            if round(float(kpi[field]), 2) != round(value, 2):
                errors.append(f'kpi_summary.{field} expected {value}, found {kpi[field]}')
    if 'stage_performance' in tables and 'kpi_summary' in tables:
        if tables['stage_performance']['event_count'].sum() != 185_527:
            errors.append('stage event counts do not reconcile')
        if tables['stage_performance']['sla_breaches'].sum() != 67_901:
            errors.append('stage breach counts do not reconcile')
    return errors


def main() -> int:
    errors = validate_exports()
    if errors:
        for error in errors:
            print(f'FAIL: {error}')
        return 1
    print('Power BI fallback exports passed schema, key, row-count, and KPI validation')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
