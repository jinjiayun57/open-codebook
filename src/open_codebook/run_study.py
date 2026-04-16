from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import yaml

from .coder import code_text
from .io_utils import ensure_output_dir, get_project_root, load_codebook, load_csv


DEFAULT_CONFIG_PATH = Path("studies") / "gles_mip_pilot" / "config.yaml"


def resolve_project_path(project_root: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return project_root / path


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as file_obj:
        config = yaml.safe_load(file_obj)

    if not isinstance(config, dict):
        raise ValueError(f"Study config must be a mapping: {config_path}")

    required_keys = [
        "study_name",
        "codebook_path",
        "data_path",
        "text_column",
        "id_column",
        "output_dir",
        "model",
        "language",
    ]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Study config is missing required keys: {missing_keys}")

    return config


def run_study(config_path: Path) -> tuple[Path, Path]:
    project_root = get_project_root()
    config = load_config(config_path)

    codebook_path = resolve_project_path(project_root, config["codebook_path"])
    data_path = resolve_project_path(project_root, config["data_path"])
    output_dir = resolve_project_path(project_root, config["output_dir"])

    ensure_output_dir(output_dir)

    codebook = load_codebook(codebook_path)
    df = load_csv(data_path)

    text_column = config["text_column"]
    id_column = config["id_column"]
    model_name = config["model"]

    for column in [text_column, id_column]:
        if column not in df.columns:
            raise ValueError(f"Input data is missing required column '{column}'.")

    coded_rows = []
    for _, row in df.iterrows():
        text_value = str(row[text_column])
        result = code_text(text_value, codebook, model_name, config=config)

        coded_row = row.to_dict()
        coded_row.update(result)
        coded_rows.append(coded_row)

    coded_df = pd.DataFrame(coded_rows)

    coded_output_path = output_dir / f"{config['study_name']}_coded.csv"
    metadata_output_path = output_dir / "run_metadata.json"

    coded_df.to_csv(coded_output_path, index=False)

    metadata = {
        "study_name": config["study_name"],
        "model": model_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "codebook_path": str(codebook_path.relative_to(project_root)),
        "data_path": str(data_path.relative_to(project_root)),
        "number_of_rows": len(coded_df),
        "language": config["language"],
        "codebook_language": config.get("codebook_language"),
    }

    with metadata_output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(metadata, file_obj, indent=2, ensure_ascii=False)

    return coded_output_path, metadata_output_path


def main() -> None:
    project_root = get_project_root()
    config_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH
    config_path = resolve_project_path(project_root, config_arg)

    try:
        coded_output_path, metadata_output_path = run_study(config_path)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return

    print(f"Saved coded output to: {coded_output_path}")
    print(f"Saved metadata to: {metadata_output_path}")


if __name__ == "__main__":
    main()
