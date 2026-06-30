"""
Merge Records Module.

Receives a deduplicated, normalized IntermediateCandidate object and
produces a single unified MergedCandidate profile.

Matching priority (used to confirm records belong to the same candidate
before merging):
    1. Email Address  — highest priority
    2. Phone Number
    3. Full Name      — fallback

Source priority for field values:
    Resume (100%) > ATS JSON (90%) > Recruiter CSV (90%)

Functions implemented:
    find_matching_candidate()    — confirms records belong to same person
    merge_candidate_records()    — orchestrates the full merge
    merge_personal_details()     — name, email, phone, company
    merge_skills()               — unique skills from all sources
    merge_education()            — unique education entries
    merge_experience()           — unique experience entries
    merge_projects()             — unique projects
    merge_certifications()       — unique certifications
    _merge_unique_list()         — shared dedup helper for all list fields

NOT performed here:
    Confidence scoring, validation.
"""

from __future__ import annotations
from models.candidate import (
    IntermediateCandidate,
    CandidateRecord,
    ResumeData,
    MergedCandidate,
)


# ══════════════════════════════════════════════════════════════════════════
# Matching
# ══════════════════════════════════════════════════════════════════════════

def find_matching_candidate(
    candidate: IntermediateCandidate,
) -> dict:
    """
    Determine whether the sources within an IntermediateCandidate belong to
    the same person by comparing email, phone, and name across sources.

    Returns a dict with:
        matched       (bool)  — True if at least two sources agree
        match_field   (str)   — the field that confirmed the match
        sources       (list)  — which sources were involved
    """
    sources = []
    emails, phones, names = set(), set(), set()

    if candidate.csv_data:
        sources.append("csv")
        if candidate.csv_data.email:   emails.add(candidate.csv_data.email.lower())
        if candidate.csv_data.phone:   phones.add(candidate.csv_data.phone)
        if candidate.csv_data.full_name: names.add(candidate.csv_data.full_name.lower())

    if candidate.resume_data:
        sources.append("resume")
        if candidate.resume_data.email: emails.add(candidate.resume_data.email.lower())
        if candidate.resume_data.phone: phones.add(candidate.resume_data.phone)
        if candidate.resume_data.name:  names.add(candidate.resume_data.name.lower())

    if candidate.ats_data:
        sources.append("ats")
        if candidate.ats_data.email:    emails.add(candidate.ats_data.email.lower())
        if candidate.ats_data.phone:    phones.add(candidate.ats_data.phone)
        if candidate.ats_data.full_name: names.add(candidate.ats_data.full_name.lower())

    # If only one source, trivially matched
    if len(sources) <= 1:
        return {"matched": True, "match_field": "single_source", "sources": sources}

    # Check email agreement (highest priority)
    if len(emails) == 1:
        return {"matched": True, "match_field": "email", "sources": sources}

    # Check phone agreement
    if len(phones) == 1 and None not in phones:
        return {"matched": True, "match_field": "phone", "sources": sources}

    # Check name agreement (fallback)
    if len(names) == 1:
        return {"matched": True, "match_field": "name", "sources": sources}

    # Sources do not agree — flag but still merge (matching already done upstream)
    return {"matched": False, "match_field": "none", "sources": sources}


# ══════════════════════════════════════════════════════════════════════════
# List merge helper
# ══════════════════════════════════════════════════════════════════════════

def _merge_unique_list(*lists: list[str]) -> list[str]:
    """
    Merge multiple lists into one, preserving order and removing
    case-insensitive duplicates.

    Priority: earlier lists take precedence for ordering.
    """
    seen: set[str] = set()
    result: list[str] = []
    for lst in lists:
        for item in (lst or []):
            item = item.strip()
            if not item:
                continue
            key = item.lower()
            if key not in seen:
                seen.add(key)
                result.append(item)
    return result


# ══════════════════════════════════════════════════════════════════════════
# Field mergers
# ══════════════════════════════════════════════════════════════════════════

