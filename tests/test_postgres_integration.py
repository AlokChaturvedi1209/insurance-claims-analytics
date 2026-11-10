"""Opt-in PostgreSQL integration tests; never run against another project by default."""
import os
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from insurance_analytics.config import Settings
from insurance_analytics.database import init_db, load_db, split_sql_statements
from insurance_analytics.generator import generate, write_csv

pytestmark = pytest.mark.skipif(
    os.getenv('RUN_POSTGRES_INTEGRATION') != '1',
    reason='set RUN_POSTGRES_INTEGRATION=1 to run PostgreSQL integration tests',
)


def test_postgres_schema_load_and_counts(tmp_path):
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        pytest.fail('DATABASE_URL is required when RUN_POSTGRES_INTEGRATION=1')
    write_csv(generate(200, seed=42), tmp_path)
    settings = Settings(database_url=database_url, data_dir=tmp_path)
    init_db(settings)
    init_db(settings)
    load_db(settings)
    engine = create_engine(database_url)
    with engine.connect() as connection:
        counts = pd.read_sql(text('SELECT COUNT(*) AS n FROM claims'), connection).iloc[0].n
        events = pd.read_sql(text('SELECT COUNT(*) AS n FROM claim_events'), connection).iloc[0].n
        orphaned = pd.read_sql(text(
            'SELECT COUNT(*) AS n FROM claims c LEFT JOIN policies p USING (policy_id) '
            'WHERE p.policy_id IS NULL'), connection).iloc[0].n
    engine.dispose()
    assert counts == 200
    assert events > counts
    assert orphaned == 0


