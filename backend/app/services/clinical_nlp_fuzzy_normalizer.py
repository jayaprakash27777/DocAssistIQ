"""DocAssistIQ Clinical NLP & Fuzzy Typo Normalizer.

Engineered to handle:
1. Fast-paced clinician shorthand, typos, phonetic misspellings, and keyboard slips.
2. Clinical medical acronyms (e.g. STEMI, DKA, HTN, DM2, PE, DVT, UTI, AKI, GCS, MAP).
3. Unstructured free-text clinical case presentations with misspelled findings.
4. Fuzzy matching for certified document generation intents and clinical calculators.
"""

import re
import difflib
from typing import Dict, List, Tuple, Optional, Any

# ---------------------------------------------------------------------------
# 1. Clinical Acronyms & Medical Jargon Dictionary
# ---------------------------------------------------------------------------
CLINICAL_ABBREVIATIONS: Dict[str, str] = {
    # Diseases & Syndromes
    "dka": "diabetic ketoacidosis",
    "stemi": "st-elevation myocardial infarction",
    "nstemi": "non-st-elevation myocardial infarction",
    "acs": "acute coronary syndrome",
    "ami": "acute myocardial infarction",
    "mi": "myocardial infarction",
    "htn": "hypertension",
    "dm": "diabetes mellitus",
    "dm2": "type 2 diabetes mellitus",
    "t2dm": "type 2 diabetes mellitus",
    "dm1": "type 1 diabetes mellitus",
    "t1dm": "type 1 diabetes mellitus",
    "pe": "pulmonary embolism",
    "dvt": "deep vein thrombosis",
    "vte": "venous thromboembolism",
    "uti": "urinary tract infection",
    "aki": "acute kidney injury",
    "ckd": "chronic kidney disease",
    "copd": "chronic obstructive pulmonary disease",
    "chf": "congestive heart failure",
    "hf": "heart failure",
    "af": "atrial fibrillation",
    "afib": "atrial fibrillation",
    "cva": "cerebrovascular accident stroke",
    "tia": "transient ischemic attack",
    "gerd": "gastroesophageal reflux disease",
    "ards": "acute respiratory distress syndrome",
    "dic": "disseminated intravascular coagulation",
    "sle": "systemic lupus erythematosus",
    "ra": "rheumatoid arthritis",
    "ibd": "inflammatory bowel disease",
    "tb": "tuberculosis",

    # Signs, Symptoms & Exam
    "sob": "shortness of breath",
    "sobo": "shortness of breath on exertion",
    "cp": "chest pain",
    "doe": "dyspnea on exertion",
    "pnd": "paroxysmal nocturnal dyspnea",
    "loc": "loss of consciousness",
    "ams": "altered mental status",
    "n/v": "nausea and vomiting",
    "nv": "nausea vomiting",
    "ha": "headache",

    # Diagnostics & Vitals
    "bp": "blood pressure",
    "sbp": "systolic blood pressure",
    "dbp": "diastolic blood pressure",
    "hr": "heart rate",
    "rr": "respiratory rate",
    "t": "temperature",
    "temp": "temperature",
    "spo2": "oxygen saturation",
    "o2": "oxygen",
    "ecg": "electrocardiogram",
    "ekg": "electrocardiogram",
    "cxr": "chest x-ray",
    "ctpa": "ct pulmonary angiogram",
    "trop": "troponin",
    "abg": "arterial blood gas",
    "fbc": "full blood count",
    "cbc": "complete blood count",
    "cmp": "comprehensive metabolic panel",
    "bmp": "basic metabolic panel",
    "lft": "liver function tests",
    "rft": "renal function tests",
    "cr": "creatinine",
    "bun": "blood urea nitrogen",
    "gcs": "glasgow coma scale",
    "map": "mean arterial pressure",
    "bmi": "body mass index",
    "esi": "emergency severity index",

    # Clinical Encounter & Documents
    "pt": "patient",
    "dr": "doctor",
    "doc": "doctor",
    "hx": "history",
    "dx": "diagnosis",
    "tx": "treatment",
    "rx": "prescription",
    "sx": "symptoms",
    "ix": "investigations",
    "ed": "emergency department",
    "er": "emergency room",
    "icu": "intensive care unit",
    "itu": "intensive treatment unit",
    "pacu": "post-anesthesia care unit",
    "ot": "operating theater",
    "or": "operating room",
}

