from __future__ import annotations

import os
import sys

# --- SQLite fallback for environments where built-in sqlite3 is broken (common on some Anaconda setups)
try:
    import sqlite3  # noqa: F401
except Exception:
    import pysqlite3  # type: ignore
    sys.modules["sqlite3"] = pysqlite3
# --------------------------------------------------------------------

from sqlmodel import SQLModel, create_engine, Session

from .config import settings

os.makedirs("./var", exist_ok=True)

engine = create_engine(settings.db_url, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
