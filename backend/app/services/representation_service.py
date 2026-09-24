"""DocAssistIQ — Enhanced Representation Service v2.

Extracts clinical representation from ALL data sources:
  1. ManualIntake (structured form fields)
  2. ClinicalFinding records (AI-suggested or confirmed)
  3. ClinicalNote.body (JSON sections — doctor notes, now included!)
  4. Free-text symptom extraction via regex NLP (no LLM needed)

This fixes the core issue: doctor notes were never parsed into
the clinical representation, causing differential diagnosis to
return INSUFFICIENT_INFO even when notes had clinical data.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical import ClinicalFinding, ClinicalNote, ManualIntake
from app.models.consultation import Consultation
from app.schemas.representation import (
    ClinicalRepresentationResponse,
    PatientContext,
    Provenance,
    RepresentationItem,
)

# ─────────────────────────────────────────────────────────────────────────────
# Fast regex-based NLP extractor (no LLM needed, instant)
# Handles doctor notes, SOAP notes, free text
# ─────────────────────────────────────────────────────────────────────────────

SYMPTOM_PATTERNS = [
    # Chief complaint patterns
    r"(?:c/o|complains? of|presenting with|presents with|c\.c\.?:?)\s*([^.;\n]{3,80})",
    r"(?:chief complaint|chief c/o|main complaint):\s*([^.;\n]{3,80})",
    # Symptom list patterns
    r"(?:symptoms?|features?|s/s):\s*([^.;\n]{3,100})",
    # SOAP: Subjective section
    r"(?:subjective|s:)\s*([^.;\n]{3,100})",
    # Direct symptom mentions (highly specific medical terms)
    r"\b(fever|cough|dyspnoea|shortness of breath|SOB|chest pain|headache|nausea|vomiting|"
    r"diarrhoea|diarrhea|abdominal pain|fatigue|malaise|rigors|chills|sweats|night sweats|"
    r"haemoptysis|haematuria|rash|jaundice|oedema|swelling|myalgia|arthralgia|sore throat|"
    r"rhinorrhoea|weight loss|loss of appetite|anorexia|palpitations|syncope|dizziness|"
    r"confusion|altered consciousness|seizures|weakness|paraesthesia|back pain|neck stiffness|"
    r"photophobia|phonophobia|dysuria|polyuria|polydipsia|polyphagia|blurred vision|"
    r"bleeding|bruising|petechiae|purpura|haemorrhage)\b",
]

DURATION_PATTERNS = [
    r"(?:duration|for|since|x)\s+(\d+\s*(?:day|week|month|year|hour|hr)s?)",
    r"(\d+\s*(?:day|week|month|year|hour|hr)s?\s*(?:duration|ago|history|h/o)?)",
    r"(?:onset|started|began)\s+(\d+\s*(?:day|week|month|year|hour|hr)s?\s*ago)",
]

SEVERITY_PATTERNS = [
    r"(?:severity|severity:|grade|vas|pain score)\s*:?\s*(\d+/\d+|\w+)",
    r"\b(mild|moderate|severe|critical|extreme|significant|minimal)\b",
    r"(?:pain\s*(?:score|rating)?)\s*:?\s*(\d+\s*/\s*10)",
]

NEGATION_PATTERNS = [
    r"(?:no|denies?|negative for|without|absent|not|never)\s+([a-z][a-z\s]{2,30}?)(?:\s*[.,;]|$)",
]

VITAL_PATTERNS = [
    r"(?:BP|blood pressure)[\s:]*(\d{2,3}\s*/\s*\d{2,3})\s*(?:mmHg)?",
    r"(?:HR|heart rate|pulse)[\s:]*(\d{2,3})\s*(?:bpm|/min)?",
    r"(?:RR|respiratory rate)[\s:]*(\d{1,2})\s*(?:/min|breaths?)?",
    r"(?:temp|temperature|T°?)[\s:]*(\d{2}(?:\.\d)?)\s*°?[CF]?",
    r"(?:SpO2|O2 sat|oxygen sat(?:uration)?)[\s:]*(\d{2,3})\s*%?",
    r"(?:GCS)[\s:]*(\d{1,2}(?:/\d{1,2})?)",
    r"(?:weight|wt)[\s:]*(\d{2,3}(?:\.\d)?)\s*(?:kg|lb)?",
]

TRAVEL_PATTERNS = [
    r"(?:travel(?:led|led to|history|h/o)|returned from|visited|trip to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"(?:from|in)\s+(India|Pakistan|Bangladesh|Nepal|Sri Lanka|Africa|Nigeria|Kenya|DRC|Congo|"
    r"Ghana|Ethiopia|Sudan|Somalia|Uganda|Tanzania|Malawi|Zambia|Zimbabwe|Mozambique|Angola|"
    r"Thailand|Vietnam|Cambodia|Myanmar|Indonesia|Malaysia|Philippines|China|"
    r"Brazil|Colombia|Peru|Bolivia|Ecuador|Venezuela|Mexico)",
]

HISTORY_PATTERNS = [
    r"(?:PMH|past medical history|known case of|k/c/o|background|comorbidities?):\s*([^.;\n]{5,100})",
    r"(?:h/o|history of)\s+([a-z][a-z\s]{3,50}?)(?:\s*[.,;]|$)",
]

MEDICATION_PATTERNS = [
    r"(?:medications?|drugs?|currently on|on treatment|Rx):\s*([^.;\n]{3,100})",
    r"(?:taking|prescribed|treatment with)\s+([A-Z][a-z]+(?:\s+\d+\s*mg)?)",
]

SHORTHAND_MAP = {
    r"\bc/o\b": "complains of",
    r"\bh/o\b": "history of",
    r"\bk/c/o\b": "known case of",
    r"\bSOB\b": "shortness of breath",
    r"\bDOE\b": "dyspnea on exertion",
    r"\bCP\b": "chest pain",
    r"\bHA\b": "headache",
    r"\bN/V\b": "nausea vomiting",
    r"\bN&V\b": "nausea and vomiting",
    r"\bHx\b": "history",
    r"\bRx\b": "treatment",
    r"\bDx\b": "diagnosis",
    r"\bIx\b": "investigations",
    r"\bFHx\b": "family history",
    r"\bSHx\b": "social history",
    r"\bPMH\b": "past medical history",
    r"\bO/E\b": "on examination",
    r"\bPt\b": "patient",
    r"\bBP\b": "blood pressure",
    r"\bHR\b": "heart rate",
    r"\bRR\b": "respiratory rate",
    r"\bSPO2\b": "oxygen saturation",
    r"\bTB\b": "tuberculosis",
    r"\bHTN\b": "hypertension",
    r"\bDM\b": "diabetes mellitus",
    r"\bT2DM\b": "type 2 diabetes mellitus",
    r"\bCOPD\b": "chronic obstructive pulmonary disease",
    r"\bMI\b": "myocardial infarction",
    r"\bPE\b": "pulmonary embolism",
    r"\bDVT\b": "deep vein thrombosis",
    r"\bCVA\b": "cerebrovascular accident",
    r"\bAKI\b": "acute kidney injury",
    r"\bDKA\b": "diabetic ketoacidosis",
    r"\bUTI\b": "urinary tract infection",
    r"\bURTI\b": "upper respiratory tract infection",
}


def _expand_shorthands(text: str) -> str:
    """Expand medical abbreviations in text."""
    for pattern, replacement in SHORTHAND_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _extract_from_text(text: str) -> dict:
    """
    Fast regex NLP extraction from free text.
    Returns dict with lists of: symptoms, duration, severity, negations, vitals, travel, history, medications.
    """
    if not text or len(text.strip()) < 3:
        return {}

    text = _expand_shorthands(text)
    text_lower = text.lower()

    results = {
        "symptoms": [],
        "duration": [],
        "severity": [],
        "negations": [],
        "vitals": [],
        "travel": [],
        "history": [],
        "medications": [],
    }

    # ── Symptoms ──────────────────────────────────────────────────────────
    # First, extract from chief complaint / symptom sentences
    for pat in SYMPTOM_PATTERNS[:4]:  # complex patterns
        for m in re.finditer(pat, text, re.IGNORECASE):
            items = [s.strip() for s in re.split(r"[,;/]|\band\b", m.group(1)) if s.strip()]
            for item in items:
                if 3 < len(item) < 60 and not item.isdigit():
                    results["symptoms"].append(item.lower().strip())

    # Direct medical term matching
    for m in re.finditer(SYMPTOM_PATTERNS[4], text, re.IGNORECASE):
        sym = m.group(1).lower().strip()
        if sym not in results["symptoms"]:
            results["symptoms"].append(sym)

    # ── Duration ──────────────────────────────────────────────────────────
    for pat in DURATION_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            d = m.group(1).strip().lower()
            if d and d not in results["duration"]:
                results["duration"].append(d)

    # ── Severity ──────────────────────────────────────────────────────────
    for pat in SEVERITY_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            s = m.group(1).strip().lower()
            if s and s not in results["severity"]:
                results["severity"].append(s)

    # ── Negations ─────────────────────────────────────────────────────────
    for pat in NEGATION_PATTERNS:
        for m in re.finditer(pat, text_lower):
            neg = m.group(1).strip()
            if neg and len(neg) > 2 and neg not in results["negations"]:
                results["negations"].append(neg)

    # ── Vitals ────────────────────────────────────────────────────────────
    for pat in VITAL_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            label = pat.split("(")[0].strip("(?:")
            label = re.sub(r"\\b|\\s|[\[\]\(\)\?]", "", label).split("|")[0][:15].strip()
            val = f"{label}: {m.group(1)}"
            if val not in results["vitals"]:
                results["vitals"].append(val)

    # ── Travel ────────────────────────────────────────────────────────────
    for pat in TRAVEL_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            loc = m.group(1).strip()
            if loc and loc not in results["travel"]:
                results["travel"].append(loc)

    # ── History ───────────────────────────────────────────────────────────
    for pat in HISTORY_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            items = [s.strip() for s in re.split(r"[,;]|\band\b", m.group(1)) if s.strip()]
            for item in items:
                if 3 < len(item) < 80:
                    results["history"].append(item.lower().strip())

    # ── Medications ───────────────────────────────────────────────────────
    for pat in MEDICATION_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            items = [s.strip() for s in re.split(r"[,;]|\band\b", m.group(1)) if s.strip()]
            for item in items:
                if 2 < len(item) < 60:
                    results["medications"].append(item.strip())

    # Deduplicate each list
    for k in results:
        seen = set()
        deduped = []
        for v in results[k]:
            if v.lower() not in seen:
                seen.add(v.lower())
                deduped.append(v)
        results[k] = deduped

    return results


def _extract_text_from_note_body(body: dict) -> str:
    """
    Extract all text content from a ClinicalNote.body JSON structure.
    Supports various SOAP and structured formats.
    """
    if not body:
        return ""

    texts = []

    # Handle dict body (common format)
    if isinstance(body, dict):
        for key, value in body.items():
            if isinstance(value, str) and value.strip():
                texts.append(f"{key}: {value}")
            elif isinstance(value, dict):
                for k2, v2 in value.items():
                    if isinstance(v2, str) and v2.strip():
                        texts.append(f"{k2}: {v2}")
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.strip():
                        texts.append(item)
                    elif isinstance(item, dict):
                        for k2, v2 in item.items():
                            if isinstance(v2, str) and v2.strip():
                                texts.append(f"{k2}: {v2}")

    elif isinstance(body, str):
        texts.append(body)
    elif isinstance(body, list):
        for item in body:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict):
                for k, v in item.items():
                    if isinstance(v, str):
                        texts.append(f"{k}: {v}")

    return "\n".join(texts)


async def build_clinical_representation(
    db: AsyncSession, consultation_id: uuid.UUID
) -> ClinicalRepresentationResponse:
    """
    Build a complete clinical representation from ALL available data sources.
    
    Sources (in order of priority):
    1. ManualIntake — structured intake form
    2. ClinicalFinding — confirmed/AI-suggested findings
    3. ClinicalNote.body — doctor notes (NOW INCLUDED via regex NLP)
    """
    # 1. Fetch all data sources in parallel
    consultation_res = await db.execute(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    consultation = consultation_res.scalar_one_or_none()

    intake_res = await db.execute(
        select(ManualIntake).where(ManualIntake.consultation_id == consultation_id)
    )
    intake = intake_res.scalar_one_or_none()

    findings_res = await db.execute(
        select(ClinicalFinding).where(ClinicalFinding.consultation_id == consultation_id)
    )
    findings = findings_res.scalars().all()

    notes_res = await db.execute(
        select(ClinicalNote).where(
            ClinicalNote.consultation_id == consultation_id,
            ClinicalNote.status.in_(["final", "draft"]),
        ).order_by(ClinicalNote.created_at.desc())
    )
    notes = notes_res.scalars().all()

    # Initialize output structure
    rep = ClinicalRepresentationResponse(  # type: ignore
        consultation_id=consultation_id,
        generated_at=datetime.now(timezone.utc),
        patient_context=PatientContext(),
    )

    def add_item(
        target_list: List[RepresentationItem],
        value: str,
        concept: str | None,
        status: str | None,
        provenance: Provenance,
    ):
        if not value:
            return
        value = value.strip()
        if not value or len(value) < 2:
            return
        for item in target_list:
            if item.value.lower() == value.lower():
                if not any(p.source_id == provenance.source_id for p in item.provenances):
                    item.provenances.append(provenance)
                return
        target_list.append(
            RepresentationItem(value=value, concept=concept, status=status, provenances=[provenance])
        )

    # ── 2. Process Manual Intake ──────────────────────────────────────────
    if intake:
        prov = Provenance(
            source_type="manual_intake",
            source_id=str(intake.id),
            timestamp=intake.updated_at or intake.created_at,
            author_id=str(intake.doctor_id),
        )
        if intake.chief_complaint:
            add_item(rep.symptoms, intake.chief_complaint, "chief_complaint", "confirmed", prov)
            # Also extract sub-items from chief complaint
            extracted = _extract_from_text(intake.chief_complaint)
            for s in extracted["symptoms"]:
                add_item(rep.symptoms, s, "symptom", "confirmed", prov)
            try:
                from app.services.clinical_note_parser import clinical_note_parser
                parsed_cc = clinical_note_parser.parse(intake.chief_complaint)
                for f in parsed_cc.get("positive_findings", []):
                    add_item(rep.symptoms, f, "symptom", "confirmed", prov)
                for df in parsed_cc.get("diagnostic_findings", []):
                    add_item(rep.symptoms, df, "diagnostic_marker", "confirmed", prov)
                for nf in parsed_cc.get("negated_findings", []):
                    add_item(rep.negations, nf, "negation", "negated", prov)
            except Exception:
                pass
        if intake.symptoms:
            for s in intake.symptoms.split(","):
                add_item(rep.symptoms, s.strip(), "symptom", "confirmed", prov)
        if intake.duration:
            add_item(rep.duration, intake.duration, "duration", "confirmed", prov)
        if intake.severity:
            add_item(rep.severity, intake.severity, "severity", "confirmed", prov)
        if intake.negations:
            for n in intake.negations.split(","):
                add_item(rep.negations, n.strip(), "negation", "negated", prov)
        if intake.past_medical_history:
            for h in intake.past_medical_history.split(","):
                add_item(rep.history, h.strip(), "history", "confirmed", prov)
        if intake.medications:
            for m in intake.medications.split(","):
                add_item(rep.medications, m.strip(), "medication", "confirmed", prov)
        if intake.allergies:
            for a in intake.allergies.split(","):
                add_item(rep.allergies, a.strip(), "allergy", "confirmed", prov)
        if intake.vitals:
            add_item(rep.vitals, intake.vitals, "vitals", "confirmed", prov)
        if intake.previous_investigations:
            add_item(
                rep.investigations, intake.previous_investigations, "investigation", "confirmed", prov
            )

    # ── 3. Process Clinical Findings ──────────────────────────────────────
    for f in findings:
        prov = Provenance(
            source_type="clinical_finding",
            source_id=str(f.id),
            timestamp=f.updated_at or f.created_at,
            author_id=None,
        )
        val = f.canonical_concept or f.value
        concept = f.concept or f.finding_type
        status = "negated" if f.negated else f.status

        if f.negated:
            add_item(rep.negations, val, concept, status, prov)  # type: ignore
        elif f.finding_type in ("symptom", "diagnosis") or concept in ("symptom", "CONDITION"):
            add_item(rep.symptoms, val, concept, status, prov)  # type: ignore
        elif f.finding_type == "measurement" or concept in ("vitals", "VITALS"):
            add_item(rep.vitals, val, concept, status, prov)  # type: ignore
        elif concept in ("medication", "MEDICATION"):
            add_item(rep.medications, val, concept, status, prov)  # type: ignore
        elif concept in ("allergy", "ALLERGY"):
            add_item(rep.allergies, val, concept, status, prov)  # type: ignore
        elif concept in ("travel_history", "travel", "TRAVEL_HISTORY", "GEOGRAPHIC_EXPOSURE"):
            add_item(rep.travel_history, val, concept, status, prov)  # type: ignore
        elif f.temporality == "past" or concept == "history":
            add_item(rep.history, val, concept, status, prov)  # type: ignore
        else:
            add_item(rep.report_findings, val, concept, status, prov)  # type: ignore

    # ── 4. Process Clinical Notes (NEW — regex NLP extraction) ────────────
    for note in notes:
        if not note.body:
            continue
        prov = Provenance(
            source_type="clinical_note",
            source_id=str(note.id),
            timestamp=note.updated_at or note.created_at,
            author_id=str(note.author_id),
        )
        # Extract full text from note body JSON
        note_text = _extract_text_from_note_body(note.body)
        if not note_text.strip():
            continue

        # Run fast regex NLP
        extracted = _extract_from_text(note_text)

        for s in extracted["symptoms"]:
            add_item(rep.symptoms, s, "symptom", "confirmed", prov)
        for d in extracted["duration"]:
            add_item(rep.duration, d, "duration", "confirmed", prov)
        for sev in extracted["severity"]:
            add_item(rep.severity, sev, "severity", "confirmed", prov)
        for n in extracted["negations"]:
            add_item(rep.negations, n, "negation", "negated", prov)
        for v in extracted["vitals"]:
            add_item(rep.vitals, v, "vitals", "confirmed", prov)
        for t in extracted["travel"]:
            add_item(rep.travel_history, t, "travel_history", "confirmed", prov)
        for h in extracted["history"]:
            add_item(rep.history, h, "history", "confirmed", prov)
        for m in extracted["medications"]:
            add_item(rep.medications, m, "medication", "confirmed", prov)

        # Run high-speed clinical note parser (clause-level negation, lab markers, exam signs, vitals)
        try:
            from app.services.clinical_note_parser import clinical_note_parser
            parsed_note = clinical_note_parser.parse(note_text)
            for f in parsed_note.get("positive_findings", []):
                add_item(rep.symptoms, f, "symptom", "confirmed", prov)
            for df in parsed_note.get("diagnostic_findings", []):
                add_item(rep.symptoms, df, "diagnostic_marker", "confirmed", prov)
            for nf in parsed_note.get("negated_findings", []):
                add_item(rep.negations, nf, "negation", "negated", prov)
            for th in parsed_note.get("travel_history", []):
                add_item(rep.travel_history, th, "travel_history", "confirmed", prov)
            for vit_name, vit_val in parsed_note.get("vitals", {}).items():
                add_item(rep.vitals, f"{vit_name}: {vit_val}", "vitals", "confirmed", prov)
            for hist in parsed_note.get("background_history", []):
                add_item(rep.history, hist, "history", "confirmed", prov)
        except Exception:
            pass

        # Detect demographic context from note if missing
        if rep.patient_context:
            if not rep.patient_context.sex:
                if re.search(r"\b(?:male|man|gentleman|boy)\b", note_text, re.IGNORECASE):
                    rep.patient_context.sex = "M"
                elif re.search(r"\b(?:female|woman|lady|girl)\b", note_text, re.IGNORECASE):
                    rep.patient_context.sex = "F"
            if not rep.patient_context.age:
                age_m = re.search(r"\b(\d{1,2})\s*(?:yo|y/o|year[- ]old|years[- ]old)\b", note_text, re.IGNORECASE)
                if age_m:
                    try:
                        rep.patient_context.age = int(age_m.group(1))
                    except Exception:
                        pass

        # Run comprehensive clinical NLP dictionary (400+ terms covering all medical specialties)
        try:
            from app.services.clinical_nlp import extractor
            nlp_findings = extractor._baseline_extract(note_text, "clinical_note")
            for item in nlp_findings:
                val = item.get("canonical_concept") or item.get("value")
                concept = item.get("concept", "SYMPTOM")
                is_neg = item.get("negated", False)
                if is_neg:
                    add_item(rep.negations, val, "negation", "negated", prov)
                elif concept == "SYMPTOM":
                    add_item(rep.symptoms, val, "symptom", "confirmed", prov)
                elif concept == "CONDITION":
                    add_item(rep.history, val, "condition", "confirmed", prov)
                elif concept == "MEDICATION":
                    add_item(rep.medications, val, "medication", "confirmed", prov)
                elif concept == "ALLERGY":
                    add_item(rep.allergies, val, "allergy", "confirmed", prov)
                elif concept in ("TRAVEL_HISTORY", "GEOGRAPHIC_EXPOSURE"):
                    add_item(rep.travel_history, val, "travel_history", "confirmed", prov)
                elif concept == "VITALS":
                    add_item(rep.vitals, val, "vitals", "confirmed", prov)
        except Exception as e:
            pass

    # ── 5. Process Consultation Raw Text / Scratchpad Notes ───────────────
    if consultation and consultation.input_text and consultation.input_text.strip():
        c_text = consultation.input_text.strip()
        prov_consult = Provenance(
            source_type="consultation_input_text",
            source_id=str(consultation.id),
            timestamp=consultation.updated_at or consultation.created_at,
            author_id=str(consultation.doctor_id),
        )

        extracted_c = _extract_from_text(c_text)
        for s in extracted_c.get("symptoms", []):
            add_item(rep.symptoms, s, "symptom", "confirmed", prov_consult)
        for d in extracted_c.get("duration", []):
            add_item(rep.duration, d, "duration", "confirmed", prov_consult)
        for sev in extracted_c.get("severity", []):
            add_item(rep.severity, sev, "severity", "confirmed", prov_consult)
        for n in extracted_c.get("negations", []):
            add_item(rep.negations, n, "negation", "negated", prov_consult)
        for v in extracted_c.get("vitals", []):
            add_item(rep.vitals, v, "vitals", "confirmed", prov_consult)
        for t in extracted_c.get("travel", []):
            add_item(rep.travel_history, t, "travel_history", "confirmed", prov_consult)
        for h in extracted_c.get("history", []):
            add_item(rep.history, h, "history", "confirmed", prov_consult)
        for m in extracted_c.get("medications", []):
            add_item(rep.medications, m, "medication", "confirmed", prov_consult)

        try:
            from app.services.clinical_note_parser import clinical_note_parser
            parsed_note = clinical_note_parser.parse(c_text)
            for f in parsed_note.get("positive_findings", []):
                add_item(rep.symptoms, f, "symptom", "confirmed", prov_consult)
            for nf in parsed_note.get("negated_findings", []):
                add_item(rep.negations, nf, "negation", "negated", prov_consult)
            for th in parsed_note.get("travel_history", []):
                add_item(rep.travel_history, th, "travel_history", "confirmed", prov_consult)
            for vit_name, vit_val in parsed_note.get("vitals", {}).items():
                add_item(rep.vitals, f"{vit_name}: {vit_val}", "vitals", "confirmed", prov_consult)
            for hist in parsed_note.get("background_history", []):
                add_item(rep.history, hist, "history", "confirmed", prov_consult)
        except Exception:
            pass

        try:
            from app.services.clinical_nlp import extractor
            nlp_findings = extractor._baseline_extract(c_text, "consultation_input_text")
            for item in nlp_findings:
                val = item.get("canonical_concept") or item.get("value")
                concept = item.get("concept", "SYMPTOM")
                is_neg = item.get("negated", False)
                if is_neg:
                    add_item(rep.negations, val, "negation", "negated", prov_consult)
                elif concept == "SYMPTOM":
                    add_item(rep.symptoms, val, "symptom", "confirmed", prov_consult)
                elif concept == "CONDITION":
                    add_item(rep.history, val, "condition", "confirmed", prov_consult)
                elif concept == "MEDICATION":
                    add_item(rep.medications, val, "medication", "confirmed", prov_consult)
                elif concept == "ALLERGY":
                    add_item(rep.allergies, val, "allergy", "confirmed", prov_consult)
                elif concept in ("TRAVEL_HISTORY", "GEOGRAPHIC_EXPOSURE"):
                    add_item(rep.travel_history, val, "travel_history", "confirmed", prov_consult)
                elif concept == "VITALS":
                    add_item(rep.vitals, val, "vitals", "confirmed", prov_consult)
        except Exception:
            pass

    return rep

