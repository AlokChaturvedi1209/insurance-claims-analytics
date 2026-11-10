"""Create lightweight charts and documented observations from synthetic reports."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

REPORT_DIR = Path('reports')
OUTPUT_DIR = REPORT_DIR / 'exploratory'


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    monthly = pd.read_csv(REPORT_DIR / 'monthly_claims.csv')
    stage = pd.read_csv(REPORT_DIR / 'stage_performance.csv')
    rejection = pd.read_csv(REPORT_DIR / 'rejection_reasons.csv')
    kpi = pd.read_csv(REPORT_DIR / 'kpi_summary.csv').iloc[0]

    monthly.pivot(index='submission_month', columns='current_status', values='claim_count').plot(
        kind='bar', stacked=True, figsize=(10, 5), title='Synthetic claims by submission month and status')
    plt.ylabel('Claims')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'monthly_status.png', dpi=120)
    plt.close()

    stage.plot.bar(x='stage', y='breach_rate_pct', legend=False, figsize=(8, 5),
                   title='Synthetic stage SLA breach rate')
    plt.ylabel('Breach rate (%)')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'stage_breaches.png', dpi=120)
    plt.close()

    rejection.plot.barh(x='rejection_reason', y='claim_count', legend=False, figsize=(8, 5),
                        title='Synthetic rejected claims by reason')
    plt.xlabel('Rejected claims')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'rejection_reasons.png', dpi=120)
    plt.close()

    top_stage = stage.sort_values('breach_rate_pct', ascending=False).iloc[0]
    top_reason = rejection.sort_values('claim_count', ascending=False).iloc[0]
    (OUTPUT_DIR / 'INSIGHTS.md').write_text(
        '# Exploratory findings\n\n'
        'These observations describe the reproducible synthetic dataset only; they are not insurer findings.\n\n'
        f'- The dataset contains {int(kpi.total_claims):,} claims and an approval rate of '
        f'{kpi.approval_rate_closed_pct:.2f}% among closed claims.\n'
        f'- {top_stage.stage} has the highest simulated stage breach rate at '
        f'{top_stage.breach_rate_pct:.2f}%.\n'
        f'- `{top_reason.rejection_reason}` is the most common simulated rejection reason '
        f'({int(top_reason.claim_count):,} claims).\n'
        '- These patterns are hypotheses for investigation, not causal conclusions.\n',
        encoding='utf-8',
    )
    print(f'Wrote three charts and INSIGHTS.md to {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
