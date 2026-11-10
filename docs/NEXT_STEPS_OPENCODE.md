# OpenCode: next execution instructions

## Current implementation
Foundation, six-table PostgreSQL schema, deterministic synthetic dataset
generator, the full generated 50,000-claim CSV dataset, analytical reports, SQL
analysis examples, CLI, validated PostgreSQL load, and the saved Power BI report
are complete. Current documentation and validation status are summarized in
`reports/TECHNICAL_VALIDATION.md` and `reports/FINAL_VALIDATION.md`.

## Prompt for OpenCode (paste into Build mode)

Inspect the existing independent insurance-claims-analytics project before changing anything. Do not restart, delete, or replace the implemented code without a reason. First create a Python virtual environment, install the project with `pip install -e ".[dev]"`, run `pytest -q`, run `claims-analytics generate --claims 200 --seed 42`, then `claims-analytics analyze`. Fix any failures while preserving the schema and independent structure.

If future work is requested, keep it scoped to this project. Preserve the
synthetic-data disclaimer, the fixed snapshot definitions, the distinction
between completed and overall SLA rates, and the manual Power BI checks called
out in the technical validation report. Do not regenerate or replace the
verified dataset without an explicit request.
