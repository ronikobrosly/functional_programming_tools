"""Immutable data types shared across the core.

These are plain values (``NamedTuple``s). Note that ``Model.estimator`` is
typed ``Any`` on purpose: the core never imports scikit-learn, it only calls a
read-only method on whatever fitted estimator the shell hands it. That keeps
this module free of any heavy or effectful dependency.
"""

from __future__ import annotations

from typing import Any, NamedTuple, Optional, Sequence


class Result(NamedTuple):
    """A tiny ``Result``/``Either`` value so the core can report failure without
    raising. ``ok`` discriminates the two cases."""

    ok: bool
    value: Any = None
    error: Optional[dict] = None


def Ok(value: Any) -> Result:      # noqa: N802  (constructor-style name)
    return Result(True, value, None)


def Err(error: dict) -> Result:    # noqa: N802
    return Result(False, None, error)


class Config(NamedTuple):
    """Everything the app needs to run, parsed from YAML by the shell."""

    host: str
    port: int
    model_path: str
    threshold: float
    default_attendance: float
    db_mode: str
    db_dsn: str


class Model(NamedTuple):
    """A trained model treated as an immutable value: fitted once, then only
    queried. ``positive_index`` is the ``predict_proba`` column for class 1."""

    estimator: Any
    feature_order: Sequence[str]
    positive_index: int
    threshold: float = 0.5


class ParsedRequest(NamedTuple):
    """A validated request. ``applicant_id`` is the key the shell will use to
    fetch the remaining feature from the database."""

    applicant_id: str
    hours_studied: float
    prior_score: float


class Prediction(NamedTuple):
    label: int
    probability: float
