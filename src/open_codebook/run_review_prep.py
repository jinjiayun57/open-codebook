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


def main() -> None:
    project_root = get_project_root()
    config_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH
    config_path = resolve_project_path(project_root, config_arg)
    config = load_config(config_path)

    output_dir = resolve_project_path(project_root, config["output_dir"])
    coded_path = output_dir / f"{config['study_name']}_coded.csv"
    review_output_path = output_dir / f"{config['study_name']}_review_template.csv"
    metadata_output_path = output_dir / "review_sample_metadata.json"

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
