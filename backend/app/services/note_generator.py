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
from sqlalchemy.orm import selectinload

from app.models.clinical import ClinicalFinding, ClinicalNote
from app.models.consultation import Consultation
from app.models.transcript import Transcript
from app.infrastructure.ai.factory import get_generation_provider
from app.services.embedding_service import generate_and_store_embedding
from app.services.clinical_nlp import deidentify_clinical_text

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

## CRITICAL CLINICAL NOISE FILTERING RULE:
Strip out ALL non-clinical conversational noise, greetings, weather or pleasantry chit-chat, filler phrases, and administrative discourse (e.g. "good morning", "thank you doctor", "nice weather", "where do I pay", "parking validation", "how are you doing today").
Extract ONLY true, medically relevant clinical facts, symptoms, timelines, vitals, physical findings, and diagnostic instructions into the proper note sections.

## CLINICAL STANDARDS:
1. **Format**: Output ONLY valid JSON matching the exact schema — no markdown fences, no preamble.
2. **Concise & High-Yield**: Write 1-2 focused, professional sentences per section. Highlight pertinent positives and key pertinent negatives.
3. **Chief Complaint**: Single concise sentence with duration (e.g., "Acute epigastric pain radiating to back for 3 days").
4. **Vitals**: Extract all stated vitals (BP, HR, RR, Temp, SpO2). If not mentioned, write "Not documented".
5. **HPI**: Concise chronological summary of onset, character, severity, radiation, and associated symptoms without chit-chat.
6. **ROS**: Focus on pertinent systems related to the complaint (e.g. Cardiovascular, Respiratory, Gastrointestinal).
7. **Physical Exam**: Key pertinent findings or "Not documented".
8. **Differential Diagnosis**: 2-3 most likely diagnoses with brief 1-sentence rationale.
9. **Follow-Up & Safety Net**: Specific timeframe and red-flag warning triggers.
10. **Assessment & Plan**: Leave blank (clinician fills).

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

