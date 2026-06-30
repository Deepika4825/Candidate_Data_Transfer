"""
Data Normalization Module.

Receives an IntermediateCandidate object (after extraction and matching)
and normalizes every field in-place across all three source objects
(csv_data, ats_data, resume_data).

Normalizations performed:
  - Name        → Title Case, collapse extra spaces
  - Email       → lowercase, strip whitespace
  - Phone       → remove country code (+91 etc.), keep 10 digits
  - Skills      → deduplicate, standardize known aliases (java/JAVA → Java)
  - Company     → standardize known abbreviations (TCS → Tata Consultancy Services)
  - Experience  → convert to float years (24 months → 2.0 years)
  - Education   → expand degree abbreviations (B.Tech → Bachelor of Technology)
  - All strings → strip leading/trailing whitespace

NOT performed here:
  - Merging, conflict resolution, confidence scoring, validation
"""

import re
import copy
from models.candidate import IntermediateCandidate, CandidateRecord, ResumeData


# ── Lookup tables ─────────────────────────────────────────────────────────

# Skill aliases → canonical name  (all keys stored lowercase)
_SKILL_ALIASES: dict[str, str] = {
    # Java ecosystem
    "java":                    "Java",
    "java programming":        "Java",
    "core java":               "Java",
    "java se":                 "Java",
    "java ee":                 "Java EE",
    "spring":                  "Spring Framework",
    "spring boot":             "Spring Boot",
    "springboot":              "Spring Boot",
    "spring mvc":              "Spring MVC",
    # Python
    "python":                  "Python",
    "python3":                 "Python",
    "python programming":      "Python",
    # Web
    "javascript":              "JavaScript",
    "js":                      "JavaScript",
    "typescript":              "TypeScript",
    "ts":                      "TypeScript",
    "react":                   "React",
    "reactjs":                 "React",
    "react.js":                "React",
    "node":                    "Node.js",
    "nodejs":                  "Node.js",
    "node.js":                 "Node.js",
    "html":                    "HTML",
    "html5":                   "HTML",
    "css":                     "CSS",
    "css3":                    "CSS",
    # Data
    "sql":                     "SQL",
    "mysql":                   "MySQL",
    "postgresql":              "PostgreSQL",
    "postgres":                "PostgreSQL",
    "mongodb":                 "MongoDB",
    "mongo":                   "MongoDB",
    "pandas":                  "Pandas",
    "numpy":                   "NumPy",
    "numpy":                   "NumPy",
    "machine learning":        "Machine Learning",
    "ml":                      "Machine Learning",
    "deep learning":           "Deep Learning",
    "dl":                      "Deep Learning",
    "data analysis":           "Data Analysis",
    "data analytics":          "Data Analysis",
    # DevOps / Tools
    "git":                     "Git",
    "github":                  "Git",
    "docker":                  "Docker",
    "kubernetes":              "Kubernetes",
    "k8s":                     "Kubernetes",
    "kafka":                   "Apache Kafka",
    "apache kafka":            "Apache Kafka",
    "redis":                   "Redis",
    "rest":                    "REST APIs",
    "rest api":                "REST APIs",
    "rest apis":               "REST APIs",
    "restful":                 "REST APIs",
    "restful api":             "REST APIs",
    # Misc
    "c++":                     "C++",
    "c#":                      "C#",
    "dotnet":                  ".NET",
    ".net":                    ".NET",
    "power bi":                "Power BI",
    "powerbi":                 "Power BI",
}

# Company name aliases → canonical name  (all keys stored lowercase)
_COMPANY_ALIASES: dict[str, str] = {
    "tcs":                          "Tata Consultancy Services",
    "tata consultancy":             "Tata Consultancy Services",
    "tata consultancy services":    "Tata Consultancy Services",
    "tata consultancy services ltd":"Tata Consultancy Services",
    "tcs ltd":                      "Tata Consultancy Services",
    "infosys":                      "Infosys",
    "infosys ltd":                  "Infosys",
    "infosys limited":              "Infosys",
    "wipro":                        "Wipro",
    "wipro ltd":                    "Wipro",
    "wipro limited":                "Wipro",
    "hcl":                          "HCL Technologies",
    "hcl technologies":             "HCL Technologies",
    "hcl tech":                     "HCL Technologies",
    "accenture":                    "Accenture",
    "cognizant":                    "Cognizant",
    "cognizant technology solutions": "Cognizant",
    "cts":                          "Cognizant",
    "tech mahindra":                "Tech Mahindra",
    "techmahindra":                 "Tech Mahindra",
    "capgemini":                    "Capgemini",
    "ibm":                          "IBM",
    "microsoft":                    "Microsoft",
    "google":                       "Google",
    "amazon":                       "Amazon",
    "meta":                         "Meta",
    "facebook":                     "Meta",
}

