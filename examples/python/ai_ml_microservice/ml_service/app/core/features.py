"""Pure feature engineering: combine the parsed payload with the value fetched
from the database into the ordered vector the model expects.

This is your old ``feature_eng.py`` -- but with the database call removed. The
DB-fetched value arrives as a plain argument (``attendance``); this module has
no idea Postgres exists. ``None`` (row not found) is resolved to a configured
default so the function stays total.
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.core.types import ParsedRequest

# Single source of truth for feature order, shared by training and serving.
FEATURE_ORDER: Tuple[str, ...] = ("hours_studied", "prior_score", "attendance_rate")


def build_feature_vector(
    parsed: ParsedRequest,
    attendance: Optional[float],
    default_attendance: float,
) -> Tuple[float, ...]:
    """Assemble the ordered feature vector. Pure and total."""
    resolved_attendance = attendance if attendance is not None else default_attendance
    return (parsed.hours_studied, parsed.prior_score, float(resolved_attendance))
