"""
Input validation helpers for the /process endpoint.
"""


def validate_csv_present(csv_file) -> str | None:
    """Return an error message if the CSV file is missing, else None."""
    if not csv_file or csv_file.filename == "":
        return "A Recruiter CSV file is required."
    return None
