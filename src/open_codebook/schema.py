from __future__ import annotations


def build_output_schema(codebook: dict) -> dict:
    codes = codebook.get("codes", [])

    if not codes:
        raise ValueError("Codebook must define a non-empty 'codes' list.")

    properties = {}
    required = []

    for code in codes:
        name = code.get("name")
        if not name:
            raise ValueError("Each codebook entry must include a 'name'.")

        field_schema = {"type": "string"}

        values = code.get("values")
        if values:
            field_schema["enum"] = [str(value).lower() for value in values]
        elif code.get("type") not in (None, "string"):
            raise ValueError(
                f"Unsupported type for code '{name}': {code.get('type')}"
            )

        properties[name] = field_schema
        required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }
