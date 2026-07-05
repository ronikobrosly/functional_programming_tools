"""
Imperative shell: persist aggregate results to an in-memory SQLite database.

This module lives in the IMPERATIVE SHELL. All functions perform I/O
(database operations) and are marked with `impure_` prefix.

Following FUNC_PROG_GUIDE §8: persistence is an effect and belongs at
the edges. The core never touches SQLite directly; it produces plain
immutable data that the shell then writes.

Functional programming highlights:
- Core data (frozen dataclasses) flows in; SQL insertion is the effect.
- The database connection is an explicit parameter, not a hidden global.
- All functions return Result types — no exceptions for expected DB errors.
- executemany replaces imperative for-loops with mutable counters — even
  in the shell we prefer declarative operations when possible.
"""

import sqlite3
from collections.abc import Mapping, Sequence

from domain_types import (
    Result,
    success,
    failure,
    UserStatsByCity,
    PostStatsByUser,
)

_VALID_TABLES = frozenset({"user_stats_by_city", "post_stats_by_user"})


def _validate_table_name(table_name: str) -> Result[str]:
    """Validate a table name against the set of known tables.

    Pure guard — prevents SQL injection at the shell boundary by rejecting
    any table name not in the allowlist."""
    if table_name in _VALID_TABLES:
        return success(table_name)
    return failure(
        f"Unknown table: '{table_name}'. Valid tables: {_VALID_TABLES}"
    )


def impure_create_users_table(conn: sqlite3.Connection) -> Result[None]:
    """Create the users_stats table in the database.

    Impure — mutates the database state. Returns success/failure rather
    than letting exceptions propagate."""
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_stats_by_city (
                city TEXT PRIMARY KEY,
                user_count INTEGER NOT NULL
            )
        """)
        conn.commit()
        return success(None)
    except sqlite3.Error as exc:
        return failure(f"Failed to create users table: {exc}")


def impure_create_posts_table(conn: sqlite3.Connection) -> Result[None]:
    """Create the posts_stats table in the database."""
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS post_stats_by_user (
                user_id INTEGER PRIMARY KEY,
                post_count INTEGER NOT NULL,
                avg_body_length REAL NOT NULL
            )
        """)
        conn.commit()
        return success(None)
    except sqlite3.Error as exc:
        return failure(f"Failed to create posts table: {exc}")


def impure_upsert_user_stats(
    conn: sqlite3.Connection,
    stats: tuple[UserStatsByCity, ...],
) -> Result[int]:
    """Insert or replace aggregated user stats in the database.

    Impure — writes to the database. Uses executemany for a single
    batch insert with parameterised queries (no SQL injection surface).

    FP note: This function receives IMMUTABLE data (tuple of frozen
    dataclasses) and performs the write effect. executemany replaces an
    imperative for-loop with a mutable counter — the number of rows
    written is derived from the input length, not accumulated via +=."""
    if not stats:
        return success(0)

    try:
        data = [(row.city, row.user_count) for row in stats]
        conn.executemany(
            """INSERT OR REPLACE INTO user_stats_by_city (city, user_count)
               VALUES (?, ?)""",
            data,
        )
        conn.commit()
        return success(len(data))
    except sqlite3.Error as exc:
        conn.rollback()
        return failure(f"Failed to write user stats: {exc}")


def impure_upsert_post_stats(
    conn: sqlite3.Connection,
    stats: tuple[PostStatsByUser, ...],
) -> Result[int]:
    """Insert or replace aggregated post stats in the database.

    Same pattern as impure_upsert_user_stats — immutable data in,
    batch write via executemany, row count from input length."""
    if not stats:
        return success(0)

    try:
        data = [
            (row.user_id, row.post_count, round(row.avg_body_length, 2))
            for row in stats
        ]
        conn.executemany(
            """INSERT OR REPLACE INTO post_stats_by_user
               (user_id, post_count, avg_body_length) VALUES (?, ?, ?)""",
            data,
        )
        conn.commit()
        return success(len(data))
    except sqlite3.Error as exc:
        conn.rollback()
        return failure(f"Failed to write post stats: {exc}")


def impure_open_database() -> Result[sqlite3.Connection]:
    """Open an in-memory SQLite database and return a connection.

    Impure — creates a new database resource. The connection is an
    explicit dependency passed to subsequent functions (no hidden globals).

    Uses :memory: for an ephemeral database — per the AGENTS.md spec,
    this is an in-memory SQLite instance."""
    try:
        conn = sqlite3.connect(":memory:")
        return success(conn)
    except sqlite3.Error as exc:
        return failure(f"Failed to open in-memory database: {exc}")


def impure_query_table(
    conn: sqlite3.Connection,
    table_name: str,
    limit: int = 10,
) -> Result[tuple[Sequence[str], tuple[tuple[object, ...], ...]]]:
    """Read rows from a table for verification/display.

    Impure — reads from the database. This is used at the end of the
    pipeline to verify that data was written correctly.

    The table name is validated against a known allowlist before use —
    no arbitrary SQL injection, even from shell code."""
    validated = _validate_table_name(table_name)
    if not validated[0]:
        return failure(validated[1])

    try:
        cursor = conn.execute(
            f"SELECT * FROM {validated[1]} LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return success((columns, tuple(rows)))
    except sqlite3.Error as exc:
        return failure(f"Failed to query table '{table_name}': {exc}")
