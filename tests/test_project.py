from pathlib import Path

import pandas as pd
import pytest

from insurance_analytics.analysis import calculate_metrics, load_csv
from insurance_analytics.generator import AS_OF, STAGES, generate, write_csv


@pytest.fixture(scope='module')
def data():
    return generate(150, seed=123)


def test_reproducible(data):
    again = generate(150, seed=123)
    pd.testing.assert_frame_equal(data['claims'],again['claims'])


def test_counts_unique_keys(data):
    assert len(data['claims']) == 150
    for table, key in [('claims','claim_id'),('customers','customer_id'),('policies','policy_id'),
                       ('claim_events','event_id'),('teams','team_id'),('sla_rules','rule_id')]:
        assert data[table][key].is_unique


def test_referential_integrity(data):
    assert set(data['claims'].policy_id).issubset(set(data['policies'].policy_id))
    assert set(data['claim_events'].claim_id).issubset(set(data['claims'].claim_id))
    assert set(data['policies'].customer_id).issubset(set(data['customers'].customer_id))


def test_claim_status_and_chronology(data):
    claims=data['claims']
    closed=claims.current_status.isin(['Approved','Rejected'])
    assert claims.loc[closed,'closed_at'].notna().all()
    assert claims.loc[~closed,'closed_at'].isna().all()
    assert (claims.loc[closed,'closed_at'] <= AS_OF).all()
    assert (claims.loc[closed,'closed_at'] >= claims.loc[closed,'submitted_at']).all()
    assert claims.loc[claims.current_status=='Rejected','rejection_reason'].notna().all()


def test_stage_ordering(data):
    for _, group in data['claim_events'].groupby('claim_id',sort=False):
        assert group.stage.tolist() == list(STAGES[:len(group)])
        assert group['exited_at'].isna().sum() <= 1
        for prev, nxt in zip(group.itertuples(),list(group.itertuples())[1:]):
            assert prev.exited_at == nxt.entered_at


def test_metrics_consistent(data):
    reports = calculate_metrics(data)
    s=reports['kpi_summary'].iloc[0]
    assert s.total_claims == 150
    assert s.approved_claims+s.rejected_claims+s.open_claims == 150
    assert reports['stage_performance'].event_count.sum() == len(data['claim_events'])
    assert reports['stage_performance'].sla_breaches.sum() == s.breached_stage_count
    completed = reports['events_enriched']['exited_at'].notna()
    assert completed.sum() == s.completed_stage_event_count
    assert (reports['events_enriched']['sla_breached'] & completed).sum() == s.completed_stage_breach_count
    assert s.completed_stage_breach_count + (
        reports['events_enriched']['sla_breached'] & ~completed
    ).sum() == s.breached_stage_count


def test_csv_roundtrip(tmp_path,data):
    write_csv(data,tmp_path)
    loaded = load_csv(tmp_path)
    assert len(loaded['claims']) == 150
    assert calculate_metrics(loaded)['kpi_summary'].iloc[0].total_claims == 150


def test_invalid_size():
    with pytest.raises(ValueError):
        generate(0)


def test_fixed_snapshot():
    assert str(AS_OF) == '2026-10-31 23:59:59'


def test_schema_exists():
    schema = (Path(__file__).resolve().parents[1] / 'sql' / '001_schema.sql').read_text()
    for name in ('customers','policies','claims','teams','claim_events','sla_rules'):
        assert f'CREATE TABLE IF NOT EXISTS {name}' in schema


def test_open_events_not_in_future(data):
    events = data['claim_events']
    assert (events['entered_at'] <= AS_OF).all()
    assert (events.loc[events['exited_at'].notna(), 'exited_at'] <= AS_OF).all()
    open_claims = data['claims'].loc[data['claims']['closed_at'].isna(), 'claim_id']
    assert (events.loc[events['claim_id'].isin(open_claims)]
            .groupby('claim_id')['exited_at'].apply(lambda col: col.isna().sum()) == 1).all()


def test_no_negative_stage_elapsed(data):
    reports = calculate_metrics(data)
    assert (reports['events_enriched']['elapsed_hours'] >= 0).all()
