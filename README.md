# OpenCodebook

**OpenCodebook** is an early-stage open-source project for AI-assisted, codebook-driven coding of social science and humanities (SSH) text data.

It is designed for settings where coding is not purely classificatory, but interpretive: subjective, sensitive, indirect, or partly implicit text that requires researcher judgment. Rather than treating LLMs as tools that replace interpretation, the project explores how open and local models can support coding in ways that keep uncertainty visible, invite researcher review, and make analytic decisions more transparent and reproducible.

The repository now has two connected layers:

- **OpenCodebook** as the core workflow engine
- **research studies** built on top of that engine

At this stage, the repo includes:

- a compact end-to-end demo
- a first research pilot on coding GLES most-important-political-problem responses

## Why this project?

Researchers in the social sciences and humanities are increasingly experimenting with LLM-assisted coding, often through ad hoc prompting. While this can be useful, it also makes coding decisions difficult to inspect, compare, or reproduce, especially when texts are ambiguous, norm-laden, or only partly explicit in what they express.

OpenCodebook is motivated by a simple question:

**How can open-source LLMs support SSH text coding without obscuring uncertainty, researcher judgment, or reproducibility?**

## Core ideas

- **AI-assisted coding, not AI replacing interpretation**
- **Local / open-source / privacy-aware workflows**
- **Researcher-defined codebooks**
- **Structured outputs**
- **Uncertainty flags and evidence spans**
- **Researcher review loops**
- **Reproducible prompts, settings, and audit trails**

## Workflow

1. Load a researcher-defined codebook
2. Read short SSH text data from a CSV file
3. Build a structured output schema from the codebook
4. Generate structured coding outputs with a local Ollama model
5. Save coded results together with run-level metadata
6. Prepare a researcher review sample and adjudication template
7. Compare model outputs against reviewed codes with agreement summaries

## Current status

OpenCodebook is still intentionally small in scope. The current version supports local LLM-based coding through Ollama and produces structured outputs for researcher review.

The repository is now organized so that the engine, a runnable demo, and study-specific materials can coexist cleanly in one place.

## Repository structure

```text
codebooks/
  demos/              Demo codebooks
  gles_mip/           GLES most-important-problem codebooks
data/
  demos/              Demo input data
  gles_mip/           GLES most-important-problem raw and interim data
notebooks/
  demos/              Demo notebooks
  gles_mip/           GLES MIP study notebooks
outputs/
  demos/              Demo outputs
  gles_mip/           GLES MIP study outputs
studies/              High-level study notes and research framing
src/open_codebook/    Core Python modules for coding workflow
```

Current core modules include:

- `schema.py`: data structures and output schema logic
- `io_utils.py`: shared path helpers and file utilities
- `coder.py`: coding logic and structured output generation
- `run_demo.py`: minimal demo pipeline
- `run_study.py`: config-driven study runner for non-demo workflows
- `review.py`: review-sample construction and adjudication-template export
- `run_review_prep.py`: CLI entry point for review preparation
- `agreement.py`: model-vs-review agreement summaries and disagreement exports
- `run_agreement.py`: CLI entry point for agreement analysis
- `reliability.py`: reserved for future human-vs-human reliability analysis

## Engine, demos, and study

### OpenCodebook as engine

The engine lives in `src/open_codebook/` and remains the core of the repository. It is responsible for:

- loading codebooks and text data
- building structured output schemas
- calling a local model through Ollama
- writing row-level outputs and run metadata
- preparing review samples for researcher adjudication
- summarizing agreement and disagreement between model output and researcher review

### Local engine demo

The local engine demo is the smallest batch workflow for the core package. It
uses the reusable modules in `src/open_codebook/`, calls a local Ollama model,
and writes reproducible CSV/JSON artifacts. Its assets live under:

- `codebooks/demos/demo_codebook.yaml`
- `data/demos/demo_responses.csv`
- `notebooks/demos/01_demo_workflow.ipynb`

Running the demo writes:

- `outputs/demos/coded_demo.csv`
- `outputs/demos/run_metadata.json`

### Hosted Gradio companion

The `demo/` directory is a self-contained Gradio app intended for Hugging Face
Spaces. It is a public-facing companion to the project rather than the primary
local workflow. It uses the Hugging Face serverless Inference API, includes the
GLES pilot agreement summaries, and lets visitors try built-in or uploaded YAML
codebooks in a browser.