# Education degree aliases → canonical name  (all keys stored lowercase)
_DEGREE_ALIASES: dict[str, str] = {
    "b.tech":               "Bachelor of Technology",
    "btech":                "Bachelor of Technology",
    "b tech":               "Bachelor of Technology",
    "be":                   "Bachelor of Engineering",
    "b.e":                  "Bachelor of Engineering",
    "b.e.":                 "Bachelor of Engineering",
    "bachelor of engineering": "Bachelor of Engineering",
    "bachelor of technology":  "Bachelor of Technology",
    "m.tech":               "Master of Technology",
    "mtech":                "Master of Technology",
    "m tech":               "Master of Technology",
    "me":                   "Master of Engineering",
    "m.e":                  "Master of Engineering",
    "m.e.":                 "Master of Engineering",
    "mba":                  "Master of Business Administration",
    "m.b.a":                "Master of Business Administration",
    "m.b.a.":               "Master of Business Administration",
    "mca":                  "Master of Computer Applications",
    "m.c.a":                "Master of Computer Applications",
    "bca":                  "Bachelor of Computer Applications",
    "b.c.a":                "Bachelor of Computer Applications",
    "bsc":                  "Bachelor of Science",
    "b.sc":                 "Bachelor of Science",
    "b.sc.":                "Bachelor of Science",
    "msc":                  "Master of Science",
    "m.sc":                 "Master of Science",
    "m.sc.":                "Master of Science",
    "phd":                  "Doctor of Philosophy",
    "ph.d":                 "Doctor of Philosophy",
    "ph.d.":                "Doctor of Philosophy",
    "10th":                 "Secondary School (10th)",
    "12th":                 "Higher Secondary (12th)",
    "sslc":                 "Secondary School (10th)",
    "hsc":                  "Higher Secondary (12th)",
}


# ── Field normalizers ─────────────────────────────────────────────────────

def _norm_name(value: str | None) -> str | None:
    """Title case, collapse internal whitespace, strip."""
    if not value:
        return None
    return " ".join(value.strip().split()).title()


def _norm_email(value: str | None) -> str | None:
    """Lowercase, strip whitespace."""
    if not value:
        return None
    return value.strip().lower()


def _norm_phone(value: str | None) -> str | None:
    """
    Remove country code (+91, 0091, 91 prefix for 10-digit numbers),
    strip all non-digit characters, return exactly 10 digits or None.
    """
    if not value:
        return None

    # Keep only digits
    digits = re.sub(r"\D", "", value.strip())

    # Strip known country code prefixes (Indian +91 / 0091 / 91)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    elif len(digits) == 13 and digits.startswith("091"):
        digits = digits[3:]
    # Handle 13-digit numbers starting with 920... etc (malformed long numbers — truncate to last 10)
    elif len(digits) > 10:
        digits = digits[-10:]

    return digits if digits else None


def _norm_skill(skill: str) -> str:
    """Return canonical skill name using alias table, else title case."""
    key = skill.strip().lower()
    return _SKILL_ALIASES.get(key, skill.strip().title())


