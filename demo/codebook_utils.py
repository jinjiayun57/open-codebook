"""Codebook loading, schema derivation, and output validation for the demo Space.

This is a self-contained subset of the logic in
``src/open_codebook/schema.py`` and ``src/open_codebook/io_utils.py``
so the ``demo/`` directory can be deployed to Hugging Face Spaces on its own.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# --- Loading ---------------------------------------------------------------


def load_codebook(codebook_path: Path | str) -> dict:
    """Read a YAML codebook from disk."""
    path = Path(codebook_path)
    with path.open("r", encoding="utf-8") as file_obj:
        return yaml.safe_load(file_obj)


def load_codebook_from_text(text: str) -> dict:
    """Parse a YAML codebook from an in-memory string (used for uploads)."""
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Uploaded codebook must be a YAML mapping at the top level.")
    return data


# --- Codebook structure ----------------------------------------------------


def get_coded_fields(codebook: dict) -> list[dict]:
    """Return the fields the model is expected to code."""
    return [
        code
        for code in codebook.get("codes", [])
        if code.get("coded_by_model", True)
    ]


def get_required_field_names(codebook: dict) -> list[str]:
    return [
        code["name"]
        for code in get_coded_fields(codebook)
        if code.get("required", True)
    ]


def _field_type(code: dict) -> str:
    code_type = code.get("type", "string")
    if code_type == "boolean":
        return "boolean"
    if code_type in (None, "string"):
        return "string"
    raise ValueError(
        f"Unsupported type for code {code.get('name')!r}: {code_type!r}."
    )


def build_output_schema(codebook: dict) -> dict:
    """Build a JSON Schema describing the expected structured output."""
    codes = get_coded_fields(codebook)
    if not codes:
        raise ValueError("Codebook must define a non-empty 'codes' list.")

    properties: dict[str, dict[str, Any]] = {}
    for code in codes:
        name = code.get("name")
        if not name:
            raise ValueError("Each codebook entry must include a 'name'.")

        code_type = _field_type(code)
        field_schema: dict[str, Any] = {"type": code_type}

        values = code.get("values")
        if values and code_type == "string":
            field_schema["enum"] = [str(value) for value in values]
        elif values and code_type == "boolean":
            field_schema["enum"] = [bool(value) for value in values]

        properties[name] = field_schema

    return {
        "type": "object",
        "properties": properties,
        "required": get_required_field_names(codebook),
    }


# --- Validation ------------------------------------------------------------


def _coerce_boolean(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise ValueError(f"Field '{field_name}' must be boolean, got {value!r}.")


def validate_code_output(output: dict, codebook: dict) -> dict:
    """Validate a model output against the codebook and apply derived codes."""
    if not isinstance(output, dict):
        raise ValueError("Model output must be a JSON object.")

    validated: dict[str, Any] = {}

    for code in get_coded_fields(codebook):
        name = code.get("name")
        if not name:
            raise ValueError("Each codebook entry must include a 'name'.")

        required = code.get("required", True)
        if required and name not in output:
            raise ValueError(f"Model output is missing required field '{name}'.")
        if name not in output:
            continue

        code_type = _field_type(code)
        value = output[name]

        if code_type == "boolean":
            value = _coerce_boolean(value, name)
            allowed_values = code.get("values")
            if allowed_values and value not in [bool(item) for item in allowed_values]:
                raise ValueError(
                    f"Field '{name}' has invalid value {value!r}; "
                    f"allowed values are {allowed_values}."
                )
        else:
            value = str(value)
            allowed_values = code.get("values")
            if allowed_values and value not in [str(item) for item in allowed_values]:
                raise ValueError(
                    f"Field '{name}' has invalid value {value!r}; "
                    f"allowed values are {allowed_values}."
                )

        validated[name] = value

    return derive_code_output(validated, codebook)


# --- Derived codes ---------------------------------------------------------


def _parse_condition_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    normalized = value.casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return value


def _condition_matches(output: dict, condition: str) -> bool:
    if "==" not in condition:
        raise ValueError(f"Unsupported derived-code condition: {condition!r}.")

    field_name, raw_expected = condition.split("==", maxsplit=1)
    return output.get(field_name.strip()) == _parse_condition_value(raw_expected)


def derive_code_output(output: dict, codebook: dict) -> dict:
    """Apply ``derived_codes`` rules (currently: boolean set_to_true_if)."""
    derived = dict(output)
    for code in codebook.get("derived_codes", []):
        name = code.get("name")
        if not name:
            raise ValueError("Each derived codebook entry must include a 'name'.")
        if code.get("type") == "boolean" and "set_to_true_if" in code:
            derived[name] = any(
                _condition_matches(derived, cond)
                for cond in code["set_to_true_if"]
            )
    return derived


# --- Upload-time sanity check ---------------------------------------------


def summarize_codebook(codebook: dict) -> dict:
    """Produce a compact summary for the upload tab UI."""
    coded = get_coded_fields(codebook)
    derived = codebook.get("derived_codes", []) or []
    return {
        "codebook_name": codebook.get("codebook_name")
        or codebook.get("project_name")
        or "(unnamed codebook)",
        "version": codebook.get("version"),
        "language": codebook.get("language"),
        "n_coded_fields": len(coded),
        "n_derived_fields": len(derived),
        "coded_field_names": [code.get("name") for code in coded],
        "derived_field_names": [code.get("name") for code in derived],
    }
