"""
Imperial shell: fetch JSON from public APIs and parse into domain types.

This module lives in the IMPERATIVE SHELL. All functions here perform I/O
(network requests, JSON parsing) and are marked with the `impure_` prefix
to indicate they have side effects.

Following FUNC_PROG_GUIDE §8: effects (network, parsing) are performed at
the edges. The core never touches the network or raw JSON strings.

Functional programming highlights:
- Raw HTTP responses are immediately converted into immutable domain records
  at the boundary, so impurity does not leak into the core.
- All functions return Result types — no exceptions for expected failures
  (network errors, bad JSON, missing fields).
- Parse, don't validate: raw dicts are validated and parsed into precise
  types (UserRecord, PostRecord) once at the shell; the core trusts them.
"""

import json
import urllib.request
import urllib.error
from functools import reduce
from typing import Any, Sequence

from domain_types import (
    Result,
    success,
    failure,
    UserRecord,
    PostRecord,
)


# ── Low-level HTTP fetch (shell) ────────────────────────────────────────────

def impure_fetch_raw(url: str, timeout: int = 10) -> Result[str]:
    """Fetch the raw response body from a URL as a string.

    This is an impure function — it performs a network call.
    Returns Result[str]: success(str) with the response body, or failure(str)
    with a description of what went wrong.

    FP note: No exception leaks out. Network errors, timeouts, and bad
    status codes are all mapped to the Result type."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return failure(f"HTTP {response.status} from {url}")
            raw_body = response.read().decode("utf-8")
            return success(raw_body)
    except urllib.error.URLError as exc:
        return failure(f"Network error fetching {url}: {exc.reason}")
    except (ValueError, OSError) as exc:
        return failure(f"Error fetching {url}: {exc}")


# ── JSON parsing (shell boundary) ───────────────────────────────────────────

def impure_parse_json_list(raw: str) -> Result[list[dict[str, Any]]]:
    """Parse a raw JSON string as a list of dicts.

    Returns Result[list[dict[str, Any]]]: success on valid JSON array,
    or failure(str). This is a boundary function — it converts
    unstructured text into structured data that the core can consume."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return failure(f"Invalid JSON: {exc}")

    if not isinstance(parsed, list):
        return failure(f"Expected a JSON array, got {type(parsed).__name__}")

    return success(parsed)


# ── Record parsers (shell boundary — parse, don't validate) ─────────────────

def _parse_user_record(raw: dict[str, Any]) -> Result[UserRecord]:
    """Parse a single raw dict into a validated UserRecord.

    Extracts the city from the nested address and the company name.
    Returns failure if required fields are missing."""
    try:
        return success(UserRecord(
            id=int(raw["id"]),
            name=str(raw["name"]),
            email=str(raw["email"]),
            city=str(raw.get("address", {}).get("city", "Unknown")),
            company=str(raw.get("company", {}).get("name", "Unknown")),
        ))
    except (KeyError, ValueError, TypeError) as exc:
        return failure(f"Bad user record field {exc}: {raw}")


def _parse_post_record(raw: dict[str, Any]) -> Result[PostRecord]:
    """Parse a single raw dict into a validated PostRecord."""
    try:
        return success(PostRecord(
            id=int(raw["id"]),
            user_id=int(raw["userId"]),
            title=str(raw["title"]),
            body=str(raw["body"]),
        ))
    except (KeyError, ValueError, TypeError) as exc:
        return failure(f"Bad post record field {exc}: {raw}")


# ── Batch parser — parse a list of raw dicts into immutable records ─────────

def parse_user_records(raw_list: list[dict[str, Any]]) -> Result[tuple[UserRecord, ...]]:
    """Parse a list of raw dicts into a tuple of validated UserRecords.

    Uses a functional fold (reduce) approach: accumulate results into an
    immutable tuple, short-circuit on the first parse failure. Returns either
    the full tuple of UserRecords or the first error encountered.

    FP note: No mutable list or .append() is used. The accumulator is an
    immutable tuple built with copy-on-write via (*acc, new_item).
    reduce ensures the pipeline is declarative — the logic reads as a
    single expression rather than a sequence of imperative mutations.
    This follows FUNC_PROG_GUIDE §6 (replace imperative accumulation
    loops with reduce) and §3 (no mutable state, copy-on-write).

    This is a pure function in terms of return value (no I/O),
    but it lives at the shell boundary because it handles raw/untyped data."""
    def fold(
        acc: Result[tuple[UserRecord, ...]],
        raw: dict[str, Any],
    ) -> Result[tuple[UserRecord, ...]]:
        if not acc[0]:
            return acc  # Short-circuit: propagate first failure
        parsed = _parse_user_record(raw)
        if not parsed[0]:
            return failure(parsed[1])  # Propagate parse failure
        existing = acc[1]  # tuple[UserRecord, ...] — immutable
        return success((*existing, parsed[1]))

    init: Result[tuple[UserRecord, ...]] = success(())
    return reduce(fold, raw_list, init)


def parse_post_records(raw_list: list[dict[str, Any]]) -> Result[tuple[PostRecord, ...]]:
    """Parse a list of raw dicts into a tuple of validated PostRecords.

    Same functional fold pattern as parse_user_records — returns a tuple
    of PostRecords or the first error, with no mutable state."""
    def fold(
        acc: Result[tuple[PostRecord, ...]],
        raw: dict[str, Any],
    ) -> Result[tuple[PostRecord, ...]]:
        if not acc[0]:
            return acc
        parsed = _parse_post_record(raw)
        if not parsed[0]:
            return failure(parsed[1])
        existing = acc[1]
        return success((*existing, parsed[1]))

    init: Result[tuple[PostRecord, ...]] = success(())
    return reduce(fold, raw_list, init)
