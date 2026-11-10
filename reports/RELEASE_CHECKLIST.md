# Release Checklist

## Cleanup Actions Completed

- Confirmed active workspace:
  the project root.
- Created `reports/PRE_CLEANUP_MANIFEST.md` before cleanup.
- Removed only the approved disposable artifacts:
  `.pytest_cache/`, `.ruff_cache/`, Python `__pycache__/` directories, and
  `src/insurance_claims_analytics.egg-info/`.
- Kept `.venv/`, generated CSV datasets, analytical reports, Docker files,
  PostgreSQL, PBIX, PBIP, report definitions, semantic-model definitions, and
  external Power BI copies unchanged.
- Added `reports/exploratory/*.png` to the generated-artifact ignore rules.
- Initialized a local Git repository. No commit, push, or publication was run.

## Screenshots Verified

All three authentic Power BI screenshots are present and staged:

- `docs/screenshots/01_executive_overview.png`
- `docs/screenshots/02_sla_bottlenecks.png`
- `docs/screenshots/03_rejection_investigation.png`

`docs/screenshots/README.md` now embeds and documents the three captures.

## Validation Results

- Default pytest: **14 passed, 2 skipped** in 4.42 seconds.
- Ruff: **passed**.
- `scripts/validate_data.py`: **passed**.
- `scripts/validate_powerbi_assets.py`: **passed**.
- PostgreSQL integration tests were intentionally not run during cleanup because
  the existing integration tests reload project tables. The previously verified
  PostgreSQL-enabled result remains 16 passing tests.

## PBIX Integrity

- File: `powerbi/claims_operations.pbix`
- Size: `6,432,822` bytes
- SHA-256 before cleanup:
  `BFE6F432C84BEFDBA9677CA8CF638705606C571544056DB5709E99FB879DBA32`
- SHA-256 after cleanup:
  `BFE6F432C84BEFDBA9677CA8CF638705606C571544056DB5709E99FB879DBA32`

The checksum is unchanged. The PBIX was not opened, moved, renamed, modified,
or deleted.

## Excluded From GitHub Staging

- `.env`
- `.venv/`
- `.pytest_cache/`
- `.ruff_cache/`
- Python `__pycache__/` directories
- `src/insurance_claims_analytics.egg-info/`
- `data/processed/*.csv`
- `reports/*.csv`
- `reports/exploratory/*.png`
- Power BI `.pbi/` local settings and caches
- `powerbi/*.pbix`
- PostgreSQL Docker named volume

The editable PBIP descriptor, report definitions, semantic-model metadata, SQL,
Python source, tests, documentation, and authentic dashboard screenshots are
staged.

## Remaining Manual Power BI Checks

- Open the PBIP project and saved PBIX in Power BI Desktop.
- Confirm the PBIP and PBIX represent the same final report.
- Refresh against PostgreSQL on `localhost:5435`.
- Confirm all three pages, relationships, visuals, measures, and slicers.
- Compare cards to the verified KPI and SLA results.

These checks require Power BI Desktop and were not performed by this cleanup.

## GitHub Publishing Readiness

- Local Git repository initialized.
- No commit or publication performed.
- No external Power BI copies or backups modified.
- No production secrets were found in staged source files. `.env.example`
  contains only the intentional local-development configuration template.
- The staged diff check reports pre-existing trailing whitespace and blank-line
  warnings in generated PBIP TMDL files. These were not changed because the
  approved cleanup prohibits modifying Power BI model metadata.
- The README and technical validation report contain the documented local
  PostgreSQL development URL; it matches the non-production Docker template and
  does not contain a production credential.
- Review the complete staged file list and run a final secret scan before the
  first commit.
- Consider distributing the 6.4 MB PBIX as a separate release artifact rather
  than committing it to the main repository.
