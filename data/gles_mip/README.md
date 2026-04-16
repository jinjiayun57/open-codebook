# GLES MIP Pilot Data

This folder contains data documentation for the GLES most-important-problem (MIP) pilot built on top of OpenCodebook.
The pilot uses GLES material to support an early-stage study of interpretable coding, issue domains, framing, ambiguity, and reliability in open-ended political problem responses. The repository keeps the data structure explicit so that raw source files, derived working files, and future study outputs remain easy to distinguish.

## Provenance

The source data for this pilot come from `GESIS` / `GLES`.

- Dataset identifier: `ZA10101`
- Pilot inputs: the open-ended response file and the main survey file

This folder is intended to document how those files are used inside the OpenCodebook repository. Raw source files should remain unchanged after download. Derived working files belong in `interim/`.

## Files

- `raw/ZA10101_v3-0-0_open-ended.csv`
  Original open-ended response file downloaded from GESIS/GLES.

- `raw/ZA10101_v3-0-0_en.sav`
  Main survey file with English labels and metadata, used for linking, inspection, and interpretation.

- `interim/gles_mip_sample.csv`
  Working pilot sample derived from `pre020s`, the pre-election most-important-political-problem response field, for annotation and reliability analysis.

## Citation and attribution

Recommended citation:

GLES. (2026). *GLES Rolling Cross-Section 2025* (ZA10101; Version 3.0.0) [Data set]. GESIS, Cologne. https://doi.org/10.4232/5.ZA10101.3.0.0

Data access:

https://search.gesis.org/research_data/ZA10101

Access category:

`A` — data and documents are released for academic research and teaching.

## Reproducibility note

For reproducibility, raw files in `raw/` should be treated as source inputs and should not be edited in place. Any cleaning, sampling, harmonization, or analysis-ready subsets should be written as derived files under `interim/`.

This separation supports transparent study setup and makes it easier to trace how the GLES MIP pilot sample was constructed from the original GLES materials.
