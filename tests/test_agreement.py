from __future__ import annotations

import unittest

import pandas as pd

from open_codebook.agreement import summarize_review_agreement


CODEBOOK = {
    "codes": [
        {"name": "issue_domain", "values": ["economy", "migration", "other"]},
        {
            "name": "specificity",
            "values": ["label_only", "named_policy", "framed_claim", "actor_reference"],
        },
        {"name": "framing", "values": ["descriptive", "evaluative", "directive"]},
        {"name": "ambiguity", "values": ["low", "medium", "high"]},
        {"name": "multi_issue", "type": "boolean", "values": [True, False]},
    ]
}


class AgreementTests(unittest.TestCase):
    def test_summarize_review_agreement_reports_nominal_and_ordinal_metrics(self) -> None:
        review_df = pd.DataFrame(
            [
                {
                    "sample_id": "s1",
                    "review_group": "flagged",
                    "issue_domain_model": "economy",
                    "issue_domain_reviewed": "economy",
                    "specificity_model": "label_only",
                    "specificity_reviewed": "named_policy",
                    "framing_model": "descriptive",
                    "framing_reviewed": "descriptive",
                    "ambiguity_model": "low",
                    "ambiguity_reviewed": "medium",
                    "multi_issue_model": False,
                    "multi_issue_reviewed": "false",
                    "issue_domain_note": "",
                    "specificity_note": "close call",
                    "framing_note": "",
                    "ambiguity_note": "some interpretation needed",
                    "multi_issue_note": "",
                },
                {
                    "sample_id": "s2",
                    "review_group": "nonflagged_audit",
                    "issue_domain_model": "migration",
                    "issue_domain_reviewed": "other",
                    "specificity_model": "framed_claim",
                    "specificity_reviewed": "framed_claim",
                    "framing_model": "evaluative",
                    "framing_reviewed": "directive",
                    "ambiguity_model": "high",
                    "ambiguity_reviewed": "high",
                    "multi_issue_model": True,
                    "multi_issue_reviewed": "true",
                    "issue_domain_note": "borderline target",
                    "specificity_note": "",
                    "framing_note": "researcher reads directive",
                    "ambiguity_note": "",
                    "multi_issue_note": "",
                },
            ]
        )

        artifacts = summarize_review_agreement(
            review_df,
            CODEBOOK,
            id_column="sample_id",
        )

        summary_df = artifacts.summary_df.set_index("variable")
        self.assertEqual(summary_df.loc["issue_domain", "measurement_level"], "nominal")
        self.assertEqual(summary_df.loc["issue_domain", "agreement_metric"], "cohen_kappa")
        self.assertEqual(summary_df.loc["specificity", "measurement_level"], "ordinal")
        self.assertEqual(summary_df.loc["specificity", "agreement_metric"], "weighted_kappa")
        self.assertEqual(summary_df.loc["multi_issue", "n_matches"], 2)
        self.assertEqual(summary_df.loc["framing", "n_matches"], 1)
        self.assertEqual(len(artifacts.disagreements_df), 4)

    def test_unreviewed_rows_are_excluded_from_comparisons(self) -> None:
        review_df = pd.DataFrame(
            [
                {
                    "sample_id": "s1",
                    "review_group": "flagged",
                    "issue_domain_model": "economy",
                    "issue_domain_reviewed": "",
                    "specificity_model": "label_only",
                    "specificity_reviewed": "",
                    "framing_model": "descriptive",
                    "framing_reviewed": "",
                    "ambiguity_model": "low",
                    "ambiguity_reviewed": "",
                    "multi_issue_model": False,
                    "multi_issue_reviewed": "",
                }
            ]
        )

        artifacts = summarize_review_agreement(
            review_df,
            CODEBOOK,
            id_column="sample_id",
        )

        self.assertTrue((artifacts.summary_df["n_compared"] == 0).all())
        self.assertTrue(artifacts.disagreements_df.empty)


if __name__ == "__main__":
    unittest.main()
