"""Pure scoring: ``(model, features) -> Prediction``.

This is the *pure half* of your old ``model.py``; the pickle-loading half now
lives in ``app.shell.model_store``. Note there is no scikit-learn import here:
we only call ``predict_proba`` on the already-fitted estimator that the shell
loaded and passed in. sklearn accepts a plain list-of-lists, so the core stays
free of numpy/sklearn too.
"""

from __future__ import annotations

from typing import Sequence

from app.core.types import Model, Prediction


def predict(model: Model, features: Sequence[float]) -> Prediction:
    """Score one feature vector. Pure with respect to ``(model, features)`` --
    ``predict_proba`` only reads the fitted estimator, never mutates it."""
    probabilities = model.estimator.predict_proba([list(features)])[0]
    probability = float(probabilities[model.positive_index])
    return Prediction(label=int(probability >= model.threshold), probability=probability)
