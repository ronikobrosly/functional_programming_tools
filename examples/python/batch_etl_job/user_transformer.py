"""
Core: Polars-based transformations on user data.

This module lives in the FUNCTIONAL CORE. Every function here is pure:
- Same inputs → same outputs (referentially transparent).
- No I/O, no mutation, no network, no environment access.
- All dependencies (the input tuple of UserRecords) are passed explicitly.

Following FUNC_PROG_GUIDE §2 (purity) and §3 (immutability):
- No in-place mutation — Polars DataFrames are immutable by default.
- The input tuple of UserRecords is never modified; new aggregates are produced.

One data source is handled as a Polars dataframe per the AGENTS.md spec.
Polars was chosen because it provides a declarative, expression-oriented API
that aligns naturally with functional programming: chainable operations,
no mutable accumulation loops, and lazy evaluation.
"""

import polars as pl
from domain_types import (
    Result,
    success,
    failure,
    UserRecord,
    UserStatsByCity,
)


def users_to_dataframe(records: tuple[UserRecord, ...]) -> pl.DataFrame:
    """Convert a tuple of immutable UserRecords into a Polars DataFrame.

    This is a pure function — converting one immutable representation to
    another. No data is mutated; a new DataFrame is created.

    FP note: The explicit conversion here serves as the bridge between
    our domain types (frozen dataclasses) and the Polars dataframe API,
    keeping both worlds clean."""
    return pl.DataFrame(
        {
            "id": [r.id for r in records],
            "name": [r.name for r in records],
            "email": [r.email for r in records],
            "city": [r.city for r in records],
            "company": [r.company for r in records],
        }
    )


def filter_empty_city(df: pl.DataFrame) -> pl.DataFrame:
    """Remove records where the city is empty or 'Unknown'.

    Pure filter — returns a new DataFrame, does not mutate the input.

    FP note: This is a self-contained filter function, composable into
    a larger pipeline. Separating concerns into small, named functions
    follows FUNC_PROG_GUIDE §9 (small, composable functions)."""
    return df.filter(
        (pl.col("city").is_not_null())
        & (pl.col("city") != "")
        & (pl.col("city") != "Unknown")
    )


def aggregate_users_by_city(df: pl.DataFrame) -> pl.DataFrame:
    """Group users by city and count them.

    Returns a DataFrame with columns: city, user_count.
    Uses Polars' declarative group_by + agg — no imperative loops.

    FP note: Instead of a for-loop with a mutable counter dict, we use
    a declarative aggregation that reads as a single expression of intent.
    This follows FUNC_PROG_GUIDE §6 (prefer map/filter/reduce over
    imperative accumulation loops)."""
    return (
        df.group_by("city")
        .agg(pl.count().alias("user_count"))
        .sort("city")
    )


def dataframe_to_user_stats(df: pl.DataFrame) -> tuple[UserStatsByCity, ...]:
    """Convert the aggregated Polars DataFrame into immutable domain records.

    The final step of the Polars pipeline — extracts rows from the DataFrame
    and wraps them in frozen dataclasses. No mutation occurs."""
    return tuple(
        UserStatsByCity(city=row[0], user_count=row[1])
        for row in df.iter_rows()
    )


# ── Composed pipeline — the main export of this module ──────────────────────

def transform_users(records: tuple[UserRecord, ...]) -> Result[tuple[UserStatsByCity, ...]]:
    """Transform user records into per-city user counts using Polars.

    This is the composed pipeline that chains the individual pure functions
    above into a single transformation step. Each function is small and
    testable in isolation; this function simply wires them together.

    Args:
        records: Immutable tuple of validated UserRecords (from the shell).

    Returns:
        Result: success(tuple[UserStatsByCity, ...]) or failure(str).

    FP note: The entire pipeline is a composition of pure functions:
        users_to_dataframe → filter_empty_city → aggregate_users_by_city
        → dataframe_to_user_stats

    If any step produces an empty result set, we still return success with
    an empty tuple — the function is total (defined for all inputs,
    including empty inputs). This follows FUNC_PROG_GUIDE §5 (totality)."""
    if not records:
        return success(())

    try:
        # Build the transformation pipeline by composing pure functions.
        # Each step returns a new value; no state is mutated.
        df = users_to_dataframe(records)
        filtered = filter_empty_city(df)
        aggregated = aggregate_users_by_city(filtered)
        stats = dataframe_to_user_stats(aggregated)
        return success(stats)
    except Exception as exc:
        # We wrap unexpected errors (Polars internal issues) into a Result
        # rather than letting an exception escape the core.
        return failure(f"User transformation failed: {exc}")
