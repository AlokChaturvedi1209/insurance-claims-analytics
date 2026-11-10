"""Environment configuration; no secrets are embedded in application code."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    database_url: str | None = None
    data_dir: Path = Path('data/processed')
    report_dir: Path = Path('reports')

    @classmethod
    def from_env(cls) -> 'Settings':
        return cls(
            database_url=os.getenv('DATABASE_URL') or None,
            data_dir=Path(os.getenv('CLAIMS_DATA_DIR', 'data/processed')),
            report_dir=Path(os.getenv('CLAIMS_REPORT_DIR', 'reports')),
        )