def _norm_skills(skills: list[str]) -> list[str]:
    """Normalize each skill, deduplicate while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for s in skills:
        s = s.strip()
        if not s:
            continue
        normalized = _norm_skill(s)
        # Deduplicate case-insensitively
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def _norm_company(value: str | None) -> str | None:
    """
    Standardize company name using alias table.
    Falls back to title-casing the original value.
    """
    if not value:
        return None
    stripped = value.strip()
    key = stripped.lower()
    return _COMPANY_ALIASES.get(key, stripped.title())


def _norm_experience(value: str | None) -> str | None:
    """
    Convert experience strings to a standard 'X.X years' format.

    Handles:
        "2 years"      → "2.0 years"
        "24 months"    → "2.0 years"
        "2.5 years"    → "2.5 years"
        "3"            → "3.0 years"
        "1 year"       → "1.0 years"
        "18 months"    → "1.5 years"
    """
    if not value:
        return None

    val = value.strip().lower()

    # Already a float/int year string like "3" or "2.5"
    try:
        years = float(val.replace("years", "").replace("year", "").strip())
        return f"{years:.1f} years"
    except ValueError:
        pass

    # Match patterns like "2 years", "2.5 years", "24 months"
    month_match = re.search(r"(\d+(?:\.\d+)?)\s*months?", val)
    year_match  = re.search(r"(\d+(?:\.\d+)?)\s*years?", val)

    if month_match:
        months = float(month_match.group(1))
        return f"{months / 12:.1f} years"
    if year_match:
        years = float(year_match.group(1))
        return f"{years:.1f} years"

    # Return as-is with strip if we can't parse
    return value.strip()


def _norm_degree(line: str) -> str:
    """
    Expand a degree abbreviation found at the start of an education line.
    Leaves the rest of the line (university, year) unchanged.

    Example:
        "B.Tech in Computer Science, JNTUH, 2023"
        → "Bachelor of Technology in Computer Science, JNTUH, 2023"
    """
    line = line.strip()
    # Try matching the first token(s) against degree aliases
    for abbr, full in sorted(_DEGREE_ALIASES.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(
            rf"^({re.escape(abbr)})\b",
            re.IGNORECASE
        )
        match = pattern.match(line)
        if match:
            return full + line[match.end():]
    return line


def _norm_education(lines: list[str]) -> list[str]:
    """Normalize each education line."""
    return [_norm_degree(line) for line in lines if line.strip()]


def _norm_str(value: str | None) -> str | None:
    """Strip leading/trailing whitespace from any string field."""
    return value.strip() if value else None


# ── CandidateRecord normalizer ────────────────────────────────────────────

def _normalize_record(rec: CandidateRecord) -> CandidateRecord:
    """Normalize all fields of a CandidateRecord in-place and return it."""
    rec.candidate_id    = _norm_str(rec.candidate_id)
    rec.full_name       = _norm_name(rec.full_name)
    rec.email           = _norm_email(rec.email)
    rec.phone           = _norm_phone(rec.phone)
    rec.current_company = _norm_company(rec.current_company)
    # Normalize extra_fields string values
    rec.extra_fields = {
        k: (v.strip() if isinstance(v, str) else v)
        for k, v in rec.extra_fields.items()
    }
    return rec


# ── ResumeData normalizer ─────────────────────────────────────────────────

def _normalize_resume(res: ResumeData) -> ResumeData:
    """Normalize all fields of a ResumeData in-place and return it."""
    res.name       = _norm_name(res.name)
    res.email      = _norm_email(res.email)
    res.phone      = _norm_phone(res.phone)
    res.skills     = _norm_skills(res.skills)
    res.education  = _norm_education(res.education)
    # Normalize experience lines — try converting each to years format
    res.experience = [
        _norm_experience(line) or line.strip()
        for line in res.experience
        if line.strip()
    ]
    res.projects   = [p.strip() for p in res.projects if p.strip()]
    return res


# ── Public API ────────────────────────────────────────────────────────────

def normalize_candidate(candidate: IntermediateCandidate) -> IntermediateCandidate:
    """
    Normalize all source data within an IntermediateCandidate object.

    Operates on a deep copy — the original is not mutated.
    Returns the normalized copy ready for the next pipeline stage (deduplication/merge).

    Args:
        candidate: IntermediateCandidate produced by the candidate_builder.

    Returns:
        A new IntermediateCandidate with all fields normalized.
    """
    normalized = copy.deepcopy(candidate)

    if normalized.csv_data:
        normalized.csv_data = _normalize_record(normalized.csv_data)

    if normalized.ats_data:
        normalized.ats_data = _normalize_record(normalized.ats_data)

    if normalized.resume_data:
        normalized.resume_data = _normalize_resume(normalized.resume_data)

    return normalized
