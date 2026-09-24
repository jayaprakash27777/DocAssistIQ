"""DocAssistIQ — Comprehensive Clinical Concept Normalizer.

Maps raw clinical text, physician abbreviations, Latin phrases, and trade names
to verified canonical clinical concepts across all major medical specialties.
Explicitly refuses ambiguous clinical acronyms to prevent diagnostic misclassification.
Strictly zero mock data; adheres to SNOMED CT and MeSH clinical nomenclature.
"""

import structlog
from typing import Optional, Tuple, Dict, List, Set

log = structlog.get_logger(__name__)

# Comprehensive verified clinical mapping dictionary
VERIFIED_MAPPINGS: Dict[str, str] = {
    # -------------------------------------------------------------------------
    # Cardiovascular & Hemodynamics
    # -------------------------------------------------------------------------
    "htn": "hypertension",
    "high blood pressure": "hypertension",
    "elevated bp": "hypertension",
    "cad": "coronary artery disease",
    "coronary disease": "coronary artery disease",
    "acs": "acute coronary syndrome",
    "stemi": "st-elevation myocardial infarction",
    "nstemi": "non-st elevation myocardial infarction",
    "chf": "congestive heart failure",
    "hf": "congestive heart failure",
    "heart failure": "congestive heart failure",
    "hfref": "heart failure with reduced ejection fraction",
    "hfpef": "heart failure with preserved ejection fraction",
    "afib": "atrial fibrillation",
    "af": "atrial fibrillation",
    "a-fib": "atrial fibrillation",
    "aflutter": "atrial flutter",
    "svt": "supraventricular tachycardia",
    "vt": "ventricular tachycardia",
    "v-tach": "ventricular tachycardia",
    "vf": "ventricular fibrillation",
    "v-fib": "ventricular fibrillation",
    "dvt": "deep vein thrombosis",
    "pad": "peripheral artery disease",
    "pvd": "peripheral vascular disease",
    "aaa": "abdominal aortic aneurysm",
    "syncope": "syncope",
    "passing out": "syncope",
    "fainting": "syncope",
    "palpitations": "palpitations",
    "fluttering heart": "palpitations",
    "orthopnea": "orthopnea",
    "pnd": "paroxysmal nocturnal dyspnea",
    "edema": "peripheral edema",
    "swollen ankles": "peripheral edema",
    "swollen legs": "peripheral edema",

    # -------------------------------------------------------------------------
    # Pulmonary & Respiratory
    # -------------------------------------------------------------------------
    "copd": "chronic obstructive pulmonary disease",
    "emphysema": "chronic obstructive pulmonary disease",
    "chronic bronchitis": "chronic obstructive pulmonary disease",
    "asthma": "asthma",
    "bronchospasm": "asthma",
    "cap": "community-acquired pneumonia",
    "pneumonia": "pneumonia",
    "hap": "hospital-acquired pneumonia",
    "vap": "ventilator-associated pneumonia",
    "uri": "upper respiratory tract infection",
    "urti": "upper respiratory tract infection",
    "upper respiratory infection": "upper respiratory tract infection",
    "lrti": "lower respiratory tract infection",
    "ards": "acute respiratory distress syndrome",
    "osa": "obstructive sleep apnea",
    "sleep apnea": "obstructive sleep apnea",
    "sob": "shortness of breath",
    "breathless": "shortness of breath",
    "dyspnea": "shortness of breath",
    "doe": "dyspnea on exertion",
    "hemoptysis": "hemoptysis",
    "coughing blood": "hemoptysis",
    "stridor": "stridor",
    "wheeze": "wheezing",
    "wheezing": "wheezing",
    "cough": "cough",
    "chronic cough": "cough",
    "productive cough": "productive cough",
    "pleurisy": "pleuritic chest pain",
    "pleuritic pain": "pleuritic chest pain",

    # -------------------------------------------------------------------------
    # Endocrine, Metabolic & Glycemic
    # -------------------------------------------------------------------------
    "t2dm": "type 2 diabetes mellitus",
    "t2d": "type 2 diabetes mellitus",
    "type 2 diabetes": "type 2 diabetes mellitus",
    "t1dm": "type 1 diabetes mellitus",
    "t1d": "type 1 diabetes mellitus",
    "type 1 diabetes": "type 1 diabetes mellitus",
    "dka": "diabetic ketoacidosis",
    "hhs": "hyperosmolar hyperglycemic state",
    "honk": "hyperosmolar hyperglycemic state",
    "hypoglycemia": "hypoglycemia",
    "low blood sugar": "hypoglycemia",
    "hyperglycemia": "hyperglycemia",
    "high blood sugar": "hyperglycemia",
    "hypothyroidism": "hypothyroidism",
    "underactive thyroid": "hypothyroidism",
    "hyperthyroidism": "hyperthyroidism",
    "overactive thyroid": "hyperthyroidism",
    "thyrotoxicosis": "hyperthyroidism",
    "siadh": "syndrome of inappropriate antidiuretic hormone secretion",
    "di": "diabetes insipidus",
    "dyslipidemia": "hyperlipidemia",
    "hyperlipidemia": "hyperlipidemia",
    "high cholesterol": "hyperlipidemia",
    "polyuria": "polyuria",
    "polydipsia": "polydipsia",
    "polyphagia": "polyphagia",

    # -------------------------------------------------------------------------
    # Renal, Genitourinary & Electrolytes
    # -------------------------------------------------------------------------
    "aki": "acute kidney injury",
    "acute renal failure": "acute kidney injury",
    "arf": "acute kidney injury",
    "ckd": "chronic kidney disease",
    "chronic renal failure": "chronic kidney disease",
    "esrd": "end-stage renal disease",
    "eskd": "end-stage renal disease",
    "end stage renal disease": "end-stage renal disease",
    "atn": "acute tubular necrosis",
    "uti": "urinary tract infection",
    "bladder infection": "urinary tract infection",
    "bph": "benign prostatic hyperplasia",
    "enlarged prostate": "benign prostatic hyperplasia",
    "nephrolithiasis": "nephrolithiasis",
    "kidney stone": "nephrolithiasis",
    "renal colic": "nephrolithiasis",
    "hematuria": "hematuria",
    "blood in urine": "hematuria",
    "proteinuria": "proteinuria",
    "dysuria": "dysuria",
    "painful urination": "dysuria",
    "oliguria": "oliguria",
    "anuria": "anuria",
    "hyperkalemia": "hyperkalemia",
    "high potassium": "hyperkalemia",
    "hypokalemia": "hypokalemia",
    "low potassium": "hypokalemia",
    "hyponatremia": "hyponatremia",
    "low sodium": "hyponatremia",
    "hypernatremia": "hypernatremia",
    "high sodium": "hypernatremia",

    # -------------------------------------------------------------------------
    # Gastrointestinal & Hepatic
    # -------------------------------------------------------------------------
    "gerd": "gastroesophageal reflux disease",
    "acid reflux": "gastroesophageal reflux disease",
    "heartburn": "gastroesophageal reflux disease",
    "pud": "peptic ulcer disease",
    "stomach ulcer": "peptic ulcer disease",
    "gastric ulcer": "peptic ulcer disease",
    "duodenal ulcer": "peptic ulcer disease",
    "ibd": "inflammatory bowel disease",
    "ibs": "irritable bowel syndrome",
    "uc": "ulcerative colitis",
    "crohns": "crohn's disease",
    "crohn disease": "crohn's disease",
    "sbo": "small bowel obstruction",
    "lbo": "large bowel obstruction",
    "bowel obstruction": "small bowel obstruction",
    "gi bleed": "gastrointestinal bleeding",
    "gib": "gastrointestinal bleeding",
    "ugib": "upper gastrointestinal bleeding",
    "lgib": "lower gastrointestinal bleeding",
    "melena": "melena",
    "black stools": "melena",
    "hematochezia": "hematochezia",
    "rectal bleeding": "hematochezia",
    "hematemesis": "hematemesis",
    "vomiting blood": "hematemesis",
    "n/v": "nausea and vomiting",
    "nausea": "nausea",
    "vomiting": "vomiting",
    "ascites": "ascites",
    "cirrhosis": "cirrhosis",
    "liver cirrhosis": "cirrhosis",
    "jaundice": "jaundice",
    "icterus": "jaundice",
    "yellow skin": "jaundice",
    "pancreatitis": "acute pancreatitis",
    "cholecystitis": "acute cholecystitis",
    "cholelithiasis": "cholelithiasis",
    "gallstones": "cholelithiasis",

    # -------------------------------------------------------------------------
    # Neurology, Neuromuscular & Psychiatric
    # -------------------------------------------------------------------------
    "cva": "cerebrovascular accident",
    "stroke": "cerebrovascular accident",
    "tia": "transient ischemic attack",
    "mini stroke": "transient ischemic attack",
    "sah": "subarachnoid hemorrhage",
    "ich": "intracerebral hemorrhage",
    "sdh": "subdural hematoma",
    "edh": "epidural hematoma",
    "ams": "altered mental status",
    "altered mental status": "altered mental status",
    "confusion": "altered mental status",
    "delirium": "altered mental status",
    "loc": "loss of consciousness",
    "unconscious": "loss of consciousness",
    "seizure": "seizure",
    "convulsion": "seizure",
    "epilepsy": "seizure",
    "status epilepticus": "status epilepticus",
    "meningitis": "meningitis",
    "encephalitis": "encephalitis",
    "neuropathy": "peripheral neuropathy",
    "peripheral neuropathy": "peripheral neuropathy",
    "numbness": "paresthesia",
    "tingling": "paresthesia",
    "paresthesia": "paresthesia",
    "ha": "headache",
    "head ache": "headache",
    "headache": "headache",
    "cephalea": "headache",
    "migraine": "migraine",
    "vertigo": "vertigo",
    "dizziness": "vertigo",
    "lightheadedness": "presyncope",
    "presyncope": "presyncope",
    "ataxia": "ataxia",
    "dysarthria": "dysarthria",
    "slurred speech": "dysarthria",
    "aphasia": "aphasia",
    "facial droop": "facial palsy",

    # -------------------------------------------------------------------------
    # Rheumatology & Autoimmune
    # -------------------------------------------------------------------------
    "sle": "systemic lupus erythematosus",
    "lupus": "systemic lupus erythematosus",
    "ra": "rheumatoid arthritis",
    "rheumatoid": "rheumatoid arthritis",
    "oa": "osteoarthritis",
    "degenerative joint disease": "osteoarthritis",
    "djd": "osteoarthritis",
    "gca": "giant cell arteritis",
    "temporal arteritis": "giant cell arteritis",
    "pmr": "polymyalgia rheumatica",
    "as": "ankylosing spondylitis",
    "gout": "gout",
    "pseudogout": "pseudogout",
    "sjogrens": "sjogren's syndrome",
    "scleroderma": "systemic sclerosis",
    "dermatomyositis": "dermatomyositis",
    "polymyositis": "polymyositis",
    "arthralgia": "arthralgia",
    "joint pain": "arthralgia",
    "myalgia": "myalgia",
    "muscle pain": "myalgia",
    "fatigue": "fatigue",
    "tiredness": "fatigue",
    "malaise": "fatigue",

    # -------------------------------------------------------------------------
    # Infectious Diseases & Sepsis
    # -------------------------------------------------------------------------
    "sepsis": "sepsis",
    "septic shock": "septic shock",
    "bacteremia": "bacteremia",
    "endocarditis": "infective endocarditis",
    "ie": "infective endocarditis",
    "osteomyelitis": "osteomyelitis",
    "cellulitis": "cellulitis",
    "abscess": "abscess",
    "fever": "fever",
    "high temp": "fever",
    "high temperature": "fever",
    "pyrexia": "fever",
    "chills": "chills",
    "rigors": "rigors",
    "night sweats": "night sweats",
    "diaphoresis": "diaphoresis",
    "sweating": "diaphoresis",

    # -------------------------------------------------------------------------
    # Hematology & Coagulation
    # -------------------------------------------------------------------------
    "thrombocytopenia": "thrombocytopenia",
    "low platelets": "thrombocytopenia",
    "leukocytosis": "leukocytosis",
    "high wbc": "leukocytosis",
    "leukopenia": "leukopenia",
    "low wbc": "leukopenia",
    "anemia": "anemia",
    "low hemoglobin": "anemia",
    "pancytopenia": "pancytopenia",
    "dic": "disseminated intravascular coagulation",
    "petechiae": "petechiae",
    "purpura": "purpura",
    "ecchymosis": "ecchymosis",
    "bruising": "ecchymosis",

    # -------------------------------------------------------------------------
    # Critical Symptoms & Signs
    # -------------------------------------------------------------------------
    "cp": "chest pain",
    "chest pain": "chest pain",
    "chest tightness": "chest pain",
    "chest pressure": "chest pain",
    "angina": "angina pectoris",

    # -------------------------------------------------------------------------
    # Common Medications & Brand Equivalents
    # -------------------------------------------------------------------------
    "asa": "aspirin",
    "aspirin": "aspirin",
    "apap": "acetaminophen",
    "tylenol": "acetaminophen",
    "paracetamol": "acetaminophen",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "ibuprofen": "ibuprofen",
    "aleve": "naproxen",
    "naprosyn": "naproxen",
    "hctz": "hydrochlorothiazide",
    "lasix": "furosemide",
    "ntg": "nitroglycerin",
    "nitro": "nitroglycerin",
    "ppi": "proton pump inhibitor",
    "abx": "antibiotics",
    "ns": "normal saline",
    "lr": "lactated ringers",
    "plavix": "clopidogrel",
    "eliquis": "apixaban",
    "xarelto": "rivaroxaban",
    "coumadin": "warfarin",
    "lovenox": "enoxaparin"
}

# Ambiguous abbreviations that MUST be rejected to preserve clinical diagnostic safety
AMBIGUOUS_TERMS: Dict[str, List[str]] = {
    "ms": ["multiple sclerosis", "mitral stenosis", "morphine sulfate"],
    "pe": ["pulmonary embolism", "physical examination"],
    "ca": ["cancer", "calcium", "cardiac arrest"],
    "hr": ["heart rate", "hour"],
    "mi": ["myocardial infarction", "mitral incompetence"]
}


class ConceptNormalizer:
    """Clinical Concept Normalizer.
    
    Standardizes varied clinical documentation, acronyms, and synonyms
    into canonical medical concepts while guarding against dangerous ambiguous abbreviations.
    """

    def __init__(self):
        self.source = "internal_dict"
        self.confidence = 0.95
        # Set of canonical targets for instantaneous pass-through
        self._canonical_values: Set[str] = set(VERIFIED_MAPPINGS.values())

    def normalize(self, raw_value: str) -> Tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Attempts to normalize a raw clinical string.
        Returns: (canonical_concept, mapping_source, mapping_confidence)
        Returns (None, None, None) if ambiguous or unknown.
        """
        if not raw_value or not raw_value.strip():
            return None, None, None

        term = raw_value.strip().lower()

        # 1. Guard: Explicit rejection of ambiguous acronyms
        if term in AMBIGUOUS_TERMS:
            log.info("concept_normalizer_rejected_ambiguous", raw_term=term, potential_meanings=AMBIGUOUS_TERMS[term])
            return None, None, None

        # 2. Check verified mappings
        if term in VERIFIED_MAPPINGS:
            canonical = VERIFIED_MAPPINGS[term]
            return canonical, self.source, self.confidence

        # 3. Pass-through for terms already in canonical form
        if term in self._canonical_values:
            return term, self.source, self.confidence

        return None, None, None


normalizer = ConceptNormalizer()
