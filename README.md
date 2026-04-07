# OpenCodebook

**OpenCodebook** is an open-source prototype for AI-assisted coding of social science and humanities (SSH) text data.
It is designed for settings where coding is not purely classificatory, but interpretive: subjective, sensitive, indirect, or partly implicit text that requires researcher judgment. Rather than treating LLMs as tools that replace interpretation, the project explores how open and local models can support coding in a way that keeps uncertainty visible, invites researcher review, and makes analytic decisions more transparent and reproducible.

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
3. Generate structured coding outputs with an open or local model
4. Extract evidence spans and flag uncertainty
5. Save coded results together with run-level metadata

## Current status

OpenCodebook is an early-stage prototype for structured coding of social science and humanities text data. The current version supports local LLM-based coding through Ollama and produces structured outputs for researcher review.

## Possible use cases

- Open-ended survey responses
- Interview excerpts
- Focus group excerpts
- Fieldnote passages or analytic memos
- Policy or institutional text snippets
- Publicly available online discussions, such as forum posts or comment threads
- Other short- to medium-length SSH text that requires interpretive coding and researcher review