# OpenCodebook

**OpenCodebook** is an early-stage open-source project for AI-assisted, codebook-driven coding of social science and humanities (SSH) text data.

It is designed for settings where coding is not purely classificatory, but interpretive: subjective, sensitive, indirect, or partly implicit text that requires researcher judgment. Rather than treating LLMs as tools that replace interpretation, the project explores how open and local models can support coding in ways that keep uncertainty visible, invite researcher review, and make analytic decisions more transparent and reproducible.

The repository now has two connected layers:

- **OpenCodebook** as the core workflow engine
- **research studies** built on top of that engine

At this stage, the repo includes:

- a compact end-to-end demo
- a first research pilot on stance, ambiguity, and interpretive coding using GLES open-ended responses

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

## Current status

OpenCodebook is still intentionally small in scope. The current version supports local LLM-based coding through Ollama and produces structured outputs for researcher review.

The repository is now organized so that the engine, a runnable demo, and study-specific materials can coexist cleanly in one place.

## Repository structure

```text
codebooks/
  demos/              Demo codebooks
  stance_ambiguity/   Study-specific codebooks
data/
  demos/              Demo input data
  stance_ambiguity/   Study-specific raw and interim data
notebooks/
  demos/              Demo notebooks
  stance_ambiguity/   Study notebooks
outputs/
  demos/              Demo outputs
  stance_ambiguity/   Study outputs
studies/              High-level study notes and research framing
src/open_codebook/    Core Python modules for coding workflow
```

Current core modules include:

- `schema.py`: data structures and output schema logic
- `io_utils.py`: shared path helpers and file utilities
- `coder.py`: coding logic and structured output generation
- `run_demo.py`: minimal demo pipeline
- `reliability.py`: placeholder module for agreement and disagreement analysis
- `run_study.py`: placeholder study runner for future non-demo workflows

## Engine, demo, and study

### OpenCodebook as engine

The engine lives in `src/open_codebook/` and remains the core of the repository. It is responsible for:

- loading codebooks and text data
- building structured output schemas
- calling a local model through Ollama
- writing row-level outputs and run metadata

### Demo workflow

The demo remains the smallest runnable example in the repository. Its assets now live under:

- `codebooks/demos/demo_codebook.yaml`
- `data/demos/demo_responses.csv`
- `notebooks/demos/01_demo_workflow.ipynb`

Running the demo writes:

- `outputs/demos/coded_demo.csv`
- `outputs/demos/run_metadata.json`

### First research study: stance and ambiguity pilot

The first serious study inside this repository is a GLES-based pilot on stance, ambiguity, and interpretive coding of open-ended responses.

Study materials live under:

- `codebooks/stance_ambiguity/`
- `data/stance_ambiguity/`
- `notebooks/stance_ambiguity/`
- `outputs/stance_ambiguity/`
- `studies/stance_ambiguity_pilot/`

## Demo workflow

The repository currently includes a small demo workflow based on:
- `codebooks/demos/demo_codebook.yaml`
- `data/demos/demo_responses.csv`

This demo illustrates how a researcher-defined codebook and a small text dataset can be connected in a modular Python workflow, where output field definitions are derived from the YAML codebook and used for structured coding and review.

## Run the demo

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3.5:4b
PYTHONPATH=src python3 -m open_codebook.run_demo
```

This repository uses a `src/` layout, so the demo is run as a module rather than as a standalone script. Ollama must be installed and running locally before you start the demo.

If the run succeeds, it writes:

- `outputs/demos/coded_demo.csv`
- `outputs/demos/run_metadata.json`

## What the demo currently does

- Loads `codebooks/demos/demo_codebook.yaml`
- Reads `data/demos/demo_responses.csv`
- Uses `text_en` as the input text column
- Sends each row to a local Ollama model for structured coding
- Saves row-level coding results and run-level metadata

## Stance and ambiguity pilot

The stance and ambiguity pilot is not yet a full runnable study. At this stage, the repository includes:

- a dedicated study folder under `studies/stance_ambiguity_pilot/`
- a study-specific codebook draft under `codebooks/stance_ambiguity/`
- placeholder notebook locations for data inspection, sampling, and reliability work
- a future workflow stub in `src/open_codebook/run_study.py`

The raw GLES source files are present under `data/stance_ambiguity/raw/`. The study remains early-stage, and the derived interim sample plus analysis outputs still need to be created.

## Current limitations

- The current demo depends on a local Ollama setup and will not run unless Ollama is installed and active.
- The coding schema is now derived from the YAML codebook, but the repo remains an early prototype rather than a fully configurable research tool.
- The stance and ambiguity pilot is still at the scaffolding stage and does not yet include the derived interim sample or finished reliability analysis.
- The repository is intended to demonstrate workflow direction and study organization rather than a finished research platform.

## Possible use cases

- Open-ended survey responses
- Interview excerpts
- Focus group excerpts
- Fieldnote passages or analytic memos
- Policy or institutional text snippets
- Publicly available online discussions, such as forum posts or comment threads
- Other short- to medium-length SSH text that requires interpretive coding and researcher review
