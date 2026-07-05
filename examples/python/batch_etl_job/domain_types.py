"""
Domain data types for the batch ETL job.

All types are immutable following functional programming principles:
- Frozen dataclasses for product types ("and" combinations of fields).
- Literal unions for tagged/sum types ("or" choices).
- Data and behavior are kept separate — types only hold data,
  transformations are free functions in other modules.

Functional programming highlights:
- No null/nil — optionality is handled via Result types.
- No mutable state — all dataclasses are frozen.
- Parse, don't validate — the shell converts raw JSON into these
  precise types; the core never re-validates.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, TypeVar, TypeGuard


# ── Monadic error handling ──────────────────────────────────────────────────

T = TypeVar("T")
U = TypeVar("U")

type Result[T] = tuple[Literal[True], T] | tuple[Literal[False], str]


def success[T](value: T) -> Result[T]:
    return (True, value)


def failure(error: str) -> Result[T]:
    return (False, error)


def is_ok[T](result: Result[T]) -> TypeGuard[tuple[Literal[True], T]]:
    return result[0]


def is_err[T](result: Result[T]) -> TypeGuard[tuple[Literal[False], str]]:
    return not result[0]


def unwrap[T](result: Result[T]) -> T:
    if result[0]:
        return result[1]
    raise RuntimeError(f"Unwrapped a failed Result: {result[1]}")


def map_result[T, U](result: Result[T], f: Callable[[T], U]) -> Result[U]:
    if result[0]:
        return success(f(result[1]))
    return result


def and_then[T, U](result: Result[T], f: Callable[[T], Result[U]]) -> Result[U]:
    if result[0]:
        return f(result[1])
    return result


# ── Job type — discriminated union via Literal ─────────────────────────────

JobType = Literal["users", "posts"]

ALL_JOB_TYPES: tuple[JobType, ...] = ("users", "posts")


def parse_job_type(raw: str) -> Result[JobType]:
    """Parse a raw CLI argument into a JobType.

    This acts as the shell boundary parser — takes untrusted string input
    and returns either a validated JobType or a clear error. The core
    never receives an invalid job type."""
    if raw in ALL_JOB_TYPES:
        return success(raw)
    return failure(f"Unknown job type: '{raw}'. Valid options: {ALL_JOB_TYPES}")


# ── Input record types (data received from the API after parsing/validation) ─

@dataclass(frozen=True)
class UserRecord:
    """A single user record from the external API (already validated).

    The shell parses raw JSON, validates required fields exist, and constructs
    an immutable UserRecord. The core receives these and never re-validates.

    Immutability: @dataclass(frozen=True) ensures no mutation after creation.
    """
    id: int
    name: str
    email: str
    city: str
    company: str


@dataclass(frozen=True)
class PostRecord:
    """A single post record from the external API (already validated).

    Same principle as UserRecord — one-time parsing at the shell boundary,
    immutable record passed through the pure core pipeline."""
    id: int
    user_id: int
    title: str
    body: str


# ── Output aggregate types (data produced by the core transformations) ────

@dataclass(frozen=True)
class UserStatsByCity:
    """Number of users grouped by city — output of the Polars transformation pipeline.

    This is produced by the pure core (user_transformer.py) and consumed
    by the shell (sqlite_saver.py). No side effects touch it."""
    city: str
    user_count: int


@dataclass(frozen=True)
class PostStatsByUser:
    """Post count and average body length grouped by user ID.

    Produced by the pure core (post_transformer.py), consumed by the shell."""
    user_id: int
    post_count: int
    avg_body_length: float


# ── Pipeline configuration — immutable records describing what to do ───────

@dataclass(frozen=True)
class JobConfig:
    """Immutable configuration describing a single job pipeline.

    The core (orchestrate.py) produces this record. The shell reads it and
    executes the effects it describes. This is the "plan of effects" pattern
    from FUNC_PROG_GUIDE §8."""
    job_type: JobType
    api_url: str
    table_name: str

