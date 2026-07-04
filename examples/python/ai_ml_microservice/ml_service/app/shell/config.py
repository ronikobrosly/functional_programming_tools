"""Config adapter: read + parse the YAML file into an immutable ``Config``.

This is the config half of your old ``main.py``. It is the only place that
knows the YAML layout; everything downstream sees a typed ``Config`` value.
"""

from __future__ import annotations

import yaml

from app.core.types import Config


def load_config(path: str) -> Config:
    """Read YAML from disk (effect) and flatten it into a ``Config`` value."""
    with open(path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    server, model, features, database = (
        raw["server"], raw["model"], raw["features"], raw["database"],
    )
    return Config(
        host=str(server["host"]),
        port=int(server["port"]),
        model_path=str(model["path"]),
        threshold=float(model["threshold"]),
        default_attendance=float(features["default_attendance"]),
        db_mode=str(database["mode"]),
        db_dsn=str(database.get("dsn", "")),
    )
