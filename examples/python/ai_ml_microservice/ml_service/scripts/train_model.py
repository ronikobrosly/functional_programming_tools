"""CLI wrapper: train the model artifact from the config's model path.

    python -m scripts.train_model            # uses ../config.yaml
    python -m scripts.train_model path.yaml
"""

from __future__ import annotations

import os
import sys

from app.model_training import train_and_save
from app.shell.config import load_config

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")


def main(config_path: str = DEFAULT_CONFIG_PATH) -> None:
    config = load_config(config_path)
    path = train_and_save(config.model_path)
    print(f"[train] wrote model artifact to '{path}'")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH)
