# Pre-Cleanup Manifest

Captured before the approved cleanup actions in the active workspace:
the project root.

## Workspace State

- Git repository present before cleanup: no.
- PostgreSQL/Docker configuration: unchanged.
- Final PBIX: `powerbi/claims_operations.pbix`.
- Final PBIX size: `6,432,822` bytes.
- Final PBIX SHA-256 before cleanup:
  `BFE6F432C84BEFDBA9677CA8CF638705606C571544056DB5709E99FB879DBA32`
- Editable PBIP descriptor:
  `powerbi/claims_operations_final.pbix.pbip`.
- Editable PBIP report directory:
  `powerbi/claims_operations_final.pbix.Report/`.
- Editable PBIP semantic-model directory:
  `powerbi/claims_operations_final.pbix.SemanticModel/`.
- Authentic dashboard screenshots present: three.

## Project Areas

```text
data/raw/                         empty placeholder
data/processed/                   six generated source CSV tables
docs/                             architecture, portfolio, next steps, screenshots
powerbi/                          PBIX, PBIP definitions, DAX, M, design docs
reports/                          validated Markdown, CSV, and exploratory outputs
scripts/                          analytics validation scripts
sql/                              schema, operational SQL, and star-schema views
src/insurance_analytics/          Python generator, analytics, CLI, database tools
tests/                            unit, asset, and PostgreSQL integration tests
```

## Disposable Artifacts Present Before Cleanup

- `.pytest_cache/`
- `.ruff_cache/`
- `scripts/__pycache__/`
- `src/insurance_analytics/__pycache__/`
- `tests/__pycache__/`
- `src/insurance_claims_analytics.egg-info/`

The `.venv/` directory, generated CSV datasets, reports, PBIX, PBIP files, and
Power BI report/semantic-model folders were explicitly excluded from cleanup.
