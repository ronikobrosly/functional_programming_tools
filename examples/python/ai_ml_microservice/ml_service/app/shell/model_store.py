"""Model-store adapter: load the pickled scikit-learn artifact from disk and
wrap it as an immutable ``Model``.

This is the I/O half of your old ``model.py`` (the prediction half now lives in
``app.core.prediction``). It reads a persisted artifact rather than retraining
at start-up.
"""

from __future__ import annotations

import pickle

from app.core.types import Model


def load_model(path: str, threshold: float) -> Model:
    """Unpickle the fitted pipeline + metadata into a ``Model`` value."""
    with open(path, "rb") as handle:
        artifact = pickle.load(handle)

    return Model(
        estimator=artifact["estimator"],
        feature_order=tuple(artifact["feature_order"]),
        positive_index=int(artifact["positive_index"]),
        threshold=float(threshold),
    )
