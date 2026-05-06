from __future__ import annotations

import json

import ollama
from ollama import ResponseError

from .schema import build_output_schema, get_coded_fields, validate_code_output


DEFAULT_PROMPT_PREAMBLE = (
    "You are helping with structured coding of short social science text."
)
DEFAULT_TASK_INSTRUCTION = (
    "Code the input response according to the codebook definitions and allowed labels."
)


def _stringify_values(values: list) -> list[str]:
    return [str(value).lower() for value in values]


def _format_guidance_items(items: list[dict]) -> list[str]:
    lines = []
    for item in items:
        value = item.get("value")
        definition = item.get("definition")
        examples = item.get("examples", [])

        if value is None:
            continue

        line = f"  - {value}"
        if definition:
            line = f"{line}: {definition}"
        lines.append(line)

        if examples:
            lines.append(f"    Examples: {', '.join(str(example) for example in examples)}")

    return lines


def _format_text_items(title: str, items: list[str]) -> list[str]:
    if not items:
        return []

    lines = [f"  {title}:"]
    lines.extend(f"    - {item}" for item in items)
    return lines


def build_prompt(codebook: dict, text: str, config: dict | None = None) -> str:
    config = config or {}
    codes = get_coded_fields(codebook)
    if not codes:
        raise ValueError("Codebook must define a non-empty 'codes' list.")

    prompt_preamble = codebook.get("prompt_preamble", DEFAULT_PROMPT_PREAMBLE)
    input_language = config.get("language", codebook.get("language", "unknown"))
    codebook_language = config.get("codebook_language", "unknown")
    task_instruction = config.get("task_instruction", DEFAULT_TASK_INSTRUCTION)
    field_names = [code["name"] for code in codes]

    prompt_lines = [
        prompt_preamble,
        "",
        f"The input response language is: {input_language}.",
        f"The codebook definition language is: {codebook_language}.",
        task_instruction,
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
    for code in codes:
        prompt_lines.append(
            f"- {code['name']} = {code.get('description', 'No description provided.')}"
        )
        prompt_lines.extend(
            _format_text_items("Coding procedure", code.get("coding_procedure", []))
        )
        prompt_lines.extend(
            _format_text_items("Tie-breakers", code.get("tie_breakers", []))
        )

        guidance_items = code.get("categories", code.get("levels", []))
        prompt_lines.extend(_format_guidance_items(guidance_items))

    prompt_lines.extend(["", "Text:", text])

    return "\n".join(prompt_lines)


def code_text(
    text: str,
    codebook: dict,
    model_name: str,
    config: dict | None = None,
) -> dict:
    prompt = build_prompt(codebook, text, config=config)
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

    result = json.loads(response["message"]["content"])
    return validate_code_output(result, codebook)
