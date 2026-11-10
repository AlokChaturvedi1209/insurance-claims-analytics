"""Generate consistent, deterministic synthetic insurance operations data."""
from pathlib import Path

import numpy as np
import pandas as pd

AS_OF = pd.Timestamp('2026-10-31 23:59:59')
STAGES = ('Intake', 'Verification', 'Assessment', 'Decision')
TYPES = ('Health', 'Motor', 'Travel', 'Home')
STAGE_HOURS = {'Intake': 12, 'Verification': 24, 'Assessment': 48, 'Decision': 24}


def generate(n_claims: int = 50_000, seed: int = 42) -> dict[str, pd.DataFrame]:
    """Generate normalized tables; claims and events are chronological and reproducible.

    Closed claims have all four finished stages. Open claims have one active stage.
    Duration variation represents simulated operations, not real company performance.
    """
    if n_claims < 1:
        raise ValueError('n_claims must be positive')
    rng = np.random.default_rng(seed)
    n_customers = max(10, (n_claims + 2) // 3)
    n_policies = max(n_claims // 2, 10)
    customers = pd.DataFrame({
        'customer_id': [f'C{i:06d}' for i in range(1, n_customers + 1)],
        'city': rng.choice(['Bengaluru','Mumbai','Delhi','Pune','Hyderabad'], n_customers),
        'state': '',
        'customer_segment': rng.choice(['Retail','SME','Corporate'], n_customers, p=[.78,.17,.05]),
    })
    customers['state'] = customers['city'].map({'Bengaluru':'Karnataka','Mumbai':'Maharashtra',
        'Delhi':'Delhi','Pune':'Maharashtra','Hyderabad':'Telangana'})
    policy_types = rng.choice(TYPES, n_policies, p=[.4,.35,.15,.1])
    # Every policy spans all generated claim submission dates.
    policies = pd.DataFrame({
        'policy_id': [f'P{i:06d}' for i in range(1, n_policies + 1)],
        'customer_id': rng.choice(customers['customer_id'].to_numpy(), n_policies),
        'insurance_type': policy_types,
        'coverage_amount': rng.integers(100_000, 2_000_001, n_policies),
        'start_date': ['2025-01-01'] * n_policies,
        'end_date': ['2027-12-31'] * n_policies,
    })
    teams = pd.DataFrame([
        ('T01','North Claims','North'), ('T02','South Claims','South'),
        ('T03','West Claims','West'), ('T04','Central Claims','Central'),
    ], columns=['team_id','team_name','region'])
    rules = pd.DataFrame([{
        'rule_id': f'R{j:03d}', 'insurance_type': kind, 'stage': stage,
        'allowed_hours': int(STAGE_HOURS[stage] * (1.25 if kind == 'Health' else 1)),
        'effective_from': '2025-01-01', 'effective_to': None,
    } for j, (kind, stage) in enumerate(((k,s) for k in TYPES for s in STAGES), 1)])
    claims_rows, events_rows = [], []
    # Use fixed old-enough submission dates for closed claims; recent ones for open claims.
    for i in range(1, n_claims + 1):
        claim_id = f'CL{i:07d}'
        policy_idx = int(rng.integers(0, n_policies))
        policy_id = f'P{policy_idx + 1:06d}'
        kind = str(policy_types[policy_idx])
        team_id = str(rng.choice(teams['team_id'].to_numpy()))
        status = str(rng.choice(['Approved','Rejected','Pending','In Review'], p=[.66,.16,.08,.10]))
        is_closed = status in ('Approved','Rejected')
        day_offset = int(rng.integers(45, 250)) if is_closed else int(rng.integers(0, 20))
        submitted_at = (AS_OF.normalize() - pd.to_timedelta(day_offset, unit='D')
                        + pd.to_timedelta(int(rng.integers(0, 15)), unit='h'))
        cursor = submitted_at
        open_stage = int(rng.integers(0, 4)) if not is_closed else 4
        for s_idx, stage in enumerate(STAGES):
            if s_idx > open_stage:
                break
            entered = cursor
            if s_idx == open_stage and not is_closed:
                exited = None
            else:
                baseline = STAGE_HOURS[stage] * (1.25 if kind == 'Health' else 1)
                # Long-tail delays, including a portion of operational outliers.
                multiplier = float(rng.lognormal(mean=-.35, sigma=.7))
                if rng.random() < .07:
                    multiplier *= 3.5
                hours = max(1, round(baseline * multiplier))
                proposed_exit = entered + pd.to_timedelta(hours, unit='h')
                # An open claim cannot complete a stage beyond the reporting snapshot.
                exited = None if (not is_closed and proposed_exit > AS_OF) else proposed_exit
                if exited is not None:
                    cursor = exited
            events_rows.append((f'E{i:07d}{s_idx}',claim_id,team_id,stage,entered,exited))
            if exited is None:
                break
        closed_at = cursor if is_closed else None
        if is_closed and closed_at > AS_OF:
            raise RuntimeError('Generator produced future closure')
        reasons = ['Missing documents','Coverage exclusion','Invalid details','Duplicate claim']
        claims_rows.append((claim_id,policy_id,team_id,int(rng.integers(2_000,200_001)),
                            submitted_at,closed_at,status,
                            str(rng.choice(reasons)) if status == 'Rejected' else None))
    claims = pd.DataFrame(claims_rows, columns=['claim_id','policy_id','assigned_team_id',
        'claim_amount','submitted_at','closed_at','current_status','rejection_reason'])
    events = pd.DataFrame(events_rows, columns=['event_id','claim_id','team_id',
        'stage','entered_at','exited_at'])
    return {'customers':customers, 'teams':teams,'policies':policies,'claims':claims,
            'claim_events':events,'sla_rules':rules}


def write_csv(tables: dict[str,pd.DataFrame], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(directory / f'{name}.csv', index=False, date_format='%Y-%m-%d %H:%M:%S')
