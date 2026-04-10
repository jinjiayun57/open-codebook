from __future__ import annotations

from pathlib import Path

from .io_utils import get_project_root


def get_stance_ambiguity_paths() -> dict[str, Path]:
    project_root = get_project_root()
    study_root = project_root / "data" / "stance_ambiguity"

    return {
        "study_root": study_root,
        "raw_dir": study_root / "raw",
        "interim_dir": study_root / "interim",
        "output_dir": project_root / "outputs" / "stance_ambiguity",
        "codebook_path": project_root
        / "codebooks"
        / "stance_ambiguity"
        / "gles_mip_codebook.yaml",
    }


def main() -> None:
    paths = get_stance_ambiguity_paths()
    print("Stance ambiguity study scaffold is in place.")
    print(f"Expected codebook: {paths['codebook_path']}")
    print(f"Expected raw data directory: {paths['raw_dir']}")
    print(f"Expected interim data directory: {paths['interim_dir']}")
    print(f"Expected output directory: {paths['output_dir']}")
    print("Add the GLES files and study-specific processing steps in a later iteration.")


if __name__ == "__main__":
    main()
