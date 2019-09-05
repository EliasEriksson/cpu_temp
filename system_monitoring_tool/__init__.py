from pathlib import Path
from .manager import create_database


PROJECT_ROOT = Path(__file__).absolute().parent.parent
DATABASE_ADRESS = f'sqlite:////{str(PROJECT_ROOT.joinpath("db.db"))}'

__all__ = ["system_monetoring_tool", "exceptions"]
