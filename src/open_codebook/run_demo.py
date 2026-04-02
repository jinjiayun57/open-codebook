from __future__ import annotations

import yaml
import json
import pandas as pd
from datetime import datetime, UTC
from pathlib import Path

def load_codebook(codebook_path: Path) -> dict:
    with codebook_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_data(data_path: Path) -> pd.DataFrame:
    return pd.read_csv(data_path)

def mock_code_text(text: str) -> dict:
    """
    Placeholder coding function for the early-stage prototype.
    This will later be replaced by structured coding with an open/local model.
    """
    lowered = text.lower()

    if "my home ground" in lowered or "prove myself" in lowered or "goal goes far beyond" in lowered:
        explicit_position = "supportive"
    elif "deeply affected" in lowered or "fight back" in lowered:
        explicit_position = "critical"
    elif "long road ahead" in lowered or "begin again" in lowered:
        explicit_position = "mixed"
    else:
        explicit_position = "unclear"

    if "hope" in lowered or "depends" in lowered or "long road ahead" in lowered:
        indirectness = "high"
        ambiguity_flag = "yes"
        human_review = "yes"
    else:
        indirectness = "medium"
        ambiguity_flag = "no"
        human_review = "no"

    if "unity" in lowered or "strongly agree" in lowered:
        norm_conforming_language = "yes"
    else:
        norm_conforming_language = "unclear"

    return {
        "explicit_position": explicit_position,
        "implied_position": explicit_position,
        "indirectness": indirectness,
        "norm_conforming_language": norm_conforming_language,
        "ambiguity_flag": ambiguity_flag,
        "evidence_span": text[:80],
        "human_review": human_review,
    }


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "demo_responses.csv"
    codebook_path = project_root / "codebooks" / "demo_codebook.yaml"
    output_dir = project_root / "outputs"

    ensure_output_dir(output_dir)

    codebook = load_codebook(codebook_path)
    df = load_data(data_path)

    text_column = codebook.get("text_column", "text_en")

    coded_rows = []
    for _, row in df.iterrows():
        text_value = str(row[text_column])
        result = mock_code_text(text_value)

        coded_row = {
            "id": row["id"],
            "source_language": row.get("source_language", ""),
            "text_original": row.get("text_original", ""),
            "text_en": row.get("text_en", ""),
            "source_context": row.get("source_context", ""),
            "event_year": row.get("event_year", ""),
            **result,
        }
        coded_rows.append(coded_row)

    coded_df = pd.DataFrame(coded_rows)

    coded_output_path = output_dir / "coded_demo.csv"
    metadata_output_path = output_dir / "run_metadata.json"

    coded_df.to_csv(coded_output_path, index=False)

    metadata = {
        "project_name": codebook.get("project_name", "unknown"),
        "text_column": text_column,
        "n_rows": len(df),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "mode": "mock_coding",
        "notes": "Early-stage demo workflow with placeholder rule-based coding.",
    }

    with metadata_output_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Saved coded output to: {coded_output_path}")
    print(f"Saved metadata to: {metadata_output_path}")


if __name__ == "__main__":
    main()