from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_coded_output(coded_path: Path) -> pd.DataFrame:
    """Load a coded output table for future agreement analysis."""
    return pd.read_csv(coded_path)


def summarize_agreement(coded_df: pd.DataFrame) -> pd.DataFrame:
    """Placeholder for future agreement and disagreement summaries."""
    return pd.DataFrame(
        [
            {
                "status": "not_implemented",
                "n_rows": len(coded_df),
                "note": "Add coder-level agreement logic in a later iteration.",
            }
        ]
    )
