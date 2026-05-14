from __future__ import annotations

import unittest
from pathlib import Path

from open_codebook.run_agreement import build_agreement_output_paths
from open_codebook.run_review_prep import build_review_output_paths
from open_codebook.run_study import build_study_output_paths


class RunnerPathTests(unittest.TestCase):
    def test_study_outputs_are_study_name_prefixed(self) -> None:
        output_dir = Path("outputs/gles_mip")

        coded_path, metadata_path = build_study_output_paths(
            output_dir,
            "gles_mip_v2",
        )

        self.assertEqual(coded_path, output_dir / "gles_mip_v2_coded.csv")
        self.assertEqual(metadata_path, output_dir / "gles_mip_v2_run_metadata.json")

    def test_review_outputs_are_study_name_prefixed(self) -> None:
        output_dir = Path("outputs/gles_mip")

        coded_path, review_path, metadata_path = build_review_output_paths(
            output_dir,
            "gles_mip_v2",
        )

        self.assertEqual(coded_path, output_dir / "gles_mip_v2_coded.csv")
        self.assertEqual(review_path, output_dir / "gles_mip_v2_review_template.csv")
        self.assertEqual(
            metadata_path,
            output_dir / "gles_mip_v2_review_sample_metadata.json",
        )

    def test_agreement_outputs_are_study_name_prefixed(self) -> None:
        output_dir = Path("outputs/gles_mip")

        (
            review_path,
            summary_path,
            disagreement_path,
            metadata_path,
        ) = build_agreement_output_paths(output_dir, "gles_mip_v2")

        self.assertEqual(review_path, output_dir / "gles_mip_v2_review_template.csv")
        self.assertEqual(summary_path, output_dir / "gles_mip_v2_agreement_summary.csv")
        self.assertEqual(
            disagreement_path,
            output_dir / "gles_mip_v2_agreement_disagreements.csv",
        )
        self.assertEqual(
            metadata_path,
            output_dir / "gles_mip_v2_agreement_metadata.json",
        )


if __name__ == "__main__":
    unittest.main()
