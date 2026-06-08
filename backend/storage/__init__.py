"""Shared storage helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SQLITE_BUSY_TIMEOUT_MS = 30_000
_WAL_READY_PATHS: set[str] = set()


def open_sqlite(path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with project-wide contention safeguards."""
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=_SQLITE_BUSY_TIMEOUT_MS / 1000)
    conn.row_factory = sqlite3.Row
    conn.execute(f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")

    key = str(db_path.resolve())
    if key not in _WAL_READY_PATHS:
        conn.execute("PRAGMA journal_mode = WAL")
        _WAL_READY_PATHS.add(key)

    return conn