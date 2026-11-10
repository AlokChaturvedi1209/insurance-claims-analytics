-- PostgreSQL 16; run once with `claims-analytics init-db`.
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    customer_segment TEXT NOT NULL CHECK (customer_segment IN ('Retail','SME','Corporate'))
);
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    team_name TEXT NOT NULL UNIQUE,
    region TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    insurance_type TEXT NOT NULL CHECK (insurance_type IN ('Health','Motor','Travel','Home')),
    coverage_amount NUMERIC(14,2) NOT NULL CHECK (coverage_amount > 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    CHECK (end_date > start_date)
);
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL REFERENCES policies(policy_id),
    assigned_team_id TEXT NOT NULL REFERENCES teams(team_id),
    claim_amount NUMERIC(14,2) NOT NULL CHECK (claim_amount > 0),
    submitted_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,
    current_status TEXT NOT NULL CHECK (current_status IN ('Approved','Rejected','Pending','In Review')),
    rejection_reason TEXT,
    CHECK (closed_at IS NULL OR closed_at >= submitted_at),
    CHECK ((current_status IN ('Approved','Rejected') AND closed_at IS NOT NULL)
        OR (current_status IN ('Pending','In Review') AND closed_at IS NULL)),
    CHECK ((current_status = 'Rejected' AND rejection_reason IS NOT NULL)
        OR (current_status <> 'Rejected' AND rejection_reason IS NULL))
);
CREATE TABLE IF NOT EXISTS claim_events (
    event_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(claim_id),
    team_id TEXT NOT NULL REFERENCES teams(team_id),
    stage TEXT NOT NULL CHECK (stage IN ('Intake','Verification','Assessment','Decision')),
    entered_at TIMESTAMP NOT NULL,
    exited_at TIMESTAMP,
    CHECK (exited_at IS NULL OR exited_at >= entered_at),
    UNIQUE(claim_id, stage)
);
CREATE TABLE IF NOT EXISTS sla_rules (
    rule_id TEXT PRIMARY KEY,
    insurance_type TEXT NOT NULL CHECK (insurance_type IN ('Health','Motor','Travel','Home')),
    stage TEXT NOT NULL CHECK (stage IN ('Intake','Verification','Assessment','Decision')),
    allowed_hours INTEGER NOT NULL CHECK (allowed_hours > 0),
    effective_from DATE NOT NULL,
    effective_to DATE,
    CHECK (effective_to IS NULL OR effective_to > effective_from),
    UNIQUE(insurance_type, stage, effective_from)
);
CREATE INDEX IF NOT EXISTS ix_claims_submitted ON claims(submitted_at);
CREATE INDEX IF NOT EXISTS ix_claims_status ON claims(current_status);
CREATE INDEX IF NOT EXISTS ix_claims_policy ON claims(policy_id);
CREATE INDEX IF NOT EXISTS ix_events_claim_stage ON claim_events(claim_id, stage);
CREATE INDEX IF NOT EXISTS ix_events_entered ON claim_events(entered_at);
CREATE INDEX IF NOT EXISTS ix_policies_type ON policies(insurance_type);
