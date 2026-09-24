"""DocAssistIQ — World-Class Hospital Note Generator (Phase 30 v2).

Generates international teaching-hospital-grade structured clinical notes from:
  - Raw unstructured doctor input text
  - Extracted ClinicalFindings
  - Transcript segments (doctor + patient voice)
  - AI diagnostic suggestions

Note format: Extended SOAP+ matching top global clinical institutions.
Sections: Chief Complaint, HPI, Vitals, ROS, PMH, Medications, Allergies,
          Family Hx, Social Hx, Physical Exam (systemic), Investigations,
          Differential Diagnosis, Assessment, Plan, Follow-Up, Safety Net.
"""

import uuid
import json
import re
import structlog
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.clinical import ClinicalFinding, ClinicalNote
from app.models.consultation import Consultation
from app.infrastructure.ai.factory import get_generation_provider
from app.services.embedding_service import generate_and_store_embedding

baseline_generation_provider = get_generation_provider()
log = structlog.get_logger(__name__)

# Extended world-class hospital note sections
SECTIONS = [
    "chief_complaint",
    "hpi",
    "vitals",
    "review_of_systems",
    "past_medical_history",
    "surgical_history",
    "medications",
    "allergies",
    "family_history",
    "social_history",
    "physical_examination",
    "investigations",
    "differential_diagnosis",
    "assessment",
    "plan",
    "follow_up_plan",
    "safety_net",
]

# Sections the AI fills (not assessment/plan — those stay blank for clinician)
AI_FILLS = {s for s in SECTIONS if s not in ("assessment", "plan")}

WORLD_CLASS_SYSTEM_PROMPT = """You are a Senior Consultant Physician AI at a world-class academic medical center.
Generate a structured, professional clinical note from the provided clinical text and findings.

## CLINICAL STANDARDS:
1. **Format**: Output ONLY valid JSON matching the exact schema — no markdown fences, no preamble.
2. **Concise & High-Yield**: Write 1-2 focused, professional sentences per section. Highlight pertinent positives and key pertinent negatives.
3. **Vitals**: Extract all stated vitals (BP, HR, RR, Temp, SpO2). If not mentioned, write "Not documented".
4. **HPI**: Concise chronological summary of onset, character, severity, radiation, and associated symptoms.
5. **ROS**: Focus on pertinent systems related to the complaint (e.g. Cardiovascular, Respiratory).
6. **Physical Exam**: Key pertinent findings or "Not documented".
7. **Differential Diagnosis**: 2-3 most likely diagnoses with brief 1-sentence rationale.
8. **Follow-Up & Safety Net**: Specific timeframe and red-flag warning triggers.
9. **Assessment & Plan**: Leave blank (clinician fills).

Output ONLY valid JSON matching this exact schema:
{
  "chief_complaint": "",
  "hpi": "",
  "vitals": "",
  "review_of_systems": "",
  "past_medical_history": "",
  "surgical_history": "",
  "medications": "",
  "allergies": "",
  "family_history": "",
  "social_history": "",
  "physical_examination": "",
  "investigations": "",
  "differential_diagnosis": "",
  "assessment": "",
  "plan": "",
  "follow_up_plan": "",
  "safety_net": ""
}"""


def _extract_vitals_from_text(text: str) -> str:
    """Extract vitals from free text using regex patterns."""
    vitals = {}

    patterns = {
        "BP": r"(?:BP|blood pressure)[:\s]*(\d{2,3}/\d{2,3})",
        "HR": r"(?:HR|heart rate|pulse)[:\s]*(\d{2,3})\s*(?:bpm|/min)?",
        "RR": r"(?:RR|respiratory rate|resp rate)[:\s]*(\d{1,2})\s*(?:/min|bpm)?",
        "Temp": r"(?:Temp|temperature|T)[:\s]*(\d{2,3}(?:\.\d)?)\s*(?:°?[CF])?",
        "SpO2": r"(?:SpO2|spo2|O2 sat|oxygen sat(?:uration)?)[:\s]*(\d{2,3})\s*%?",
        "Weight": r"(?:weight|wt)[:\s]*(\d{2,3}(?:\.\d)?)\s*(?:kg|lbs?)?",
        "Height": r"(?:height|ht)[:\s]*(\d{1,3}(?:\.\d)?)\s*(?:cm|m|ft)?",
        "GCS": r"(?:GCS|glasgow)[:\s]*(\d{1,2}(?:/15)?)",
    }

    for key, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            vitals[key] = m.group(1)

    if vitals:
        parts = [f"{k}: {v}" for k, v in vitals.items()]
        return " | ".join(parts)
    return "Not documented"