def test_postgres_full_dataset_repeat_load_integrity_and_views():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        pytest.fail('DATABASE_URL is required when RUN_POSTGRES_INTEGRATION=1')
    root = Path(__file__).resolve().parents[1]
    data_dir = root / 'data' / 'processed'
    settings = Settings(database_url=database_url, data_dir=data_dir)
    init_db(settings)
    load_db(settings)
    load_db(settings)

    engine = create_engine(database_url)
    with engine.begin() as connection:
        counts = {
            name: connection.execute(text(f'SELECT COUNT(*) FROM {name}')).scalar_one()
            for name in ('customers', 'teams', 'policies', 'claims', 'claim_events', 'sla_rules')
        }
        checks = {
            'duplicate_customer_ids': (
                'SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM customers'
            ),
            'duplicate_team_ids': 'SELECT COUNT(*) - COUNT(DISTINCT team_id) FROM teams',
            'duplicate_policy_ids': (
                'SELECT COUNT(*) - COUNT(DISTINCT policy_id) FROM policies'
            ),
            'duplicate_claim_ids': 'SELECT COUNT(*) - COUNT(DISTINCT claim_id) FROM claims',
            'duplicate_event_ids': (
                'SELECT COUNT(*) - COUNT(DISTINCT event_id) FROM claim_events'
            ),
            'duplicate_rule_ids': (
                'SELECT COUNT(*) - COUNT(DISTINCT rule_id) FROM sla_rules'
            ),
            'orphan_customers': (
                'SELECT COUNT(*) FROM policies p LEFT JOIN customers c USING (customer_id) '
                'WHERE c.customer_id IS NULL'
            ),
            'orphan_policies': (
                'SELECT COUNT(*) FROM claims c LEFT JOIN policies p USING (policy_id) '
                'WHERE p.policy_id IS NULL'
            ),
            'orphan_claim_teams': (
                'SELECT COUNT(*) FROM claims c LEFT JOIN teams t '
                'ON c.assigned_team_id = t.team_id WHERE t.team_id IS NULL'
            ),
            'orphan_event_claims': (
                'SELECT COUNT(*) FROM claim_events e LEFT JOIN claims c USING (claim_id) '
                'WHERE c.claim_id IS NULL'
            ),
            'orphan_event_teams': (
                'SELECT COUNT(*) FROM claim_events e LEFT JOIN teams t ON e.team_id = t.team_id '
                'WHERE t.team_id IS NULL'
            ),
            'policy_window_violations': (
                "SELECT COUNT(*) FROM claims c JOIN policies p USING (policy_id) "
                "WHERE c.submitted_at::date NOT BETWEEN p.start_date AND p.end_date"
            ),
            'future_closures': (
                "SELECT COUNT(*) FROM claims "
                "WHERE closed_at > TIMESTAMP '2026-10-31 23:59:59'"
            ),
            'negative_amounts': (
                'SELECT (SELECT COUNT(*) FROM claims '
                'WHERE claim_amount < 0 OR claim_amount IS NULL) + '
                '(SELECT COUNT(*) FROM policies '
                'WHERE coverage_amount < 0 OR coverage_amount IS NULL)'
            ),
            'timestamp_violations': (
                "SELECT COUNT(*) FROM claim_events e JOIN claims c USING (claim_id) "
                "WHERE e.entered_at < c.submitted_at OR e.exited_at < e.entered_at "
                "OR e.exited_at > TIMESTAMP '2026-10-31 23:59:59' "
                "OR (c.closed_at IS NOT NULL AND c.closed_at < c.submitted_at)"
            ),
            'open_stage_duplicates': (
                'SELECT COUNT(*) - COUNT(DISTINCT claim_id) FROM claim_events '
                'WHERE exited_at IS NULL'
            ),
        }
        integrity = {
            name: connection.execute(text(query)).scalar_one()
            for name, query in checks.items()
        }
        stage_order_violations = connection.execute(text("""
            WITH ordered AS (
                SELECT stage, entered_at, exited_at,
                       LAG(stage) OVER (PARTITION BY claim_id ORDER BY entered_at) AS previous_stage,
                       LAG(exited_at) OVER (PARTITION BY claim_id ORDER BY entered_at) AS previous_exit
                FROM claim_events
            )
            SELECT COUNT(*)
            FROM ordered
            WHERE (previous_stage IS NOT NULL AND NOT (
                (previous_stage = 'Intake' AND stage = 'Verification') OR
                (previous_stage = 'Verification' AND stage = 'Assessment') OR
                (previous_stage = 'Assessment' AND stage = 'Decision')
            ))
            OR (previous_exit IS NOT NULL AND previous_exit <> entered_at)
        """)).scalar_one()

        views_sql = (root / 'sql' / '003_powerbi_star_schema.sql').read_text()
        for statement in split_sql_statements(views_sql):
            connection.execute(text(statement))
        view_counts = {
            name: connection.execute(text(f'SELECT COUNT(*) FROM {name}')).scalar_one()
            for name in ('vw_fact_claim', 'vw_fact_claim_event')
        }
        sla_metrics = connection.execute(text("""
            WITH eligible AS (
                SELECT e.exited_at, e.entered_at, r.allowed_hours,
                       COALESCE(e.exited_at, TIMESTAMP '2026-10-31 23:59:59') AS end_at
                FROM claim_events e
                JOIN claims c USING (claim_id)
                JOIN policies p USING (policy_id)
                JOIN sla_rules r ON r.insurance_type = p.insurance_type
                    AND r.stage = e.stage
                    AND e.entered_at::date >= r.effective_from
                    AND (r.effective_to IS NULL OR e.entered_at::date < r.effective_to)
            )
            SELECT COUNT(*) AS events,
                   COUNT(*) FILTER (WHERE exited_at IS NOT NULL) AS completed_events,
                   COUNT(*) FILTER (WHERE end_at > entered_at + allowed_hours * INTERVAL '1 hour') AS breaches,
                   COUNT(*) FILTER (WHERE exited_at IS NOT NULL
                       AND end_at > entered_at + allowed_hours * INTERVAL '1 hour') AS completed_breaches
            FROM eligible
        """)).mappings().one()
        view_columns = connection.execute(text("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN (
                'vw_dim_customer', 'vw_dim_team', 'vw_dim_policy', 'vw_dim_sla_rule',
                'vw_fact_claim', 'vw_fact_claim_event'
              )
        """)).fetchall()
    engine.dispose()

    assert counts == {
        'customers': 16_667, 'teams': 4, 'policies': 25_000,
        'claims': 50_000, 'claim_events': 185_527, 'sla_rules': 16,
    }
    assert all(value == 0 for value in integrity.values())
    assert stage_order_violations == 0
    assert view_counts == {'vw_fact_claim': 50_000, 'vw_fact_claim_event': 185_527}
    assert dict(sla_metrics) == {
        'events': 185_527, 'completed_events': 176_416,
        'breaches': 67_901, 'completed_breaches': 59_722,
    }
    metadata = {(row[0], row[1]): row[2] for row in view_columns}
    assert metadata[('vw_dim_customer', 'customer_id')] == 'text'
    assert metadata[('vw_dim_policy', 'policy_id')] == 'text'
    assert metadata[('vw_dim_team', 'team_id')] == 'text'
    assert metadata[('vw_dim_sla_rule', 'allowed_hours')] == 'integer'
    assert metadata[('vw_fact_claim', 'claim_id')] == 'text'
    assert metadata[('vw_fact_claim_event', 'claim_id')] == 'text'
    assert metadata[('vw_fact_claim_event', 'allowed_hours')] == 'integer'
