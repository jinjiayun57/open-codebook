"""HF Inference API wrapper for the OpenCodebook demo Space.

Replaces the local Ollama call in ``src/open_codebook/coder.py`` with a
serverless Hugging Face Inference API call. The prompt construction logic is
kept close to the engine version so the demo behaviour tracks the production
workflow.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError

from codebook_utils import (
    get_coded_fields,
    validate_code_output,
)


# --- Config ----------------------------------------------------------------

DEFAULT_MODEL = os.environ.get(
    "OPENCODEBOOK_DEMO_MODEL",
    "Qwen/Qwen2.5-7B-Instruct",
)
DEFAULT_MAX_TOKENS = int(os.environ.get("OPENCODEBOOK_DEMO_MAX_TOKENS", "512"))
DEFAULT_TEMPERATURE = float(os.environ.get("OPENCODEBOOK_DEMO_TEMPERATURE", "0.0"))

DEFAULT_PROMPT_PREAMBLE = (
    "You are helping with structured coding of short social-science text."
)
DEFAULT_TASK_INSTRUCTION = (
    "Code the input response according to the codebook definitions and "
    "allowed labels."
)


# --- Data types ------------------------------------------------------------


@dataclass
class CodingResult:
    """A successful coding outcome plus diagnostic context."""

    coded: dict
    model: str
    prompt_chars: int
    raw_response: str
    attempts: int


# --- Token handling --------------------------------------------------------


class MissingTokenError(RuntimeError):
    """Raised when no Hugging Face API token is available."""


def _resolve_token() -> str:
    token = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    )
    if not token:
        raise MissingTokenError(
            "No Hugging Face token found. Set HF_TOKEN as a Space secret "
            "(Settings → Variables and secrets) or as a local environment "
            "variable."
        )
    return token


# --- Prompt construction ---------------------------------------------------


def _stringify_values(values: list) -> list[str]:
    return [str(value).lower() for value in values]


def _format_guidance_items(items: list[dict]) -> list[str]:
    lines = []
    for item in items:
        value = item.get("value")
        if value is None:
            continue
        definition = item.get("definition")
        examples = item.get("examples", [])
        line = f"  - {value}"
        if definition:
            line = f"{line}: {definition}"
        lines.append(line)
        if examples:
            lines.append(
                "    Examples: "
                + ", ".join(str(example) for example in examples)
            )
    return lines


def build_prompt(codebook: dict, text: str, config: dict | None = None) -> str:
    """Build the coding prompt. Mirrors the engine's coder.build_prompt."""
    config = config or {}
    codes = get_coded_fields(codebook)
    if not codes:
        raise ValueError("Codebook must define a non-empty 'codes' list.")

    prompt_preamble = codebook.get("prompt_preamble", DEFAULT_PROMPT_PREAMBLE)
    input_language = config.get("language", codebook.get("language", "unknown"))
    codebook_language = config.get("codebook_language", "unknown")
    task_instruction = config.get("task_instruction", DEFAULT_TASK_INSTRUCTION)
    field_names = [code["name"] for code in codes]

    lines: list[str] = [
        prompt_preamble,
        "",
        f"The input response language is: {input_language}.",
        f"The codebook definition language is: {codebook_language}.",
        task_instruction,
        "",
        "Return ONLY a single valid JSON object with exactly these fields "
        "(no prose, no code fences):",
    ]
    lines.extend(f"- {name}" for name in field_names)

    enum_codes = [code for code in codes if code.get("values")]
    if enum_codes:
        lines.append("")
        lines.append("Allowed values:")
        for code in enum_codes:
            lines.append(
                f"- {code['name']}: "
                + ", ".join(_stringify_values(code["values"]))
            )

    lines.append("")
    lines.append("Definitions:")
    for code in codes:
        lines.append(
            f"- {code['name']} = "
            + code.get("description", "No description provided.")
        )
        guidance_items = code.get("categories", code.get("levels", []))
        lines.extend(_format_guidance_items(guidance_items))

    lines.extend(["", "Text:", text])
    return "\n".join(lines)


# --- Response parsing ------------------------------------------------------


_JSON_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def _extract_json_object(raw: str) -> dict:
    """Extract a JSON object from a model response, tolerating small noise."""
    stripped = _JSON_FENCE_RE.sub("", raw.strip())

    # Fast path: the whole response is the object.
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Fallback: grab the first balanced {...} block.
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "Model response did not contain a JSON object. "
            f"First 200 chars: {stripped[:200]!r}"
        )
    candidate = stripped[start : end + 1]
    return json.loads(candidate)


# --- Inference call --------------------------------------------------------


class InferenceError(RuntimeError):
    """Raised when the inference call fails for a reason worth surfacing."""


def _call_model(
    client: InferenceClient,
    model: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except HfHubHTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        if status == 429:
            raise InferenceError(
                "Hugging Face Inference API rate limit hit. Please wait a "
                "moment and try again, or switch to the Examples tab to see "
                "pre-computed outputs."
            ) from exc
        if status in (401, 403):
            raise InferenceError(
                "Hugging Face token rejected. Confirm that HF_TOKEN is set "
                "correctly as a Space secret."
            ) from exc
        if status == 404:
            raise InferenceError(
                f"Model '{model}' is not available through the serverless "
                "Inference API right now. Try a different model via the "
                "OPENCODEBOOK_DEMO_MODEL environment variable."
            ) from exc
        raise InferenceError(
            f"Inference API error ({status}): {exc}"
        ) from exc

    choices = getattr(response, "choices", None) or []
    if not choices:
        raise InferenceError("Inference API returned no choices.")
    content = choices[0].message.content
    if not content:
        raise InferenceError("Inference API returned an empty response.")
    return content


# --- Public entry point ----------------------------------------------------


def code_text(
    text: str,
    codebook: dict,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    config: dict | None = None,
) -> CodingResult:
    """Code a single text with the configured HF Inference API model."""
    if not text or not text.strip():
        raise ValueError("Input text is empty.")

    token = _resolve_token()
    client = InferenceClient(token=token)

    prompt = build_prompt(codebook, text, config=config)
    last_error: Exception | None = None
    raw_response = ""

    for attempt in (1, 2):
        attempt_prompt = prompt
        if attempt == 2:
            attempt_prompt = (
                prompt
                + "\n\nReminder: output must be a single JSON object and nothing else."
            )
        raw_response = _call_model(
            client,
            model=model,
            prompt=attempt_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            parsed = _extract_json_object(raw_response)
            coded = validate_code_output(parsed, codebook)
            return CodingResult(
                coded=coded,
                model=model,
                prompt_chars=len(prompt),
                raw_response=raw_response,
                attempts=attempt,
            )
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc

    raise InferenceError(
        "Model output could not be parsed into the codebook schema after two "
        f"attempts. Last error: {last_error}. Raw response (truncated): "
        f"{raw_response[:400]!r}"
    )
