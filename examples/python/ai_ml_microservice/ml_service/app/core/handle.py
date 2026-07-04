"""Pure composition of the *second slice of bread* in the sandwich.

Given the parsed request and the value the shell fetched from the database,
``complete`` runs the remaining pure steps -- featurize, predict, shape the
response -- with no I/O. The orchestration in ``app.wiring`` calls this after
the (impure) database read.
"""

from __future__ import annotations

from app.core.features import build_feature_vector
from app.core.prediction import predict
from app.core.types import Config, Model, ParsedRequest, Prediction


def _to_response_body(applicant_id: str, prediction: Prediction) -> dict:
    return {
        "applicant_id": applicant_id,
        "label": prediction.label,
        "probability": round(prediction.probability, 6),
        "outcome": "pass" if prediction.label == 1 else "fail",
    }


def complete(
    model: Model,
    config: Config,
    parsed: ParsedRequest,
    attendance: float | None,
) -> dict:
    """featurize -> predict -> shape. Pure and total."""
    features = build_feature_vector(parsed, attendance, config.default_attendance)
    prediction = predict(model, features)
    return _to_response_body(parsed.applicant_id, prediction)
