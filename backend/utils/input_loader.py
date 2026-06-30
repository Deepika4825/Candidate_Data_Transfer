"""
Input loader — resolves file paths from the shared input/ folder.

    project/
    ├── input/
    │   ├── candidates.csv
    │   ├── ats.json
    │   ├── config.json
    │   └── Deepika_Resume.pdf   ← any .pdf or .docx files here are treated as resumes
    ├── backend/
    └── frontend/
"""
import os

# Project root = two levels up from this file (backend/utils/input_loader.py)
_BACKEND_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
INPUT_DIR     = os.path.join(_PROJECT_ROOT, "input")

# Known fixed filenames for each source type
_SOURCE_FILES = {
    "csv":    "candidates.csv",
    "json":   "ats.json",
    "config": "config.json",
}


def get_input_path(source: str) -> str:
    """
    Return the absolute path to the input file for a given source key.

    Args:
        source: One of 'csv', 'json', 'config'.

    Raises:
        FileNotFoundError: If the file does not exist in the input/ folder.
    """
    filename = _SOURCE_FILES.get(source)
    if not filename:
        raise ValueError(f"Unknown source key: '{source}'")

    path = os.path.join(INPUT_DIR, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Input file not found: {path}\n"
            f"Make sure '{filename}' exists in the input/ folder."
        )
    return path


def get_resume_paths() -> list[str]:
    """
    Return sorted list of absolute paths for every .pdf / .docx file
    found in the input/ folder. Only the resume for the uploaded person
    should be present — the backend processes each file and returns only
    the candidate whose data matches.
    """
    if not os.path.isdir(INPUT_DIR):
        return []

    resume_paths = []
    for fname in os.listdir(INPUT_DIR):
        ext = os.path.splitext(fname)[1].lower()
        if ext in (".pdf", ".docx"):
            resume_paths.append(os.path.join(INPUT_DIR, fname))

    return sorted(resume_paths)
