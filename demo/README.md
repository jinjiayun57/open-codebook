---
title: OpenCodebook Demo
emoji: 📋
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
short_description: AI-assisted, codebook-driven coding of social-science text.
---

# OpenCodebook Demo

Interactive companion to the [OpenCodebook](https://github.com/) research project.
This Space lets visitors try AI-assisted, codebook-driven coding of short
social-science and humanities text, inspect the first pilot study
(GLES most-important-problem responses), and optionally upload their own
YAML codebook.

## What this Space contains

- **Try it** — type or paste a short response, pick a codebook, and see the
  structured coding output (issue domain, specificity, framing, ambiguity,
  multi-issue flag, plus a derived review flag).
- **Examples** — a small public gallery of short texts you can load with one
  click.
- **Pilot results** — summary of the GLES MIP pilot: agreement between the
  model output and a researcher review on 95 rows, with distribution charts
  and illustrative disagreements.
- **Upload codebook** — upload your own YAML codebook, validate it, and try it
  against custom text.

## Important notes on this hosted demo

This Space uses the Hugging Face serverless Inference API to call a small
instruct-tuned language model. The production OpenCodebook workflow is
designed to run **locally through Ollama**. The hosted demo is therefore a
deliberately limited experience intended to illustrate the workflow, not to
reproduce production behaviour.

Rate limits, model availability, and cold-start latency on Spaces can all
affect response time. If a call fails, try again or use the Examples tab,
which can also fall back to pre-computed outputs when available.

## Deployment

See `DEPLOY.md` for how to push this directory to a new Hugging Face Space
and configure the `HF_TOKEN` secret.

## License

MIT. GLES materials are used under GESIS access category A and are not
republished here; only derived summary statistics are shown.
