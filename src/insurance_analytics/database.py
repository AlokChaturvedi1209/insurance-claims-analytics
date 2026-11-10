"""Optional PostgreSQL schema and bulk loader. Never drops existing databases."""
import re
from pathlib import Path

from sqlalchemy import create_engine, text

from .analysis import load_csv
from .config import Settings

ROOT = Path(__file__).resolve().parents[2]
ORDER = ('customers','teams','policies','claims','claim_events','sla_rules')
_DOLLAR_QUOTE = re.compile(r'\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$')


def split_sql_statements(sql: str) -> list[str]:
    """Split SQL on statement terminators while preserving SQL string contents."""
    statements: list[str] = []
    current: list[str] = []
    index = 0
    quote: str | None = None
    dollar_quote: str | None = None
    block_comment_depth = 0

    while index < len(sql):
        if dollar_quote:
            end = sql.find(dollar_quote, index)
            if end == -1:
                current.append(sql[index:])
                break
            current.append(sql[index:end + len(dollar_quote)])
            index = end + len(dollar_quote)
            dollar_quote = None
            continue

        if block_comment_depth:
            if sql.startswith('/*', index):
                block_comment_depth += 1
                index += 2
            elif sql.startswith('*/', index):
                block_comment_depth -= 1
                index += 2
            else:
                index += 1
            continue

        if quote:
            current.append(sql[index])
            if sql[index] == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    current.append(sql[index + 1])
                    index += 2
                    continue
                quote = None
            index += 1
            continue

        if sql.startswith('--', index):
            newline = sql.find('\n', index)
            index = len(sql) if newline == -1 else newline + 1
            continue
        if sql.startswith('/*', index):
            block_comment_depth = 1
            index += 2
            continue
        if sql[index] in "'\"":
            quote = sql[index]
            current.append(sql[index])
            index += 1
            continue
        dollar_match = _DOLLAR_QUOTE.match(sql, index)
        if dollar_match:
            dollar_quote = dollar_match.group(0)
            current.append(dollar_quote)
            index = dollar_match.end()
            continue
        if sql[index] == ';':
            statement = ''.join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(sql[index])
        index += 1

    statement = ''.join(current).strip()
    if statement:
        statements.append(statement)
    return statements


def init_db(settings: Settings) -> None:
    if not settings.database_url:
        raise ValueError('DATABASE_URL missing; copy .env.example to .env')
    sql = (ROOT / 'sql' / '001_schema.sql').read_text()
    engine = create_engine(settings.database_url)
    with engine.begin() as con:
        for statement in split_sql_statements(sql):
            con.execute(text(statement))
    engine.dispose()


def load_db(settings: Settings) -> None:
    if not settings.database_url:
        raise ValueError('DATABASE_URL missing; copy .env.example to .env')
    tables = load_csv(settings.data_dir)
    engine = create_engine(settings.database_url)
    with engine.begin() as con:
        # Reload deterministic synthetic dataset only; no CASCADE and no external tables.
        for name in reversed(ORDER):
            con.execute(text(f'DELETE FROM {name}'))
        for name in ORDER:
            tables[name].to_sql(name, con, if_exists='append', index=False, chunksize=2000, method='multi')
    engine.dispose()
