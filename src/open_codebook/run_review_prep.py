from __future__ import annotations

import sys
from pathlib import Path

from .io_utils import get_project_root
from .review import write_review_outputs
from .run_study import DEFAULT_CONFIG_PATH, load_config, resolve_project_path


def _parse_int_arg(args: list[str], index: int, default: int) -> int:
    if len(args) <= index:
        return default
    return int(args[index])


def build_review_output_paths(
    output_dir: Path,
    study_name: str,
) -> tuple[Path, Path, Path]:
    return (
        output_dir / f"{study_name}_coded.csv",
        output_dir / f"{study_name}_review_template.csv",
        output_dir / f"{study_name}_review_sample_metadata.json",
    )


def main() -> None:
    project_root = get_project_root()
    config_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH
    config_path = resolve_project_path(project_root, config_arg)
    config = load_config(config_path)

    output_dir = resolve_project_path(project_root, config["output_dir"])
    coded_path, review_output_path, metadata_output_path = build_review_output_paths(
        output_dir,
        config["study_name"],
    )

    nonflagged_sample_size = _parse_int_arg(sys.argv, 2, default=24)
    random_seed = _parse_int_arg(sys.argv, 3, default=20260421)

    result = write_review_outputs(
        coded_path=coded_path,
        codebook_path=resolve_project_path(project_root, config["codebook_path"]),
        output_path=review_output_path,
        metadata_path=metadata_output_path,
        id_column=config["id_column"],
        flag_column="review_flag",
        strata_column="issue_domain",
        nonflagged_sample_size=nonflagged_sample_size,
        random_seed=random_seed,
    )

    print(f"Saved review template to: {review_output_path}")
    print(f"Saved review sampling metadata to: {metadata_output_path}")
    print(f"Prepared {len(result.review_df)} rows for review.")


if __name__ == "__main__":
    main()
