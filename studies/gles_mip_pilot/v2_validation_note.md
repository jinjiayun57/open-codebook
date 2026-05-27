# GLES MIP Pilot — v2 Validation Note

This note summarizes the first validation pass for `codebook_v2.yaml`. The
purpose of v2 was to address systematic disagreement patterns found in the v1
review pass, especially for `framing`, `specificity`, `ambiguity`, and
`issue_domain`.

## Source files

- v2 coded output: `outputs/gles_mip/gles_mip_v2_coded.csv`
- v1 human-reviewed anchor: `outputs/gles_mip/gles_mip_v1_review_template.csv`
- v2-on-v1 comparison table:
  `outputs/gles_mip/gles_mip_v2_on_v1_review_template.csv`
- v2 agreement summary:
  `outputs/gles_mip/gles_mip_v2_agreement_summary.csv`
- v2 disagreement rows:
  `outputs/gles_mip/gles_mip_v2_agreement_disagreements.csv`

The v2 agreement table compares v2 model outputs against the same 95
human-reviewed rows used for the v1 agreement pass.

## Summary results

| Variable | v1 %-agree | v1 κ | v2 %-agree | v2 κ | Interpretation |
|---|---:|---:|---:|---:|---|
| `issue_domain` | 0.63 | 0.57 | 0.7474 | 0.6882 | improved |
| `specificity` | 0.54 | 0.31 | 0.6421 | 0.4931 | improved, still imperfect |
| `framing` | 0.59 | 0.35 | 0.7789 | 0.6277 | strongest improvement |
| `ambiguity` | 0.42 | 0.27 | 0.6105 | 0.3735 | improved, still weak |
| `multi_issue` | 0.94 | 0.86 | 0.8947 | 0.7489 | still strong, slightly worsened |

For `specificity` and `ambiguity`, κ is weighted κ because both are ordinal
fields. For the other variables, κ is Cohen's κ.

## Interpretation

v2 improved four of the five coded variables. The clearest gain is
`framing`, where v2 added more explicit rules for German nominalized
complaints and non-imperative directives. This appears to reduce v1's tendency
to overuse broad descriptive or evaluative categories.

`issue_domain` also improved. The v2 codebook made the
`democracy_governance` tie-breaker more explicit, especially for complaints
about political behavior, political elites, missing leadership, and general
political failure.

`specificity` improved but remains imperfect. The model is less likely than in
v1 to collapse difficult short responses into `label_only`, but distinguishing
`label_only` from `framed_claim` remains a hard interpretive boundary.

`ambiguity` improved but remains the weakest dimension. This suggests that the
ambiguity scale is not only a prompt clarity problem. Short MIP responses often
contain genuine interpretive uncertainty, especially when a terse phrase points
to a recognizable issue domain but leaves the intended meaning underspecified.

`multi_issue` remains highly reliable in absolute terms, but it worsened
slightly from v1. This should be checked in the v2 disagreement rows. A likely
hypothesis is that v2's broader sensitivity to compound or complex expressions
may sometimes over-detect multiple issues.

## Next step

Run a focused error audit on
`outputs/gles_mip/gles_mip_v2_agreement_disagreements.csv`, especially:

- remaining `ambiguity` disagreements
- remaining `specificity` disagreements
- `multi_issue` cases that worsened from v1 to v2
- whether the revised `review_flag` catches the remaining high-risk rows
