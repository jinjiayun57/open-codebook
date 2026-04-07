from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

import pandas as pd
import yaml
import ollama


MODEL_NAME = "qwen3.5:4b"


def load_codebook(codebook_path):
    with codebook_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data(data_path):
    return pd.read_csv(data_path)


def llm_code_text(text):
    prompt = f"""
You are helping with structured coding of short social science text.

Return only a valid JSON object with exactly these fields:
- explicit_position
- implied_position
- indirectness
- norm_conforming_language
- ambiguity_flag
- evidence_span
- human_review

Allowed values:
- explicit_position: supportive, critical, mixed, unclear
- implied_position: supportive, critical, mixed, unclear
- indirectness: low, medium, high
- norm_conforming_language: yes, no, unclear
- ambiguity_flag: yes, no
- human_review: yes, no

Definitions:
- explicit_position = the position explicitly expressed in the text
- implied_position = the implied or underlying position, if inferable
- indirectness = degree to which the response is indirect, hedged, or self-moderated
- norm_conforming_language = whether the response appears shaped by socially normative or cautious phrasing
- ambiguity_flag = whether the text is difficult to code confidently
- evidence_span = a short text span copied from the input
- human_review = whether manual review is recommended

Text:
{text}
""".strip()

    schema = {
        "type": "object",
        "properties": {
            "explicit_position": {
                "type": "string",
                "enum": ["supportive", "critical", "mixed", "unclear"],
            },
            "implied_position": {
                "type": "string",
                "enum": ["supportive", "critical", "mixed", "unclear"],
            },
            "indirectness": {
                "type": "string",
                "enum": ["low", "medium", "high"],
            },
            "norm_conforming_language": {
                "type": "string",
                "enum": ["yes", "no", "unclear"],
            },
            "ambiguity_flag": {
                "type": "string",
                "enum": ["yes", "no"],
            },
            "evidence_span": {"type": "string"},
            "human_review": {
                "type": "string",
                "enum": ["yes", "no"],
            },
        },
        "required": [
            "explicit_position",
            "implied_position",
            "indirectness",
            "norm_conforming_language",
            "ambiguity_flag",
            "evidence_span",
            "human_review",
        ],
    }

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        format=schema,
        think=False,
        stream=False,
        options={"temperature": 0},
    )

    content = response["message"]["content"]
    return json.loads(content)

def ensure_output_dir(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)


def main():
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
        result = llm_code_text(text_value)

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
        "model": MODEL_NAME,
        "notes": "Early-stage demo workflow using a local Ollama model.",
    }

    with metadata_output_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Saved coded output to: {coded_output_path}")
    print(f"Saved metadata to: {metadata_output_path}")


if __name__ == "__main__":
    main()