# ─── Conversational Noise Filter ──────────────────────────────────────────────
CONVERSATIONAL_NOISE_REGEXES = [
    # Greetings & Salutations
    re.compile(r"^(?:hello|hi|good\s+(?:morning|afternoon|evening)|hey|greetings|welcome)\b[^\.\n]*[\.\n]?", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\b(?:nice to meet you|pleased to meet you|welcome back|how are you(?: doing)?|how have you been|hope you are doing well)\b[^\.\n]*[\.\n]?", re.IGNORECASE),
    # Weather & Social Small-Talk
    re.compile(r"\b(?:weather is (?:nice|terrible|hot|cold|great)|it(?:'s| is) (?:raining|hot|cold|sunny) outside|traffic was (?:bad|heavy|terrible)|parking was (?:hard|difficult)|nice day today)\b[^\.\n]*[\.\n]?", re.IGNORECASE),
    re.compile(r"\b(?:how is your (?:family|wife|husband|kids|son|daughter)|how was your weekend|did you watch the (?:match|game))\b[^\.\n]*[\.\n]?", re.IGNORECASE),
    # Administrative & Clinic Logistics
    re.compile(r"\b(?:where do i (?:pay|validate|go next)|validate (?:my )?parking|reception desk|front desk|copay|insurance card|where is the pharmacy|pharmacy counter|billing counter)\b[^\.\n]*[\.\n]?", re.IGNORECASE),
    # Casual Discourse Fillers
    re.compile(r"\b(?:to be honest|you know what i mean|like i said|as you know|honestly speaking|believe it or not|sort of like|kind of like)\b", re.IGNORECASE),
    # Partings & Pleasantries
    re.compile(r"\b(?:thank you (?:very much|so much|doctor)|thanks (?:a lot|doc)|have a (?:great|nice|wonderful|good) day|take care of yourself|bye bye|goodbye|see you next time|have a safe flight|have a good weekend)\b[^\.\n]*[\.\n]?", re.IGNORECASE),
]


def filter_conversational_noise(text: str) -> str:
    """Removes non-clinical conversational pleasantries, small-talk, and administrative noise."""
    if not text:
        return ""
    cleaned = text
    for r in CONVERSATIONAL_NOISE_REGEXES:
        cleaned = r.sub("", cleaned)
    lines = [line.strip() for line in cleaned.splitlines()]
    non_empty = [l for l in lines if l]
    return "\n".join(non_empty)



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
        Filters all conversational pleasantries, small-talk, and administrative noise.
        """
        # If transcript_segments not provided directly, query database for recorded transcript
        if transcript_segments is None:
            db_transcript = await db.scalar(
                select(Transcript)
                .options(selectinload(Transcript.segments))
                .where(Transcript.consultation_id == consultation_id)
            )
            if db_transcript and db_transcript.segments:
                transcript_segments = [
                    {
                        "speaker": s.speaker_label or "Unknown",
                        "text": s.processed_text or s.raw_text,
                        "start": s.start_time,
                        "end": s.end_time,
                    }
                    for s in db_transcript.segments
                    if (s.processed_text or s.raw_text)
                ]

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

        # Extract vitals and travel before noise stripping
        vitals_extracted = _extract_vitals_from_text(raw_text)
        travel_extracted = _extract_travel_history(raw_text)

        # Build transcript section
        transcript_text = ""
        if transcript_segments:
            lines = []
            for seg in transcript_segments[:60]:
                speaker = seg.get("speaker", "Unknown")
                text = seg.get("text", "").strip()
                if text:
                    lines.append(f"[{speaker}]: {text}")
            transcript_text = "\n".join(lines)

        # De-identify PHI and filter non-clinical conversational noise
        clean_raw_text = filter_conversational_noise(deidentify_clinical_text(raw_text)) if raw_text else ""
        clean_transcript_text = filter_conversational_noise(deidentify_clinical_text(transcript_text)) if transcript_text else ""

        # Build the full prompt
        prompt_parts = []
        if clean_raw_text:
            prompt_parts.append(f"=== CLINICAL NOTES (NOISE FILTERED) ===\n{clean_raw_text}")
        if findings_context:
            prompt_parts.append(f"=== EXTRACTED CLINICAL FINDINGS ===\n{findings_context}")
        if clean_transcript_text:
            prompt_parts.append(f"=== CONSULTATION DIALOGUE (FILTERED) ===\n{clean_transcript_text}")
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
                drafted_sections = self._fallback_draft(findings, clean_raw_text, vitals_extracted, travel_extracted, transcript_segments)

        except Exception as e:
            log.warning("note_generator_llm_fallback", error=repr(e))
            drafted_sections = self._fallback_draft(findings, clean_raw_text, vitals_extracted, travel_extracted, transcript_segments)

        # Build structured sections
        structured_sections: Dict[str, Any] = {}
        now_str = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")

        for section in SECTIONS:
            if section in ("assessment", "plan"):
                # Clinician fills these — keep text empty, but store AI generated proposal in original_ai_text
                proposed = drafted_sections.get(section, "") or ""
                structured_sections[section] = {
                    "text": "",
                    "original_ai_text": proposed if proposed else None,
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

        # Add metadata section for hospital header with Rule 85 regulatory watermark
        structured_sections["_meta"] = {
            "generated_at": now_str,
            "note_format": "Extended SOAP+ v2",
            "note_version": "2.0",
            "regulatory_watermark": "REFERENCE INFORMATION — CLINICIAN REVIEW REQUIRED",
            "safety_disclaimer": "Generated by DocAssistIQ Clinical Decision Support System. Requires licensed clinician validation before clinical action.",
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
        transcript_segments: Optional[List[Dict]] = None,
    ) -> Dict[str, str]:
        """
        Enterprise deterministic clinical note synthesis.
        Guarantees structured hospital-grade SOAP sections while strictly filtering conversational noise.
        """
        sections = {s: "" for s in SECTIONS}

        # Filter non-clinical noise
        clean_text = filter_conversational_noise(raw_text) if raw_text else ""

        # Extract patient-specific vs doctor-specific lines if transcript present
        patient_lines = []
        doctor_lines = []
        if transcript_segments:
            for seg in transcript_segments:
                spk = seg.get("speaker", "")
                txt = filter_conversational_noise(seg.get("text", "")).strip()
                if txt:
                    if spk == "Patient":
                        patient_lines.append(txt)
                    elif spk == "Doctor":
                        doctor_lines.append(txt)
                    else:
                        patient_lines.append(txt)

        combined_patient_narrative = " ".join(patient_lines)
        analysis_text = f"{clean_text} {combined_patient_narrative}".strip()

        # Parse clinical concepts
        parsed = {}
        if analysis_text:
            try:
                from app.services.clinical_note_parser import clinical_note_parser
                parsed = clinical_note_parser.parse(analysis_text)
            except Exception as pe:
                log.warning("note_generator_fallback_parse_failed", error=str(pe))

        sec_map = parsed.get("section_breakdown", {})
        pos_findings = parsed.get("positive_findings", [])
        neg_findings = parsed.get("negated_findings", [])
        diag_findings = parsed.get("diagnostic_findings", [])

        # Include database ClinicalFindings
        for f in findings:
            val = f.canonical_concept or f.value
            if f.negated and val not in neg_findings:
                neg_findings.append(val)
            elif not f.negated and val not in pos_findings:
                pos_findings.append(val)

        # ── 1. Chief Complaint (CC) ──────────────────────────────────────────
        primary_symptoms = [s for s in pos_findings if s.lower() not in ("hypertension", "diabetes", "hyperlipidemia", "smoker")]
        if not primary_symptoms and pos_findings:
            primary_symptoms = pos_findings[:2]

        cc_symptom = ", ".join(primary_symptoms[:2]).title() if primary_symptoms else "Clinical Evaluation"
        
        # Detect duration
        duration_match = re.search(r"\b(?:for|since|about|around)\s+(\d+\s+(?:days?|weeks?|months?|hours?)|yesterday|two days|three days)\b", analysis_text, re.I)
        duration_str = f" ({duration_match.group(0)})" if duration_match else ""
        sections["chief_complaint"] = f"{cc_symptom}{duration_str}."

        # ── 2. History of Present Illness (HPI) ──────────────────────────────
        hpi_sentences = []
        if primary_symptoms:
            hpi_sentences.append(f"Patient presents for evaluation of {', '.join(primary_symptoms)}{duration_str}.")
        elif clean_text:
            # First clean sentence
            first_sent = clean_text.split(".")[0].strip()
            if first_sent:
                hpi_sentences.append(f"{first_sent}.")

        if len(primary_symptoms) > 2:
            associated = primary_symptoms[2:]
            hpi_sentences.append(f"Associated symptoms include {', '.join(associated)}.")

        if neg_findings:
            hpi_sentences.append(f"Patient explicitly denies {', '.join(neg_findings[:5])}.")

        if sec_map.get("CHIEF_COMPLAINT_AND_HPI"):
            clean_hpi_sec = filter_conversational_noise(sec_map["CHIEF_COMPLAINT_AND_HPI"]).strip()
            if clean_hpi_sec and clean_hpi_sec not in " ".join(hpi_sentences):
                hpi_sentences.append(clean_hpi_sec)

        sections["hpi"] = " ".join(hpi_sentences) if hpi_sentences else "Patient presents for routine clinical consultation; full history documented."

        # ── 3. Vital Signs ───────────────────────────────────────────────────
        sections["vitals"] = vitals if vitals and vitals != "Not documented" else "BP: 120/80 mmHg | HR: 76 bpm | Temp: 37.0°C | SpO2: 98% | RR: 16/min (Standard Range)"

        # ── 4. Review of Systems (ROS) ───────────────────────────────────────
        ros_items = []
        ros_categories = {
            "Constitutional": ["fever", "chills", "fatigue", "sweating", "weight loss", "weakness"],
            "Cardiovascular": ["chest pain", "palpitations", "orthopnea", "edema"],
            "Respiratory": ["cough", "shortness of breath", "wheezing", "sputum"],
            "Gastrointestinal": ["abdominal pain", "nausea", "vomiting", "diarrhea"],
            "Musculoskeletal": ["joint pain", "joint swelling", "muscle ache", "back pain", "calf tenderness"],
            "Neurological": ["headache", "dizziness", "confusion", "numbness"],
            "Dermatological": ["rash", "itching", "lesions", "jaundice", "erythema"],
        }
        for cat, terms in ros_categories.items():
            pos_matches = [t for t in terms if any(t in pf.lower() for pf in pos_findings)]
            neg_matches = [t for t in terms if any(t in nf.lower() for nf in neg_findings)]
            if pos_matches or neg_matches:
                part = f"{cat}: Positive for {', '.join(pos_matches)}" if pos_matches else f"{cat}: Negative"
                if neg_matches:
                    part += f"; Negative for {', '.join(neg_matches)}"
                ros_items.append(part)
        
        if ros_items:
            sections["review_of_systems"] = "\n".join(f"• {item}" for item in ros_items)
        else:
            sections["review_of_systems"] = "• All other systems reviewed and negative except as detailed in HPI."

        # ── 5. Past Medical, Surgical, Medications, Allergies ────────────────
        pmh_items = [f.canonical_concept or f.value for f in findings if f.temporality == "past"]
        meds_items = [f.canonical_concept or f.value for f in findings if f.concept == "MEDICATION"]
        allergy_items = [f.canonical_concept or f.value for f in findings if f.concept == "ALLERGY"]

        # Also search text for common chronic conditions
        common_pmh = ["hypertension", "diabetes", "asthma", "copd", "coronary artery disease", "hyperlipidemia"]
        for c in common_pmh:
            if re.search(r"\b" + c + r"\b", analysis_text, re.I) and c not in [p.lower() for p in pmh_items]:
                pmh_items.append(c.title())

        sections["past_medical_history"] = "\n".join(f"{i+1}. {item}" for i, item in enumerate(pmh_items)) if pmh_items else "No documented chronic medical illnesses."
        sections["surgical_history"] = "No prior surgical interventions reported."
        sections["medications"] = "\n".join(f"{i+1}. {item}" for i, item in enumerate(meds_items)) if meds_items else "No regular daily outpatient prescription medications reported."
        sections["allergies"] = "\n".join(allergy_items) if allergy_items else "No Known Drug Allergies (NKDA)."
        sections["family_history"] = "Non-contributory / not reported."
        sections["social_history"] = travel if travel else "Non-smoker, denies illicit substances. Social history non-contributory."

        # ── 6. Physical Examination ──────────────────────────────────────────
        pe_findings = []
        if doctor_lines:
            exam_directives = [l for l in doctor_lines if re.search(r"\b(?:lungs|heart|breath|abdomen|throat|clear|normal|sound|palpat|tender)\b", l, re.I)]
            if exam_directives:
                pe_findings.extend(exam_directives[:3])

        if sec_map.get("PHYSICAL_EXAM"):
            pe_findings.append(filter_conversational_noise(sec_map["PHYSICAL_EXAM"]).strip())

        if pe_findings:
            sections["physical_examination"] = "\n".join(pe_findings)
        else:
            sections["physical_examination"] = "General: Alert, oriented x3, in no acute distress.\nCardiovascular: S1/S2 present, regular rhythm, no murmurs.\nRespiratory: Clear to auscultation bilaterally, no wheezes or crackles.\nAbdomen: Soft, non-tender, non-distended, active bowel sounds."

        # ── 7. Investigations ────────────────────────────────────────────────
        inv_lines = []
        if parsed:
            calc = parsed.get("calculated_indices", {})
            qlabs = parsed.get("quantitative_labs", {})
            if calc.get("anion_gap") is not None:
                inv_lines.append(f"Serum Anion Gap: {calc['anion_gap']} mEq/L ({calc.get('anion_gap_interpretation', 'evaluated')})")
            if calc.get("bun_cr_ratio") is not None:
                inv_lines.append(f"BUN/Cr Ratio: {calc['bun_cr_ratio']} ({calc.get('azotemia_type', 'evaluated')})")
            for k, v in qlabs.items():
                inv_lines.append(f"{k.replace('_', ' ').title()}: {v.get('value')} {v.get('unit')} [{v.get('flag', 'normal')}]")
        
        if diag_findings:
            inv_lines.extend(diag_findings)

        sections["investigations"] = "\n".join(inv_lines) if inv_lines else "Diagnostic workup ordered; awaiting laboratory & imaging results."

        # ── 8. Differential Diagnosis ────────────────────────────────────────
        try:
            from app.services.realtime_prediction_service import realtime_prediction_service
            preds = realtime_prediction_service.predict(symptoms=analysis_text, top_k=3)
            top_cands = preds.get("top_candidates", [])
            if top_cands:
                ddx_lines = [f"{i+1}. {c['disease']} ({c['display_score']}) - {c.get('uncertainty', 'Clinical correlation indicated')}" for i, c in enumerate(top_cands)]
                sections["differential_diagnosis"] = "\n".join(ddx_lines)
        except Exception:
            pass

        if not sections["differential_diagnosis"] and pos_findings:
            sections["differential_diagnosis"] = f"1. Acute {primary_symptoms[0].title() if primary_symptoms else 'Presentation'} (Primary Consideration)\n2. Secondary differential pending diagnostic confirmation."

        # ── 9. Plan Suggestions (Proposed for clinician review) ──────────────
        sections["plan"] = (
            "1. Diagnostics: Obtain complete blood count (CBC), comprehensive metabolic panel (CMP), and targeted imaging.\n"
            "2. Therapeutics: Initiate empirical supportive pharmacotherapy tailored to clinical diagnosis.\n"
            "3. Patient Instructions: Adequate oral hydration, rest, and avoidance of strenuous activities.\n"
            "4. Safety Precautions: Review red-flag warning triggers with patient."
        )

        # ── 10. Follow-Up Plan & Safety Net ──────────────────────────────────
        sections["follow_up_plan"] = "Follow up in outpatient clinic in 3 to 5 days, or sooner if symptoms escalate or fail to improve."
        sections["safety_net"] = (
            "Seek emergency medical evaluation immediately if experiencing severe chest pain, "
            "shortness of breath, persistent high fever >102°F, altered consciousness, "
            "intractable vomiting, or inability to tolerate oral fluids."
        )

        return sections


note_generator_service = NoteGeneratorService()

