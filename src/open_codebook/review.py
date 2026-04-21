from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from random import Random

import pandas as pd

from .io_utils import ensure_output_dir, load_codebook
from .schema import get_coded_fields


DEFAULT_FLAG_COLUMN = "review_flag"
DEFAULT_STRATA_COLUMN = "issue_domain"
DEFAULT_NONFLAGGED_SAMPLE_SIZE = 24
DEFAULT_RANDOM_SEED = 20260421


@dataclass(frozen=True)
class ReviewSampleResult:
    review_df: pd.DataFrame
    metadata: dict


def _coerce_bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series

    normalized = series.astype(str).str.strip().str.casefold()
    return normalized.map({"true": True, "false": False}).fillna(False)


def _allocate_stratified_sample(
    group_sizes: dict[str, int],
    target_n: int,
) -> dict[str, int]:
    if target_n <= 0:
        return {}

    available_groups = {
        str(group): int(size)
        for group, size in group_sizes.items()
        if pd.notna(group) and int(size) > 0
    }
    if not available_groups:
        return {}

    allocations = {group: 0 for group in available_groups}
    remaining = min(target_n, sum(available_groups.values()))

    # First pass: guarantee broad coverage before adding extra cases.
    for group, size in sorted(
        available_groups.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        if remaining == 0:
            break
        allocations[group] += 1
        remaining -= 1

    while remaining > 0:
        candidates = [
            (group, size - allocations[group])
            for group, size in available_groups.items()
            if allocations[group] < size
        ]
        if not candidates:
            break

        for group, _ in sorted(candidates, key=lambda item: (-item[1], item[0])):
            if remaining == 0:
                break
            if allocations[group] >= available_groups[group]:
                continue
            allocations[group] += 1
            remaining -= 1

    return {group: n for group, n in allocations.items() if n > 0}


def _sample_group_rows(
    df: pd.DataFrame,
    strata_column: str,
    allocations: dict[str, int],
    random_seed: int,
) -> pd.DataFrame:
    sampled_groups = []

    for offset, (group, n_rows) in enumerate(sorted(allocations.items())):
        group_df = df[df[strata_column].astype(str) == group]
        sampled_groups.append(
            group_df.sample(n=n_rows, random_state=random_seed + offset)
        )

    if not sampled_groups:
        return df.iloc[0:0].copy()

    return pd.concat(sampled_groups, ignore_index=False)


def _interleave_by_group(
    df: pd.DataFrame,
    strata_column: str,
    random_seed: int,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    randomizer = Random(random_seed)
    group_frames = []

    for group_name, group_df in df.groupby(strata_column, dropna=False, sort=True):
        shuffled = group_df.sample(frac=1, random_state=random_seed + len(group_frames))
        group_frames.append((group_name, shuffled.reset_index(drop=True)))

    randomizer.shuffle(group_frames)

    rows = []
    row_number = 1
    active_groups = list(group_frames)

    while active_groups:
        next_round = []
        for group_name, group_df in active_groups:
            if group_df.empty:
                continue

            row = group_df.iloc[0].copy()
            row["review_queue_position"] = row_number
            row["review_issue_domain_group"] = group_name
            rows.append(row)
            row_number += 1

            remaining = group_df.iloc[1:].reset_index(drop=True)
            if not remaining.empty:
                next_round.append((group_name, remaining))

        active_groups = next_round

    return pd.DataFrame(rows)


def build_review_sample(
    coded_df: pd.DataFrame,
    codebook: dict,
    *,
    id_column: str,
    flag_column: str = DEFAULT_FLAG_COLUMN,
    strata_column: str = DEFAULT_STRATA_COLUMN,
    nonflagged_sample_size: int = DEFAULT_NONFLAGGED_SAMPLE_SIZE,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> ReviewSampleResult:
    if id_column not in coded_df.columns:
        raise ValueError(f"Coded output is missing id column '{id_column}'.")
    if flag_column not in coded_df.columns:
        raise ValueError(f"Coded output is missing flag column '{flag_column}'.")
    if strata_column not in coded_df.columns:
        raise ValueError(f"Coded output is missing strata column '{strata_column}'.")

    coded_fields = [code["name"] for code in get_coded_fields(codebook)]
    if not coded_fields:
        raise ValueError("Codebook must define at least one coded field.")

    working_df = coded_df.copy()
    working_df[flag_column] = _coerce_bool_series(working_df[flag_column])

    flagged_df = working_df[working_df[flag_column]].copy()
    flagged_df["review_group"] = "flagged"
    flagged_df["selection_reason"] = "model_review_flag"

    nonflagged_df = working_df[~working_df[flag_column]].copy()
    group_sizes = nonflagged_df[strata_column].astype(str).value_counts().to_dict()
    allocations = _allocate_stratified_sample(group_sizes, nonflagged_sample_size)
    sampled_nonflagged_df = _sample_group_rows(
        nonflagged_df,
        strata_column=strata_column,
        allocations=allocations,
        random_seed=random_seed,
    ).copy()
    sampled_nonflagged_df["review_group"] = "nonflagged_audit"
    sampled_nonflagged_df["selection_reason"] = "stratified_nonflagged_sample"

    selected_df = pd.concat(
        [flagged_df, sampled_nonflagged_df],
        ignore_index=False,
    ).drop_duplicates(subset=[id_column])

    ordered_frames = []
    for offset, (group_name, group_df) in enumerate(
        selected_df.groupby("review_group", sort=False),
        start=1,
    ):
        ordered_group_df = _interleave_by_group(
            group_df,
            strata_column=strata_column,
            random_seed=random_seed + offset,
        )
        ordered_group_df["review_group_order"] = offset
        ordered_frames.append(ordered_group_df)

    if ordered_frames:
        selected_df = pd.concat(ordered_frames, ignore_index=True)
    else:
        selected_df = selected_df.iloc[0:0].copy()

    base_columns = [
        column
        for column in working_df.columns
        if column not in coded_fields
    ]
    model_columns = {field: f"{field}_model" for field in coded_fields}

    template_df = selected_df[
        [
            column
            for column in [
                "review_group",
                "selection_reason",
                "review_group_order",
                "review_queue_position",
                "review_issue_domain_group",
                *base_columns,
            ]
            if column in selected_df.columns
        ]
    ].copy()
    for field in coded_fields:
        template_df[f"{field}_model"] = selected_df[field]
        template_df[f"{field}_reviewed"] = ""
        template_df[f"{field}_note"] = ""

    template_df["reviewer_id"] = ""
    template_df["review_timestamp"] = ""
    template_df["final_decision"] = ""

    front_columns = [
        id_column,
        "review_group",
        "selection_reason",
        "review_group_order",
        "review_queue_position",
        "review_issue_domain_group",
    ]
    ordered_columns = (
        [column for column in front_columns if column in template_df.columns]
        + [
            column
            for column in template_df.columns
            if column not in front_columns
            and column not in model_columns.values()
            and not column.endswith("_reviewed")
            and not column.endswith("_note")
            and column not in {"reviewer_id", "review_timestamp", "final_decision"}
        ]
        + list(model_columns.values())
        + [f"{field}_reviewed" for field in coded_fields]
        + [f"{field}_note" for field in coded_fields]
        + ["reviewer_id", "review_timestamp", "final_decision"]
    )
    template_df = template_df.loc[:, ordered_columns]

    metadata = {
        "n_total_rows": len(coded_df),
        "n_flagged_rows": int(len(flagged_df)),
        "n_nonflagged_rows": int(len(nonflagged_df)),
        "n_review_rows": int(len(template_df)),
        "n_nonflagged_sampled": int(len(sampled_nonflagged_df)),
        "flag_column": flag_column,
        "strata_column": strata_column,
        "coded_fields": coded_fields,
        "nonflagged_sample_size_requested": nonflagged_sample_size,
        "nonflagged_sample_size_realized": int(len(sampled_nonflagged_df)),
        "nonflagged_allocations": allocations,
        "random_seed": random_seed,
    }

    return ReviewSampleResult(review_df=template_df, metadata=metadata)


def write_review_outputs(
    coded_path: Path,
    codebook_path: Path,
    output_path: Path,
    metadata_path: Path,
    *,
    id_column: str,
    flag_column: str = DEFAULT_FLAG_COLUMN,
    strata_column: str = DEFAULT_STRATA_COLUMN,
    nonflagged_sample_size: int = DEFAULT_NONFLAGGED_SAMPLE_SIZE,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> ReviewSampleResult:
    ensure_output_dir(output_path.parent)
    coded_df = pd.read_csv(coded_path)
    codebook = load_codebook(codebook_path)

    result = build_review_sample(
        coded_df,
        codebook,
        id_column=id_column,
        flag_column=flag_column,
        strata_column=strata_column,
        nonflagged_sample_size=nonflagged_sample_size,
        random_seed=random_seed,
    )

    result.review_df.to_csv(output_path, index=False)
    with metadata_path.open("w", encoding="utf-8") as file_obj:
        json.dump(result.metadata, file_obj, indent=2, ensure_ascii=False)

    return result