# ---------------------------------------------------------------------------
# 2. Canonical Clinical Terms for Spell Correction & Levenshtein Normalization
# ---------------------------------------------------------------------------
CANONICAL_CLINICAL_VOCABULARY: List[str] = [
    # Commands & Intents
    "generate", "calculate", "document", "prescription", "certificate", "referral",
    "summary", "instructions", "triage", "radiology", "requisition", "timeline",
    "profile", "examination", "assessment", "investigation", "symptoms", "vitals",
    "allergies", "medications", "discharge", "operative", "emergency", "consultation",
    
    # Common Misspelled Disease & Medical Terms
    "dengue", "fever", "diabetic", "ketoacidosis", "stroke", "ischemic", "hemorrhagic",
    "malaria", "typhoid", "cholera", "pneumonia", "asthma", "hypertension", "hypotension",
    "anaphylaxis", "hyperkalemia", "hypokalemia", "hypoglycemia", "hyperglycemia",
    "sepsis", "septic", "shock", "epilepticus", "meningitis", "encephalitis",
    "infarction", "coronary", "syndrome", "tachycardia", "bradycardia", "arrhythmia",
    "fibrillation", "embolism", "thrombosis", "myocardial", "pulmonary", "pericarditis",
    "appendicitis", "pancreatitis", "cholecystitis", "hepatitis", "cirrhosis",
    "weight", "height", "kilos", "kilograms", "centimeters", "pressure", "arterial",
    "patient", "doctor", "license", "consent", "timeline", "intake", "subjective",
    "objective", "amoxicillin", "paracetamol", "ibuprofen", "metformin", "heparin",
    "aspirin", "clopidogrel", "ticagrelor", "atorvastatin", "insulin", "ceftriaxone",
]

# Common typographical substitutions map for instant sub-millisecond replacement
COMMON_TYPOS_MAP: Dict[str, str] = {
    # Document actions
    "genrate": "generate", "generat": "generate", "gnrate": "generate", "mak": "make",
    "sumary": "summary", "summery": "summary", "sumry": "summary", "sumery": "summary",
    "dischrg": "discharge", "discharg": "discharge", "dicharge": "discharge",
    "opperative": "operative", "oprative": "operative", "opertive": "operative", "operativ": "operative",
    "triag": "triage", "traige": "triage", "triagee": "triage",
    "radilogy": "radiology", "radology": "radiology", "radiologi": "radiology",
    "certifcate": "certificate", "certificat": "certificate", "certficate": "certificate", "sertificate": "certificate",
    "prescribtion": "prescription", "prescripion": "prescription", "perscription": "prescription", "prescrption": "prescription",
    "prescrib": "prescribe", "prescibe": "prescribe",
    "refferal": "referral", "referal": "referral", "refrral": "referral",
    "instrucshuns": "instructions", "instructns": "instructions", "instruxions": "instructions", "instructins": "instructions",
    
    # Calculators
    "calclate": "calculate", "calcualte": "calculate", "calclat": "calculate", "calculat": "calculate",
    "bmmi": "bmi", "bmy": "bmi",
    "hight": "height", "heigt": "height", "heigth": "height", "hit": "height",
    "weigt": "weight", "weigth": "weight", "weit": "weight", "wight": "weight",
    "blod": "blood", "bood": "blood",
    "presure": "pressure", "pressre": "pressure",
    
    # Questions & Demographics
    "wat": "what", "wut": "what", "whut": "what",
    "patint": "patient", "pateint": "patient", "patien": "patient", "ptient": "patient",
    "docter": "doctor", "doctur": "doctor",
    "aeg": "age", "ag": "age",
    "symtoms": "symptoms", "symptms": "symptoms", "symtomes": "symptoms", "symptomms": "symptoms",
    
    # Common Diseases
    "dengu": "dengue", "denge": "dengue", "denguee": "dengue",
    "diabetik": "diabetic", "diabtic": "diabetic", "diabates": "diabetes", "diabtes": "diabetes",
    "ketoacidoss": "ketoacidosis", "ketoasidosis": "ketoacidosis", "ketoacidos": "ketoacidosis",
    "strok": "stroke", "strke": "stroke",
    "pnumonia": "pneumonia", "pneumona": "pneumonia", "pnemoni": "pneumonia", "pneomonia": "pneumonia",
    "typhod": "typhoid", "tiphoid": "typhoid", "typoid": "typhoid",
    "malari": "malaria", "malariia": "malaria",
    "cholra": "cholera", "kolera": "cholera",
    "meningits": "meningitis", "meninjitis": "meningitis",
    "anaphylacti": "anaphylaxis", "anafilaxis": "anaphylaxis",
    "hyperkalemi": "hyperkalemia", "hypokalemi": "hypokalemia",
    "infarctn": "infarction", "infartion": "infarction",
    "coronry": "coronary",
    # Clinical presentation & symptoms
    "presnted": "presented", "presentd": "presented", "presentedd": "presented",
    "ches": "chest", "chset": "chest",
    "radiatn": "radiating", "radiatng": "radiating", "radiatting": "radiating",
    "profus": "profuse",
    "diaphoretic": "diaphoresis", "diaphoretc": "diaphoresis",
    "elevatn": "elevation", "elevtion": "elevation", "elevted": "elevated",
    "troponn": "troponin", "troponine": "troponin",
    "positve": "positive", "pos": "positive",
    "negatve": "negative", "neg": "negative",
    "sever": "severe", "sevear": "severe",
    "mangment": "management", "mangement": "management", "managment": "management",
    "diagnsis": "diagnosis", "diagnois": "diagnosis",
    "urget": "urgent", "urgnt": "urgent",
    "metfomin": "metformin", "metformn": "metformin",
}


