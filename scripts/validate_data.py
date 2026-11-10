"""Validate generated tables and analytical aggregates for this project."""
from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import pandas as pd

from insurance_analytics.analysis import calculate_metrics, load_csv
from insurance_analytics.generator import AS_OF, STAGES


def validate(tables: dict[str, pd.DataFrame]) -> list[str]:
    """Return validation failures; an empty list means the data is valid."""
    errors: list[str] = []
    keys = {
        'customers': 'customer_id', 'teams': 'team_id', 'policies': 'policy_id',
        'claims': 'claim_id', 'claim_events': 'event_id', 'sla_rules': 'rule_id',
    }
    for table, key in keys.items():
        if tables[table][key].duplicated().any():
            errors.append(f'{table}.{key} is not unique')

    checks = [
        ('policies.customer_id', tables['policies']['customer_id'], tables['customers']['customer_id']),
        ('claims.policy_id', tables['claims']['policy_id'], tables['policies']['policy_id']),
        ('claims.assigned_team_id', tables['claims']['assigned_team_id'], tables['teams']['team_id']),
        ('claim_events.claim_id', tables['claim_events']['claim_id'], tables['claims']['claim_id']),
        ('claim_events.team_id', tables['claim_events']['team_id'], tables['teams']['team_id']),
    ]
    for name, values, targets in checks:
        if not values.isin(set(targets)).all():
            errors.append(f'{name} has orphaned foreign keys')

    policies = tables['policies'].set_index('policy_id')
    claims = tables['claims']
    claim_policies = policies.loc[claims['policy_id']]
    submitted_dates = claims['submitted_at'].dt.normalize()
    if not ((submitted_dates >= claim_policies['start_date'].reset_index(drop=True)) &
            (submitted_dates <= claim_policies['end_date'].reset_index(drop=True))).all():
        errors.append('claim submissions fall outside policy time windows')

    if claims.loc[claims['closed_at'].notna(), 'closed_at'].gt(AS_OF).any():
        errors.append('closed claims include a future closure')
    if claims.loc[claims['closed_at'].notna(), 'closed_at'].lt(
            claims.loc[claims['closed_at'].notna(), 'submitted_at']).any():
        errors.append('closed claims precede submission')

    events = tables['claim_events']
    for claim_id, group in events.groupby('claim_id', sort=False):
        stages = group['stage'].tolist()
        if stages != list(STAGES[:len(stages)]):
            errors.append(f'{claim_id} has invalid claim-stage ordering')
        if group['exited_at'].isna().sum() > 1:
            errors.append(f'{claim_id} has multiple active stages')
        rows = list(group.itertuples())
        for previous, current in itertools.pairwise(rows):
            if previous.exited_at != current.entered_at:
                errors.append(f'{claim_id} has a stage time gap')
    if events['entered_at'].gt(AS_OF).any() or events['exited_at'].dropna().gt(AS_OF).any():
        errors.append('claim events include future timestamps')

    reports = calculate_metrics(tables)
    summary = reports['kpi_summary'].iloc[0]
    if summary.total_claims != len(claims):
        errors.append('KPI total does not match claims')
    if summary.approved_claims + summary.rejected_claims + summary.open_claims != len(claims):
        errors.append('KPI status counts do not reconcile')
    if reports['stage_performance']['event_count'].sum() != len(events):
        errors.append('stage event counts do not reconcile')
    if reports['stage_performance']['sla_breaches'].sum() != summary.breached_stage_count:
        errors.append('stage breach counts do not reconcile')
    completed = reports['events_enriched']['exited_at'].notna()
    completed_breaches = int((reports['events_enriched']['sla_breached'] & completed).sum())
    if int(completed.sum()) != summary.completed_stage_event_count:
        errors.append('completed stage event counts do not reconcile')
    if completed_breaches != summary.completed_stage_breach_count:
        errors.append('completed stage breach counts do not reconcile')
    if summary.completed_stage_breach_count + int(
        (reports['events_enriched']['sla_breached'] & ~completed).sum()
    ) != summary.breached_stage_count:
        errors.append('completed and active stage breach definitions do not reconcile')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate synthetic insurance claim tables')
    parser.add_argument('--data-dir', type=Path, default=Path('data/processed'))
    args = parser.parse_args()
    errors = validate(load_csv(args.data_dir))
    if errors:
        for error in errors:
            print(f'FAIL: {error}')
        return 1
    print('Validation passed: keys, foreign keys, policy windows, stages, timestamps, and metrics')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
