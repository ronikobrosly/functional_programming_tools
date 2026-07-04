"""Wiring: the impure orchestration that assembles the per-request flow.

This is where the **pure/impure/pure sandwich** is made explicit. ``build_run``
closes over the loaded model, config, and a database fetcher, and returns a
``run(raw_body) -> (status, body)`` function whose body reads, top to bottom:

    parse_request        (PURE)   -- decide validity + what to fetch
    fetch_attendance     (IMPURE) -- the one database read, in the middle
    complete             (PURE)   -- featurize, predict, shape response

The core functions never learn that Postgres exists; the DB value simply
arrives as an argument to ``complete``.
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple

from app.core.handle import complete
from app.core.types import Config, Model
from app.core.validation import parse_request
from app.shell.db import Fetcher, make_inmemory_fetcher, make_postgres_fetcher


def choose_fetcher(config: Config) -> Fetcher:
    """Select a database backend from config. Postgres in prod, in-memory for
    the demo/tests."""
    if config.db_mode == "postgres":
        return make_postgres_fetcher(config.db_dsn)
    return make_inmemory_fetcher()


def build_run(
    model: Model,
    config: Config,
    fetch_attendance: Fetcher,
) -> Callable[[bytes], Tuple[int, dict]]:
    """Return the per-request pipeline with dependencies injected."""

    def run(raw_body: bytes) -> Tuple[int, dict]:
        parsed_result = parse_request(raw_body)                 # --- PURE ---
        if not parsed_result.ok:
            return (400, parsed_result.error)
        parsed = parsed_result.value

        try:
            attendance: Optional[float] = fetch_attendance(parsed.applicant_id)  # IMPURE
        except Exception as exc:  # noqa: BLE001  (turn any DB failure into a value)
            return (503, {"error": "feature store unavailable", "detail": str(exc)})

        body = complete(model, config, parsed, attendance)      # --- PURE ---
        return (200, body)

    return run
