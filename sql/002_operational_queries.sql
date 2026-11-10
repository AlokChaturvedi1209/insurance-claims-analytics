-- Reusable SQL analyses for PostgreSQL / Power BI direct import.
-- As-of date is fixed for reproducible demonstration: 2026-10-31 23:59:59.

-- 1. Claim status breakdown by insurance type.
SELECT p.insurance_type, c.current_status, COUNT(*) AS claim_count,
       SUM(c.claim_amount) AS total_claim_amount
FROM claims c JOIN policies p ON c.policy_id = p.policy_id
GROUP BY p.insurance_type, c.current_status
ORDER BY p.insurance_type, claim_count DESC;

-- 2. Closed claim turnaround with per-type ranking.
WITH closed_claims AS (
 SELECT c.claim_id, p.insurance_type, c.assigned_team_id,
        EXTRACT(EPOCH FROM (c.closed_at - c.submitted_at))/3600 AS turnaround_hours
 FROM claims c JOIN policies p USING (policy_id)
 WHERE c.closed_at IS NOT NULL
)
SELECT *, DENSE_RANK() OVER (PARTITION BY insurance_type ORDER BY turnaround_hours DESC) AS delay_rank
FROM closed_claims;

-- 3. Active stage SLA breach monitor, using valid effective rule.
SELECT e.claim_id, e.stage, t.team_name, r.allowed_hours,
       ROUND((EXTRACT(EPOCH FROM (TIMESTAMP '2026-10-31 23:59:59' - e.entered_at))/3600)::numeric,2)
         AS open_hours,
       (TIMESTAMP '2026-10-31 23:59:59' - e.entered_at) > r.allowed_hours * INTERVAL '1 hour'
         AS is_breached
FROM claim_events e JOIN claims c USING (claim_id)
JOIN policies p USING (policy_id)
JOIN teams t ON e.team_id = t.team_id
JOIN sla_rules r ON r.insurance_type = p.insurance_type AND r.stage = e.stage
 AND e.entered_at::date >= r.effective_from
 AND (r.effective_to IS NULL OR e.entered_at::date < r.effective_to)
WHERE e.exited_at IS NULL;

-- 4. Root-cause candidate: frequency of rejected-claim reasons.
SELECT rejection_reason, COUNT(*) AS rejections,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),2) AS pct_of_rejections
FROM claims WHERE current_status='Rejected'
GROUP BY rejection_reason ORDER BY rejections DESC;
