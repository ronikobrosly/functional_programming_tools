"""Entry point: load config, ensure a model artifact exists, wire, and serve.

This is the composition root -- the only place that pulls the shell adapters
and the pure core together. It stays small: read config, load (or train) the
model, choose a database fetcher, build the per-request ``run``, start serving.
"""

from __future__ import annotations

import os
import sys

from app.model_training import train_and_save
from app.shell.config import load_config
from app.shell.http import make_handler, serve
from app.shell.model_store import load_model
from app.wiring import build_run, choose_fetcher

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")


def build_app(config_path: str = DEFAULT_CONFIG_PATH):
    """Assemble the running pieces. Returns ``(config, model, run)``."""
    config = load_config(config_path)

    if not os.path.exists(config.model_path):
        print(f"[main] artifact '{config.model_path}' not found; training a fresh one...")
        train_and_save(config.model_path)

    model = load_model(config.model_path, config.threshold)
    fetch = choose_fetcher(config)
    run = build_run(model, config, fetch)
    return config, model, run


def main(config_path: str = DEFAULT_CONFIG_PATH) -> None:
    config, model, run = build_app(config_path)
    health_body = {"status": "ok", "features": list(model.feature_order)}
    handler = make_handler(run, health_body)
    serve(config.host, config.port, handler)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH)
