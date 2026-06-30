"""
Parser for Resume files (.pdf and .docx).

Stage 1 — Text extraction:
    PDF  → PyMuPDF (fitz)
    DOCX → python-docx

Stage 2 — Field extraction via regex:
    Name, Email, Phone, Skills, Education, Experience, Projects
"""
import os
import re
from models.candidate import ResumeData


# ── Regex patterns ────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Covers: +91-9999999999 / (123) 456-7890 / 123.456.7890 / +1 800 555 1234
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?)?\d{3,4}[\s\-.]?\d{4}"
)

# Section header keywords — used to split the resume into sections
_SECTION_HEADERS = {
    "skills":      re.compile(r"^\s*(skills?|technical\s+skills?|core\s+competenc)", re.I),
    "education":   re.compile(r"^\s*(education|academic|qualifications?)", re.I),
    "experience":  re.compile(r"^\s*(experience|work\s+history|employment|professional\s+experience)", re.I),
    "projects":    re.compile(r"^\s*(projects?|key\s+projects?|personal\s+projects?)", re.I),
}

# Lines that are likely section headers (short, title-cased or all-caps)
_HEADER_ANY = re.compile(
    r"^\s*(?:skills?|education|experience|projects?|certifications?|awards?|"
    r"summary|objective|profile|publications?|languages?|interests?|references?)",
    re.I,
)


# ── Text extraction ───────────────────────────────────────────────────────

def _extract_text_pdf(file_path: str) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF parsing. Install with: pip install PyMuPDF"
        ) from exc

    parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            parts.append(page.get_text())

    text = "\n".join(parts).strip()
    if not text:
        raise ValueError("PDF resume contains no extractable text.")
    return text


def _extract_text_docx(file_path: str) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise ImportError(
            "python-docx is required for DOCX parsing. Install with: pip install python-docx"
        ) from exc

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ValueError("DOCX resume contains no extractable text.")
    return text


# ── Field extraction ──────────────────────────────────────────────────────

def _extract_email(text: str) -> str | None:
    match = _EMAIL_RE.search(text)
    return match.group(0).lower() if match else None


def _extract_phone(text: str) -> str | None:
    match = _PHONE_RE.search(text)
    if match:
        # Clean up to digits + leading +
        raw = match.group(0).strip()
        return raw
    return None


def _extract_name(lines: list[str], email: str | None) -> str | None:
    """
    Heuristic: the candidate name is usually one of the first 1-4 non-empty lines
    that is NOT an email, phone number, URL, or section header.
    """
    for line in lines[:8]:
        line = line.strip()
        if not line:
            continue
        if _EMAIL_RE.search(line):
            continue
        if _PHONE_RE.search(line):
            continue
        if re.search(r"https?://|www\.", line, re.I):
            continue
        if _HEADER_ANY.match(line):
            continue
        # Must look like a name: 2–4 words, mostly alpha
        words = line.split()
        if 2 <= len(words) <= 5 and all(re.match(r"[A-Za-z\.\-']+$", w) for w in words):
            return line
    return None


def _split_into_sections(text: str) -> dict[str, list[str]]:
    """
    Split resume text into named sections based on section header keywords.
    Returns a dict: { section_name → [lines] }
    """
    sections: dict[str, list[str]] = {k: [] for k in _SECTION_HEADERS}
    sections["_preamble"] = []   # lines before any recognised section

    current = "_preamble"
    for line in text.splitlines():
        matched_section = None
        for section_name, pattern in _SECTION_HEADERS.items():
            if pattern.match(line):
                matched_section = section_name
                break

        if matched_section:
            current = matched_section
        else:
            sections[current].append(line)

    return sections


def _clean_lines(lines: list[str]) -> list[str]:
    """Strip blank lines and deduplicate while preserving order."""
    seen = set()
    result = []
    for line in lines:
        line = line.strip()
        if line and line not in seen:
            seen.add(line)
            result.append(line)
    return result


# ── Public API ────────────────────────────────────────────────────────────

def parse_resume(file_path: str) -> ResumeData:
    """
    Extract structured data from a PDF or DOCX resume.

    Args:
        file_path: Absolute path to the saved resume file.

    Returns:
        ResumeData instance with name, email, phone, skills, education,
        experience, projects, and raw_text populated where found.

    Raises:
        ValueError:  If the file extension is unsupported or text is empty.
        ImportError: If a required parsing library is missing.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        raw_text = _extract_text_pdf(file_path)
    elif ext == ".docx":
        raw_text = _extract_text_docx(file_path)
    else:
        raise ValueError(f"Unsupported resume format: '{ext}'. Expected .pdf or .docx.")

    lines = raw_text.splitlines()
    sections = _split_into_sections(raw_text)

    email = _extract_email(raw_text)
    phone = _extract_phone(raw_text)
    name  = _extract_name(lines, email)

    return ResumeData(
        name       = name,
        email      = email,
        phone      = phone,
        skills     = _clean_lines(sections.get("skills", [])),
        education  = _clean_lines(sections.get("education", [])),
        experience = _clean_lines(sections.get("experience", [])),
        projects   = _clean_lines(sections.get("projects", [])),
        raw_text   = raw_text,
    )
