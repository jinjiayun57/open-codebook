from __future__ import annotations


def get_coded_fields(codebook: dict) -> list[dict]:
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
    raise ValueError(f"Unsupported type for code '{code.get('name')}': {code_type}")


def build_output_schema(codebook: dict) -> dict:
    codes = get_coded_fields(codebook)

    if not codes:
        raise ValueError("Codebook must define a non-empty 'codes' list.")

    properties = {}
    required = get_required_field_names(codebook)

    for code in codes:
        name = code.get("name")
        if not name:
            raise ValueError("Each codebook entry must include a 'name'.")

        code_type = _field_type(code)
        field_schema = {"type": code_type}

        values = code.get("values")
        if values and code_type == "string":
            field_schema["enum"] = [str(value) for value in values]
        elif values and code_type == "boolean":
            field_schema["enum"] = [bool(value) for value in values]

        properties[name] = field_schema

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _coerce_boolean(value, field_name: str) -> bool:
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
    if not isinstance(output, dict):
        raise ValueError("Model output must be a JSON object.")

    validated = {}

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


def _parse_condition_value(raw_value: str):
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
        raise ValueError(f"Unsupported derived-code condition: {condition!r}")

    field_name, raw_expected_value = condition.split("==", maxsplit=1)
    field_name = field_name.strip()
    expected_value = _parse_condition_value(raw_expected_value)

    return output.get(field_name) == expected_value


def derive_code_output(output: dict, codebook: dict) -> dict:
    derived = dict(output)

    for code in codebook.get("derived_codes", []):
        name = code.get("name")
        if not name:
            raise ValueError("Each derived codebook entry must include a 'name'.")

        if code.get("type") == "boolean" and "set_to_true_if" in code:
            derived[name] = any(
                _condition_matches(derived, condition)
                for condition in code["set_to_true_if"]
            )

    return derived