def normalize_clinical_query(text: str) -> str:
    """
    Intelligently cleans, expands clinical abbreviations, and corrects common
    spelling errors in clinical user text.
    """
    if not text:
        return ""

    raw = text.strip()
    words = re.findall(r"\b[\w'-]+\b|[^\w\s]", raw)
    normalized_words = []

    for w in words:
        low = w.lower()

        # 1. Direct typo dictionary check
        if low in COMMON_TYPOS_MAP:
            normalized_words.append(COMMON_TYPOS_MAP[low])
            continue

        # 2. Clinical abbreviation expansion
        if low in CLINICAL_ABBREVIATIONS:
            # Preserve acronym expansion
            normalized_words.append(CLINICAL_ABBREVIATIONS[low])
            continue

        # 3. Fuzzy Levenshtein match against canonical vocabulary if word length >= 4
        if len(low) >= 4 and not low.isdigit() and low.isalpha():
            matches = difflib.get_close_matches(low, CANONICAL_CLINICAL_VOCABULARY, n=1, cutoff=0.82)
            if matches:
                normalized_words.append(matches[0])
                continue

        normalized_words.append(w)

    reconstructed = " ".join(normalized_words)
    # Clean spacing around punctuation
    reconstructed = re.sub(r"\s+([.,;:?!])", r"\1", reconstructed)
    reconstructed = re.sub(r"\s*/\s*", "/", reconstructed)
    return reconstructed


def fuzzy_match_token(candidate: str, target: str, cutoff: float = 0.78) -> bool:
    """Check if candidate word closely matches target word using SequenceMatcher."""
    c_low = candidate.lower().strip()
    t_low = target.lower().strip()
    if c_low == t_low or c_low in t_low or t_low in c_low:
        return True
    return difflib.SequenceMatcher(None, c_low, t_low).ratio() >= cutoff


