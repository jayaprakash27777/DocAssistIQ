"""DocAssistIQ — Clinical NLP Extractor (Phase 28 v2).

Enhanced clinical information extraction:
- LLM-based extraction with structured output
- Text chunking for long notes (2000 char chunks with 200 char overlap)
- Medical shorthand expansion before extraction
- Vitals extraction from free text
- Deduplication across chunks
- Robust negation and temporality handling
"""

import re
import json
import asyncio
from typing import List, Dict, Any, Set
from app.services.llm_service import llm_service
from app.services.concept_normalizer import normalizer
import structlog

log = structlog.get_logger(__name__)

# Medical shorthand → full expansion mapping
SHORTHAND_MAP = {
    # Common abbreviations
    r"\bc/o\b": "complains of",
    r"\bh/o\b": "history of",
    r"\bk/c/o\b": "known case of",
    r"\bk/a\b": "known as",
    r"\bSOB\b": "shortness of breath",
    r"\bDOE\b": "dyspnea on exertion",
    r"\bCP\b": "chest pain",
    r"\bHA\b": "headache",
    r"\bN/V\b": "nausea vomiting",
    r"\bN&V\b": "nausea and vomiting",
    r"\bNVD\b": "nausea vomiting diarrhoea",
    r"\bH/A\b": "headache",
    r"\bPt\b": "patient",
    r"\bPt\.\b": "patient",
    r"\bHx\b": "history",
    r"\bRx\b": "treatment",
    r"\bDx\b": "diagnosis",
    r"\bIx\b": "investigations",
    r"\bFHx\b": "family history",
    r"\bSHx\b": "social history",
    r"\bPMH\b": "past medical history",
    r"\bO/E\b": "on examination",
    r"\bO\.E\.\b": "on examination",
    r"\bHPE\b": "history of presenting episode",
    r"\bHPC\b": "history of presenting complaint",
    r"\bPC\b": "presenting complaint",
    r"\bAOF\b": "as of",
    r"\bCNS\b": "central nervous system",
    r"\bCVS\b": "cardiovascular system",
    r"\bRS\b": "respiratory system",
    r"\bGIT\b": "gastrointestinal tract",
    r"\bGUS\b": "genitourinary system",
    r"\bBP\b": "blood pressure",
    r"\bHR\b": "heart rate",
    r"\bRR\b": "respiratory rate",
    r"\bSPO2\b": "oxygen saturation",
    r"\bSp02\b": "oxygen saturation",
    r"\bO2 sat\b": "oxygen saturation",
    r"\bT°\b": "temperature",
    r"\bTemp\b": "temperature",
    r"\bWt\b": "weight",
    r"\bHt\b": "height",
    r"\bBMI\b": "body mass index",
    r"\bGCS\b": "glasgow coma scale",
    r"\bUTI\b": "urinary tract infection",
    r"\bURTI\b": "upper respiratory tract infection",
    r"\bLRTI\b": "lower respiratory tract infection",
    r"\bCOPD\b": "chronic obstructive pulmonary disease",
    r"\bDM\b": "diabetes mellitus",
    r"\bT2DM\b": "type 2 diabetes mellitus",
    r"\bT1DM\b": "type 1 diabetes mellitus",
    r"\bHTN\b": "hypertension",
    r"\bIHD\b": "ischaemic heart disease",
    r"\bACS\b": "acute coronary syndrome",
    r"\bMI\b": "myocardial infarction",
    r"\bSTEMI\b": "ST elevation myocardial infarction",
    r"\bNSTEMI\b": "non-ST elevation myocardial infarction",
    r"\bPE\b": "pulmonary embolism",
    r"\bDVT\b": "deep vein thrombosis",
    r"\bCVA\b": "cerebrovascular accident stroke",
    r"\bTIA\b": "transient ischaemic attack",
    r"\bSAH\b": "subarachnoid haemorrhage",
    r"\bSLE\b": "systemic lupus erythematosus",
    r"\bRA\b": "rheumatoid arthritis",
    r"\bCKD\b": "chronic kidney disease",
    r"\bAKI\b": "acute kidney injury",
    r"\bDKA\b": "diabetic ketoacidosis",
    r"\bHHS\b": "hyperosmolar hyperglycaemic state",
    r"\bCLD\b": "chronic liver disease",
    r"\bHBV\b": "hepatitis B virus",
    r"\bHCV\b": "hepatitis C virus",
    r"\bHAV\b": "hepatitis A virus",
    r"\bTB\b": "tuberculosis",
    r"\bMTB\b": "mycobacterium tuberculosis",
    r"\bHIV\b": "human immunodeficiency virus",
    r"\bAIDS\b": "acquired immunodeficiency syndrome",
    r"\bMAL\b": "malaria",
    r"\bPID\b": "pelvic inflammatory disease",
    r"\bECTOPIC\b": "ectopic pregnancy",
    r"\bPPH\b": "postpartum haemorrhage",
    r"\bRIF\b": "right iliac fossa",
    r"\bLIF\b": "left iliac fossa",
    r"\bRUQ\b": "right upper quadrant",
    r"\bLUQ\b": "left upper quadrant",
    r"\bRLQ\b": "right lower quadrant",
    r"\bLLQ\b": "left lower quadrant",
    r"\bEPIG\b": "epigastric",
    r"\bWBC\b": "white blood cell count",
    r"\bRBC\b": "red blood cell count",
    r"\bHb\b": "haemoglobin",
    r"\bHGB\b": "haemoglobin",
    r"\bPLT\b": "platelet count",
    r"\bCRP\b": "C-reactive protein",
    r"\bESR\b": "erythrocyte sedimentation rate",
    r"\bLFT\b": "liver function tests",
    r"\bRFT\b": "renal function tests",
    r"\bTFT\b": "thyroid function tests",
    r"\bFBC\b": "full blood count",
    r"\bFBP\b": "full blood picture",
    r"\bECG\b": "electrocardiogram",
    r"\bCXR\b": "chest X-ray",
    r"\bUSS\b": "ultrasound scan",
    r"\bCT\b": "CT scan",
    r"\bMRI\b": "MRI scan",
    r"\bLP\b": "lumbar puncture",
    r"\bCSF\b": "cerebrospinal fluid",
    r"\bPCR\b": "polymerase chain reaction test",
    r"\bANA\b": "antinuclear antibody",
    r"\banti-dsDNA\b": "anti-double stranded DNA antibody",
    r"\bABG\b": "arterial blood gas",
    r"\bVBG\b": "venous blood gas",
    r"\bU&E\b": "urea and electrolytes",
    r"\bU/E\b": "urea and electrolytes",
    r"\bPO\b": "oral route",
    r"\bIV\b": "intravenous",
    r"\bIM\b": "intramuscular",
    r"\bSC\b": "subcutaneous",
    r"\bOD\b": "once daily",
    r"\bBD\b": "twice daily",
    r"\bTDS\b": "three times daily",
    r"\bQDS\b": "four times daily",
    r"\bPRN\b": "as needed",
    r"\bNO\b": "no",
    r"\bNKDA\b": "no known drug allergies",
    r"\bNKA\b": "no known allergies",
    r"\bNIL\b": "nil",
}

