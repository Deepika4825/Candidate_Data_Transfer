"""
Parser for the Runtime Config JSON file.

Reads and validates the user-supplied configuration / field-mapping file.
The config controls how source fields are normalised and merged.
"""
import json


# Top-level keys that are recognised in the config file
KNOWN_KEYS = {
    "field_mappings",
    "normalization_rules",
    "merge_strategy",
    "output_schema",
    "filters",
}


def parse_config(file_path: str) -> dict:
    """
    Parse and lightly validate the runtime config JSON file.

    Args:
        file_path: Absolute path to the saved config .json file.

    Returns:
        Parsed config as a Python dict.

    Raises:
        ValueError: If the file is empty, invalid JSON, or not a JSON object.
    """
    with open(file_path, encoding="utf-8") as fh:
        content = fh.read().strip()

    if not content:
        raise ValueError("Config JSON file is empty.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(
            "Config JSON must be a JSON object (dict), "
            f"but got {type(data).__name__}."
        )

    # Warn about unrecognised top-level keys (non-fatal)
    unknown = set(data.keys()) - KNOWN_KEYS
    if unknown:
        # In production, log this as a warning rather than raising
        pass  # e.g. logging.warning("Unknown config keys: %s", unknown)

    return data
