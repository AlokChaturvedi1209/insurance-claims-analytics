"""CLI entrypoint: offline-first with optional PostgreSQL workflow."""
import argparse

from .analysis import calculate_metrics, export_reports, load_csv
from .config import Settings
from .database import init_db, load_db
from .generator import generate, write_csv


def main() -> None:
    parser = argparse.ArgumentParser(description='Insurance claims portfolio analytics')
    sub = parser.add_subparsers(dest='command', required=True)
    generator = sub.add_parser('generate', help='generate reproducible CSV tables')
    generator.add_argument('--claims', type=int, default=50_000)
    generator.add_argument('--seed', type=int, default=42)
    sub.add_parser('analyze', help='calculate metrics and CSV reports')
    sub.add_parser('init-db', help='create PostgreSQL schema')
    sub.add_parser('load-db', help='replace standalone project tables with generated data')
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.command == 'generate':
        tables = generate(args.claims, args.seed)
        write_csv(tables, settings.data_dir)
        print(f'Generated {len(tables["claims"]):,} claims in {settings.data_dir}')
    elif args.command == 'analyze':
        reports = calculate_metrics(load_csv(settings.data_dir))
        export_reports(reports, settings.report_dir)
        print(reports['kpi_summary'].to_string(index=False))
        print(f'Exported {len(reports)} reports to {settings.report_dir}')
    elif args.command == 'init-db':
        init_db(settings)
        print('Schema initialized')
    elif args.command == 'load-db':
        load_db(settings)
        print('Tables loaded')

if __name__ == '__main__':
    main()
