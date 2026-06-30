"""
Parser for Recruiter CSV files.

Reads the CSV, extracts structured CandidateRecord objects, and returns
a list of records plus a raw-rows list for debugging.

Expected columns (case-insensitive, flexible):
    Candidate ID, Full Name, Email, Phone, Current Company, Resume URL
    Any additional columns are stored in extra_fields.
"""
import csv
from models.candidate import CandidateRecord


# Canonical field → possible CSV column name variations (all lower-cased for matching)
_FIELD_ALIASES: dict[str, list[str]] = {
    "candidate_id":    ["candidate id", "candidate_id", "id", "candidateid"],
    "full_name":       ["full name", "full_name", "name", "candidate name", "candidate_name"],
    "email":           ["email", "email address", "email_address", "e-mail"],
    "phone":           ["phone", "phone number", "phone_number", "mobile", "contact"],
    "current_company": ["current company", "current_company", "company", "employer", "organisation", "organization"],
}


def _map_headers(fieldnames: list[str]) -> dict[str, str]:
    """
    Return a mapping of { csv_column_name → canonical_field_name }
    for columns that match a known alias.
    """
    mapping: dict[str, str] = {}
    for col in fieldnames:
        col_lower = col.strip().lower()
        for canonical, aliases in _FIELD_ALIASES.items():
            if col_lower in aliases:
                mapping[col] = canonical
                break
    return mapping


def parse_csv(file_path: str) -> list[CandidateRecord]:
    """
    Parse a recruiter CSV file into a list of CandidateRecord objects.

    Args:
        file_path: Absolute path to the saved .csv file.

    Returns:
        List of CandidateRecord instances (one per data row).

    Raises:
        ValueError: If the file is empty or has no data rows.
    """
    records: list[CandidateRecord] = []

    with open(file_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)

        if not reader.fieldnames:
            raise ValueError("CSV file appears to be empty or has no header row.")

        header_map = _map_headers(list(reader.fieldnames))

        for row in reader:
            # Normalise: strip all values
            row = {k: (v.strip() if v else "") for k, v in row.items()}

            canonical: dict[str, str]  = {}
            extra:     dict[str, str]  = {}

            for col, val in row.items():
                if col in header_map:
                    canonical[header_map[col]] = val or None
                else:
                    extra[col] = val

            record = CandidateRecord(
                candidate_id    = canonical.get("candidate_id")    or None,
                full_name       = canonical.get("full_name")       or None,
                email           = canonical.get("email")           or None,
                phone           = canonical.get("phone")           or None,
                current_company = canonical.get("current_company") or None,
                extra_fields    = extra,
            )
            records.append(record)

    if not records:
        raise ValueError("CSV file contains a header but no data rows.")

    return records
