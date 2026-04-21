from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import yaml


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_codebook(codebook_path: Path) -> dict:
    with codebook_path.open("r", encoding="utf-8") as file_obj:
        return yaml.safe_load(file_obj)


def load_csv(data_path: Path) -> pd.DataFrame:
    with data_path.open("r", encoding="utf-8", newline="") as file_obj:
        sample = file_obj.read(4096)
        file_obj.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

    return pd.read_csv(data_path, sep=delimiter)


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
