from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_coded_output(coded_path: Path) -> pd.DataFrame:
    """Load a coded output table for future human-vs-human reliability analysis."""
    return pd.read_csv(coded_path)


def summarize_agreement(coded_df: pd.DataFrame) -> pd.DataFrame:
    """Reserved for future classical reliability work between human coders."""
    return pd.DataFrame(
        [
            {
                "status": "not_implemented",
                "n_rows": len(coded_df),
                "note": (
                    "Model-vs-review agreement now lives in open_codebook.agreement. "
                    "Keep this module for future human-vs-human reliability work."
                ),
            }
        ]
    )
