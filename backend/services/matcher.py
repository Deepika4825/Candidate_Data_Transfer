"""
Candidate matching service.

Matches ResumeData and ATS CandidateRecords against the CSV CandidateRecords
using a three-tier priority:
    1. Email address  (exact, case-insensitive)
    2. Phone number   (digits-only comparison)
    3. Full name      (case-insensitive, stripped)

After a successful match the candidate_id from the CSV record is assigned
to the matched object.
"""
import re
from models.candidate import CandidateRecord, ResumeData


# ── Normalisation helpers ─────────────────────────────────────────────────

def _norm_email(value: str | None) -> str | None:
    """Lowercase and strip an email address."""
    return value.strip().lower() if value else None


def _norm_phone(value: str | None) -> str | None:
    """Strip everything except digits; return None if fewer than 7 digits remain."""
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return digits if len(digits) >= 7 else None


def _norm_name(value: str | None) -> str | None:
    """Lowercase, collapse whitespace."""
    if not value:
        return None
    return " ".join(value.strip().lower().split())


# ── Core match function ───────────────────────────────────────────────────

def match_to_csv(
    candidate_email: str | None,
    candidate_phone: str | None,
    candidate_name:  str | None,
    csv_records:     list[CandidateRecord],
) -> tuple[CandidateRecord | None, str]:
    """
    Try to find a matching CandidateRecord from the CSV list.

    Args:
        candidate_email: Email extracted from resume or ATS record.
        candidate_phone: Phone extracted from resume or ATS record.
        candidate_name:  Name extracted from resume or ATS record.
        csv_records:     List of CandidateRecord objects from the CSV.

    Returns:
        (matched_record, match_method) where match_method is one of:
        'email', 'phone', 'name', or 'unmatched'.
    """
    # ── Pass 1: Email ────────────────────────────────────────────────────
    if candidate_email:
        norm_email = _norm_email(candidate_email)
        for rec in csv_records:
            if _norm_email(rec.email) == norm_email:
                return rec, "email"

    # ── Pass 2: Phone ────────────────────────────────────────────────────
    if candidate_phone:
        norm_phone = _norm_phone(candidate_phone)
        if norm_phone:
            for rec in csv_records:
                if _norm_phone(rec.phone) == norm_phone:
                    return rec, "phone"

    # ── Pass 3: Full name ────────────────────────────────────────────────
    if candidate_name:
        norm_name = _norm_name(candidate_name)
        for rec in csv_records:
            if _norm_name(rec.full_name) == norm_name:
                return rec, "name"

    return None, "unmatched"


# ── Resume matcher ────────────────────────────────────────────────────────

def match_resume(
    resume: ResumeData,
    csv_records: list[CandidateRecord],
) -> tuple[ResumeData, CandidateRecord | None, str]:
    """
    Match a ResumeData object against the CSV records.
    Assigns candidate_id to the resume if a match is found.

    Returns:
        (resume_with_id, matched_csv_record, match_method)
    """
    matched_rec, method = match_to_csv(
        resume.email, resume.phone, resume.name, csv_records
    )

    if matched_rec:
        resume.candidate_id = matched_rec.candidate_id

    return resume, matched_rec, method


# ── ATS record matcher ────────────────────────────────────────────────────

def match_ats_record(
    ats_record:  CandidateRecord,
    csv_records: list[CandidateRecord],
) -> tuple[CandidateRecord, CandidateRecord | None, str]:
    """
    Match a single ATS CandidateRecord against the CSV records.
    Assigns candidate_id to the ATS record if a match is found.

    Returns:
        (ats_record_with_id, matched_csv_record, match_method)
    """
    # If the ATS record already carries a candidate_id, try direct ID match first
    if ats_record.candidate_id:
        for rec in csv_records:
            if rec.candidate_id and rec.candidate_id == ats_record.candidate_id:
                return ats_record, rec, "candidate_id"

    matched_rec, method = match_to_csv(
        ats_record.email, ats_record.phone, ats_record.full_name, csv_records
    )

    if matched_rec and not ats_record.candidate_id:
        ats_record.candidate_id = matched_rec.candidate_id

    return ats_record, matched_rec, method
