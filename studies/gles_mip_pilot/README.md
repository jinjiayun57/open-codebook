# GLES MIP Pilot

This pilot is the first research-oriented study organized inside the OpenCodebook repository.

The focus is on coding open-ended GLES responses to the most-important-political-problem question. The aim is not to turn the repository into a separate study-specific codebase, but to show how a reusable coding engine can support a concrete empirical project.

At this stage, the pilot includes:

- a study-specific issue-domain codebook
- a revised v2 codebook draft informed by the first disagreement diagnosis
- a reserved data structure for raw and interim GLES files
- a runnable study configuration under `studies/gles_mip_pilot/config.yaml`
- a v2 rerun configuration under `studies/gles_mip_pilot/config_v2.yaml`
- a first model-coded pilot output under `outputs/gles_mip/gles_mip_v1_coded.csv`
- a review template and agreement outputs under `outputs/gles_mip/`
- notebooks for inspection, sampling, and follow-up analysis

## Useful commands

To evaluate v2 model outputs against the v1 human-reviewed sample:

```bash
PYTHONPATH=src .venv/bin/python -m open_codebook.run_agreement \
  studies/gles_mip_pilot/config_v2.yaml \
  outputs/gles_mip/gles_mip_v2_on_v1_review_template.csv
```
