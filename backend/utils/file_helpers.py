"""
Utility helpers for saving uploaded files safely.
"""
import os
import uuid
from werkzeug.utils import secure_filename

# Absolute path to the uploads directory
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# Allowed extensions per field name
ALLOWED_EXTENSIONS = {
    "csv_file":    {".csv"},
    "json_file":   {".json"},
    "resume_file": {".pdf", ".docx"},
    "config_file": {".json"},
}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _allowed(filename: str, field: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(field, set())


def save_upload(file_storage, field: str) -> str:
    """
    Validate extension, generate a unique filename, save to uploads/,
    and return the absolute file path.
    """
    original_name = secure_filename(file_storage.filename)

    if not _allowed(original_name, field):
        allowed = ", ".join(ALLOWED_EXTENSIONS.get(field, set()))
        raise ValueError(
            f"Invalid file type for '{field}': '{original_name}'. "
            f"Allowed: {allowed}"
        )

    ext        = os.path.splitext(original_name)[1].lower()
    unique_name = f"{field}_{uuid.uuid4().hex}{ext}"
    dest_path  = os.path.join(UPLOAD_DIR, unique_name)

    file_storage.save(dest_path)
    return dest_path
