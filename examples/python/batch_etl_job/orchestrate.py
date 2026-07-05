"""
Core: pipeline composition and job-type dispatch.

This module lives in the FUNCTIONAL CORE. Every function is pure:
- Maps a JobType to a specific pipeline configuration.
- Decides what URL to fetch from and what table to write to.
- Does NOT perform any effects — just returns a description (JobConfig).

Following FUNC_PROG_GUIDE §8:
"The core may return a *plan* of effects; it does not run them."

The JobConfig record serves as that plan — the shell reads it and
executes the described effects (fetch URL, write to table).

FP note: This is the strategy pattern expressed as a pure function
from JobType → JobConfig. Adding a new job type means adding a new
branch here — pattern matching on the union type ensures exhaustiveness.
"""

from domain_types import (
    Result,
    success,
    failure,
    JobType,
    JobConfig,
)


# ── API endpoints (constants — pure values, no I/O) ─────────────────────────

_USER_API = "https://jsonplaceholder.typicode.com/users"
_POST_API = "https://jsonplaceholder.typicode.com/posts"


# ── Job configuration lookup (pure, exhaustive dispatch) ────────────────────

def resolve_job_config(job_type: JobType) -> Result[JobConfig]:
    """Resolve a JobType to an immutable JobConfig.

    This is a pure function — given the same JobType, it always returns
    the same JobConfig. No network, no I/O, no randomness.

    The match on JobType is exhaustive (covers all `Literal` variants),
    so the type checker ensures we handle every possible job type.

    Returns:
        Result[JobConfig]: success(JobConfig) with the resolved configuration,
        or failure(str) for an unrecognized job type (should never happen
        at the type level, but included for defensive totality).

    FP note: This embodies the "parse, don't validate" approach —
    by the time JobType reaches this function, it's already a valid
    literal, so no runtime validation is needed. The defensive else
    branch exists only for type-system edge cases."""
    if job_type == "users":
        config = JobConfig(
            job_type=job_type,
            api_url=_USER_API,
            table_name="user_stats_by_city",
        )
        return success(config)

    if job_type == "posts":
        config = JobConfig(
            job_type=job_type,
            api_url=_POST_API,
            table_name="post_stats_by_user",
        )
        return success(config)

    # Defensive: should be unreachable with proper type narrowing
    return failure(f"Unhandled job type: {job_type}")
