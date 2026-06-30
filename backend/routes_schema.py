"""
Output Schema Generator — /generate-profile endpoint.

Receives a resolved candidate object + schema_type from the frontend.
  - schema_type = "default"  → return all fields
  - schema_type = "custom"   → return only selected fields from selected_fields list
  - schema_type = "config"   → use config.json output_schema

Returns the final candidate profile JSON with only the requested fields,
plus the generated config.json that was used.
"""
import os
import json
from flask import Blueprint, request, jsonify
from utils.input_loader import get_input_path

schema_bp = Blueprint("schema", __name__)

# All available output fields and how they map to candidate data keys
ALL_FIELDS = {
    "Candidate ID":         "candidate_id",
    "Full Name":            "name",
    "Email":                "email",
    "Phone":                "phone",
    "Current Company":      "current_company",
    "Skills":               "skills",
    "Education":            "education",
    "Experience":           "experience",
    "Projects":             "projects",
    "Certifications":       "certifications",
    "Overall Confidence":   "overall_confidence",
    "Status":               "status",
}

# Default schema includes all fields
DEFAULT_FIELDS = list(ALL_FIELDS.keys())


def _build_output(candidate: dict, fields: list[str]) -> dict:
    """Project candidate data into the requested fields only."""
    output = {}
    for label in fields:
        key = ALL_FIELDS.get(label)
        if not key:
            continue
        if key == "overall_confidence":
            conf = candidate.get("confidence", {})
            output[label] = conf.get("percentage", "N/A")
        elif key == "status":
            conf = candidate.get("confidence", {})
            output[label] = conf.get("status", "Processed")
        else:
            val = candidate.get(key)
            if val is not None:
                output[label] = val
    return output


@schema_bp.post("/generate-profile")
def generate_profile():
    """
    Generate a final candidate profile using the selected output schema.

    Body:
        candidate      (dict)  — resolved candidate object from /process
        schema_type    (str)   — "default" | "custom" | "config"
        selected_fields (list) — field labels selected (for custom schema)
        sources        (list)  — source keys used
    """
    body = request.get_json(silent=True) or {}
    candidate       = body.get("candidate", {})
    schema_type     = body.get("schema_type", "default")
    selected_fields = body.get("selected_fields", [])

    if not candidate:
        return jsonify({"error": "No candidate data provided."}), 400

    # ── Determine fields to include ───────────────────────────────────────
    if schema_type == "default":
        fields = DEFAULT_FIELDS
        config_used = {"output_schema": {f: ALL_FIELDS[f] for f in DEFAULT_FIELDS}}

    elif schema_type == "custom":
        if not selected_fields:
            return jsonify({"error": "No fields selected for custom schema."}), 400
        fields = [f for f in selected_fields if f in ALL_FIELDS]
        config_used = {
            "schema_type":   "custom",
            "output_schema": {f: ALL_FIELDS[f] for f in fields},
        }
        # Write generated config.json to input/ folder
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "input", "config.json"
            )
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(config_used, fh, indent=2)
        except Exception:
            pass  # non-fatal

    elif schema_type == "config":
        try:
            config_path = get_input_path("config")
            with open(config_path, encoding="utf-8") as fh:
                cfg = json.load(fh)
            schema = cfg.get("output_schema", {})
            # output_schema can be dict {label: key} or list [label, ...]
            if isinstance(schema, dict):
                fields = list(schema.keys())
            elif isinstance(schema, list):
                fields = schema
            else:
                fields = DEFAULT_FIELDS
            config_used = cfg
        except FileNotFoundError:
            return jsonify({
                "error": "config.json not found in input/ folder.",
                "message": "Please upload a valid config.json or use Default Output Schema."
            }), 400
        except Exception as exc:
            return jsonify({"error": f"Could not read config.json: {exc}"}), 400
    else:
        fields = DEFAULT_FIELDS
        config_used = {}

    # ── Build output profile ───────────────────────────────────────────────
    profile = _build_output(candidate, fields)

    return jsonify({
        "profile":     profile,
        "config_used": config_used,
        "fields":      fields,
        "schema_type": schema_type,
    }), 200


@schema_bp.get("/available-fields")
def available_fields():
    """Return all available output field labels."""
    return jsonify({"fields": list(ALL_FIELDS.keys())}), 200