def _extract_travel_history(text: str) -> str:
    """Extract travel history for social history section."""
    travel_pattern = r"(?:travel(?:led|ed)?|visited?|returned? from|trip to)\s+([A-Za-z\s,]+?)(?:\.|,|\n|$)"
    matches = re.findall(travel_pattern, text, re.IGNORECASE)
    if matches:
        return "Travel: " + "; ".join(set(m.strip() for m in matches))
    return ""


def _clean_and_parse_json(raw: str) -> Dict[str, Any]:
    """Clean markdown fences and repair partial JSON if possible."""
    if not raw:
        return {}
    clean = raw.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    elif clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    clean = clean.strip()

    first_brace = clean.find("{")
    if first_brace == -1:
        return {}

    last_brace = clean.rfind("}")
    if last_brace != -1 and last_brace > first_brace:
        candidate = clean[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Attempt basic repair if truncated
    candidate = clean[first_brace:]
    open_quotes = candidate.count('"') - candidate.count(r'\"')
    if open_quotes % 2 != 0:
        candidate += '"'
    open_braces = candidate.count("{") - candidate.count("}")
    for _ in range(max(0, open_braces)):
        candidate += "}"
    try:
        return json.loads(candidate)
    except Exception:
        parsed = {}
        for m in re.finditer(r'"([a-zA-Z0-9_]+)"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', candidate):
            parsed[m.group(1)] = m.group(2)
        return parsed


class NoteGeneratorService:

    async def draft_note_from_findings(
        self,
        db: AsyncSession,
        consultation_id: uuid.UUID,
        doctor_id: uuid.UUID,
        transcript_segments: Optional[List[Dict]] = None,
    ) -> ClinicalNote:
        """
        Generates a world-class hospital-grade clinical note.
        Combines: raw unstructured text + extracted findings + transcript.
        """
        # Get findings
        findings_result = await db.scalars(
            select(ClinicalFinding).where(ClinicalFinding.consultation_id == consultation_id)
        )
        findings = findings_result.all()

        findings_context = "\n".join([
            f"- [{f.concept.upper()}] {f.canonical_concept or f.value}"
            f"{' (NEGATED)' if f.negated else ''}"
            f"{' [PAST]' if f.temporality == 'past' else ''}"
            for f in findings
        ])

        # Get consultation text
        consultation = await db.scalar(
            select(Consultation).where(Consultation.id == consultation_id)
        )
        raw_text = consultation.input_text if consultation else ""

        # Extract vitals from raw text
        vitals_extracted = _extract_vitals_from_text(raw_text)
        travel_extracted = _extract_travel_history(raw_text)

        # Build transcript section
        transcript_text = ""
        if transcript_segments:
            lines = []
            for seg in transcript_segments[:50]:  # cap at 50 segments
                speaker = seg.get("speaker", "Unknown")
                text = seg.get("text", "").strip()
                if text:
                    lines.append(f"[{speaker}]: {text}")
            transcript_text = "\n".join(lines)

        # Build the full prompt
        prompt_parts = []
        if raw_text:
            prompt_parts.append(f"=== RAW CLINICAL NOTES ===\n{raw_text}")
        if findings_context:
            prompt_parts.append(f"=== EXTRACTED CLINICAL FINDINGS ===\n{findings_context}")
        if transcript_text:
            prompt_parts.append(f"=== CONSULTATION TRANSCRIPT ===\n{transcript_text}")
        if vitals_extracted != "Not documented":
            prompt_parts.append(f"=== AUTO-EXTRACTED VITALS ===\n{vitals_extracted}")
        if travel_extracted:
            prompt_parts.append(f"=== AUTO-EXTRACTED TRAVEL HISTORY ===\n{travel_extracted}")

        full_prompt = "\n\n".join(prompt_parts) or "No clinical data provided."

        log.info("note_generator_request", consultation_id=str(consultation_id),
                 text_length=len(raw_text), findings_count=len(findings))

        drafted_sections = {}
        try:
            from app.infrastructure.ai.interfaces import GenerationRequest
            request = GenerationRequest(
                prompt=full_prompt,
                system_prompt=WORLD_CLASS_SYSTEM_PROMPT,
                json_schema={"type": "object"},
                max_tokens=1200
            )
            result = await baseline_generation_provider.generate(request, timeout=3.0)
            raw_result = result.text.strip()
            drafted_sections = _clean_and_parse_json(raw_result)

            if not drafted_sections:
                log.warning("note_generator_llm_empty_json, falling back")
                drafted_sections = self._fallback_draft(findings, raw_text, vitals_extracted, travel_extracted)

        except Exception as e:
            log.warning("note_generator_llm_fallback", error=repr(e))
            drafted_sections = self._fallback_draft(findings, raw_text, vitals_extracted, travel_extracted)

        # Build structured sections
        structured_sections: Dict[str, Any] = {}
        now_str = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")

        for section in SECTIONS:
            if section in ("assessment", "plan"):
                # Clinician fills these — never pre-populate
                structured_sections[section] = {
                    "text": "",
                    "original_ai_text": None,
                    "status": "draft"
                }
            else:
                val = drafted_sections.get(section, "") or ""
                # Inject auto-extracted vitals if AI missed them
                if section == "vitals" and not val and vitals_extracted != "Not documented":
                    val = vitals_extracted
                structured_sections[section] = {
                    "text": val,
                    "original_ai_text": val,
                    "status": "draft",
                    "generated_at": now_str,
                }

        # Add metadata section for hospital header
        structured_sections["_meta"] = {
            "generated_at": now_str,
            "note_format": "Extended SOAP+ v2",
            "note_version": "2.0",
        }

        # Upsert note
        note_result = await db.scalars(
            select(ClinicalNote).where(ClinicalNote.consultation_id == consultation_id)
        )
        existing_note = note_result.first()

        if existing_note:
            current_body = existing_note.body or {}
            for section in SECTIONS:
                if section not in ("assessment", "plan"):
                    existing_val = current_body.get(section, "")
                    existing_text = (
                        existing_val.get("text", "") if isinstance(existing_val, dict)
                        else existing_val
                    )
                    original_ai = existing_val.get("original_ai_text", "") if isinstance(existing_val, dict) else ""
                    if not existing_text or existing_text.strip() == original_ai.strip() or existing_note.status == "draft":
                        current_body[section] = structured_sections[section]
                elif section not in current_body:
                    current_body[section] = {"text": "", "original_ai_text": None, "status": "draft"}
            current_body["_meta"] = structured_sections["_meta"]
            existing_note.body = current_body
            existing_note.is_ai_generated = True
            existing_note.version += 1
            note = existing_note
        else:
            tenant_id = db.info.get("tenant_id") or (consultation.tenant_id if consultation else None)
            note = ClinicalNote(
                tenant_id=tenant_id,
                consultation_id=consultation_id,
                author_id=doctor_id,
                note_type="progress",
                body=structured_sections,
                status="draft",
                is_ai_generated=True,
                last_edited_by_id=None,
            )
            db.add(note)

        await db.commit()
        await db.refresh(note)

        # Generate embedding for the new note
        try:
            body = note.body or {}
            text_parts = []
            for k, v in body.items():
                if k.startswith("_"):
                    continue
                text = v.get("text", "") if isinstance(v, dict) else str(v)
                if text:
                    text_parts.append(f"{k.upper().replace('_',' ')}: {text}")
            note_content = "\n\n".join(text_parts)
            if note_content.strip():
                await generate_and_store_embedding(
                    db,
                    source_record_id=str(consultation_id),
                    source_record_type="clinical_note",
                    content=note_content,
                )
        except Exception as e:
            log.error("note_embedding_failed", error=str(e))

        return note

    def _fallback_draft(
        self,
        findings: List[ClinicalFinding],
        raw_text: str,
        vitals: str,
        travel: str,
    ) -> Dict[str, str]:
        """Deterministic fallback when LLM is unavailable, enriched by neuro-symbolic clinical engines."""
        sections = {s: "" for s in SECTIONS}

        hpi_parts, pmh_parts, meds_parts, allergy_parts, ddx_parts = [], [], [], [], []

        if raw_text:
            try:
                from app.services.clinical_note_parser import clinical_note_parser
                from app.services.realtime_prediction_service import realtime_prediction_service

                parsed = clinical_note_parser.parse(raw_text)
                sec_map = parsed.get("section_breakdown", {})
                if sec_map:
                    if sec_map.get("CHIEF_COMPLAINT_AND_HPI"):
                        sections["hpi"] = sec_map["CHIEF_COMPLAINT_AND_HPI"].strip()
                    if sec_map.get("PAST_MEDICAL_HISTORY"):
                        sections["past_medical_history"] = sec_map["PAST_MEDICAL_HISTORY"].strip()
                    if sec_map.get("PHYSICAL_EXAM"):
                        sections["physical_examination"] = sec_map["PHYSICAL_EXAM"].strip()
                    if sec_map.get("LABS_AND_DIAGNOSTICS"):
                        sections["investigations"] = sec_map["LABS_AND_DIAGNOSTICS"].strip()
                    if sec_map.get("MEDICATIONS_AND_EXPOSURES"):
                        sections["medications"] = sec_map["MEDICATIONS_AND_EXPOSURES"].strip()

                # Calculated indices & labs into investigations
                calc = parsed.get("calculated_indices", {})
                qlabs = parsed.get("quantitative_labs", {})
                lab_lines = []
                if calc.get("anion_gap") is not None:
                    lab_lines.append(f"Serum Anion Gap: {calc['anion_gap']} mEq/L ({calc.get('anion_gap_interpretation', 'evaluated')})")
                if calc.get("bun_cr_ratio") is not None:
                    lab_lines.append(f"BUN/Cr Ratio: {calc['bun_cr_ratio']} ({calc.get('azotemia_type', 'evaluated')})")
                if calc.get("csf_serum_glucose_ratio") is not None:
                    lab_lines.append(f"CSF/Serum Glucose Ratio: {calc['csf_serum_glucose_ratio']} ({calc.get('csf_interpretation', 'evaluated')})")
                for k, v in qlabs.items():
                    lab_lines.append(f"{k.replace('_', ' ').title()}: {v.get('value')} {v.get('unit')} [{v.get('flag', 'normal')}]")
                if lab_lines:
                    current_inv = sections.get("investigations", "")
                    sections["investigations"] = (current_inv + "\n\n" if current_inv else "") + "\n".join(lab_lines)

                # Real-time top differentials
                preds = realtime_prediction_service.predict(symptoms=raw_text, top_k=3)
                top_cands = preds.get("top_candidates", [])
                if top_cands:
                    ddx_lines = [f"{i+1}. {c['disease']} ({c['display_score']}) - {c.get('uncertainty', '')}" for i, c in enumerate(top_cands)]
                    diff_rec = preds.get("differentiating_recommendation")
                    if diff_rec:
                        ddx_lines.append(f"\nNext Best Test: {diff_rec['differentiating_investigation']} (Urgency: {diff_rec['urgency']})")
                    sections["differential_diagnosis"] = "\n".join(ddx_lines)
            except Exception as pe:
                log.warning("note_generator_parser_enrichment_failed", error=str(pe))

        if not sections.get("hpi") and raw_text:
            hpi_parts.append(raw_text.strip())

        for f in findings:
            val = f.canonical_concept or f.value
            suffix = " (negated)" if f.negated else ""
            if f.temporality == "past":
                pmh_parts.append(f"{val}{suffix}")
            elif f.concept == "MEDICATION":
                meds_parts.append(f"{val}{suffix}")
            elif f.concept == "ALLERGY":
                allergy_parts.append(f"{val}{suffix}")
            elif f.concept == "CONDITION":
                ddx_parts.append(f"{val}")
            else:
                if not raw_text:
                    hpi_parts.append(f"{val}{suffix}")

        if not sections.get("hpi"):
            sections["hpi"] = "\n\n".join(hpi_parts) if hpi_parts else "See raw notes."
        if not sections.get("vitals"):
            sections["vitals"] = vitals
        if not sections.get("past_medical_history") and pmh_parts:
            sections["past_medical_history"] = "\n".join(f"{i+1}. {v}" for i, v in enumerate(pmh_parts))
        if not sections.get("medications") and meds_parts:
            sections["medications"] = "\n".join(f"{i+1}. {v}" for i, v in enumerate(meds_parts))
        if not sections.get("allergies") and allergy_parts:
            sections["allergies"] = "\n".join(allergy_parts)
        if not sections.get("social_history") and travel:
            sections["social_history"] = travel
        if not sections.get("differential_diagnosis") and ddx_parts:
            sections["differential_diagnosis"] = "\n".join(f"{i+1}. {v}" for i, v in enumerate(ddx_parts[:4]))
        sections["safety_net"] = "Return immediately if: symptoms worsen, new concerning symptoms develop, fever spikes, or unable to tolerate oral medications."

        return sections


note_generator_service = NoteGeneratorService()
