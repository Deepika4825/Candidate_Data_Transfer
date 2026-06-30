"""
Conflict Resolution Module.

Executes after Merge Records.

Purpose:
    Compare field values across Resume, ATS JSON, and Recruiter CSV sources.
    When values conflict, select the value from the highest-priority source.
    For list fields, merge all unique values instead of replacing.
    Record which source supplied each resolved value for traceability.

Source Priority (highest → lowest):
    1. Resume       (most direct candidate-authored data)
    2. ATS JSON     (structured recruiter system data)
    3. Recruiter CSV (spreadsheet data)

Rules:
    - Identical values → keep as-is, no conflict.
    - Conflicting scalar fields → use highest-priority source that has a value.
    - List fields (skills, education, experience, projects, certifications)
      → merge all unique values from all sources.
    - Record source for each field in conflict_log.

NOT performed here:
    Confidence scoring, output schema projection, validation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from models.candidate import IntermediateCandidate, MergedCandidate


# ── Source priority ────────────────────────────────────────────────────────
# Lower index = higher priority
SOURCE_PRIORITY = ["resume", "ats", "csv"]


@dataclass
class ResolvedCandidate:
    """
    Conflict-free unified candidate profile produced after conflict resolution.
    Extends MergedCandidate by adding a conflict_log for traceability.
    """
    candidate_id:    str | None   = None
    name:            str | None   = None
    email:           str | None   = None
    phone:           str | None   = None
    current_company: str | None   = None
    skills:          list[str]    = field(default_factory=list)
    education:       list[str]    = field(default_factory=list)
    experience:      list[str]    = field(default_factory=list)
    projects:        list[str]    = field(default_factory=list)
    certifications:  list[str]    = field(default_factory=list)
    additional_info: dict         = field(default_factory=dict)
    # Traceability: { field_name → { "value": ..., "source": ..., "conflict": bool } }
    conflict_log:    dict         = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "candidate_id":    self.candidate_id,
            "name":            self.name,
            "email":           self.email,
            "phone":           self.phone,
            "current_company": self.current_company,
            "skills":          self.skills,
            "education":       self.education,
            "experience":      self.experience,
            "projects":        self.projects,
            "certifications":  self.certifications,
            "additional_info": self.additional_info,
            "conflict_log":    self.conflict_log,
        }


# ══════════════════════════════════════════════════════════════════════════
# Scalar field resolver
# ══════════════════════════════════════════════════════════════════════════

def _resolve_scalar(
    field_name: str,
    values: dict[str, str | None],   # { "resume": val, "ats": val, "csv": val }
    resolved: ResolvedCandidate,
) -> str | None:
    """
    Resolve a scalar (single-value) field conflict.

    - Collects non-None values from all sources.
    - If all present values are identical → no conflict, return value.
    - If values differ → pick from highest-priority source.
    - Logs the result in conflict_log.

    Args:
        field_name: Name of the field being resolved.
        values:     Dict mapping source name to value.
        resolved:   ResolvedCandidate to write the conflict_log into.

    Returns:
        The resolved value (str or None).
    """
    present = {
        src: val.strip()
        for src, val in values.items()
        if val and str(val).strip()
    }

    if not present:
        return None

    unique_vals = set(v.lower() for v in present.values())

    if len(unique_vals) == 1:
        # All sources agree — no conflict
        winning_src = next(
            (s for s in SOURCE_PRIORITY if s in present), list(present.keys())[0]
        )
        resolved.conflict_log[field_name] = {
            "value":    present[winning_src],
            "source":   winning_src,
            "conflict": False,
        }
        return present[winning_src]

    # Conflict detected — pick from highest-priority source
    for src in SOURCE_PRIORITY:
        if src in present:
            resolved.conflict_log[field_name] = {
                "value":             present[src],
                "source":            src,
                "conflict":          True,
                "all_values":        present,
            }
            return present[src]

    return None


# ══════════════════════════════════════════════════════════════════════════
# List field merger
# ══════════════════════════════════════════════════════════════════════════

def _merge_lists(
    field_name: str,
    lists: dict[str, list[str]],   # { "resume": [...], "ats": [...], "csv": [...] }
    resolved: ResolvedCandidate,
) -> list[str]:
    """
    Merge list fields by combining all unique values from all sources.
    Order is preserved by source priority (resume first, then ats, then csv).

    Args:
        field_name: Name of the list field.
        lists:      Dict mapping source name to list of values.
        resolved:   ResolvedCandidate to write the conflict_log into.

    Returns:
        Merged, deduplicated list of values.
    """
    seen: set[str] = set()
    result: list[str] = []
    sources_contributed: list[str] = []

    for src in SOURCE_PRIORITY:
        src_list = lists.get(src, []) or []
        added = 0
        for item in src_list:
            item = item.strip()
            if not item:
                continue
            key = item.lower()
            if key not in seen:
                seen.add(key)
                result.append(item)
                added += 1
        if added:
            sources_contributed.append(src)

    resolved.conflict_log[field_name] = {
        "value":               result,
        "source":              "+".join(sources_contributed) if sources_contributed else "none",
        "conflict":            False,  # lists are always merged, not replaced
        "sources_contributed": sources_contributed,
    }
    return result


# ══════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════

def resolve_conflicts(
    candidate: IntermediateCandidate,
) -> ResolvedCandidate:
    """
    Resolve conflicts across all sources in an IntermediateCandidate and
    produce a conflict-free ResolvedCandidate profile.

    Args:
        candidate: Normalized, deduplicated IntermediateCandidate
                   (output of deduplicator, after normalization).

    Returns:
        ResolvedCandidate — conflict-free profile ready for confidence scoring.
    """
    csv    = candidate.csv_data
    resume = candidate.resume_data
    ats    = candidate.ats_data

    resolved = ResolvedCandidate()

    # ── candidate_id — always from CSV ────────────────────────────────────
    resolved.candidate_id = (
        (csv and csv.candidate_id) or
        (ats and ats.candidate_id) or
        None
    )

    # ── Scalar fields ──────────────────────────────────────────────────────

    resolved.name = _resolve_scalar("name", {
        "resume": resume.name        if resume else None,
        "ats":    ats.full_name      if ats    else None,
        "csv":    csv.full_name      if csv    else None,
    }, resolved)

    resolved.email = _resolve_scalar("email", {
        "resume": resume.email       if resume else None,
        "ats":    ats.email          if ats    else None,
        "csv":    csv.email          if csv    else None,
    }, resolved)

    resolved.phone = _resolve_scalar("phone", {
        "resume": resume.phone       if resume else None,
        "ats":    ats.phone          if ats    else None,
        "csv":    csv.phone          if csv    else None,
    }, resolved)

    resolved.current_company = _resolve_scalar("current_company", {
        "resume": None,              # resume does not extract company
        "ats":    ats.current_company if ats   else None,
        "csv":    csv.current_company if csv   else None,
    }, resolved)

    # ── List fields — merge all unique values ──────────────────────────────

    # Skills
    ats_skills: list[str] = []
    if ats and "skills" in ats.extra_fields:
        raw = ats.extra_fields["skills"]
        if isinstance(raw, list):
            ats_skills = [str(s).strip() for s in raw if s]
        elif isinstance(raw, str):
            ats_skills = [s.strip() for s in raw.split(",") if s.strip()]

    resolved.skills = _merge_lists("skills", {
        "resume": resume.skills if resume else [],
        "ats":    ats_skills,
        "csv":    [],
    }, resolved)

    # Education
    ats_edu: list[str] = []
    if ats:
        raw = ats.extra_fields.get("education", "")
        if isinstance(raw, list):
            ats_edu = [str(e).strip() for e in raw if e]
        elif isinstance(raw, str) and raw.strip():
            ats_edu = [raw.strip()]

    resolved.education = _merge_lists("education", {
        "resume": resume.education if resume else [],
        "ats":    ats_edu,
        "csv":    [],
    }, resolved)

    # Experience
    ats_exp: list[str] = []
    if ats:
        exp_years = ats.extra_fields.get("experience_years", "")
        if exp_years:
            ats_exp = [f"{exp_years} years experience"]

    csv_exp: list[str] = []
    if csv:
        exp_val = (
            csv.extra_fields.get("Experience") or
            csv.extra_fields.get("experience") or ""
        )
        if exp_val:
            csv_exp = [f"{exp_val} years experience"]

    resolved.experience = _merge_lists("experience", {
        "resume": resume.experience if resume else [],
        "ats":    ats_exp,
        "csv":    csv_exp,
    }, resolved)

    # Projects
    resolved.projects = _merge_lists("projects", {
        "resume": resume.projects if resume else [],
        "ats":    [],
        "csv":    [],
    }, resolved)

    # Certifications
    resume_certs: list[str] = (
        resume.certifications if (resume and hasattr(resume, "certifications")) else []
    )
    ats_certs: list[str] = []
    if ats:
        raw = ats.extra_fields.get("certifications", [])
        if isinstance(raw, list):
            ats_certs = [str(c).strip() for c in raw if c]
        elif isinstance(raw, str) and raw.strip():
            ats_certs = [raw.strip()]

    resolved.certifications = _merge_lists("certifications", {
        "resume": resume_certs,
        "ats":    ats_certs,
        "csv":    [],
    }, resolved)

    # ── Additional info (extra_fields not handled above) ──────────────────
    _HANDLED = {
        "skills", "education", "experience", "experience_years",
        "certifications", "projects", "current_role",
    }
    if csv:
        for k, v in csv.extra_fields.items():
            if k.lower() not in _HANDLED and v:
                resolved.additional_info.setdefault(k, str(v).strip())
    if ats:
        for k, v in ats.extra_fields.items():
            if k.lower() not in _HANDLED and v and not isinstance(v, list):
                resolved.additional_info.setdefault(k, str(v).strip())

    return resolved
