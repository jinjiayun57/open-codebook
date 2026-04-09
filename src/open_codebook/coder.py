from __future__ import annotations

import json

import ollama
from ollama import ResponseError

from .schema import build_output_schema


DEFAULT_PROMPT_PREAMBLE = (
    "You are helping with structured coding of short social science text."
)


def _stringify_values(values: list) -> list[str]:
    return [str(value).lower() for value in values]


def build_prompt(codebook: dict, text: str) -> str:
    codes = codebook.get("codes", [])
    if not codes:
        raise ValueError("Codebook must define a non-empty 'codes' list.")

    prompt_preamble = codebook.get("prompt_preamble", DEFAULT_PROMPT_PREAMBLE)
    field_names = [code["name"] for code in codes]

    prompt_lines = [
        prompt_preamble,
        "",
        "Return only a valid JSON object with exactly these fields:",
    ]
    prompt_lines.extend(f"- {name}" for name in field_names)

    enum_codes = [code for code in codes if code.get("values")]
    if enum_codes:
        prompt_lines.append("")
        prompt_lines.append("Allowed values:")
        prompt_lines.extend(
            f"- {code['name']}: {', '.join(_stringify_values(code['values']))}"
            for code in enum_codes
        )

    prompt_lines.append("")
    prompt_lines.append("Definitions:")
    prompt_lines.extend(
        f"- {code['name']} = {code.get('description', 'No description provided.')}"
        for code in codes
    )

    prompt_lines.extend(["", "Text:", text])

    return "\n".join(prompt_lines)


def code_text(text: str, codebook: dict, model_name: str) -> dict:
    prompt = build_prompt(codebook, text)
    schema = build_output_schema(codebook)

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            think=False,
            stream=False,
            options={"temperature": 0},
        )
    except ConnectionError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Please make sure Ollama is installed "
            "and running locally, then try again."
        ) from exc
    except ResponseError as exc:
        if exc.status_code == 404:
            raise RuntimeError(
                f"Ollama model '{model_name}' was not found. Run "
                f"'ollama pull {model_name}' and try again."
            ) from exc
        raise

    return json.loads(response["message"]["content"])
