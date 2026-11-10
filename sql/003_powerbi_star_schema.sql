-- Optional Power BI-friendly views. Run after 001_schema.sql; views do not copy data.
CREATE OR REPLACE VIEW vw_dim_customer AS SELECT * FROM customers;
CREATE OR REPLACE VIEW vw_dim_team AS SELECT * FROM teams;
CREATE OR REPLACE VIEW vw_dim_policy AS SELECT * FROM policies;
CREATE OR REPLACE VIEW vw_dim_sla_rule AS SELECT * FROM sla_rules;
CREATE OR REPLACE VIEW vw_fact_claim AS
SELECT c.*, p.insurance_type, p.customer_id
FROM claims c JOIN policies p USING (policy_id);
CREATE OR REPLACE VIEW vw_fact_claim_event AS
SELECT e.*, c.policy_id, c.current_status, p.insurance_type,
    r.rule_id, r.allowed_hours, r.effective_from, r.effective_to
FROM claim_events e
JOIN claims c USING (claim_id)
JOIN policies p USING (policy_id)
JOIN sla_rules r ON r.insurance_type = p.insurance_type
    AND r.stage = e.stage
    AND e.entered_at::date >= r.effective_from
    AND (r.effective_to IS NULL OR e.entered_at::date < r.effective_to);
