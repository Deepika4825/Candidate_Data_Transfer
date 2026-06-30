"""
Parser for ATS JSON files.

Reads the JSON export, converts each candidate entry into the same
CandidateRecord structure used by the CSV parser.

Supports two common ATS JSON layouts:
  1. A list of candidate objects at the top level:
       [ { "id": "...", "name": "...", ... }, ... ]

  2. A wrapper object with a candidates/applicants/data key:
       { "candidates": [ ... ] }
       { "applicants": [ ... ] }
       { "data": [ ... ] }

Field names are matched using the same alias table as the CSV parser
so the internal structure is always consistent.
"""
import json
from models.candidate import CandidateRecord


# Same alias table as csv_parser — keeps the internal schema consistent
_FIELD_ALIASES: dict[str, list[str]] = {
    "candidate_id":    ["candidate_id", "candidate id", "id", "applicant_id", "applicantid"],
    "full_name":       ["full_name", "full name", "name", "candidate_name", "applicant_name", "fullname"],
    "email":           ["email", "email_address", "emailaddress", "e-mail", "e_mail"],
    "phone":           ["phone", "phone_number", "phonenumber", "mobile", "contact_number", "contactnumber"],
    "current_company": ["current_company", "current company", "company", "employer", "organisation", "organization"],
}

# Keys that may wrap the candidate list in the top-level dict
_LIST_WRAPPER_KEYS = ["candidates", "applicants", "data", "results", "records"]


def _resolve_alias(key: str) -> str | None:
    """Return the canonical field name for a given key, or None if unknown."""
    key_lower = key.strip().lower()
    for canonical, aliases in _FIELD_ALIASES.items():
        if key_lower in aliases:
            return canonical
    return None


def _entry_to_record(entry: dict) -> CandidateRecord:
    """Convert a single ATS JSON object into a CandidateRecord."""
    canonical: dict[str, str] = {}
    extra:     dict[str, str] = {}

    for key, val in entry.items():
        # Stringify non-string leaf values for uniformity
        str_val = str(val).strip() if val is not None else None
        resolved = _resolve_alias(key)
        if resolved:
            canonical[resolved] = str_val or None
        else:
            extra[key] = str_val or ""

    return CandidateRecord(
        candidate_id    = canonical.get("candidate_id")    or None,
        full_name       = canonical.get("full_name")       or None,
        email           = canonical.get("email")           or None,
        phone           = canonical.get("phone")           or None,
        current_company = canonical.get("current_company") or None,
        extra_fields    = extra,
    )


def parse_ats_json(file_path: str) -> list[CandidateRecord]:
    """
    Parse an ATS-exported JSON file into a list of CandidateRecord objects.

    Args:
        file_path: Absolute path to the saved .json file.

    Returns:
        List of CandidateRecord instances.

    Raises:
        ValueError: If the file is empty, invalid JSON, or has an unrecognised structure.
    """
    with open(file_path, encoding="utf-8") as fh:
        content = fh.read().strip()

    if not content:
        raise ValueError("ATS JSON file is empty.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in ATS file: {exc}") from exc

    # ── Resolve the candidate list ────────────────────────────────────────
    candidate_list: list[dict] = []

    if isinstance(data, list):
        candidate_list = data

    elif isinstance(data, dict):
        # Try known wrapper keys
        for wrapper_key in _LIST_WRAPPER_KEYS:
            if wrapper_key in data and isinstance(data[wrapper_key], list):
                candidate_list = data[wrapper_key]
                break
        else:
            # Single candidate object wrapped in a dict
            candidate_list = [data]
    else:
        raise ValueError(
            f"ATS JSON must be a list or object, got {type(data).__name__}."
        )

    if not candidate_list:
        raise ValueError("ATS JSON contains no candidate entries.")

    records = [_entry_to_record(e) for e in candidate_list if isinstance(e, dict)]

    if not records:
        raise ValueError("ATS JSON entries could not be converted to candidate records.")

    return records
