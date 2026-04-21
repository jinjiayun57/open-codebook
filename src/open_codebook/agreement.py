from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .io_utils import load_codebook, load_csv
from .schema import get_coded_fields


DEFAULT_ORDINAL_FIELDS = {"specificity", "ambiguity"}


@dataclass(frozen=True)
class AgreementArtifacts:
    summary_df: pd.DataFrame
    disagreements_df: pd.DataFrame
    metadata: dict


def _normalize_string(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _normalize_boolean(value) -> bool | None:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().casefold()
    if not normalized:
        return None
    if normalized == "true":
        return True
    if normalized == "false":
        return False

    raise ValueError(f"Could not parse boolean review value: {value!r}")


def _normalize_series(series: pd.Series, code: dict) -> pd.Series:
    code_type = code.get("type", "string")
    if code_type == "boolean":
        return series.map(_normalize_boolean)
    return series.map(_normalize_string)


def _safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _cohen_kappa(model_values: list, reviewed_values: list) -> float | None:
    if not model_values:
        return None

    categories = sorted({*model_values, *reviewed_values}, key=lambda value: str(value))
    if len(categories) <= 1:
        return 1.0

    n = len(model_values)
    observed = sum(
        1 for model_value, reviewed_value in zip(model_values, reviewed_values)
        if model_value == reviewed_value
    ) / n

    expected = 0.0
    for category in categories:
        model_prob = model_values.count(category) / n
        reviewed_prob = reviewed_values.count(category) / n
        expected += model_prob * reviewed_prob

    if expected == 1.0:
        return 1.0

    return _safe_divide(observed - expected, 1 - expected)


def _weighted_kappa(
    model_values: list,
    reviewed_values: list,
    ordered_categories: list,
) -> float | None:
    if not model_values:
        return None

    categories = [
        category for category in ordered_categories
        if category in set(model_values) or category in set(reviewed_values)
    ]
    if len(categories) <= 1:
        return 1.0

    index = {category: idx for idx, category in enumerate(categories)}
    n = len(model_values)
    max_distance = len(categories) - 1

    observed_disagreement = 0.0
    for model_value, reviewed_value in zip(model_values, reviewed_values):
        distance = abs(index[model_value] - index[reviewed_value]) / max_distance
        observed_disagreement += distance
    observed_disagreement /= n

    model_probs = {
        category: model_values.count(category) / n
        for category in categories
    }
    reviewed_probs = {
        category: reviewed_values.count(category) / n
        for category in categories
    }

    expected_disagreement = 0.0
    for model_category in categories:
        for reviewed_category in categories:
            distance = abs(index[model_category] - index[reviewed_category]) / max_distance
            expected_disagreement += (
                distance
                * model_probs[model_category]
                * reviewed_probs[reviewed_category]
            )

    if expected_disagreement == 0.0:
        return 1.0

    return _safe_divide(1 - observed_disagreement / expected_disagreement, 1)


def _value_distribution(values: pd.Series) -> str:
    if values.empty:
        return ""

    counts = values.astype(str).value_counts(dropna=False).sort_index()
    return "; ".join(f"{label}={count}" for label, count in counts.items())


def summarize_review_agreement(
    review_df: pd.DataFrame,
    codebook: dict,
    *,
    id_column: str,
    ordinal_fields: set[str] | None = None,
) -> AgreementArtifacts:
    if id_column not in review_df.columns:
        raise ValueError(f"Review table is missing id column '{id_column}'.")

    ordinal_fields = ordinal_fields or DEFAULT_ORDINAL_FIELDS
    coded_fields = get_coded_fields(codebook)

    summary_rows = []
    disagreement_rows = []
    reviewed_row_counts = {}

    for code in coded_fields:
        field_name = code["name"]
        model_column = f"{field_name}_model"
        reviewed_column = f"{field_name}_reviewed"
        note_column = f"{field_name}_note"

        if model_column not in review_df.columns or reviewed_column not in review_df.columns:
            raise ValueError(
                f"Review table must contain '{model_column}' and '{reviewed_column}'."
            )

        working_df = review_df[
            [column for column in [id_column, "review_group", model_column, reviewed_column, note_column] if column in review_df.columns]
        ].copy()
        working_df["model_value"] = _normalize_series(working_df[model_column], code)
        working_df["reviewed_value"] = _normalize_series(working_df[reviewed_column], code)
        compared_df = working_df[working_df["reviewed_value"].notna()].copy()

        reviewed_row_counts[field_name] = int(len(compared_df))
        if compared_df.empty:
            summary_rows.append(
                {
                    "variable": field_name,
                    "measurement_level": "ordinal" if field_name in ordinal_fields else "nominal",
                    "agreement_metric": "weighted_kappa"
                    if field_name in ordinal_fields
                    else "cohen_kappa",
                    "n_compared": 0,
                    "n_matches": 0,
                    "percent_agreement": None,
                    "kappa": None,
                    "model_distribution": "",
                    "reviewed_distribution": "",
                    "note": "No reviewed values available yet.",
                }
            )
            continue

        matches = compared_df["model_value"] == compared_df["reviewed_value"]
        percent_agreement = matches.mean()
        model_values = compared_df["model_value"].tolist()
        reviewed_values = compared_df["reviewed_value"].tolist()

        if field_name in ordinal_fields:
            kappa = _weighted_kappa(model_values, reviewed_values, code.get("values", []))
            metric_name = "weighted_kappa"
            measurement_level = "ordinal"
        else:
            kappa = _cohen_kappa(model_values, reviewed_values)
            metric_name = "cohen_kappa"
            measurement_level = "nominal"

        summary_rows.append(
            {
                "variable": field_name,
                "measurement_level": measurement_level,
                "agreement_metric": metric_name,
                "n_compared": int(len(compared_df)),
                "n_matches": int(matches.sum()),
                "percent_agreement": round(float(percent_agreement), 4),
                "kappa": None if kappa is None else round(float(kappa), 4),
                "model_distribution": _value_distribution(compared_df["model_value"]),
                "reviewed_distribution": _value_distribution(compared_df["reviewed_value"]),
                "note": "",
            }
        )

        disagreements = compared_df.loc[~matches].copy()
        if not disagreements.empty:
            disagreements["variable"] = field_name
            disagreements["model_value"] = disagreements["model_value"].astype(str)
            disagreements["reviewed_value"] = disagreements["reviewed_value"].astype(str)
            disagreements["note"] = (
                disagreements[note_column].fillna("").astype(str)
                if note_column in disagreements.columns
                else ""
            )
            disagreement_rows.append(
                disagreements[
                    [column for column in [id_column, "review_group", "variable", "model_value", "reviewed_value", "note"] if column in disagreements.columns]
                ]
            )

    summary_df = pd.DataFrame(summary_rows)
    disagreements_df = (
        pd.concat(disagreement_rows, ignore_index=True)
        if disagreement_rows
        else pd.DataFrame(columns=[id_column, "review_group", "variable", "model_value", "reviewed_value", "note"])
    )

    metadata = {
        "id_column": id_column,
        "ordinal_fields": sorted(ordinal_fields),
        "n_review_rows": int(len(review_df)),
        "n_variables": int(len(coded_fields)),
        "reviewed_row_counts": reviewed_row_counts,
    }

    return AgreementArtifacts(
        summary_df=summary_df,
        disagreements_df=disagreements_df,
        metadata=metadata,
    )


def write_agreement_outputs(
    review_path: Path,
    codebook_path: Path,
    summary_output_path: Path,
    disagreement_output_path: Path,
    metadata_output_path: Path,
    *,
    id_column: str,
    ordinal_fields: set[str] | None = None,
) -> AgreementArtifacts:
    review_df = load_csv(review_path)
    codebook = load_codebook(codebook_path)

    artifacts = summarize_review_agreement(
        review_df,
        codebook,
        id_column=id_column,
        ordinal_fields=ordinal_fields,
    )

    summary_output_path.parent.mkdir(parents=True, exist_ok=True)
    artifacts.summary_df.to_csv(summary_output_path, index=False)
    artifacts.disagreements_df.to_csv(disagreement_output_path, index=False)
    with metadata_output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(artifacts.metadata, file_obj, indent=2, ensure_ascii=False)

    return artifacts
