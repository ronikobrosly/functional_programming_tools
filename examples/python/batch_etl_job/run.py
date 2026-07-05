"""
Imperative shell: CLI entry point for the batch ETL job.

This module is the IMPERATIVE SHELL. It performs effects:
- Reads CLI arguments (sys.argv)
- Fetches data from the network
- Writes to the database
- Prints output (stdout)

Following FUNC_PROG_GUIDE §1 (functional core, imperative shell):
The shell is thin — it gathers inputs, delegates to pure core functions,
and performs the effects the core's output describes.

Usage:
    python run.py users    # Fetch users, transform with Polars, save to SQLite
    python run.py posts    # Fetch posts, transform with pure Python, save to SQLite

Functional programming notes are inline throughout.
"""

import sys
import sqlite3

from domain_types import (
    Result,
    success,
    failure,
    is_err,
    parse_job_type,
    JobType,
    JobConfig,
)
from orchestrate import resolve_job_config
from json_fetcher import (
    impure_fetch_raw,
    impure_parse_json_list,
    parse_user_records,
    parse_post_records,
)
from user_transformer import transform_users
from post_transformer import transform_posts
from sqlite_saver import (
    impure_open_database,
    impure_create_users_table,
    impure_create_posts_table,
    impure_upsert_user_stats,
    impure_upsert_post_stats,
    impure_query_table,
)


# ── Shell: CLI arg parsing ──────────────────────────────────────────────────

def impure_read_job_type(argv: list[str]) -> Result[JobType]:
    """Read the job type from command-line arguments.

    Impure — reads sys.argv (external state). Validates the argument
    and returns a parsed JobType or an error message."""
    if len(argv) < 2:
        return failure(
            "Usage: python run.py <job_type>\n"
            "  Valid job types: users, posts\n"
            "  users — fetch user data, transform with Polars\n"
            "  posts — fetch post data, transform with pure Python"
        )
    return parse_job_type(argv[1])


# ── Shell: orchestrated ETL pipeline for a single job type ─────────────────

def _etl_users(
    conn: sqlite3.Connection,
    raw_records: list[dict[str, object]],
) -> Result[int]:
    records_result = parse_user_records(raw_records)
    if not records_result[0]:
        return records_result
    user_records = records_result[1]

    transform_result = transform_users(user_records)
    if not transform_result[0]:
        return transform_result
    stats = transform_result[1]

    table_result = impure_create_users_table(conn)
    if not table_result[0]:
        return table_result
    return impure_upsert_user_stats(conn, stats)


def _etl_posts(
    conn: sqlite3.Connection,
    raw_records: list[dict[str, object]],
) -> Result[int]:
    records_result = parse_post_records(raw_records)
    if not records_result[0]:
        return records_result
    post_records = records_result[1]

    transform_result = transform_posts(post_records)
    if not transform_result[0]:
        return transform_result
    stats = transform_result[1]

    table_result = impure_create_posts_table(conn)
    if not table_result[0]:
        return table_result
    return impure_upsert_post_stats(conn, stats)


def _extract_raw_records(raw_result: Result[str]) -> Result[list[dict[str, object]]]:
    if not raw_result[0]:
        return raw_result
    raw_json = raw_result[1]
    parsed_result = impure_parse_json_list(raw_json)
    if not parsed_result[0]:
        return parsed_result
    return success(parsed_result[1])


def impure_run_etl(
    job_type: JobType,
    conn: sqlite3.Connection,
    config: JobConfig,
) -> Result[int]:
    raw_result = impure_fetch_raw(config.api_url)
    records_result = _extract_raw_records(raw_result)
    if not records_result[0]:
        return records_result

    raw_records = records_result[1]

    if job_type == "users":
        return _etl_users(conn, raw_records)
    else:  # job_type == "posts"
        return _etl_posts(conn, raw_records)


# ── Shell: verification — query the database to confirm data was saved ─────

def impure_verify_results(
    conn: sqlite3.Connection,
    config: JobConfig,
) -> Result[int]:
    query_result = impure_query_table(conn, config.table_name, limit=5)
    if not query_result[0]:
        return query_result

    columns, rows = query_result[1]
    print(f"\n=== Results from table '{config.table_name}' (first 5 rows) ===")
    print("  " + " | ".join(columns))
    print("  " + "-" * 50)
    for row in rows:
        print("  " + " | ".join(str(v) for v in row))

    return success(len(rows))


# ── Main entry point ────────────────────────────────────────────────────────

def impure_main(argv: list[str]) -> int:
    """Main entry point — the outermost shell function.

    Chains the entire ETL workflow:
        1. Parse CLI args → JobType (shell)
        2. Resolve job config → JobConfig (core, pure)
        3. Open database (shell)
        4. Run ETL pipeline (shell, calling core)
        5. Verify results (shell)
        6. Print summary (shell)

    Returns 0 on success, 1 on failure (exit codes for the scheduler).

    FP note: The entire flow is a sequence of Result-returning steps
    chained with explicit error checks. No exception handlers outside
    of individual impure functions. Control flow is expressed through
    data (Result values) rather than thrown exceptions."""
    print("=" * 60)
    print("  Batch ETL Job — Functional Programming Demo")
    print("=" * 60)

    # 1. Parse CLI args (shell)
    job_type_result = impure_read_job_type(argv)
    if not job_type_result[0]:
        print(f"\nERROR: {job_type_result[1]}")
        return 1
    job_type: JobType = job_type_result[1]

    # 2. Resolve configuration (core — pure)
    config_result = resolve_job_config(job_type)
    if not config_result[0]:
        print(f"\nERROR: {config_result[1]}")
        return 1
    config: JobConfig = config_result[1]

    print(f"\nJob type : {config.job_type}")
    print(f"API URL  : {config.api_url}")
    print(f"Table    : {config.table_name}")

    # 3. Open the in-memory SQLite database (shell)
    db_result = impure_open_database()
    if not db_result[0]:
        print(f"\nERROR: {db_result[1]}")
        return 1
    conn: sqlite3.Connection = db_result[1]

    # 4. Run the ETL pipeline (shell, using core)
    print(f"\n--- Running ETL pipeline ---")
    etl_result = impure_run_etl(job_type, conn, config)
    if not etl_result[0]:
        print(f"\nPipeline FAILED: {etl_result[1]}")
        return 1

    rows_saved: int = etl_result[1]
    print(f"\nPipeline SUCCESS: {rows_saved} row(s) written to '{config.table_name}'")

    # 5. Verify results by reading back from the database (shell)
    verify_result = impure_verify_results(conn, config)
    if is_err(verify_result):
        print(f"\nVerification FAILED: {verify_result[1]}")
        return 1

    # 6. Summary
    print(f"\n{'=' * 60}")
    print(f"  Job completed successfully!")
    print(f"  Total rows saved: {rows_saved}")
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(impure_main(sys.argv))
