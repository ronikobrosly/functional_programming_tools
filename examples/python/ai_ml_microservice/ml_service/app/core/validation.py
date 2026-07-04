"""Pure request parsing and validation: ``bytes -> Result[ParsedRequest]``.

This is the *first slice of bread* in the pure/impure/pure sandwich. It decides
what a valid request looks like and, crucially, extracts the ``applicant_id``
that the shell will need to fetch the remaining feature. It performs no I/O.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from app.core.types import Err, Ok, ParsedRequest, Result


def _as_float(value: Any) -> Optional[float]:
    """Coerce to float, returning None on failure. Pure and total."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_request(raw_body: bytes) -> Result:
    """Validate raw request bytes into a ``ParsedRequest`` or an error dict."""
    try:
        payload = json.loads(raw_body or b"{}")
    except json.JSONDecodeError as exc:
        return Err({"error": "invalid JSON", "detail": str(exc)})

    if not isinstance(payload, dict):
        return Err({"error": "expected a JSON object of features"})

    applicant_id = payload.get("applicant_id")
    if not isinstance(applicant_id, str) or not applicant_id:
        return Err({"error": "missing or invalid 'applicant_id'"})

    hours = _as_float(payload.get("hours_studied", 0.0))
    prior = _as_float(payload.get("prior_score", 0.0))
    if hours is None or prior is None:
        return Err({"error": "'hours_studied' and 'prior_score' must be numbers"})

    return Ok(ParsedRequest(applicant_id=applicant_id, hours_studied=hours, prior_score=prior))
