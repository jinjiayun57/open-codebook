from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_codebook(codebook_path: Path) -> dict:
    with codebook_path.open("r", encoding="utf-8") as file_obj:
        return yaml.safe_load(file_obj)


def load_csv(data_path: Path) -> pd.DataFrame:
    return pd.read_csv(data_path)


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