def merge_personal_details(
    merged:   MergedCandidate,
    csv:      CandidateRecord | None,
    resume:   ResumeData      | None,
    ats:      CandidateRecord | None,
) -> None:
    """
    Merge name, email, phone, and current_company into the MergedCandidate.

    Priority: Resume > ATS > CSV
    Candidate ID always comes from CSV (it is the authoritative source).
    """
    # Candidate ID — always from CSV
    merged.candidate_id = (
        (csv    and csv.candidate_id) or
        (ats    and ats.candidate_id) or
        None
    )

    # Name — Resume first (regex-extracted), then ATS, then CSV
    merged.name = (
        (resume and resume.name)      or
        (ats    and ats.full_name)    or
        (csv    and csv.full_name)    or
        None
    )
    if merged.name:
        merged.sources_used["name"] = "resume" if (resume and resume.name) \
            else ("ats" if (ats and ats.full_name) else "csv")

    # Email — Resume first, then ATS, then CSV
    merged.email = (
        (resume and resume.email)  or
        (ats    and ats.email)     or
        (csv    and csv.email)     or
        None
    )
    if merged.email:
        merged.sources_used["email"] = "resume" if (resume and resume.email) \
            else ("ats" if (ats and ats.email) else "csv")

    # Phone — Resume first (if present), then CSV, then ATS
    merged.phone = (
        (resume and resume.phone)  or
        (csv    and csv.phone)     or
        (ats    and ats.phone)     or
        None
    )
    if merged.phone:
        merged.sources_used["phone"] = "resume" if (resume and resume.phone) \
            else ("csv" if (csv and csv.phone) else "ats")

    # Current Company — CSV first (most reliable for current employer), then ATS
    merged.current_company = (
        (csv and csv.current_company) or
        (ats and ats.current_company) or
        None
    )
    if merged.current_company:
        merged.sources_used["current_company"] = "csv" if (csv and csv.current_company) else "ats"


def merge_skills(
    merged: MergedCandidate,
    resume: ResumeData      | None,
    ats:    CandidateRecord | None,
) -> None:
    """
    Merge skills from Resume and ATS JSON.
    Resume skills take priority in ordering (highest confidence source).
    CSV does not carry skills.
    """
    resume_skills = resume.skills if resume else []

    # ATS skills may be stored as a list in extra_fields
    ats_skills: list[str] = []
    if ats and "skills" in ats.extra_fields:
        raw = ats.extra_fields["skills"]
        if isinstance(raw, list):
            ats_skills = [str(s).strip() for s in raw if s]
        elif isinstance(raw, str):
            ats_skills = [s.strip() for s in raw.split(",") if s.strip()]

    merged.skills = _merge_unique_list(resume_skills, ats_skills)

    if merged.skills:
        merged.sources_used["skills"] = (
            "resume+ats" if (resume_skills and ats_skills) else
            "resume"     if resume_skills else "ats"
        )


def merge_education(
    merged: MergedCandidate,
    resume: ResumeData      | None,
    ats:    CandidateRecord | None,
) -> None:
    """
    Merge education entries from Resume and ATS JSON.
    Resume entries take ordering priority.
    """
    resume_edu = resume.education if resume else []

    # ATS education may be a string or list in extra_fields
    ats_edu: list[str] = []
    if ats:
        raw = ats.extra_fields.get("education", "")
        if isinstance(raw, list):
            ats_edu = [str(e).strip() for e in raw if e]
        elif isinstance(raw, str) and raw.strip():
            ats_edu = [raw.strip()]

    merged.education = _merge_unique_list(resume_edu, ats_edu)

    if merged.education:
        merged.sources_used["education"] = (
            "resume+ats" if (resume_edu and ats_edu) else
            "resume"     if resume_edu else "ats"
        )


def merge_experience(
    merged: MergedCandidate,
    resume: ResumeData      | None,
    ats:    CandidateRecord | None,
    csv:    CandidateRecord | None,
) -> None:
    """
    Merge experience entries from Resume, ATS, and CSV.

    Resume experience lines (role descriptions) take priority.
    ATS experience_years and CSV Experience numeric fields are
    appended as summary lines if not already covered.
    """
    resume_exp = resume.experience if resume else []

    ats_exp: list[str] = []
    if ats:
        # experience_years stored in extra_fields
        exp_years = ats.extra_fields.get("experience_years", "")
        if exp_years:
            ats_exp = [f"{exp_years} years experience"]

    csv_exp: list[str] = []
    if csv:
        exp_val = csv.extra_fields.get("Experience", "") or csv.extra_fields.get("experience", "")
        if exp_val:
            csv_exp = [f"{exp_val} years experience"]

    merged.experience = _merge_unique_list(resume_exp, ats_exp, csv_exp)

    if merged.experience:
        sources = []
        if resume_exp: sources.append("resume")
        if ats_exp:    sources.append("ats")
        if csv_exp:    sources.append("csv")
        merged.sources_used["experience"] = "+".join(sources) if sources else "none"