CHUNK_SIZE = 5000  # characters per chunk (allows full clinical encounter in single prompt)
CHUNK_OVERLAP = 250  # overlap to avoid missing cross-boundary findings


def expand_shorthands(text: str) -> str:
    """Expand medical abbreviations and shorthand to full terms."""
    for pattern, expansion in SHORTHAND_MAP.items():
        text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split long text into overlapping chunks to avoid missing findings at boundaries."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Try to break at a sentence boundary when not at end
        if end < len(text):
            boundary = text.rfind(".", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunks.append(text[start:end])
        # CRITICAL: if we've consumed to the end, stop — otherwise start
        # would go back (end - overlap < end) creating an infinite loop
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def extract_vitals_findings(text: str) -> List[Dict[str, Any]]:
    """Extract structured vitals from free text using regex."""
    vitals_findings = []
    patterns = [
        (r"(?:BP|blood pressure)[:\s]+([\d]{2,3}/[\d]{2,3})(?:\s*mmHg)?", "blood pressure"),
        (r"(?:HR|heart rate|pulse)[:\s]+(\d{2,3})(?:\s*(?:bpm|/min))?", "heart rate"),
        (r"(?:RR|respiratory rate)[:\s]+(\d{1,2})(?:\s*/min)?", "respiratory rate"),
        (r"(?:Temp|temperature|T)[:\s]+(\d{2,3}(?:\.\d)?)(?:\s*°?[CF])?", "temperature"),
        (r"(?:SpO2|spo2|O2 sat(?:uration)?)[:\s]+(\d{2,3})(?:\s*%)?", "oxygen saturation"),
        (r"(?:weight|Wt)[:\s]+(\d{2,3}(?:\.\d)?)(?:\s*(?:kg|lbs?))?", "weight"),
        (r"(?:height|Ht)[:\s]+(\d{1,3}(?:\.\d)?)(?:\s*(?:cm|m))?", "height"),
        (r"(?:GCS|glasgow)[:\s]+(\d{1,2}(?:/15)?)", "GCS score"),
        (r"(?:days? since return|returned (\d+) days?)", "days since return"),
    ]
    for pattern, vital_name in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
            vitals_findings.append({
                "concept": "VITALS",
                "value": f"{vital_name}: {value}",
                "negated": False,
                "temporality": "current",
                "source": "vitals_regex",
                "confidence": 0.95,
                "canonical_concept": vital_name,
                "mapping_source": "regex",
                "mapping_confidence": 0.95,
            })
    return vitals_findings


def deduplicate_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate findings keeping highest confidence."""
    seen: Set[str] = set()
    deduped = []
    for f in findings:
        concept = f.get("concept", "")
        # For travel/geographic concepts, canonical_concept is None — use value as key
        if concept in ("TRAVEL_HISTORY", "GEOGRAPHIC_EXPOSURE"):
            key = f"{concept}-{f.get('value', '').lower()}-{f.get('negated', False)}"
        else:
            key = f"{concept}-{f.get('canonical_concept', f.get('value', ''))}-{f.get('negated', False)}"
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    return deduped

class AwaitableFindings(list):
    """List that can be accessed synchronously or awaited asynchronously."""
    def __init__(self, initial_findings: list, coro_fn=None):
        super().__init__(initial_findings)
        self._coro_fn = coro_fn

    def __await__(self):
        if self._coro_fn:
            return self._coro_fn().__await__()
        async def _self():
            return list(self)
        return _self().__await__()


class ClinicalExtractor:
    """
    Live LLM clinical information extraction with deterministic baseline.
    Supports both synchronous execution (returns AwaitableFindings)
    and async awaiting (enhances with LLM chunks).
    """
    def __init__(self):
        pass

    def extract(self, text: str, source_context: str = "clinical_note") -> Any:
        if not text:
            return AwaitableFindings([])

        # Step 1: Expand medical shorthands
        expanded_text = expand_shorthands(text)

        # Step 2: Extract vitals via regex (fast, reliable)
        baseline_findings: List[Dict[str, Any]] = extract_vitals_findings(expanded_text)

        # Step 3: Run baseline extractor (deterministic — captures symptoms, conditions, travel, etc.)
        baseline_findings.extend(self._baseline_extract(expanded_text, source_context))

        async def _async_runner():
            all_findings = list(baseline_findings)
            chunks = chunk_text(expanded_text)
            log.info("nlp_extract_start", original_len=len(text), expanded_len=len(expanded_text), chunks=len(chunks))
            try:
                # Cap at 2 chunks max for responsive clinical workflow
                for chunk_idx, chunk in enumerate(chunks[:2]):
                    chunk_findings = await asyncio.wait_for(
                        self._extract_chunk(chunk, source_context, chunk_idx),
                        timeout=65.0
                    )
                    all_findings.extend(chunk_findings)
            except (asyncio.TimeoutError, TimeoutError):
                log.warning("nlp_extract_timeout_using_baseline", chunks_processed=len(all_findings))
            except Exception as e:
                log.warning("nlp_extract_runner_error", error=repr(e))

            deduped = deduplicate_findings(all_findings)
            log.info("nlp_extract_done", raw_findings=len(all_findings), deduped=len(deduped))
            return deduped

        return AwaitableFindings(baseline_findings, _async_runner)

    async def _extract_chunk(self, text: str, source_context: str, chunk_idx: int = 0) -> List[Dict[str, Any]]:
        """Run LLM extraction on a single text chunk."""
        system_prompt = """You are an Expert Clinical Medical Data Extraction AI.
Your task is to carefully read the provided clinical text (or audio transcript) and extract every single clinical finding.
You must be thorough. Do not miss any symptoms, conditions, medications, allergies, vitals, or travel history.
Crucially, you must accurately determine if the patient DENIES the finding (negated: true) and whether it is a past or current issue (temporality).

CRITICAL TRAVEL EXTRACTION RULES:
- If the text mentions ANY country, city, region, or area the patient visited, traveled to, or returned from — extract it as concept "TRAVEL_HISTORY".
- Phrases like "returned from", "traveled to", "spent time in", "visited", "came back from", "was in [country]", "trip to", "including time in" all indicate travel history.
- Extract the SPECIFIC country or location name (e.g. "Democratic Republic of the Congo", "DRC", "Congo", "West Africa").
- If there is mention of a specific outbreak, endemic area, or disease zone — also extract it as concept "GEOGRAPHIC_EXPOSURE".
- Extract the approximate duration in the country if mentioned (e.g. "three weeks in DRC").
- Extract any mention of "ongoing infectious disease outbreak" or known outbreak region as GEOGRAPHIC_EXPOSURE.
- Extract the number of days since return (e.g. "8 days after returning") as a VITALS finding with value like "days_since_return: 8".

Return ONLY valid JSON matching this exact schema:
{
  "findings": [
    {
      "concept": "string (strictly one of: SYMPTOM, CONDITION, MEDICATION, ALLERGY, VITALS, TRAVEL_HISTORY, GEOGRAPHIC_EXPOSURE)",
      "value": "string (the exact specific medical term, country name, or phrase)",
      "negated": boolean (true if patient denies it, false if they have it or visited it),
      "temporality": "string (strictly 'current' or 'past')"
    }
  ]
}
"""
        user_prompt = f"Extract all clinical findings from this text chunk:\n\n{text}\n\nReturn JSON only."

        # Normalize concept names from LLM (it often uses wrong case/format)
        _CONCEPT_ALIASES = {
            "travelhistory": "TRAVEL_HISTORY", "travel_history": "TRAVEL_HISTORY",
            "travel history": "TRAVEL_HISTORY", "travelhistory": "TRAVEL_HISTORY",
            "geographic_exposure": "GEOGRAPHIC_EXPOSURE",
            "geographicexposure": "GEOGRAPHIC_EXPOSURE",
            "symptom": "SYMPTOM", "condition": "CONDITION", "medication": "MEDICATION",
            "allergy": "ALLERGY", "vitals": "VITALS", "vital": "VITALS",
        }

        try:
            response_json = await llm_service.generate_json_compact(
                user_prompt, system=system_prompt, max_output_tokens=450
            )
            raw_findings = response_json.get("findings", [])

            findings = []
            for item in raw_findings:
                raw_concept = item.get("concept", "UNKNOWN")
                # Normalize concept name
                concept = _CONCEPT_ALIASES.get(raw_concept.lower().replace(" ", ""), raw_concept.upper())

                raw_val = item.get("value", "")
                if not raw_val:
                    continue

                # For TRAVEL_HISTORY, preserve original casing (country names need capitals)
                if concept in ("TRAVEL_HISTORY", "GEOGRAPHIC_EXPOSURE"):
                    val = raw_val  # Keep original casing from LLM
                else:
                    val = raw_val.lower()

                canon, mapping_src, mapping_conf = normalizer.normalize(val.lower())
                findings.append({
                    "concept": concept,
                    "value": val,
                    "certainty": "high",
                    "negated": item.get("negated", False),
                    "temporality": item.get("temporality", "current"),
                    "source": source_context,
                    "confidence": 0.90,
                    "canonical_concept": canon,
                    "mapping_source": mapping_src,
                    "mapping_confidence": mapping_conf,
                })

            # If LLM returned nothing useful, log it (baseline still runs from extract())
            if not findings:
                log.warning("llm_chunk_extraction_empty", chunk=chunk_idx)

            return findings
        except Exception as e:
            log.warning("llm_chunk_extraction_failed", error=str(e), chunk=chunk_idx)
            return []  # Baseline already running from extract() — no need to call again
            
    def _baseline_extract(self, text: str, source_context: str) -> List[Dict[str, Any]]:
        import re
        text_lower = text.lower()
        findings = []

        # ================================================================
        # COMPREHENSIVE CLINICAL KEYWORD DICTIONARY
        # 400+ terms covering all medical specialties
        # ================================================================
        keywords: dict[str, str] = {
            # ---- FEVER ----
            "fever": "SYMPTOM", "high-grade fever": "SYMPTOM", "high fever": "SYMPTOM",
            "low-grade fever": "SYMPTOM", "febrile": "SYMPTOM", "pyrexia": "SYMPTOM",
            "chills": "SYMPTOM", "rigors": "SYMPTOM", "night sweats": "SYMPTOM",

            # ---- FATIGUE / WEAKNESS ----
            "fatigue": "SYMPTOM", "weakness": "SYMPTOM", "profound weakness": "SYMPTOM",
            "extreme weakness": "SYMPTOM", "generalized weakness": "SYMPTOM",
            "malaise": "SYMPTOM", "lethargy": "SYMPTOM", "drowsiness": "SYMPTOM",

            # ---- HEAD / NEUROLOGICAL ----
            "headache": "SYMPTOM", "severe headache": "SYMPTOM",
            "sudden severe headache": "SYMPTOM", "thunderclap headache": "SYMPTOM",
            "worst headache of life": "SYMPTOM", "migraine": "SYMPTOM",
            "confusion": "SYMPTOM", "altered consciousness": "SYMPTOM",
            "loss of consciousness": "SYMPTOM", "syncope": "SYMPTOM", "fainting": "SYMPTOM",
            "dizziness": "SYMPTOM", "vertigo": "SYMPTOM",
            "seizures": "SYMPTOM", "convulsions": "SYMPTOM",
            "stiff neck": "SYMPTOM", "neck stiffness": "SYMPTOM", "nuchal rigidity": "SYMPTOM",
            "photophobia": "SYMPTOM", "phonophobia": "SYMPTOM",
            "facial drooping": "SYMPTOM", "face droop": "SYMPTOM",
            "arm weakness": "SYMPTOM", "leg weakness": "SYMPTOM",
            "speech difficulty": "SYMPTOM", "slurred speech": "SYMPTOM", "aphasia": "SYMPTOM",
            "hemiparesis": "SYMPTOM", "hemiplegia": "SYMPTOM",
            "ataxia": "SYMPTOM", "balance problems": "SYMPTOM",
            "numbness": "SYMPTOM", "tingling": "SYMPTOM", "paresthesia": "SYMPTOM",
            "ascending weakness": "SYMPTOM", "progressive weakness": "SYMPTOM",
            "tremor": "SYMPTOM", "agitation": "SYMPTOM", "restlessness": "SYMPTOM",
            "hallucinations": "SYMPTOM", "memory loss": "SYMPTOM",
            "double vision": "SYMPTOM", "diplopia": "SYMPTOM",
            "vision loss": "SYMPTOM", "blurred vision": "SYMPTOM",
            "vision changes": "SYMPTOM", "visual disturbance": "SYMPTOM",

            # ---- CARDIOVASCULAR ----
            "chest pain": "SYMPTOM", "chest tightness": "SYMPTOM",
            "crushing chest pain": "SYMPTOM", "chest pressure": "SYMPTOM",
            "tearing chest pain": "SYMPTOM", "pleuritic chest pain": "SYMPTOM",
            "radiating chest pain": "SYMPTOM", "jaw pain": "SYMPTOM",
            "left arm pain": "SYMPTOM", "shoulder pain": "SYMPTOM",
            "shortness of breath": "SYMPTOM", "dyspnea": "SYMPTOM",
            "tachycardia": "SYMPTOM", "rapid heart rate": "SYMPTOM",
            "palpitations": "SYMPTOM", "diaphoresis": "SYMPTOM",
            "sweating": "SYMPTOM", "orthopnea": "SYMPTOM",
            "paroxysmal nocturnal dyspnea": "SYMPTOM",
            "leg swelling": "SYMPTOM", "ankle swelling": "SYMPTOM",
            "peripheral edema": "SYMPTOM", "bilateral leg swelling": "SYMPTOM",
            "calf pain": "SYMPTOM", "calf tenderness": "SYMPTOM",
            "unilateral leg swelling": "SYMPTOM",
            "nosebleed": "SYMPTOM", "epistaxis": "SYMPTOM",
            "bradycardia": "SYMPTOM", "slow heart rate": "SYMPTOM",
            "hypotension": "SYMPTOM", "hypertension": "CONDITION",
            "palpitations": "SYMPTOM",

            # ---- GASTROINTESTINAL ----
            "nausea": "SYMPTOM", "vomiting": "SYMPTOM", "diarrhea": "SYMPTOM",
            "watery diarrhea": "SYMPTOM", "bloody diarrhea": "SYMPTOM",
            "chronic diarrhea": "SYMPTOM", "loose stools": "SYMPTOM",
            "abdominal pain": "SYMPTOM", "severe abdominal pain": "SYMPTOM",
            "right lower quadrant pain": "SYMPTOM", "epigastric pain": "SYMPTOM",
            "severe epigastric pain": "SYMPTOM", "upper abdominal pain": "SYMPTOM",
            "lower abdominal pain": "SYMPTOM", "pelvic pain": "SYMPTOM",
            "colicky abdominal pain": "SYMPTOM", "crampy abdominal pain": "SYMPTOM",
            "pain radiating to back": "SYMPTOM",
            "loss of appetite": "SYMPTOM", "anorexia": "SYMPTOM",
            "weight loss": "SYMPTOM", "weight gain": "SYMPTOM",
            "jaundice": "SYMPTOM", "yellowing of skin": "SYMPTOM",
            "dark urine": "SYMPTOM", "pale stool": "SYMPTOM",
            "constipation": "SYMPTOM", "obstipation": "SYMPTOM",
            "inability to pass gas": "SYMPTOM",
            "abdominal distension": "SYMPTOM", "bloating": "SYMPTOM",
            "ascites": "SYMPTOM", "abdominal swelling": "SYMPTOM",
            "rebound tenderness": "SYMPTOM", "guarding": "SYMPTOM",
            "rigidity": "SYMPTOM", "peritonism": "SYMPTOM",
            "hematemesis": "SYMPTOM", "vomiting blood": "SYMPTOM",
            "melena": "SYMPTOM", "black stool": "SYMPTOM", "dark stool": "SYMPTOM",
            "coffee-ground vomiting": "SYMPTOM", "rectal bleeding": "SYMPTOM",
            "blood in stool": "SYMPTOM", "tenesmus": "SYMPTOM",
            "heartburn": "SYMPTOM", "belching": "SYMPTOM",
            "dysphagia": "SYMPTOM", "difficulty swallowing": "SYMPTOM",
            "hiccups": "SYMPTOM", "pruritus": "SYMPTOM", "itching": "SYMPTOM",

            # ---- RESPIRATORY ----
            "cough": "SYMPTOM", "persistent cough": "SYMPTOM", "chronic cough": "SYMPTOM",
            "paroxysmal cough": "SYMPTOM", "coughing fits": "SYMPTOM",
            "wheeze": "SYMPTOM", "wheezing": "SYMPTOM",
            "hemoptysis": "SYMPTOM", "coughing blood": "SYMPTOM",
            "sputum": "SYMPTOM", "purulent sputum": "SYMPTOM",
            "tachypnea": "SYMPTOM", "rapid breathing": "SYMPTOM",
            "cyanosis": "SYMPTOM", "hypoxia": "SYMPTOM", "low oxygen": "SYMPTOM",
            "chest tightness": "SYMPTOM", "use of accessory muscles": "SYMPTOM",
            "stridor": "SYMPTOM", "hoarseness": "SYMPTOM",
            "reduced breath sounds": "SYMPTOM", "crackles": "SYMPTOM",

            # ---- RENAL / URINARY ----
            "dysuria": "SYMPTOM", "painful urination": "SYMPTOM",
            "burning urination": "SYMPTOM", "frequency": "SYMPTOM",
            "urinary frequency": "SYMPTOM", "urinary urgency": "SYMPTOM",
            "suprapubic pain": "SYMPTOM", "flank pain": "SYMPTOM",
            "costovertebral angle tenderness": "SYMPTOM",
            "hematuria": "SYMPTOM", "blood in urine": "SYMPTOM",
            "reduced urine output": "SYMPTOM", "oliguria": "SYMPTOM", "anuria": "SYMPTOM",
            "cloudy urine": "SYMPTOM", "foul-smelling urine": "SYMPTOM",
            "nocturia": "SYMPTOM", "polyuria": "SYMPTOM", "frequent urination": "SYMPTOM",
            "proteinuria": "SYMPTOM", "edema": "SYMPTOM",

            # ---- EYES ----
            "redness of the eyes": "SYMPTOM", "conjunctival redness": "SYMPTOM",
            "conjunctivitis": "SYMPTOM", "red eyes": "SYMPTOM",
            "exophthalmos": "SYMPTOM", "eye protrusion": "SYMPTOM",

            # ---- MUSCULOSKELETAL ----
            "joint pain": "SYMPTOM", "arthralgia": "SYMPTOM", "arthritis": "SYMPTOM",
            "joint swelling": "SYMPTOM", "morning stiffness": "SYMPTOM",
            "muscle pain": "SYMPTOM", "muscle aches": "SYMPTOM", "myalgia": "SYMPTOM",
            "back pain": "SYMPTOM", "neck pain": "SYMPTOM",
            "bone pain": "SYMPTOM", "severe bone pain": "SYMPTOM",
            "leg pain": "SYMPTOM", "arm pain": "SYMPTOM",
            "muscle rigidity": "SYMPTOM", "tremor": "SYMPTOM",

            # ---- SKIN / DERMATOLOGY ----
            "rash": "SYMPTOM", "skin rash": "SYMPTOM", "skin eruption": "SYMPTOM",
            "skin lesion": "SYMPTOM", "skin lesions": "SYMPTOM",
            "skin redness": "SYMPTOM", "erythema": "SYMPTOM",
            "skin swelling": "SYMPTOM", "skin warmth": "SYMPTOM",
            "skin pain": "SYMPTOM", "painful lesions": "SYMPTOM",
            "vesicular rash": "SYMPTOM", "pustular rash": "SYMPTOM",
            "macular rash": "SYMPTOM", "petechial rash": "SYMPTOM",
            "purpuric rash": "SYMPTOM", "malar rash": "SYMPTOM",
            "butterfly rash": "SYMPTOM", "photosensitive rash": "SYMPTOM",
            "lymph node swelling": "SYMPTOM", "swollen lymph nodes": "SYMPTOM",
            "lymphadenopathy": "SYMPTOM", "lymph node enlargement": "SYMPTOM",
            "mucosal lesion": "SYMPTOM", "oral lesion": "SYMPTOM",
            "mouth ulcers": "SYMPTOM", "oral ulcers": "SYMPTOM",
            "hair loss": "SYMPTOM", "alopecia": "SYMPTOM",
            "jaundice": "SYMPTOM", "pallor": "SYMPTOM",
            "clammy skin": "SYMPTOM", "dry skin": "SYMPTOM",
            "ecchymosis": "SYMPTOM", "bruising": "SYMPTOM", "easy bruising": "SYMPTOM",

            # ---- HEMORRHAGIC ----
            "bleeding": "SYMPTOM", "hemorrhage": "SYMPTOM",
            "haemorrhage": "SYMPTOM", "haemorrhaging": "SYMPTOM",
            "spontaneous bleeding": "SYMPTOM", "unexplained bleeding": "SYMPTOM",

            # ---- ENDOCRINE / METABOLIC ----
            "polyuria": "SYMPTOM", "polydipsia": "SYMPTOM",
            "excessive thirst": "SYMPTOM", "fruity breath": "SYMPTOM",
            "acetone breath": "SYMPTOM", "Kussmaul breathing": "SYMPTOM",
            "heat intolerance": "SYMPTOM", "cold intolerance": "SYMPTOM",
            "hyperpigmentation": "SYMPTOM", "darkening of skin": "SYMPTOM",
            "goiter": "SYMPTOM", "neck swelling": "SYMPTOM",
            "salt craving": "SYMPTOM", "dehydration": "SYMPTOM",

            # ---- OB/GYN ----
            "vaginal bleeding": "SYMPTOM", "vaginal discharge": "SYMPTOM",
            "missed period": "SYMPTOM", "amenorrhea": "SYMPTOM",
            "pelvic pain": "SYMPTOM", "dyspareunia": "SYMPTOM",
            "shoulder tip pain": "SYMPTOM",
            "positive pregnancy test": "SYMPTOM",

            # ---- SICKLE CELL ----
            "severe bone pain": "SYMPTOM", "priapism": "SYMPTOM",
            "acute chest syndrome": "SYMPTOM",

            # ---- GENERAL ----
            "sore throat": "SYMPTOM", "loss of taste": "SYMPTOM",
            "loss of smell": "SYMPTOM", "runny nose": "SYMPTOM",
            "swollen glands": "SYMPTOM",

            # ---- CONDITIONS ----
            "hypertension": "CONDITION", "diabetes": "CONDITION",
            "asthma": "CONDITION", "tuberculosis": "CONDITION",
            "malaria": "CONDITION", "dengue": "CONDITION",
            "ebola": "CONDITION", "cholera": "CONDITION",
            "typhoid": "CONDITION", "hepatitis": "CONDITION",
            "hiv": "CONDITION", "pneumonia": "CONDITION",
            "copd": "CONDITION", "chronic obstructive pulmonary disease": "CONDITION",
            "heart failure": "CONDITION",
            "kidney disease": "CONDITION", "liver disease": "CONDITION",
            "stroke": "CONDITION", "epilepsy": "CONDITION",
            "sickle cell": "CONDITION", "lupus": "CONDITION",
            "rheumatoid arthritis": "CONDITION", "cancer": "CONDITION",

            # ---- MEDICATIONS ----
            "ibuprofen": "MEDICATION", "paracetamol": "MEDICATION",
            "acetaminophen": "MEDICATION", "aspirin": "MEDICATION",
            "lisinopril": "MEDICATION", "metformin": "MEDICATION",
            "antimalarial": "MEDICATION", "doxycycline": "MEDICATION",
            "ciprofloxacin": "MEDICATION", "amoxicillin": "MEDICATION",
            "warfarin": "MEDICATION", "insulin": "MEDICATION",
            "prednisolone": "MEDICATION", "prednisone": "MEDICATION",
            "methotrexate": "MEDICATION", "hydroxychloroquine": "MEDICATION",
            "antidepressant": "MEDICATION", "ssri": "MEDICATION",
            "sertraline": "MEDICATION", "fluoxetine": "MEDICATION",
            "clopidogrel": "MEDICATION", "atorvastatin": "MEDICATION",
            "omeprazole": "MEDICATION", "pantoprazole": "MEDICATION",
            "tylenol": "MEDICATION",

            # ---- ALLERGIES ----
            "penicillin": "ALLERGY", "sulfa": "ALLERGY",
            "latex": "ALLERGY", "nsaid": "ALLERGY",
        }

        # Match spans and evaluate negation and temporality in preceding window
        NEGATION_TRIGGERS = ["no", "not", "denies", "deny", "denied", "without", "ruled out", "zero", "negative for"]
        PAST_TRIGGERS = ["history", "previous", "past", "ago", "last", "prior"]

        matched_spans = []
        for kw, concept in keywords.items():
            pattern = r'\b' + re.escape(kw) + r'\b'
            for m in re.finditer(pattern, text_lower):
                matched_spans.append((m.start(), m.end(), kw, concept))

        # Sort by start position and resolve overlaps (prefer longer match)
        matched_spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        resolved_spans = []
        for s, e, kw, concept in matched_spans:
            overlap = any(s >= rs and s < re_pos or e > rs and e <= re_pos for rs, re_pos, _, _ in resolved_spans)
            if not overlap:
                resolved_spans.append((s, e, kw, concept))

        resolved_spans.sort(key=lambda x: x[0])

        for start, end, kw, concept in resolved_spans:
            preceding = text_lower[max(0, start - 45):start]
            if "." in preceding:
                preceding = preceding[preceding.rfind(".") + 1:]
            pre_tokens = set(re.findall(r'\b\w+\b', preceding))

            negated = any(t in NEGATION_TRIGGERS for t in pre_tokens)
            temporality = "past" if any(t in PAST_TRIGGERS for t in pre_tokens) else "current"
            canon, mapping_src, mapping_conf = normalizer.normalize(kw)

            findings.append({
                "concept": concept,
                "value": kw,
                "certainty": "high",
                "negated": negated,
                "temporality": temporality,
                "source": source_context,
                "confidence": 0.85,
                "canonical_concept": canon,
                "mapping_source": mapping_src,
                "mapping_confidence": mapping_conf,
            })

        # === Travel History Detection ===
        travel_countries = [
            # ---- AFRICA ----
            ("democratic republic of the congo", "Democratic Republic of the Congo"),
            ("drc", "Democratic Republic of the Congo"),
            ("congo", "Congo"),
            ("west africa", "West Africa"),
            ("sub-saharan africa", "Sub-Saharan Africa"),
            ("central africa", "Central Africa"),
            ("east africa", "East Africa"),
            ("nigeria", "Nigeria"), ("ghana", "Ghana"), ("uganda", "Uganda"),
            ("kenya", "Kenya"), ("ethiopia", "Ethiopia"), ("sierra leone", "Sierra Leone"),
            ("guinea", "Guinea"), ("liberia", "Liberia"), ("cameroon", "Cameroon"),
            ("angola", "Angola"), ("zambia", "Zambia"), ("tanzania", "Tanzania"),
            ("mozambique", "Mozambique"), ("zimbabwe", "Zimbabwe"),
            ("south africa", "South Africa"), ("namibia", "Namibia"),
            ("botswana", "Botswana"), ("malawi", "Malawi"),
            ("rwanda", "Rwanda"), ("burundi", "Burundi"),
            ("somalia", "Somalia"), ("sudan", "Sudan"), ("south sudan", "South Sudan"),
            ("chad", "Chad"), ("niger", "Niger"), ("mali", "Mali"),
            ("senegal", "Senegal"), ("ivory coast", "Ivory Coast"),
            ("cote d'ivoire", "Ivory Coast"),
            ("togo", "Togo"), ("benin", "Benin"), ("burkina faso", "Burkina Faso"),
            ("central african republic", "Central African Republic"),
            ("gabon", "Gabon"), ("equatorial guinea", "Equatorial Guinea"),
            ("eritrea", "Eritrea"), ("djibouti", "Djibouti"),
            ("madagascar", "Madagascar"), ("mauritania", "Mauritania"),
            ("guinea-bissau", "Guinea-Bissau"),
            # ---- SOUTH AND SOUTHEAST ASIA ----
            ("india", "India"), ("pakistan", "Pakistan"), ("bangladesh", "Bangladesh"),
            ("sri lanka", "Sri Lanka"), ("nepal", "Nepal"), ("bhutan", "Bhutan"),
            ("myanmar", "Myanmar"), ("burma", "Myanmar"),
            ("thailand", "Thailand"), ("vietnam", "Vietnam"), ("laos", "Laos"),
            ("cambodia", "Cambodia"), ("indonesia", "Indonesia"),
            ("malaysia", "Malaysia"), ("singapore", "Singapore"),
            ("philippines", "Philippines"), ("timor-leste", "Timor-Leste"),
            ("papua new guinea", "Papua New Guinea"),
            # ---- EAST ASIA ----
            ("china", "China"), ("hong kong", "Hong Kong"),
            ("taiwan", "Taiwan"), ("south korea", "South Korea"),
            ("north korea", "North Korea"), ("japan", "Japan"),
            ("mongolia", "Mongolia"),
            # ---- CENTRAL ASIA ----
            ("afghanistan", "Afghanistan"), ("tajikistan", "Tajikistan"),
            ("uzbekistan", "Uzbekistan"), ("kazakhstan", "Kazakhstan"),
            ("kyrgyzstan", "Kyrgyzstan"), ("turkmenistan", "Turkmenistan"),
            # ---- MIDDLE EAST ----
            ("saudi arabia", "Saudi Arabia"), ("yemen", "Yemen"),
            ("iraq", "Iraq"), ("iran", "Iran"), ("syria", "Syria"),
            ("jordan", "Jordan"), ("lebanon", "Lebanon"), ("israel", "Israel"),
            ("palestine", "Palestine"), ("oman", "Oman"), ("uae", "UAE"),
            ("united arab emirates", "UAE"), ("qatar", "Qatar"),
            ("kuwait", "Kuwait"), ("bahrain", "Bahrain"),
            ("middle east", "Middle East"),
            # ---- LATIN AMERICA ----
            ("brazil", "Brazil"), ("colombia", "Colombia"), ("peru", "Peru"),
            ("venezuela", "Venezuela"), ("bolivia", "Bolivia"),
            ("ecuador", "Ecuador"), ("paraguay", "Paraguay"), ("uruguay", "Uruguay"),
            ("argentina", "Argentina"), ("chile", "Chile"),
            ("mexico", "Mexico"), ("guatemala", "Guatemala"), ("honduras", "Honduras"),
            ("el salvador", "El Salvador"), ("nicaragua", "Nicaragua"),
            ("costa rica", "Costa Rica"), ("panama", "Panama"),
            ("cuba", "Cuba"), ("haiti", "Haiti"), ("dominican republic", "Dominican Republic"),
            ("jamaica", "Jamaica"), ("trinidad", "Trinidad"),
            ("guyana", "Guyana"), ("suriname", "Suriname"),
            # ---- OCEANIA ----
            ("australia", "Australia"), ("new zealand", "New Zealand"),
            ("fiji", "Fiji"), ("solomon islands", "Solomon Islands"),
            ("vanuatu", "Vanuatu"),
            # ---- OUTBREAK CONTEXT PHRASES ----
            ("outbreak area", "Country with ongoing outbreak"),
            ("ongoing outbreak", "Country with ongoing outbreak"),
            ("endemic area", "Country with ongoing outbreak"),
            ("disease zone", "Country with ongoing outbreak"),
            ("infectious disease outbreak", "Country with ongoing outbreak"),
            ("affected region", "Country with ongoing outbreak"),
            ("epidemic zone", "Country with ongoing outbreak"),
        ]

        found_countries = set()
        for country_lower, country_display in travel_countries:
            if country_lower in text_lower and country_display not in found_countries:
                found_countries.add(country_display)
                canon, mapping_src, mapping_conf = normalizer.normalize(country_display)
                findings.append({
                    "concept": "TRAVEL_HISTORY",
                    "value": country_display,
                    "certainty": "high",
                    "negated": False,
                    "temporality": "past",
                    "source": source_context,
                    "confidence": 0.90,
                    "canonical_concept": canon,
                    "mapping_source": mapping_src,
                    "mapping_confidence": mapping_conf
                })

        # === Days Since Return Detection ===
        days_patterns = [
            r"(\d+)\s+days?\s+after\s+return",
            r"(\d+)\s+days?\s+after\s+arriv",
            r"approximately\s+(\d+)\s+days?\s+after",
        ]
        for pattern in days_patterns:
            match = re.search(pattern, text_lower)
            if match:
                days = match.group(1)
                canon, mapping_src, mapping_conf = normalizer.normalize(f"days_since_return: {days}")
                findings.append({
                    "concept": "VITALS",
                    "value": f"days_since_return: {days}",
                    "certainty": "high",
                    "negated": False,
                    "temporality": "current",
                    "source": source_context,
                    "confidence": 0.85,
                    "canonical_concept": canon,
                    "mapping_source": mapping_src,
                    "mapping_confidence": mapping_conf
                })
                break

        # === Weeks Since Return Extraction (incubation window) ===
        week_map = [
            (r"(\d+)\s+weeks?\s+after\s+return", lambda m: str(int(m.group(1)) * 7)),
            (r"(\d+)\s+weeks?\s+after\s+arriv", lambda m: str(int(m.group(1)) * 7)),
            (r"approximately\s+(\d+)\s+weeks?\s+after", lambda m: str(int(m.group(1)) * 7)),
            (r"several\s+weeks\s+after", lambda _: "21"),
            (r"three\s+weeks\s+after", lambda _: "21"),
            (r"two\s+weeks\s+after", lambda _: "14"),
            (r"four\s+weeks\s+after", lambda _: "28"),
            (r"five\s+weeks\s+after", lambda _: "35"),
        ]
        for wpat, wfn in week_map:
            wm = re.search(wpat, text_lower)
            if wm:
                try:
                    wdays = wfn(wm)
                    findings.append({
                        "concept": "VITALS",
                        "value": f"days_since_return: {wdays}",
                        "certainty": "medium",
                        "negated": False,
                        "temporality": "current",
                        "source": source_context,
                        "confidence": 0.78,
                        "canonical_concept": f"days_since_return: {wdays}",
                        "mapping_source": "regex_weeks",
                        "mapping_confidence": 0.78
                    })
                except Exception:
                    pass
                break

        # === Geographic + Exposure Context Detection (comprehensive upgrade) ===
        # Feeds geographic scoring engine. Rural/agricultural = Hantavirus clue.
        geo_exposure_map = [
            (r"stayed in accommodation close to agricultural", "agricultural land"),
            (r"accommodation close to agricultural", "agricultural land"),
            (r"close to agricultural land", "agricultural land"),
            (r"accommodation.*?agricultural", "agricultural land"),
            (r"agricultural land", "agricultural land"),
            (r"agricultural area", "agricultural land"),
            (r"rural.*?accommodation", "rural accommodation"),
            (r"stayed.*?rural", "rural area"),
            (r"rural area", "rural area"),
            (r"rural setting", "rural area"),
            (r"farming area", "farm"),
            (r"farm stay", "farm"),
            (r"rodent exposure", "rodent exposure"),
            (r"rodent droppings", "rodent exposure"),
            (r"rodent infestation", "rodent exposure"),
            (r"mouse droppings", "rodent exposure"),
            (r"rat droppings", "rodent exposure"),
            (r"\brural\b", "rural area"),
            (r"\bfarm\b", "farm"),
            (r"andes mountains", "Andes"),
            (r"andes region", "Andes"),
            (r"\bandes\b", "Andes"),
            (r"patagonia", "Patagonia"),
            (r"south america", "South America"),
            (r"southern cone", "South America"),
            (r"latin america", "latin america"),
            (r"outbreak area", "Ongoing infectious disease outbreak area"),
            (r"endemic area", "Ongoing infectious disease outbreak area"),
            (r"disease zone", "Ongoing infectious disease outbreak area"),
            (r"epidemic zone", "Ongoing infectious disease outbreak area"),
            (r"\boutbreak\b", "Ongoing infectious disease outbreak area"),
            (r"\bendemic\b", "Ongoing infectious disease outbreak area"),
        ]
        rural_geo_vals = {
            "rural area", "agricultural land", "farm", "rodent exposure",
            "rural accommodation", "Andes", "Patagonia", "South America", "latin america",
        }
        added_exposures: set = set()
        for gpattern, exposure_val in geo_exposure_map:
            if exposure_val in added_exposures:
                continue
            if re.search(gpattern, text_lower):
                added_exposures.add(exposure_val)
                canon, mapping_src, mapping_conf = normalizer.normalize(exposure_val)
                concept = "TRAVEL_HISTORY" if exposure_val in rural_geo_vals else "GEOGRAPHIC_EXPOSURE"
                findings.append({
                    "concept": concept,
                    "value": exposure_val,
                    "certainty": "high",
                    "negated": False,
                    "temporality": "past",
                    "source": source_context,
                    "confidence": 0.88,
                    "canonical_concept": canon,
                    "mapping_source": mapping_src,
                    "mapping_confidence": mapping_conf
                })

        return findings

extractor = ClinicalExtractor()
