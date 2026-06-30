"""
Confidence Scoring Module.

Scoring formula:
  1. Source Weight   — Resume=40, ATS=30, CSV=20 (capped at 90)
  2. Cross-Source Match Bonus — +3 per field confirmed by 2+ sources (max +12)
  3. Conflict Penalty         — -4 per conflicting field
  4. Completeness Bonus       — +2 per present field: name/email/phone/company/skills/education/experience (max +14)

Score bands:
  95-100  : Successfully Unified
  85-94   : High Confidence - Successfully Unified
  75-84   : Medium Confidence
  60-74   : Low Confidence - Review Recommended
  <60     : Insufficient Data
"""

from __future__ import annotations
from services.conflict_resolver import ResolvedCandidate

_SOURCE_WEIGHTS = {"resume": 40, "ats": 30, "csv": 20}
_SCALAR_FIELDS  = ["name", "email", "phone", "current_company"]
_COMPLETENESS_FIELDS = ["name", "email", "phone", "current_company",
                        "skills", "education", "experience"]


def calculate_confidence(resolved: ResolvedCandidate,
                         sources_present: list[str]) -> dict:
    score = 0
    breakdown = {}

    # 1. Source weight
    src_pts = min(sum(_SOURCE_WEIGHTS.get(s, 0) for s in sources_present), 90)
    score += src_pts
    breakdown["source_weight"] = {
        "sources": sources_present,
        "points":  src_pts,
        "detail":  {s: _SOURCE_WEIGHTS.get(s, 0) for s in sources_present},
    }

    # 2. Cross-source match bonus + conflict detection
    match_bonus    = 0
    conflict_count = 0
    num_sources    = len(sources_present)

    for fld in _SCALAR_FIELDS:
        log = resolved.conflict_log.get(fld, {})
        if not log:
            continue
        if log.get("conflict") is False and log.get("value"):
            match_bonus += 3 if num_sources >= 2 else 1
        elif log.get("conflict") is True:
            conflict_count += 1

    score += match_bonus
    breakdown["cross_source_match_bonus"] = {
        "points":        match_bonus,
        "sources_count": num_sources,
    }

    # 3. Conflict penalty
    penalty = conflict_count * 4
    score  -= penalty
    breakdown["conflict_penalty"] = {
        "conflicts_found": conflict_count,
        "points_deducted": penalty,
    }

    # 4. Completeness bonus
    comp_pts      = 0
    missing_fields = []
    for fld in _COMPLETENESS_FIELDS:
        val = getattr(resolved, fld, None)
        if val and (not isinstance(val, list) or len(val) > 0):
            comp_pts += 2
        else:
            missing_fields.append(fld)

    score += comp_pts
    breakdown["completeness_bonus"] = {
        "points":         comp_pts,
        "missing_fields": missing_fields,
    }

    score = max(0, min(100, score))

    return {
        "score":      score,
        "percentage": f"{score}%",
        "status":     _status_label(score),
        "breakdown":  breakdown,
    }


def _status_label(score: int) -> str:
    if score >= 95:
        return "Successfully Unified"
    elif score >= 85:
        return "High Confidence — Successfully Unified"
    elif score >= 75:
        return "Medium Confidence"
    elif score >= 60:
        return "Low Confidence — Review Recommended"
    else:
        return "Insufficient Data"
