from __future__ import annotations

import sys
from pathlib import Path

from .agreement import write_agreement_outputs
from .io_utils import get_project_root
from .run_study import DEFAULT_CONFIG_PATH, load_config, resolve_project_path


def build_agreement_output_paths(
    output_dir: Path,
    study_name: str,
) -> tuple[Path, Path, Path, Path]:
    return (
        output_dir / f"{study_name}_review_template.csv",
        output_dir / f"{study_name}_agreement_summary.csv",
        output_dir / f"{study_name}_agreement_disagreements.csv",
        output_dir / f"{study_name}_agreement_metadata.json",
    )


def main() -> None:
    project_root = get_project_root()
    config_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH
    config_path = resolve_project_path(project_root, config_arg)
    config = load_config(config_path)

    output_dir = resolve_project_path(project_root, config["output_dir"])
    (
        review_path,
        summary_path,
        disagreement_path,
        metadata_path,
    ) = build_agreement_output_paths(output_dir, config["study_name"])

    artifacts = write_agreement_outputs(
        review_path=review_path,
        codebook_path=resolve_project_path(project_root, config["codebook_path"]),
        summary_output_path=summary_path,
        disagreement_output_path=disagreement_path,
        metadata_output_path=metadata_path,
        id_column=config["id_column"],
    )

    print(f"Saved agreement summary to: {summary_path}")
    print(f"Saved disagreement rows to: {disagreement_path}")
    print(f"Saved agreement metadata to: {metadata_path}")
    print(
        "Compared reviewed rows per variable: "
        f"{artifacts.metadata['reviewed_row_counts']}"
    )


if __name__ == "__main__":
    main()
