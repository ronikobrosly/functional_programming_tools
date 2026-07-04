"""Offline training: build synthetic data, fit an sklearn pipeline, pickle it.

Writing a file is an effect, so this lives outside ``core``. ``fit`` mutates the
estimator in place -- that mutation is confined here, at the "train once"
boundary; the served ``Model`` is read-only thereafter.

The data generation is fully vectorised (NumPy), so there are no Python-level
loops and no recursion.
"""

from __future__ import annotations

import os
import pickle
from typing import Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.core.features import FEATURE_ORDER


def synthetic_dataset(n_samples: int = 600, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """A deterministic 'does the student pass?' dataset over 3 features."""
    rng = np.random.default_rng(seed)
    hours = rng.uniform(0.0, 8.0, n_samples)
    prior_score = rng.uniform(0.0, 1.0, n_samples)
    attendance = rng.uniform(0.0, 1.0, n_samples)

    latent = 0.9 * hours + 2.5 * prior_score + 2.0 * attendance - 4.5
    labels = (latent + rng.normal(0.0, 0.5, n_samples) > 0.0).astype(int)

    features = np.column_stack((hours, prior_score, attendance))
    return features, labels


def fit_pipeline(features: np.ndarray, labels: np.ndarray):
    """Fit scaler + logistic regression. The one place an estimator mutates."""
    estimator = make_pipeline(StandardScaler(), LogisticRegression())
    estimator.fit(features, labels)
    return estimator


def train_and_save(path: str, seed: int = 42) -> str:
    """Train and pickle a ``{estimator, feature_order, positive_index}`` artifact."""
    features, labels = synthetic_dataset(seed=seed)
    estimator = fit_pipeline(features, labels)
    positive_index = int(np.where(estimator.classes_ == 1)[0][0])

    artifact = {
        "estimator": estimator,
        "feature_order": FEATURE_ORDER,
        "positive_index": positive_index,
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as handle:
        pickle.dump(artifact, handle)
    return path
