from __future__ import annotations

import unittest

import pandas as pd

from open_codebook.review import build_review_sample


CODEBOOK = {
    "codes": [
        {"name": "issue_domain", "values": ["economy", "migration", "other"]},
        {"name": "specificity", "values": ["label_only", "framed_claim"]},
        {"name": "ambiguity", "values": ["low", "medium", "high"]},
        {"name": "multi_issue", "type": "boolean", "values": [True, False]},
    ]
}


class ReviewSampleTests(unittest.TestCase):
    def test_build_review_sample_includes_flagged_and_nonflagged_audit(self) -> None:
        coded_df = pd.DataFrame(
            [
                {
                    "sample_id": "a1",
                    "response_text": "Economy",
                    "issue_domain": "economy",
                    "specificity": "label_only",
                    "ambiguity": "low",
                    "multi_issue": False,
                    "review_flag": False,
                },
                {
                    "sample_id": "a2",
                    "response_text": "Migration",
                    "issue_domain": "migration",
                    "specificity": "label_only",
                    "ambiguity": "low",
                    "multi_issue": False,
                    "review_flag": False,
                },
                {
                    "sample_id": "a3",
                    "response_text": "Policy failure",
                    "issue_domain": "economy",
                    "specificity": "framed_claim",
                    "ambiguity": "high",
                    "multi_issue": False,
                    "review_flag": True,
                },
                {
                    "sample_id": "a4",
                    "response_text": "Two issues",
                    "issue_domain": "other",
                    "specificity": "framed_claim",
                    "ambiguity": "medium",
                    "multi_issue": True,
                    "review_flag": True,
                },
            ]
        )

        result = build_review_sample(
            coded_df,
            CODEBOOK,
            id_column="sample_id",
            nonflagged_sample_size=2,
            random_seed=7,
        )

        review_df = result.review_df
        self.assertEqual(len(review_df), 4)
        self.assertCountEqual(
            review_df["sample_id"].tolist(),
            ["a1", "a2", "a3", "a4"],
        )
        self.assertIn("issue_domain_model", review_df.columns)
        self.assertIn("issue_domain_reviewed", review_df.columns)
        self.assertIn("issue_domain_note", review_df.columns)
        self.assertEqual(result.metadata["n_flagged_rows"], 2)
        self.assertEqual(result.metadata["n_nonflagged_sampled"], 2)

    def test_nonflagged_sampling_spreads_across_issue_domain_when_possible(self) -> None:
        coded_df = pd.DataFrame(
            [
                {
                    "sample_id": f"e{i}",
                    "response_text": "Economy",
                    "issue_domain": "economy",
                    "specificity": "label_only",
                    "ambiguity": "low",
                    "multi_issue": False,
                    "review_flag": False,
                }
                for i in range(3)
            ]
            + [
                {
                    "sample_id": f"m{i}",
                    "response_text": "Migration",
                    "issue_domain": "migration",
                    "specificity": "label_only",
                    "ambiguity": "low",
                    "multi_issue": False,
                    "review_flag": False,
                }
                for i in range(3)
            ]
            + [
                {
                    "sample_id": "f1",
                    "response_text": "Flagged case",
                    "issue_domain": "other",
                    "specificity": "framed_claim",
                    "ambiguity": "high",
                    "multi_issue": False,
                    "review_flag": True,
                }
            ]
        )

        result = build_review_sample(
            coded_df,
            CODEBOOK,
            id_column="sample_id",
            nonflagged_sample_size=2,
            random_seed=11,
        )

        audit_df = result.review_df[result.review_df["review_group"] == "nonflagged_audit"]
        self.assertEqual(len(audit_df), 2)
        self.assertCountEqual(
            audit_df["review_issue_domain_group"].tolist(),
            ["economy", "migration"],
        )


if __name__ == "__main__":
    unittest.main()
