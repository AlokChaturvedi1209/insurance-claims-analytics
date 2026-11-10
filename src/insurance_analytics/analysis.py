"""File-based analytics; works without PostgreSQL for straightforward evaluation."""
from pathlib import Path

import pandas as pd

from .generator import AS_OF

TABLE_NAMES = ('customers','teams','policies','claims','claim_events','sla_rules')


def load_csv(directory: Path) -> dict[str,pd.DataFrame]:
    data = {}
    dates = {'policies':['start_date','end_date'], 'claims':['submitted_at','closed_at'],
             'claim_events':['entered_at','exited_at'],
             'sla_rules':['effective_from','effective_to']}
    for name in TABLE_NAMES:
        data[name] = pd.read_csv(directory / f'{name}.csv', parse_dates=dates.get(name))
    return data


def calculate_metrics(tables: dict[str,pd.DataFrame], as_of: pd.Timestamp = AS_OF
                      ) -> dict[str,pd.DataFrame]:
    claims = tables['claims'].merge(tables['policies'][['policy_id','insurance_type']],
                                   on='policy_id',validate='many_to_one')
    claims = claims.merge(tables['teams'][['team_id','team_name']],
                          left_on='assigned_team_id',right_on='team_id',validate='many_to_one')
    closed = claims['current_status'].isin(['Approved','Rejected'])
    claims['turnaround_hours'] = ((claims['closed_at'] - claims['submitted_at'])
                                  .dt.total_seconds() / 3600).where(closed)
    claims['pending_age_hours'] = ((as_of - claims['submitted_at'])
                                   .dt.total_seconds() / 3600).where(~closed)
    claims['submission_month'] = claims['submitted_at'].dt.to_period('M').astype(str)

    events = tables['claim_events'].merge(claims[['claim_id','insurance_type','team_name']],
                                         on='claim_id', validate='many_to_one')
    rules = tables['sla_rules'].copy()
    # Match rule effective at event entry; use oldest if multiple? Disallow overlap by checking.
    events = events.merge(rules[['insurance_type','stage','allowed_hours','effective_from','effective_to']],
                          on=['insurance_type','stage'], how='left', validate='many_to_many')
    active = ((events['entered_at'].dt.normalize() >= events['effective_from']) &
        (events['effective_to'].isna() |
         (events['entered_at'].dt.normalize() < events['effective_to'])))
    events = events.loc[active].copy()
    if events['event_id'].duplicated().any():
        raise ValueError('Overlapping effective SLA rules')
    if events['allowed_hours'].isna().any() or len(events) != len(tables['claim_events']):
        raise ValueError('Missing effective SLA rule')
    events['elapsed_hours'] = ((events['exited_at'].fillna(as_of) - events['entered_at'])
                                .dt.total_seconds() / 3600)
    events['sla_breached'] = events['elapsed_hours'] > events['allowed_hours']
    events['is_open_stage'] = events['exited_at'].isna()
    events['closed_stage_hours'] = events['elapsed_hours'].where(~events['is_open_stage'])

    total = len(claims)
    completed_events = ~events['is_open_stage']
    overall_breaches = int(events['sla_breached'].sum())
    completed_breaches = int((events['sla_breached'] & completed_events).sum())
    summary = pd.DataFrame([{
        'as_of':as_of, 'total_claims':total, 'approved_claims':int((claims.current_status=='Approved').sum()),
        'rejected_claims':int((claims.current_status=='Rejected').sum()),
        'open_claims':int((~closed).sum()),
        'approval_rate_closed_pct':round(100*(claims.current_status=='Approved').sum()/max(1,int(closed.sum())),2),
        'avg_closed_turnaround_hours':round(float(claims['turnaround_hours'].mean()),2),
        'open_claims_older_than_72h':int((claims['pending_age_hours']>72).sum()),
        'breached_stage_count':overall_breaches,
        'stage_sla_breach_rate_pct':round(float(events['sla_breached'].mean()*100),2),
        'completed_stage_event_count':int(completed_events.sum()),
        'completed_stage_breach_count':completed_breaches,
        'completed_stage_sla_breach_rate_pct':round(
            100 * completed_breaches / max(1, int(completed_events.sum())), 2
        ),
    }])
    stage = (events.groupby('stage',as_index=False).agg(
        event_count=('event_id','size'),sla_breaches=('sla_breached','sum'),
        avg_completed_stage_hours=('closed_stage_hours','mean')))
    stage['breach_rate_pct'] = (100*stage.sla_breaches/stage.event_count).round(2)
    team = (events.groupby('team_name',as_index=False).agg(
        stages=('event_id','size'), breaches=('sla_breached','sum')))
    team['breach_rate_pct'] = (100*team.breaches/team.stages).round(2)
    monthly = (claims.groupby(['submission_month','current_status'],as_index=False)
               .agg(claim_count=('claim_id','size')))
    rejection = (claims.loc[claims.current_status=='Rejected']
                 .groupby('rejection_reason',as_index=False)
                 .agg(claim_count=('claim_id','size')).sort_values('claim_count',ascending=False))
    return {'claims_enriched':claims, 'events_enriched':events, 'kpi_summary':summary,
            'stage_performance':stage, 'team_performance':team,
            'monthly_claims':monthly, 'rejection_reasons':rejection}


def export_reports(reports: dict[str,pd.DataFrame], directory: Path) -> None:
    directory.mkdir(parents=True,exist_ok=True)
    for name, frame in reports.items():
        frame.to_csv(directory / f'{name}.csv', index=False)