The hosted companion is deliberately limited: rate limits, model availability,
and serverless behaviour can differ from the local Ollama workflow. Its
deployment notes live in:

- `demo/README.md`
- `demo/DEPLOY.md`

### First research study: GLES MIP pilot

The first serious study inside this repository is a GLES-based pilot on coding open-ended responses to the most-important-political-problem question. The study focuses on issue domain, specificity, framing, ambiguity, and reliability rather than forcing stance labels onto short issue mentions.

Study materials live under:

- `codebooks/gles_mip/`
- `data/gles_mip/`
- `notebooks/gles_mip/`
- `outputs/gles_mip/`
- `studies/gles_mip_pilot/`

The GLES pilot codebooks are:

- `codebooks/gles_mip/codebook_v1.yaml`: original pilot codebook used for the first 95-row agreement pass
- `codebooks/gles_mip/codebook_v2.yaml`: revised draft informed by the v1 disagreement diagnosis

An older stance-oriented draft is kept for reference under:

- `codebooks/gles_mip/archive/gles_mip_codebook.yaml`

## Local engine demo

The repository includes a small local demo workflow based on:
- `codebooks/demos/demo_codebook.yaml`
- `data/demos/demo_responses.csv`

This demo illustrates how a researcher-defined codebook and a small text dataset can be connected in a modular Python workflow, where output field definitions are derived from the YAML codebook and used for structured coding and review.

## Run the local demo

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3.5:4b
PYTHONPATH=src python3 -m open_codebook.run_demo
```

This repository uses a `src/` layout, so the local demo is run as a module rather than as a standalone script. Ollama must be installed and running locally before you start the demo.

If the run succeeds, it writes:

- `outputs/demos/coded_demo.csv`
- `outputs/demos/run_metadata.json`

## What the local demo currently does

- Loads `codebooks/demos/demo_codebook.yaml`
- Reads `data/demos/demo_responses.csv`
- Uses `text_en` as the input text column
- Sends each row to a local Ollama model for structured coding
- Saves row-level coding results and run-level metadata

## Run the hosted companion locally

The browser demo under `demo/` is separate from the local engine workflow. To
run it from the project root:

```bash
cd demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
HF_TOKEN=your_hugging_face_token python3 app.py
```

For deployment to Hugging Face Spaces, see `demo/DEPLOY.md`.

## GLES MIP pilot

The GLES MIP pilot now has a runnable study workflow plus a first completed model-coded pilot sample. The repository currently includes:

- a dedicated study folder under `studies/gles_mip_pilot/`
- a study-specific issue-domain codebook under `codebooks/gles_mip/`
- a config-driven study runner in `src/open_codebook/run_study.py`
- a completed pilot coding output in `outputs/gles_mip/gles_mip_v1_coded.csv`
- a review template in `outputs/gles_mip/gles_mip_v1_review_template.csv`
- agreement outputs in `outputs/gles_mip/agreement_summary.csv` and `outputs/gles_mip/agreement_disagreements.csv`
- notebooks for data inspection, sampling, and follow-up analysis

The raw GLES source files are present under `data/gles_mip/raw/`. The pilot sample used for the first study run is stored under `data/gles_mip/interim/`.

## Current limitations

- The local engine demo depends on a local Ollama setup and will not run unless Ollama is installed and active.
- The hosted Gradio companion uses the Hugging Face serverless Inference API and may be affected by rate limits, model availability, cold starts, and provider-side behaviour.
- The coding schema is now derived from the YAML codebook, but the repo remains an early prototype rather than a fully configurable research tool.
- The current agreement workflow compares model outputs against researcher review, but it does not yet implement fuller validation utilities, reviewer-assignment workflows, or human-vs-human reliability analysis.
- The GLES MIP pilot now includes coded outputs and first-pass agreement results, but the codebook and review protocol are still being refined in response to disagreement patterns.
- The repository is intended to demonstrate workflow direction and study organization rather than a finished research platform.

## Possible use cases

- Open-ended survey responses
- Interview excerpts
- Focus group excerpts
- Fieldnote passages or analytic memos
- Policy or institutional text snippets
- Publicly available online discussions, such as forum posts or comment threads
- Other short- to medium-length SSH text that requires interpretive coding and researcher review
