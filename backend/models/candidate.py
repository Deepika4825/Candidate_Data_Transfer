"""
Internal candidate data model.

Every parser converts its source data into this structure.
At this stage: no normalisation, no deduplication, no conflict resolution.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class CandidateRecord:
    """
    Flat candidate record extracted from a single source (CSV row or ATS JSON entry).
    """
    candidate_id:    Optional[str] = None
    full_name:       Optional[str] = None
    email:           Optional[str] = None
    phone:           Optional[str] = None
    current_company: Optional[str] = None
    extra_fields:    dict          = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResumeData:
    """
    Fields extracted from the resume text via regex.
    """
    candidate_id:   Optional[str] = None
    name:           Optional[str] = None
    email:          Optional[str] = None
    phone:          Optional[str] = None
    skills:         list[str]     = field(default_factory=list)
    education:      list[str]     = field(default_factory=list)
    experience:     list[str]     = field(default_factory=list)
    projects:       list[str]     = field(default_factory=list)
    certifications: list[str]     = field(default_factory=list)
    raw_text:       str           = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IntermediateCandidate:
    """
    Intermediate candidate object — holds raw, unmerged data from all sources
    side-by-side after matching, normalisation, and deduplication.
    """
    candidate_id:     Optional[str]             = None
    csv_data:         Optional[CandidateRecord] = None
    ats_data:         Optional[CandidateRecord] = None
    resume_data:      Optional[ResumeData]      = None
    match_method:     Optional[str]             = None
    ats_match_method: Optional[str]             = None

    def to_dict(self) -> dict:
        return {
            "candidate_id":     self.candidate_id,
            "match_method":     self.match_method,
            "ats_match_method": self.ats_match_method,
            "csv_data":         self.csv_data.to_dict()    if self.csv_data    else None,
            "ats_data":         self.ats_data.to_dict()    if self.ats_data    else None,
            "resume_data":      self.resume_data.to_dict() if self.resume_data else None,
        }


@dataclass
class MergedCandidate:
    """
    Unified candidate profile produced after merging all sources.
    This is the final output object of the merge stage.

    Source priority for each field:
        Resume (100%) > ATS JSON (90%) > Recruiter CSV (90%)
    """
    candidate_id:    Optional[str] = None
    name:            Optional[str] = None
    email:           Optional[str] = None
    phone:           Optional[str] = None
    current_company: Optional[str] = None
    skills:          list[str]     = field(default_factory=list)
    education:       list[str]     = field(default_factory=list)
    experience:      list[str]     = field(default_factory=list)
    projects:        list[str]     = field(default_factory=list)
    certifications:  list[str]     = field(default_factory=list)
    # Extra fields collected from all sources
    additional_info: dict          = field(default_factory=dict)
    # Audit trail — which source provided each field
    sources_used:    dict          = field(default_factory=dict)

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
            "sources_used":    self.sources_used,
        }
