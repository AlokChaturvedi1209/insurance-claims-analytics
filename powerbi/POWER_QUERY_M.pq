// Power BI Desktop > Transform data > New source > Blank query.
// Use the PostgreSQL connector with Server=localhost:5435 and Database=claims_analytics.
// Credentials are entered in Power BI Desktop and are intentionally not stored here.

let
    Source = PostgreSQL.Database("localhost:5435", "claims_analytics"),
    Data = Source{[Schema="public", Item="vw_fact_claim"]}[Data],
    AddSubmittedDate = Table.AddColumn(
        Data,
        "Submitted Date",
        each Date.From([submitted_at]),
        type date
    ),
    AddClosedDate = Table.AddColumn(
        AddSubmittedDate,
        "Closed Date",
        each if [closed_at] = null then null else Date.From([closed_at]),
        type date
    )
in
    AddClosedDate

// Repeat the source pattern for these queries, changing Item:
// vw_dim_customer, vw_dim_team, vw_dim_policy, vw_dim_sla_rule,
// vw_fact_claim_event.
// For vw_fact_claim_event, retain the PostgreSQL timestamp and numeric types;
// do not expand events into claim rows or merge it into vw_fact_claim.
