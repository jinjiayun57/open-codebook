# OpenCodebook

**OpenCodebook** is an early-stage open-source prototype for AI-assisted, codebook-driven coding of social science and humanities (SSH) text data.

It is designed for settings where coding is not purely classificatory, but interpretive: subjective, sensitive, indirect, or partly implicit text that requires researcher judgment. Rather than treating LLMs as tools that replace interpretation, the project explores how open and local models can support coding in a way that keeps uncertainty visible, invites researcher review, and makes analytic decisions more transparent and reproducible.

At this stage, the repository is best understood as a compact end-to-end demo: a small codebook, a small CSV dataset, and a Python script that sends each text item to a local Ollama model and saves structured outputs for researcher review.

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
- **Researcher review loop**
- **Reproducible prompts, model settings, and audit trails**

## Workflow

1. Load a researcher-defined codebook
2. Read short SSH text data from a CSV file
3. Build the structured output schema from the codebook
4. Generate structured coding outputs with a local Ollama model
5. Save coded results together with run-level metadata

## Current status

OpenCodebook is an early-stage prototype for structured coding of social science and humanities text data. The current version supports local LLM-based coding through Ollama and produces structured outputs for researcher review.

The current demo is intentionally small in scope. It is run as a Python module from the project root.

## Repository structure

```text
codebooks/            YAML codebooks used to define coding categories
data/                 Demo SSH text data in CSV format
notebooks/            Example notebook showing the demo workflow
src/open_codebook/    Core Python modules for coding workflow
```

Current core modules include:

- `schema.py`: data structures and output schema logic
- `io_utils.py`: reading and writing codebooks, input text, and outputs
- `coder.py`: coding logic and structured output generation
- `run_demo.py`: minimal demo pipeline


## Demo workflow

The repository currently includes a small demo workflow based on:
- `codebooks/demo_codebook.yaml`
- `data/demo_responses.csv`

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

- `outputs/coded_demo.csv`
- `outputs/run_metadata.json`

## What the demo currently does

- Loads `codebooks/demo_codebook.yaml`
- Reads `data/demo_responses.csv`
- Uses `text_en` as the input text column
- Sends each row to a local Ollama model for structured coding
- Saves row-level coding results and run-level metadata

## Current limitations

- The current demo depends on a local Ollama setup and will not run unless Ollama is installed and active.
- The coding schema is now derived from the YAML codebook, but the demo remains a small prototype rather than a fully configurable research tool.
- The repository is an early prototype intended to demonstrate workflow direction rather than a fully packaged research tool.

## Possible use cases

- Open-ended survey responses
- Interview excerpts
- Focus group excerpts
- Fieldnote passages or analytic memos
- Policy or institutional text snippets
- Publicly available online discussions, such as forum posts or comment threads
- Other short- to medium-length SSH text that requires interpretive coding and researcher review
