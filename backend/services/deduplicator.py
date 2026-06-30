"""
Deduplication Module.

Two levels of deduplication are performed:

LEVEL 1 — Candidate-level deduplication:
    Detects duplicate candidate records (same person appearing more than once)
    using the following priority:
        1. Email        (primary identifier — exact match, already normalized)
        2. Phone Number (exact match, already normalized to 10 digits)
        3. Full Name    (exact match, already normalized to title case)
    When a duplicate is found the first occurrence is kept and any missing
    source data from the duplicate is absorbed into the primary record.

LEVEL 2 — Within-candidate list deduplication:
    For each candidate, removes duplicate entries inside list fields:
        - Skills        (case-insensitive dedup, preserve original order)
        - Education     (case-insensitive dedup, preserve original order)
        - Experience    (case-insensitive dedup, preserve original order)
        - Projects      (case-insensitive dedup, preserve original order)
        - Certifications (case-insensitive dedup, preserve original order)

NOT performed here:
    Field-level merging, conflict resolution, confidence scoring, validation.
"""

from __future__ import annotations
from models.candidate import IntermediateCandidate


# ══════════════════════════════════════════════════════════════════════════
# LEVEL 2 — Within-candidate list deduplication helpers
# ══════════════════════════════════════════════════════════════════════════

def _dedup_list(items: list[str]) -> list[str]:
    """
    Remove duplicate strings from a list while preserving original order.
    Comparison is case-insensitive and ignores leading/trailing whitespace.

    Example:
        ["Python", "python", "SQL", "Python 3", "sql"]
        → ["Python", "SQL", "Python 3"]
    """
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _dedup_resume_lists(candidate: IntermediateCandidate) -> IntermediateCandidate:
    """
    Remove duplicate entries from all list fields in resume_data.
    Operates in-place on the candidate object.
    """
    if candidate.resume_data is None:
        return candidate

    rd = candidate.resume_data
    rd.skills      = _dedup_list(rd.skills)
    rd.education   = _dedup_list(rd.education)
    rd.experience  = _dedup_list(rd.experience)
    rd.projects    = _dedup_list(rd.projects)

    # certifications — stored in extra_fields if present
    if hasattr(rd, "certifications"):
        rd.certifications = _dedup_list(rd.certifications)

    return candidate


# ══════════════════════════════════════════════════════════════════════════
# LEVEL 1 — Candidate-level deduplication helpers
# ══════════════════════════════════════════════════════════════════════════

def _get_email(c: IntermediateCandidate) -> str | None:
    """Return the best normalized email across all sources."""
    return (
        (c.csv_data    and c.csv_data.email)    or
        (c.resume_data and c.resume_data.email) or
        (c.ats_data    and c.ats_data.email)    or
        None
    )


def _get_phone(c: IntermediateCandidate) -> str | None:
    """Return the best normalized phone across all sources."""
    return (
        (c.csv_data    and c.csv_data.phone)    or
        (c.resume_data and c.resume_data.phone) or
        (c.ats_data    and c.ats_data.phone)    or
        None
    )


def _get_name(c: IntermediateCandidate) -> str | None:
    """Return the best normalized name across all sources."""
    return (
        (c.resume_data and c.resume_data.name)   or
        (c.csv_data    and c.csv_data.full_name) or
        (c.ats_data    and c.ats_data.full_name) or
        None
    )


def _absorb(primary: IntermediateCandidate,
            duplicate: IntermediateCandidate) -> None:
    """
    Absorb missing source slots from a duplicate into the primary.
    Only fills slots that are completely absent in the primary.
    Does NOT resolve field-level conflicts (that is the merger's job).
    """
    if primary.csv_data is None and duplicate.csv_data is not None:
        primary.csv_data = duplicate.csv_data

    if primary.ats_data is None and duplicate.ats_data is not None:
        primary.ats_data         = duplicate.ats_data
        primary.ats_match_method = duplicate.ats_match_method

    if primary.resume_data is None and duplicate.resume_data is not None:
        primary.resume_data  = duplicate.resume_data
        primary.match_method = duplicate.match_method

    if primary.candidate_id is None and duplicate.candidate_id is not None:
        primary.candidate_id = duplicate.candidate_id


# ══════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════

def deduplicate_candidates(
    candidates: list[IntermediateCandidate],
) -> tuple[list[IntermediateCandidate], list[dict]]:
    """
    Run both levels of deduplication on a list of normalized candidates.

    Level 1: Remove duplicate candidate records (same person from multiple sources).
    Level 2: Remove duplicate list entries (skills, education, etc.) within each candidate.

    Args:
        candidates: List of normalized IntermediateCandidate objects.

    Returns:
        Tuple of:
          - Deduplicated list of IntermediateCandidate objects
          - Deduplication report: list of dicts describing merged duplicates
    """

    # ── LEVEL 1: Candidate-level deduplication ────────────────────────────
    seen_ids:    dict[str, int] = {}
    seen_emails: dict[str, int] = {}
    seen_phones: dict[str, int] = {}
    seen_names:  dict[str, int] = {}

    result: list[IntermediateCandidate] = []
    report: list[dict] = []

    for candidate in candidates:
        cid   = candidate.candidate_id
        email = _get_email(candidate)
        phone = _get_phone(candidate)
        name  = _get_name(candidate)

        duplicate_of: int | None = None
        match_field:  str | None = None

        # Check in priority order: email → phone → name
        if email and email in seen_emails:
            duplicate_of = seen_emails[email]
            match_field  = "email"

        elif phone and phone in seen_phones:
            duplicate_of = seen_phones[phone]
            match_field  = "phone"

        elif name and name in seen_names:
            duplicate_of = seen_names[name]
            match_field  = "name"

        elif cid and cid in seen_ids:
            duplicate_of = seen_ids[cid]
            match_field  = "candidate_id"

        if duplicate_of is not None:
            # Duplicate found — absorb into primary record
            primary = result[duplicate_of]
            _absorb(primary, candidate)
            report.append({
                "action":         "merged",
                "duplicate_name": name or cid or "unknown",
                "matched_by":     match_field,
                "merged_into":    primary.candidate_id or f"record_{duplicate_of}",
            })
            continue

        # Not a duplicate — register and add
        idx = len(result)
        result.append(candidate)

        if cid:   seen_ids[cid]     = idx
        if email: seen_emails[email] = idx
        if phone: seen_phones[phone] = idx
        if name:  seen_names[name]   = idx

    # ── LEVEL 2: Within-candidate list deduplication ──────────────────────
    for candidate in result:
        _dedup_resume_lists(candidate)

        # Also dedup skills stored in ATS extra_fields if present
        if candidate.ats_data and "skills" in candidate.ats_data.extra_fields:
            raw_skills = candidate.ats_data.extra_fields.get("skills", [])
            if isinstance(raw_skills, list):
                candidate.ats_data.extra_fields["skills"] = _dedup_list(
                    [str(s) for s in raw_skills]
                )

    return result, report
