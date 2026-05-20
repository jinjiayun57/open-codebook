from pathlib import Path
from open_codebook.io_utils import get_project_root, load_csv

project_root = get_project_root()

review_path = project_root / "outputs/gles_mip/gles_mip_v1_review_template.csv"
v2_path = project_root / "outputs/gles_mip/gles_mip_v2_coded.csv"
out_path = project_root / "outputs/gles_mip/gles_mip_v2_on_v1_review_template.csv"

fields = [
    "issue_domain",
    "specificity",
    "framing",
    "ambiguity",
    "multi_issue"
]

review_df = load_csv(review_path)
v2_df = load_csv(v2_path)

v2_lookup = v2_df.set_index("sample_id")

out_df = review_df.copy()

for field in fields:
    out_df[f"{field}_model"] = out_df["sample_id"].map(v2_lookup[field])
    

out_df["review_flag"] = out_df["sample_id"].map(v2_lookup["review_flag"])

out_df.to_csv(out_path, index=False)

print("wrote:", out_path)
print("Rows:", len(out_df))
print("Missing v2 matches:", out_df["issue_domain_model"].isna().sum())
