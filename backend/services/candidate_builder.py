"""
Candidate builder service.

Assembles the IntermediateCandidate object after all sources have been
parsed and matched. No normalisation, deduplication, or conflict
resolution is performed at this stage.

Rules:
- If resume is provided: only produce a candidate for the CSV row that
  the resume matched. Unmatched CSV rows are NOT included.
- If no resume: produce one candidate per CSV row (with ATS if matched).
- ATS records are always matched against CSV and attached where found.
"""
from models.candidate import (
    CandidateRecord,
    ResumeData,
    IntermediateCandidate,
)
from services.matcher import match_resume, match_ats_record


def build_intermediate_candidate(
    csv_records:  list[CandidateRecord],
    resume:       ResumeData            | None,
    ats_records:  list[CandidateRecord] | None,
) -> list[IntermediateCandidate]:
    """
    Build intermediate candidate objects.

    Args:
        csv_records:  Parsed CSV records (may be empty if CSV not selected).
        resume:       Parsed resume data (may be None).
        ats_records:  Parsed ATS records (may be None or empty).

    Returns:
        List of IntermediateCandidate objects — only for matched candidates.
    """

    # ── Step 1: Match ATS records → CSV ──────────────────────────────────
    # Map: csv_key → (ats_record, match_method)
    ats_match_map: dict[str, tuple[CandidateRecord, str]] = {}

    if ats_records and csv_records:
        for ats_rec in ats_records:
            ats_rec, matched_csv_rec, method = match_ats_record(ats_rec, csv_records)
            if matched_csv_rec:
                key = _key_for(matched_csv_rec, csv_records)
                if key not in ats_match_map:
                    ats_match_map[key] = (ats_rec, method)

    # ── Step 2: Resume path — only return the one matched CSV row ─────────
    if resume:
        matched_csv_rec = None
        resume_method   = "unmatched"

        if csv_records:
            # Match resume against CSV
            resume, matched_csv_rec, resume_method = match_resume(resume, csv_records)

        if matched_csv_rec:
            # Found a CSV match — build one candidate for that row only
            key = _key_for(matched_csv_rec, csv_records)
            attached_ats, ats_method = ats_match_map.get(key, (None, None))

            return [IntermediateCandidate(
                candidate_id     = matched_csv_rec.candidate_id,
                csv_data         = matched_csv_rec,
                ats_data         = attached_ats,
                resume_data      = resume,
                match_method     = resume_method,
                ats_match_method = ats_method,
            )]
        else:
            # Resume could not be matched to any CSV row —
            # return a standalone candidate with only resume data
            return [IntermediateCandidate(
                candidate_id     = None,
                csv_data         = None,
                ats_data         = None,
                resume_data      = resume,
                match_method     = "unmatched",
                ats_match_method = None,
            )]

    # ── Step 3: No resume — return all CSV rows with ATS attached ─────────
    candidates: list[IntermediateCandidate] = []
    for csv_rec in csv_records:
        key = _key_for(csv_rec, csv_records)
        attached_ats, ats_method = ats_match_map.get(key, (None, None))

        candidates.append(IntermediateCandidate(
            candidate_id     = csv_rec.candidate_id,
            csv_data         = csv_rec,
            ats_data         = attached_ats,
            resume_data      = None,
            match_method     = None,
            ats_match_method = ats_method,
        ))

    return candidates


# ── Helper ────────────────────────────────────────────────────────────────

def _key_for(rec: CandidateRecord, all_records: list[CandidateRecord]) -> str:
    """Return a stable key for a record."""
    if rec.candidate_id:
        return rec.candidate_id
    try:
        return f"__row_{all_records.index(rec)}"
    except ValueError:
        return "__row_unknown"