def fuzzy_intent_detect(query: str) -> Dict[str, Any]:
    """
    Detects clinician intent (document generation, calculator, demographic lookup, emergency)
    with high tolerance for typos, abbreviations, and informal phrasing.
    """
    normalized = normalize_clinical_query(query)
    q = normalized.lower()

    result: Dict[str, Any] = {
        "original_query": query,
        "normalized_query": normalized,
        "intent": "general_clinical_qa",
        "document_type": None,
        "calculator_type": None,
        "demographic_field": None,
        "is_unstructured_case": False,
        "extracted_entities": {},
    }

    # 1. Document Generation Intent
    doc_trigger_words = ["generate", "create", "make", "order", "write", "draft", "prepare", "issue", "print"]
    doc_target_words = ["summary", "note", "certificate", "order", "prescription", "plan", "letter", "report", "triage", "requisition"]

    has_doc_trigger = any(fuzzy_match_token(w, t) for w in q.split() for t in doc_trigger_words)
    has_doc_target = any(fuzzy_match_token(w, t) for w in q.split() for t in doc_target_words)

    if has_doc_trigger or has_doc_target:
        if any(w in q for w in ["operative", "operation", "surgery", "surgical", "procedure note", "op note"]):
            result["intent"] = "generate_document"
            result["document_type"] = "operative_note"
        elif any(w in q for w in ["triage", "emergency transfer", "ed transfer", "emergency department triage"]):
            result["intent"] = "generate_document"
            result["document_type"] = "emergency_triage"
        elif any(w in q for w in ["radiology", "imaging", "x-ray", "xray", "ct scan", "mri requisition", "ultrasound order"]):
            result["intent"] = "generate_document"
            result["document_type"] = "radiology_order"
        elif any(w in q for w in ["discharge instructions", "home instructions", "patient instructions", "post-discharge instructions"]):
            result["intent"] = "generate_document"
            result["document_type"] = "discharge_instructions"
        elif any(w in q for w in ["discharge summary", "discharge note", "discharge report", "inpatient summary"]):
            result["intent"] = "generate_document"
            result["document_type"] = "discharge_summary"
        elif any(w in q for w in ["medical certificate", "sick note", "sick leave", "medical excuse", "leave certificate"]):
            result["intent"] = "generate_document"
            result["document_type"] = "medical_certificate"
        elif any(w in q for w in ["care plan", "treatment plan", "clinical care plan", "management plan"]):
            result["intent"] = "generate_document"
            result["document_type"] = "care_plan"
        elif any(w in q for w in ["referral letter", "referral note", "specialist referral", "referral to"]):
            result["intent"] = "generate_document"
            result["document_type"] = "referral_letter"
        elif any(w in q for w in ["lab order", "laboratory requisition", "investigation order", "blood tests order"]):
            result["intent"] = "generate_document"
            result["document_type"] = "lab_order"
        elif any(w in q for w in ["e-prescription", "prescription", "prescribe", "rx order", "medication order"]):
            result["intent"] = "generate_document"
            result["document_type"] = "e_prescription"
        elif any(w in q for w in ["sports clearance", "fitness certificate", "fitness to fly", "school certificate", "travel certificate", "certificate of fitness"]):
            result["intent"] = "generate_document"
            # Form clean dynamic doc type
            custom_match = re.search(r"(?:generate|issue|create|make|write)\s+(?:a\s+|an\s+|the\s+)?([a-z0-9_\s]{3,40})(?:\s+certificate|\s+letter|\s+document|\s+note)?", q)
            if custom_match:
                slug = re.sub(r"[^a-z0-9]+", "_", custom_match.group(1).strip()).strip("_")
                result["document_type"] = f"{slug}_certificate" if "certificate" not in slug else slug
            else:
                result["document_type"] = "sports_clearance_certificate"

    # 2. Clinical Calculator Intent
    if any(w in q for w in ["bmi", "body mass index"]):
        result["intent"] = "clinical_calculator"
        result["calculator_type"] = "bmi"
    elif any(w in q for w in ["map", "mean arterial pressure", "mean arterial"]):
        result["intent"] = "clinical_calculator"
        result["calculator_type"] = "map"
    elif any(w in q for w in ["curb-65", "curb 65", "curb65", "pneumonia score"]):
        result["intent"] = "clinical_calculator"
        result["calculator_type"] = "curb65"
    elif any(w in q for w in ["cha2ds2", "chads", "chads vasc", "cha2ds2-vasc", "stroke risk score"]):
        result["intent"] = "clinical_calculator"
        result["calculator_type"] = "cha2ds2_vasc"
    elif any(w in q for w in ["gcs", "glasgow coma", "glasgow coma scale"]):
        result["intent"] = "clinical_calculator"
        result["calculator_type"] = "gcs"
    elif any(w in q for w in ["normal vitals", "vitals reference", "vital signs table", "vital signs range"]):
        result["intent"] = "clinical_calculator"
        result["calculator_type"] = "normal_vitals"

    # 3. Patient Demographics Intent
    age_indicators = ["age", "how old", "patient age", "age of patient", "patient's age", "demographic", "dob", "birth"]
    if any(fuzzy_match_token(w, "age") for w in q.split()) or any(ind in q for ind in age_indicators):
        if not any(dis in q for dis in ["dengue", "dka", "malaria", "typhoid", "stroke", "covid"]):
            result["intent"] = "patient_demographic"
            result["demographic_field"] = "age"

    # 4. Unstructured Clinical Presentation / Case Presentation Detection
    case_indicators = [
        "presented with", "presented", "complaining of", "on examination", "on exam",
        "past medical history", "past history", "blood pressure", "heart rate",
        "oxygen saturation", "electrocardiogram", "ecg", "ekg", "bp", "hr", "spo2",
        "admitted with", "vital signs", "vitals", "st elevation", "troponin",
        "creatinine", "respiratory distress", "chest pain", "shortness of breath"
    ]
    indicator_count = sum(1 for ind in case_indicators if ind in q)
    has_hemodynamics = bool(
        re.search(r"\b(?:blood pressure|heart rate|oxygen saturation|temperature|bp|hr|spo2|vitals)\b", q)
        and re.search(r"\d{2,3}\s*/\s*\d{2,3}|\d{2,3}\s*bpm|\d{2,3}\s*%", q)
    )

    if (len(q.split()) > 10 and indicator_count >= 2) or (indicator_count >= 3) or has_hemodynamics:
        result["is_unstructured_case"] = True
        result["intent"] = "unstructured_case_presentation"

    return result

    return result