def merge_projects(
    merged: MergedCandidate,
    resume: ResumeData | None,
) -> None:
    """
    Merge project entries — sourced from Resume only at this stage.
    """
    merged.projects = _merge_unique_list(resume.projects if resume else [])
    if merged.projects:
        merged.sources_used["projects"] = "resume"


def merge_certifications(
    merged: MergedCandidate,
    resume: ResumeData      | None,
    ats:    CandidateRecord | None,
) -> None:
    """
    Merge certification entries from Resume and ATS JSON.
    """
    resume_certs: list[str] = []
    if resume and hasattr(resume, "certifications"):
        resume_certs = resume.certifications or []

    ats_certs: list[str] = []
    if ats:
        raw = ats.extra_fields.get("certifications", [])
        if isinstance(raw, list):
            ats_certs = [str(c).strip() for c in raw if c]
        elif isinstance(raw, str) and raw.strip():
            ats_certs = [raw.strip()]

    merged.certifications = _merge_unique_list(resume_certs, ats_certs)
    if merged.certifications:
        merged.sources_used["certifications"] = (
            "resume+ats" if (resume_certs and ats_certs) else
            "resume"     if resume_certs else "ats"
        )


# ══════════════════════════════════════════════════════════════════════════
# Main orchestrator
# ══════════════════════════════════════════════════════════════════════════

def merge_candidate_records(
    candidate: IntermediateCandidate,
) -> MergedCandidate:
    """
    Merge all source records within an IntermediateCandidate into a single
    unified MergedCandidate profile.

    Steps:
        1. Confirm records belong to the same person (find_matching_candidate)
        2. Merge personal details (name, email, phone, company)
        3. Merge skills
        4. Merge education
        5. Merge experience
        6. Merge projects
        7. Merge certifications
        8. Collect additional info from extra_fields

    Args:
        candidate: Deduplicated, normalized IntermediateCandidate.

    Returns:
        MergedCandidate — unified profile ready for confidence scoring.
    """
    csv    = candidate.csv_data
    resume = candidate.resume_data
    ats    = candidate.ats_data

    merged = MergedCandidate()

    # Step 1 — Confirm match
    match_info = find_matching_candidate(candidate)
    merged.sources_used["match_confirmed"] = match_info["match_field"]
    merged.sources_used["sources_present"] = match_info["sources"]

    # Step 2 — Personal details
    merge_personal_details(merged, csv, resume, ats)

    # Step 3 — Skills
    merge_skills(merged, resume, ats)

    # Step 4 — Education
    merge_education(merged, resume, ats)

    # Step 5 — Experience
    merge_experience(merged, resume, ats, csv)

    # Step 6 — Projects
    merge_projects(merged, resume)

    # Step 7 — Certifications
    merge_certifications(merged, resume, ats)

    # Step 8 — Additional info (extra_fields from all sources)
    _collect_additional_info(merged, csv, ats)

    return merged


# ══════════════════════════════════════════════════════════════════════════
# Additional info collector
# ══════════════════════════════════════════════════════════════════════════

# Keys already handled by dedicated merge functions — skip from additional_info
_HANDLED_KEYS = {
    "skills", "education", "experience", "experience_years",
    "certifications", "projects", "current_role",
}


def _collect_additional_info(
    merged: MergedCandidate,
    csv:    CandidateRecord | None,
    ats:    CandidateRecord | None,
) -> None:
    """
    Collect any remaining extra fields from CSV and ATS into additional_info.
    Skips fields already handled by dedicated merge functions.
    """
    if csv:
        for key, val in csv.extra_fields.items():
            if key.lower() not in _HANDLED_KEYS and val:
                merged.additional_info.setdefault(key, str(val).strip())

    if ats:
        for key, val in ats.extra_fields.items():
            if key.lower() not in _HANDLED_KEYS and val:
                if isinstance(val, list):
                    continue   # lists already handled above
                merged.additional_info.setdefault(key, str(val).strip())
