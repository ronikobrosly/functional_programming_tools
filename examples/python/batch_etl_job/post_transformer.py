"""
Core: Pure Python transformations on post data.

This module lives in the FUNCTIONAL CORE. Every function here is pure:
- Same inputs → same outputs.
- No I/O, no mutation, no network.
- Dependencies passed explicitly as arguments.

Unlike user_transformer.py (which uses Polars), this module uses only
the Python standard library with functional programming techniques:
map, filter, reduce, comprehensions, and immutable data structures.

This fulfills the AGENTS.md requirement that the second data source
is processed without Polars while still following the functional style.
"""

from functools import reduce
from domain_types import (
    Result,
    success,
    failure,
    PostRecord,
    PostStatsByUser,
)


def compute_body_length(record: PostRecord) -> int:
    """Pure helper: compute the character length of a post body.

    Extracted as its own function so it can be mapped over a sequence
    and tested in isolation. Following FUNC_PROG_GUIDE §9."""
    return len(record.body)


def average(values: tuple[int, ...]) -> float:
    """Pure helper: compute the arithmetic mean of an immutable tuple.

    Returns 0.0 for an empty tuple — the function is total (defined for
    all inputs of its declared type). This follows FUNC_PROG_GUIDE §5."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def group_posts_by_user(
    records: tuple[PostRecord, ...],
) -> dict[int, tuple[PostRecord, ...]]:
    """Group post records by user_id, returning an immutable grouping.

    FP note: Uses reduce to build a new dict (copy-on-write via dict
    unpacking) instead of mutating an accumulator in a for-loop.
    Each step produces a new dict — the input is never modified.

    This follows FUNC_PROG_GUIDE §3 (immutability) and §10 (copy-on-write):
    the spread operator {**acc, key: new_value} creates a fresh dict for
    each accumulation step."""
    def add_to_group(
        acc: dict[int, tuple[PostRecord, ...]],
        record: PostRecord,
    ) -> dict[int, tuple[PostRecord, ...]]:
        existing = acc.get(record.user_id, ())
        # Create a new dict with the updated entry — copy-on-write.
        # Neither the old dict nor the old tuple is mutated.
        return {**acc, record.user_id: (*existing, record)}

    return reduce(add_to_group, records, {})


def stats_for_single_user(
    user_id: int,
    user_posts: tuple[PostRecord, ...],
) -> PostStatsByUser:
    """Compute aggregated stats for a single user's posts.

    Pure function: given a user_id and their posts, returns an immutable
    PostStatsByUser record. No side effects, no mutation.

    FP note: Uses map (a higher-order function) to compute body lengths
    from records. This is more declarative than a mutable accumulator loop."""
    lengths = tuple(map(compute_body_length, user_posts))
    return PostStatsByUser(
        user_id=user_id,
        post_count=len(user_posts),
        avg_body_length=average(lengths),
    )


# ── Composed pipeline — the main export ─────────────────────────────────────

def transform_posts(records: tuple[PostRecord, ...]) -> Result[tuple[PostStatsByUser, ...]]:
    """Transform post records into per-user post statistics.

    This is the composed pipeline using only pure Python functional
    techniques (no Polars). Each sub-step is a small, testable function.

    Pipeline:
        group_posts_by_user → (map stats_for_single_user over each group)

    Args:
        records: Immutable tuple of validated PostRecords.

    Returns:
        Result: success(tuple[PostStatsByUser, ...]) sorted by user_id,
        or failure(str) on error.

    FP note: The entire transformation is a composition of pure functions.
    No imperative loops, no mutable state, no exceptions for expected paths."""
    if not records:
        return success(())

    try:
        grouped = group_posts_by_user(records)

        # For each user group, compute stats. Sorted for deterministic output.
        stats = tuple(
            stats_for_single_user(uid, posts)
            for uid, posts in sorted(grouped.items())
        )
        return success(stats)
    except Exception as exc:
        # Unexpected errors (e.g., from malformed data that somehow passed
        # validation) are wrapped into the Result type rather than thrown.
        return failure(f"Post transformation failed: {exc}")
