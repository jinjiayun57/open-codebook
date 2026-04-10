from __future__ import annotations

import json
from datetime import datetime, UTC

import pandas as pd


from .coder import code_text
from .io_utils import ensure_output_dir, get_project_root, load_codebook, load_csv


def main():
    project_root = get_project_root()
    data_path = project_root / "data" / "demos" / "demo_responses.csv"
    codebook_path = project_root / "codebooks" / "demos" / "demo_codebook.yaml"
    output_dir = project_root / "outputs" / "demos"

    ensure_output_dir(output_dir)

    codebook = load_codebook(codebook_path)
    df = load_csv(data_path)

    text_column = codebook.get("text_column", "text_en")
    model_name = codebook.get("model_name", "qwen3.5:4b")

    coded_rows = []
    for _, row in df.iterrows():
        text_value = str(row[text_column])
        result = code_text(text_value, codebook, model_name)

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
        "n_rows": len(coded_df),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "mode": "ollama_structured_coding",
        "model": model_name,
        "notes": "Early-stage demo workflow using a local Ollama model.",
    }

    with metadata_output_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Saved coded output to: {coded_output_path}")
    print(f"Saved metadata to: {metadata_output_path}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Error: {exc}")