def extract_vitals_from_unstructured(text: str) -> Dict[str, str]:
    """Extract blood pressure, heart rate, spo2, temp, rr even from sloppy text."""
    vitals = {}
    norm = normalize_clinical_query(text)

    # Blood Pressure: e.g. 120/80, bp 85/55, 130 / 85 mmHg
    bp_match = re.search(r"\b(?:bp|blood pressure)?[:\s]*(\d{2,3})\s*/\s*(\d{2,3})\b", norm, re.I)
    if bp_match:
        vitals["blood_pressure"] = f"{bp_match.group(1)}/{bp_match.group(2)} mmHg"
        sbp, dbp = int(bp_match.group(1)), int(bp_match.group(2))
        vitals["map"] = f"{round((2 * dbp + sbp) / 3.0, 1)} mmHg"

    # Heart Rate: e.g. hr 118, pulse 95, hr: 120 bpm
    hr_match = re.search(r"\b(?:hr|heart rate|pulse)[:\s]*(\d{2,3})\b", norm, re.I)
    if hr_match:
        vitals["heart_rate"] = f"{hr_match.group(1)} bpm"

    # SpO2: e.g. spo2 92%, o2 sat 94
    spo2_match = re.search(r"\b(?:spo2|o2 sat|saturation)[:\s]*(\d{2,3})\s*%?\b", norm, re.I)
    if spo2_match:
        vitals["spo2"] = f"{spo2_match.group(1)}%"

    # Temperature: e.g. temp 102f, 38.5c
    temp_match = re.search(r"\b(?:temp|temperature)[:\s]*(\d{2,3}(?:\.\d+)?)\s*(?:°?([cfCF]))?\b", norm, re.I)
    if temp_match:
        unit = temp_match.group(2) or "°C"
        vitals["temperature"] = f"{temp_match.group(1)} {unit.upper()}"

    # Respiratory Rate: e.g. rr 28, resp 24
    rr_match = re.search(r"\b(?:rr|resp rate|respiratory rate)[:\s]*(\d{1,2})\b", norm, re.I)
    if rr_match:
        vitals["respiratory_rate"] = f"{rr_match.group(1)} breaths/min"

    return vitals
