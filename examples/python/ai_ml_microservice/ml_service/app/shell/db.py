"""Database adapter: fetch one extra feature (``attendance_rate``) by applicant.

Your old ``database.py``. Each builder returns a *fetcher function* of type
``Callable[[str], Optional[float]]`` -- a plain value in, a plain value out,
with ``None`` meaning "no row". Returning a function (rather than doing the
query at import time) lets ``app.wiring`` inject whichever backend the config
selects, and lets tests inject a stub with no database at all.

The real Postgres driver is imported lazily so this module (and the whole app
in in-memory mode) imports fine even when ``psycopg`` isn't installed.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

Fetcher = Callable[[str], Optional[float]]

# Stands in for rows in a Postgres `students` table for the runnable demo.
DEMO_ATTENDANCE: Dict[str, float] = {
    "stu-001": 0.96,
    "stu-002": 0.58,
    "stu-003": 0.31,
    "stu-004": 0.84,
}


def make_inmemory_fetcher(table: Optional[Dict[str, float]] = None) -> Fetcher:
    """Return a fetcher backed by an in-memory dict (demo / tests)."""
    data = dict(DEMO_ATTENDANCE if table is None else table)

    def fetch(applicant_id: str) -> Optional[float]:
        return data.get(applicant_id)

    return fetch


def make_postgres_fetcher(dsn: str) -> Fetcher:
    """Return a fetcher backed by a real Postgres query.

    ``psycopg`` is imported lazily so importing this module never requires the
    driver unless Postgres mode is actually selected.
    """
    import psycopg  # noqa: PLC0415  (intentional lazy import)

    def fetch(applicant_id: str) -> Optional[float]:
        with psycopg.connect(dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT attendance_rate FROM students WHERE id = %s",
                    (applicant_id,),
                )
                row = cursor.fetchone()
        return None if row is None else float(row[0])

    return fetch
