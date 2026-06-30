"""
Route definitions.

POST /process  — full extraction/matching/normalize/dedup/merge/conflict/confidence pipeline
/generate-profile is handled by routes_schema.py
"""
from flask import Blueprint, request, jsonify
import os

from utils.input_loader import get_input_path, get_resume_paths

from parsers.csv_parser    import parse_csv
from parsers.json_parser   import parse_ats_json
from parsers.resume_parser import parse_resume
from parsers.config_parser import parse_config

from services.candidate_builder  import build_intermediate_candidate
from services.normalizer         import normalize_candidate
from services.deduplicator       import deduplicate_candidates
from services.conflict_resolver  import resolve_conflicts
from services.confidence_scorer  import calculate_confidence
from models.candidate import ResumeData

process_bp = Blueprint("process", __name__)


@process_bp.post("/process")
def process():
    body     = request.get_json(silent=True) or {}
    selected = body.get("sources", [])

    result = {
        "status":             "success",
        "csv":                "Not selected",
        "json":               "Not selected",
        "resume":             "Not selected",
        "config":             "Not selected",
        "errors":             [],
        "candidates":         [],
        "deduplication":      [],
        "duplicates_removed": 0,
    }

    if not selected:
        result["status"] = "error"
        result["errors"].append("Please select at least one data source.")
        return jsonify(result), 400

    # ── CSV ──────────────────────────────────────────────────────────────
    csv_records = []
    if "csv" in selected:
        try:
            csv_records = parse_csv(get_input_path("csv"))
            result["csv"] = f"Loaded ({len(csv_records)} record(s))"
        except Exception as exc:
            result["csv"] = f"Error: {exc}"
            result["errors"].append(str(exc))

    # ── ATS JSON ─────────────────────────────────────────────────────────
    ats_records = None
    if "json" in selected:
        try:
            ats_records = parse_ats_json(get_input_path("json"))
            result["json"] = f"Loaded ({len(ats_records)} record(s))"
        except Exception as exc:
            result["json"] = f"Error: {exc}"
            result["errors"].append(str(exc))

    # ── Resumes ──────────────────────────────────────────────────────────
    all_resume_data: list[ResumeData] = []
    if "resume" in selected:
        resume_paths = get_resume_paths()
        if not resume_paths:
            result["resume"] = "No resume files found in input/ folder"
            result["errors"].append("No .pdf or .docx files found in the input/ folder.")
        else:
            loaded = 0
            for rpath in resume_paths:
                try:
                    rd = parse_resume(rpath)
                    rd._source_filename = os.path.basename(rpath)
                    all_resume_data.append(rd)
                    loaded += 1
                except Exception as exc:
                    result["errors"].append(f"Resume parse error ({rpath}): {exc}")
            result["resume"] = f"Loaded ({loaded} resume(s))"

    # ── Config ───────────────────────────────────────────────────────────
    if "config" in selected:
        try:
            parse_config(get_input_path("config"))
            result["config"] = "Loaded"
        except Exception as exc:
            result["config"] = f"Error: {exc}"
            result["errors"].append(str(exc))

    # ── Build → Normalize → Deduplicate → Conflict → Confidence ──────────
    try:
        normalized: list = []
        resume_only_mode = "resume" in selected and "csv" not in selected

        if all_resume_data:
            # Always load CSV for matching purposes (even if not selected)
            # so the resume can be matched to a candidate_id
            match_csv_records = csv_records
            if not match_csv_records:
                try:
                    match_csv_records = parse_csv(get_input_path("csv"))
                except Exception:
                    match_csv_records = []

            all_cands: dict = {}
            for resume in all_resume_data:
                for c in build_intermediate_candidate(
                    csv_records=match_csv_records,
                    resume=resume,
                    ats_records=ats_records,
                ):
                    c = normalize_candidate(c)
                    # If user only selected resume (not csv), strip csv_data from output
                    if resume_only_mode:
                        c.csv_data = None
                    # Only keep if resume was actually matched
                    if c.resume_data is None:
                        continue
                    key = c.candidate_id or id(c)
                    if key not in all_cands:
                        all_cands[key] = c
            normalized = list(all_cands.values())
        else:
            normalized = [
                normalize_candidate(c)
                for c in build_intermediate_candidate(
                    csv_records=csv_records, resume=None, ats_records=ats_records
                )
            ]

        deduped, dedup_report = deduplicate_candidates(normalized)

        final = []
        for c in deduped:
            resolved = resolve_conflicts(c)
            sources  = (
                (["csv"]    if c.csv_data    else []) +
                (["ats"]    if c.ats_data    else []) +
                (["resume"] if c.resume_data else [])
            )
            entry = resolved.to_dict()
            entry["confidence"]      = calculate_confidence(resolved, sources)
            entry["resume_filename"] = getattr(c.resume_data, "_source_filename", None) if c.resume_data else None
            entry["sources_present"] = sources
            final.append(entry)

        result["candidates"]         = final
        result["deduplication"]      = dedup_report
        result["duplicates_removed"] = len(normalized) - len(deduped)

    except Exception as exc:
        result["errors"].append(f"Pipeline error: {exc}")

    if result["errors"]:
        result["status"] = "partial" if result["candidates"] else "error"

    return jsonify(result), 200
