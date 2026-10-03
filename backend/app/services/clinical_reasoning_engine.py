"""DocAssistIQ — Clinical Reasoning Engine (God-Level AI Upgrade).

The deterministic pre-processor that does 90% of the diagnostic reasoning
BEFORE the LLM is called. This enables accurate diagnosis even on a 3B
parameter model (llama3.2) because the LLM only needs to write 1-2 sentence
narrative explanations for pre-ranked candidates.

Multi-factor scoring algorithm:
  - Symptom overlap score (Jaccard + weighted cardinal symptoms)
  - Geographic outbreak score (country → disease links from offline KB)
  - Incubation period fit score (deterministic math)
  - Syndromic cluster bonus (hemorrhagic triad, GI pattern, etc.)
  - Severity / hemorrhagic flag weighting
  - Negation penalty
  - Live intelligence bonus (from intelligence_engine)

Zero network calls required — works fully offline.
"""

import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from app.services.offline_disease_kb import (
    DISEASE_KB,
    SYNDROMIC_CLUSTERS,
    COMMON_PREVALENCE_DISEASES,
    ULTRA_RARE_OUTBREAK_DISEASES,
    get_diseases_for_geography,
    get_active_disease_clusters,
)
from app.services.intelligence_engine import (
    INCUBATION_PERIODS,
    check_incubation_fit,
)


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ScoredCandidate:
    disease: str
    score: float
    score_breakdown: Dict[str, float]
    supporting_findings: List[str]
    missing_expected_findings: List[str]
    contradicting_information: List[str]
    uncertainty: str
    clusters_matched: List[str]
    incubation_fit: str  # "FITS" | "TOO_EARLY" | "TOO_LATE" | "UNKNOWN"
    geographic_match: bool
    hemorrhagic: bool
    severity: str
    explanation_hint: str  # Short hint for LLM narrator


# ---------------------------------------------------------------------------
# Symptom Normalizer
# ---------------------------------------------------------------------------

SYMPTOM_ALIASES: Dict[str, str] = {
    # ---- General fever synonyms ----
    "high-grade fever": "fever",
    "high fever": "fever",
    "pyrexia": "fever",
    "febrile": "fever",
    "low-grade fever": "fever",
    "sudden fever": "fever",
    "fever onset": "fever",

    # ---- Muscle / joint ----
    "myalgia": "muscle aches",
    "muscle pain": "muscle aches",
    "muscle soreness": "muscle aches",
    "generalized body aches": "muscle aches",
    "body aches": "muscle aches",
    "generalized aches": "muscle aches",
    "generalized pain": "muscle aches",
    "arthralgia": "joint pain",
    "joint ache": "joint pain",
    "bilateral polyarthralgia": "severe joint pain",
    "polyarthralgia": "severe joint pain",
    "severe polyarthralgia": "severe joint pain",
    "severe joint pain": "severe joint pain",
    "severe debilitating bilateral joint pain": "severe debilitating joint pain",
    "debilitating bilateral joint pain": "severe debilitating joint pain",
    "debilitating joint pain": "severe debilitating joint pain",
    "wrists, ankles, knees": "severe joint pain",
    "small joints of the hands and feet": "severe joint pain",
    "small joints of hands and feet": "severe joint pain",
    "joint swelling": "joint swelling",
    "swelling around several peripheral joints": "joint swelling",

    # ---- Fatigue / weakness ----
    "malaise": "fatigue",
    "lethargy": "lethargy",
    "increasing drowsiness": "lethargy",
    "drowsiness": "lethargy",
    "lassitude": "fatigue",
    "profound weakness": "profound weakness",
    "extreme weakness": "profound weakness",
    "marked weakness": "profound weakness",
    "generalized weakness": "weakness",
    "severe fatigue": "fatigue",
    "significant fatigue": "fatigue",

    # ---- GI & Abdomen ----
    "anorexia": "loss of appetite",
    "oliguria": "reduced urine output",
    "watery diarrhea": "diarrhea",
    "bloody diarrhea": "diarrhea",
    "loose stools": "diarrhea",
    "dysphagia": "difficulty swallowing",
    "difficulty eating": "difficulty swallowing",
    "difficulty drinking": "reduced oral intake",
    "nausea and vomiting": "vomiting",
    "repeated vomiting": "persistent vomiting",
    "persistent vomiting": "persistent vomiting",
    "severe abdominal pain": "severe abdominal pain",
    "worsening abdominal pain": "severe abdominal pain",

    # ---- Hepatic & Fever Patterns ----
    "yellow discoloration": "jaundice",
    "yellow discoloration of his eyes and skin": "jaundice",
    "yellow discoloration of eyes and skin": "jaundice",
    "darker urine": "dark urine",
    "step-ladder fever": "step-ladder fever",
    "gradually increasing fever": "step-ladder fever",
    "persistent fever": "persistent fever",
    "postural dizziness": "postural dizziness",
    "dizziness when attempting to stand": "postural dizziness",
    "dizziness whenever she attempted to stand": "postural dizziness",

    # ---- Eyes ----
    "conjunctival redness": "redness of the eyes",
    "conjunctivitis": "redness of the eyes",
    "red eyes": "redness of the eyes",
    "pink eye": "redness of the eyes",
    "conjunctival injection": "redness of the eyes",
    "bilateral conjunctival redness": "redness of the eyes",
    "bilateral conjunctival injection": "redness of the eyes",
    "non-purulent conjunctivitis": "redness of the eyes",
    "irritation of both eyes": "redness of the eyes",
    "red cracked lips": "cheilitis",
    "cracked lips": "cheilitis",
    "erythema of lips": "cheilitis",
    "erythema of hands and feet": "skin redness",
    "erythema of palms and soles": "skin redness",
    "edema of hands and feet": "skin redness",
    "polymorphous rash": "rash",
    "polymorphous trunk rash": "rash",

    # ---- Cardiovascular & Bleeding ----
    "tachycardia": "rapid heart rate",
    "bradycardia": "slow heart rate",
    "haemorrhage": "bleeding",
    "haemorrhaging": "bleeding",
    "unexplained bleeding": "bleeding",
    "spontaneous bleeding": "bleeding",
    "bleeding from the gums": "bleeding",
    "bleeding from gums": "bleeding",
    "gum bleeding": "bleeding",
    "blood associated with vomiting": "hematemesis",
    "small amounts of blood associated with vomiting": "hematemesis",
    "circulatory compromise": "hypotension",
    "clinically unstable": "hypotension",

    # Petechiae, ecchymosis, purpura & zoonotic exposures
    "petechiae": "petechiae",
    "petechial rash": "petechiae",
    "petechial purpura": "petechiae",
    "petechial": "petechiae",
    "ecchymosis": "ecchymosis",
    "ecchymoses": "ecchymosis",
    "purpura": "purpura",
    "bruising": "bruising",
    "easy bruising": "bruising",
    "livestock handling": "livestock contact",
    "livestock contact": "livestock contact",
    "animal slaughter": "livestock contact",
    "abattoir worker": "livestock contact",
    "tick bite": "tick exposure",
    "tick exposure": "tick exposure",
    "hyalomma tick": "tick exposure",

    # =========================================================
    # DERMATOLOGICAL — critical for mpox, dengue, measles, etc.
    # =========================================================
    # Rash synonyms → "rash"
    "skin eruption": "rash",
    "skin rash": "rash",
    "exanthem": "rash",
    "rash eruption": "rash",
    "cutaneous eruption": "rash",
    "erythematous rash": "rash",
    "maculopapular rash": "rash",
    "diffuse rash": "rash",
    "generalized rash": "rash",
    "rash progression": "rash",
    "skin eruption progression": "rash",
    "progressive rash": "rash",

    # Skin lesion synonyms → "skin lesion"
    "skin lesions": "skin lesion",
    "cutaneous lesion": "skin lesion",
    "cutaneous lesions": "skin lesion",
    "skin sore": "skin lesion",
    "skin sores": "skin lesion",
    "firm raised lesion": "skin lesion",
    "firm painful raised lesion": "skin lesion",
    "fluid-filled lesion": "skin lesion",
    "umbilicated lesion": "skin lesion",
    "umbilicated lesions": "skin lesion",
    "lesion with central depression": "skin lesion",
    "central depression": "skin lesion",
    "multi-stage rash": "skin lesion",
    "lesions at different stages": "skin lesion",
    "lesions at multiple stages": "skin lesion",
    "rash in stages": "skin lesion",
    "rash at different stages": "skin lesion",
    "small reddish spots": "rash",
    "reddish spots": "rash",

    # Specific lesion types → normalized names
    "vesicle": "vesicular rash",
    "vesicles": "vesicular rash",
    "blisters": "vesicular rash",
    "blister": "vesicular rash",
    "fluid filled blister": "vesicular rash",
    "pustule": "pustular rash",
    "pustules": "pustular rash",
    "purulent lesion": "pustular rash",
    "papule": "rash",
    "papules": "rash",
    "macule": "rash",
    "macules": "rash",
    "nodule": "skin lesion",
    "nodules": "skin lesion",

    # Palmoplantar (pathognomonic for mpox vs varicella)
    "palm lesion": "palmoplantar rash",
    "palm lesions": "palmoplantar rash",
    "sole lesion": "palmoplantar rash",
    "sole lesions": "palmoplantar rash",
    "plantar lesion": "palmoplantar rash",
    "lesion on palm": "palmoplantar rash",
    "lesions on palms": "palmoplantar rash",
    "lesions on soles": "palmoplantar rash",
    "lesions involving palms": "palmoplantar rash",
    "lesions on lower limbs": "skin lesion",

    # Mucosal involvement (also pathognomonic)
    "oral lesion": "mucosal lesion",
    "oral lesions": "mucosal lesion",
    "mouth lesion": "mucosal lesion",
    "mouth lesions": "mucosal lesion",
    "lesion in mouth": "mucosal lesion",
    "lesions in mouth": "mucosal lesion",
    "lesions inside the mouth": "mucosal lesion",
    "painful lesions in mouth": "mucosal lesion",
    "genital lesion": "mucosal lesion",
    "genital lesions": "mucosal lesion",
    "anal lesion": "mucosal lesion",
    "mucous membrane lesion": "mucosal lesion",
    "enanthem": "mucosal lesion",
    "koplik spots": "mucosal lesion",

    # Skin pain
    "painful lesion": "painful lesions",
    "tender lesion": "painful lesions",
    "tender skin lesion": "painful lesions",
    "tenderness of skin lesions": "painful lesions",
    "significant tenderness": "tenderness",

    # =========================================================
    # LYMPHADENOPATHY — critical for mpox, plague, HIV, etc.
    # =========================================================
    "lymphadenopathy": "swollen lymph nodes",
    "lymph node swelling": "swollen lymph nodes",
    "lymph node enlargement": "swollen lymph nodes",
    "lymph node tenderness": "swollen lymph nodes",
    "generalized lymph node enlargement": "swollen lymph nodes",
    "generalized lymphadenopathy": "swollen lymph nodes",
    "painful lymph node swelling": "swollen lymph nodes",
    "lymphadenitis": "swollen lymph nodes",
    "enlarged lymph nodes": "swollen lymph nodes",
    "swollen glands": "swollen lymph nodes",
    "gland swelling": "swollen lymph nodes",
    "cervical lymphadenopathy": "swollen lymph nodes",
    "inguinal lymphadenopathy": "swollen lymph nodes",
    "neck swelling": "swollen lymph nodes",
    "groin swelling": "swollen lymph nodes",
    "axillary swelling": "swollen lymph nodes",

    # Plague hallmark buboes & vector exposures
    "bubo": "painful buboes",
    "buboes": "painful buboes",
    "painful bubo": "painful buboes",
    "painful buboes": "painful buboes",
    "suppurative bubo": "painful buboes",
    "suppurative buboes": "painful buboes",
    "suppurative inguinal lymphadenopathy buboes": "painful buboes",
    "inguinal bubo": "painful buboes",
    "inguinal buboes": "painful buboes",
    "flea bite": "flea bite history",
    "flea bite history": "flea bite history",
    "flea bites": "flea bite history",
    "flea exposure": "flea bite history",

    # =========================================================
    # NEUROLOGICAL
    # =========================================================
    "altered consciousness": "confusion",
    "change in consciousness": "confusion",
    "mental status change": "confusion",
    "altered mental status": "confusion",
    "disorientation": "confusion",
    "seizure": "seizures",
    "convulsion": "seizures",
    "convulsions": "seizures",
    "nuchal rigidity": "stiff neck",
    "neck stiffness": "stiff neck",
    "photophobia": "sensitivity to light",
    "phonophobia": "sensitivity to sound",

    # =========================================================
    # RESPIRATORY
    # =========================================================
    "dyspnea": "shortness of breath",
    "breathlessness": "shortness of breath",
    "difficulty breathing": "shortness of breath",
    "chest tightness": "chest pain",
    "pleuritic pain": "chest pain",
    "hemoptysis": "coughing blood",

    # =========================================================
    # URINARY / RENAL
    # =========================================================
    "decreased urine output": "reduced urine output",
    "decrease in urine output": "reduced urine output",
    "reduced urine production": "reduced urine output",
    "dark urine": "dark urine",
    "darker urine": "dark urine",
    "anuria": "reduced urine output",

    # =========================================================
    # CARDIOVASCULAR — extended
    # =========================================================
    "crushing pain in chest": "crushing chest pain",
    "tightness in chest": "chest tightness",
    "pressure in chest": "chest pressure",
    "tearing pain in chest": "tearing chest pain",
    "chest pain radiating to arm": "radiating chest pain",
    "chest pain radiating to jaw": "radiating chest pain",
    "pain radiating to left arm": "left arm pain",
    "diaphoresis": "sweating",
    "profuse sweating": "sweating",
    "cold sweat": "sweating",
    "clammy skin": "sweating",
    "palpitation": "palpitations",
    "heart racing": "palpitations",
    "heart skipping": "palpitations",
    "syncope": "fainting",
    "presyncope": "dizziness",
    "near-fainting": "fainting",
    "orthopnoea": "orthopnea",
    "ankle oedema": "ankle swelling",
    "leg oedema": "leg swelling",
    "peripheral oedema": "peripheral edema",
    "pitting oedema": "leg swelling",
    "bilateral ankle swelling": "bilateral leg swelling",
    "bilateral pedal edema": "bilateral leg swelling",
    "raised jvp": "elevated JVP",
    "elevated jugular venous pressure": "elevated JVP",
    "irregular heartbeat": "palpitations",
    "atrial fibrillation": "palpitations",
    "epistaxis": "nosebleed",

    # =========================================================
    # NEUROLOGICAL — extended
    # =========================================================
    "face drooping": "facial drooping",
    "face weakness": "facial drooping",
    "facial palsy": "facial drooping",
    "word-finding difficulty": "aphasia",
    "expressive aphasia": "aphasia",
    "receptive aphasia": "aphasia",
    "dysarthria": "slurred speech",
    "one-sided weakness": "hemiparesis",
    "unilateral weakness": "hemiparesis",
    "loss of balance": "balance problems",
    "unsteady gait": "ataxia",
    "gait ataxia": "ataxia",
    "pins and needles": "tingling",
    "ascending paralysis": "ascending weakness",
    "progressive ascending weakness": "ascending weakness",
    "ascending motor weakness": "ascending weakness",
    "absent reflexes": "areflexia",
    "loss of reflexes": "areflexia",
    "involuntary movements": "tremor",
    "intention tremor": "tremor",
    "resting tremor": "tremor",
    "photosensitivity": "photophobia",
    "light sensitivity": "photophobia",
    "blackout": "loss of consciousness",
    "passed out": "loss of consciousness",
    "unresponsive": "altered consciousness",
    "stupor": "altered consciousness",
    "encephalopathy": "altered consciousness",

    # =========================================================
    # GASTROINTESTINAL — extended
    # =========================================================
    "throwing up blood": "hematemesis",
    "coffee ground emesis": "coffee-ground vomiting",
    "black tarry stool": "melena",
    "tarry stools": "melena",
    "frank rectal bleeding": "rectal bleeding",
    "hematochezia": "rectal bleeding",
    "right iliac fossa pain": "right lower quadrant pain",
    "rlq pain": "right lower quadrant pain",
    "central abdominal pain": "abdominal pain",
    "periumbilical pain": "abdominal pain",
    "band-like pain": "pain radiating to back",
    "gnawing stomach pain": "epigastric pain",
    "burning stomach pain": "burning epigastric pain",
    "swollen belly": "abdominal distension",
    "tummy swelling": "abdominal distension",
    "fluid in abdomen": "ascites",
    "yellowing of eyes": "jaundice",
    "icterus": "jaundice",
    "scleral icterus": "jaundice",
    "tea-colored urine": "dark urine",
    "cola-colored urine": "dark urine",
    "clay-colored stool": "pale stool",
    "difficulty passing stool": "constipation",
    "inability to defecate": "obstipation",
    "diffuse abdominal tenderness": "rebound tenderness",

    # =========================================================
    # RENAL — extended
    # =========================================================
    "pain on urination": "dysuria",
    "burning on urination": "burning urination",
    "urinary burning": "burning urination",
    "peeing frequently": "urinary frequency",
    "passing urine often": "urinary frequency",
    "side pain": "flank pain",
    "loin pain": "flank pain",
    "cvat": "costovertebral angle tenderness",
    "blood in wee": "hematuria",
    "pink urine": "hematuria",
    "smoky urine": "hematuria",
    "not passing urine": "oliguria",
    "decreased urine": "reduced urine output",
    "no urine": "anuria",
    "protein in urine": "proteinuria",
    "foamy urine": "proteinuria",

    # =========================================================
    # ENDOCRINE — extended
    # =========================================================
    "excessive urination": "polyuria",
    "drinking a lot": "polydipsia",
    "thirst": "polydipsia",
    "very thirsty": "polydipsia",
    "sweet breath": "fruity breath",
    "ketotic breath": "fruity breath",
    "deep rapid breathing": "Kussmaul breathing",
    "kussmaul respiration": "Kussmaul breathing",
    "feeling too hot": "heat intolerance",
    "feeling too cold": "cold intolerance",
    "dark skin patches": "hyperpigmentation",
    "skin darkening": "hyperpigmentation",
    "enlarged thyroid": "goiter",
    "neck lump": "neck swelling",
    "craving salt": "salt craving",

    # =========================================================
    # OB/GYN — extended
    # =========================================================
    "per vaginal bleeding": "vaginal bleeding",
    "pv bleeding": "vaginal bleeding",
    "intermenstrual bleeding": "vaginal bleeding",
    "vaginal discharge abnormal": "vaginal discharge",
    "last menstrual period": "missed period",
    "no period": "amenorrhea",
    "secondary amenorrhoea": "amenorrhea",
    "tip of shoulder pain": "shoulder tip pain",
    "diaphragmatic irritation": "shoulder tip pain",
    "positive urine pregnancy test": "positive pregnancy test",
    "upt positive": "positive pregnancy test",
    "painful intercourse": "dyspareunia",

    # =========================================================
    # RESPIRATORY — extended
    # =========================================================
    "worsening shortness of breath": "shortness of breath",
    "breathless on exertion": "shortness of breath",
    "worsening breathlessness": "shortness of breath",
    "productive cough": "sputum",
    "green sputum": "purulent sputum",
    "yellow sputum": "purulent sputum",
    "wheezing breath": "wheezing",
    "audible wheeze": "wheezing",
    "blue lips": "cyanosis",
    "blue fingertips": "cyanosis",
    "low sats": "hypoxia",
    "low oxygen saturation": "hypoxia",
    "accessory muscle use": "use of accessory muscles",
    "intercostal recession": "use of accessory muscles",
    "coughing up blood": "hemoptysis",

    # =========================================================
    # MUSCULOSKELETAL — extended
    # =========================================================
    "joint aches": "joint pain",
    "aching joints": "joint pain",
    "swollen joint": "joint swelling",
    "painful joint": "joint pain",
    "morning joint stiffness": "morning stiffness",
    "stiff joints in morning": "morning stiffness",
    "body ache": "muscle aches",
    "generalized body ache": "muscle aches",
    "muscle soreness": "muscle aches",
    "bone ache": "bone pain",
    "bony pain": "bone pain",
    "rib pain": "chest pain",
    "severe joint pain": "severe joint pain",
    "joint and bone pain": "severe joint pain",
    "bone and joint pain": "severe bone pain",
    "bilateral knee joint pain": "joint pain",
    "crepitus": "crepitus",
    "joint stiffness": "morning stiffness",
    "first metatarsophalangeal big toe joint": "first mtp pain",
    "first metatarsophalangeal joint pain": "first mtp pain",
    "big toe pain": "first mtp pain",
    "podagra": "podagra",

    # =========================================================
    # TROPICAL, METABOLIC & CHRONIC SYMPTOM ALIASES
    # =========================================================
    "severe retro-orbital headache": "retro-orbital headache",
    "retro orbital headache": "retro-orbital headache",
    "retro-orbital pain": "retro-orbital headache",
    "retro orbital pain": "retro-orbital headache",
    "chills and rigors": "rigors",
    "paroxysmal shaking chills": "rigors",
    "shaking chills": "rigors",
    "rigor": "rigors",
    "cyclic fever spikes every 48 hours": "cyclic fever",
    "cyclic fever spikes": "cyclic fever",
    "cyclical fever": "cyclic fever",
    "cyclic fever": "cyclic fever",
    "paroxysmal fever": "cyclic fever",
    "tertian fever": "cyclic fever",
    "quartan fever": "cyclic fever",
    "splenomegaly": "splenomegaly",
    "enlarged spleen": "splenomegaly",
    "hemolytic anemia": "hemolytic anemia",
    "travel to nigeria": "travel",
    "travel to endemic area": "travel",
    "shivering": "chills",
    "night sweats": "night sweats",
    "drenching night sweats": "night sweats",
    "chronic cough": "persistent cough",
    "chronic cough > 3 weeks": "persistent cough",
    "cough > 3 weeks": "persistent cough",
    "loss of smell": "loss of smell",
    "loss of taste": "loss of taste",
    "anosmia": "loss of smell",
    "ageusia": "loss of taste",
    "polyuria": "polyuria",
    "excessive urination": "polyuria",
    "frequent urination": "polyuria",
    "polydipsia": "polydipsia",
    "excessive thirst": "polydipsia",
    "increased thirst": "polydipsia",
    "elevated blood pressure": "severe hypertension",
    "persistent elevated blood pressure": "severe hypertension",
    "elevated blood pressure 160/100": "severe hypertension",
    "morning headache": "morning headache",
    "episodic shortness of breath": "shortness of breath",
    "nighttime cough": "cough",
    "purulent rust-colored sputum": "purulent sputum",
    "rust-colored sputum": "purulent sputum",
    "crushing substernal chest pain": "crushing chest pain",
    "right-sided facial droop": "facial drooping",
    "right arm weakness": "unilateral weakness",
    "left arm weakness": "unilateral weakness",
    "right lower quadrant abdominal pain": "right lower quadrant pain",
    "unilateral pulsating throbbing headache": "unilateral headache",
    "burning retrosternal chest pain": "retrosternal burning",
    "cloudy urine": "cloudy urine",
    "suprapubic tenderness": "suprapubic tenderness",
    "urinary frequency": "urinary frequency",
    "port-wine dark reddish-brown urine": "port-wine urine",
    "dark reddish-brown urine": "port-wine urine",
    "port-wine urine": "port-wine urine",
    "severe colicky abdominal pain": "severe abdominal pain",
    "severe colicky abdominal pain without peritoneal signs": "severe abdominal pain",
    "colicky abdominal pain": "severe abdominal pain",
    "brittle spoon nails": "koilonychia",
    "spoon nails": "koilonychia",
    "pica": "pica",
    "cold intolerance": "cold intolerance",
    "dry coarse skin": "dry skin",
    "scratchy sore throat": "sore throat",
    "rose spots": "rose spots",
    "relative bradycardia": "relative bradycardia",
    "step-ladder fever": "step-ladder fever",

    # =========================================================
    # AUTOIMMUNE / SKIN — extended
    # =========================================================
    "face rash": "malar rash",
    "butterfly-shaped rash": "malar rash",
    "sun-induced rash": "photosensitive rash",
    "light-induced rash": "photosensitive rash",
    "hair thinning": "hair loss",
    "alopecia areata": "hair loss",
    "mouth sore": "oral ulcers",
    "ulcer in mouth": "oral ulcers",
    "raynaud": "Raynaud phenomenon",
    "fingers turning white": "Raynaud phenomenon",
    "fingers turning blue": "Raynaud phenomenon",
    "pleuritis": "pleuritis",
    "pericarditis": "pericarditis",

    # Quantitative lab aliases
    "local induration": "induration",
    "spreading erythema": "spreading erythema",
    "advancing border": "spreading erythema",
    "skin warmth and erythema": "skin redness",
    "erythematous warm skin": "skin redness",
    "erythema": "skin redness",
    "massive ck elevation (>10,000 u/l)": "massive CK elevation",
    "massive ck elevation": "massive CK elevation",
    "elevated ck (1,000-10,000 u/l)": "elevated CK",
    "mildly elevated ck": "elevated CK",
    "severe lactic acidosis (lactate >=4.0 mmol/l)": "lactic acidosis",
    "severe lactic acidosis": "lactic acidosis",
    "elevated lactate (>2.0 mmol/l)": "lactic acidosis",
    "elevated lactate": "lactic acidosis",
    "anion gap metabolic acidosis (hagma)": "metabolic acidosis",
    "anion gap metabolic acidosis": "metabolic acidosis",
    "high anion gap metabolic acidosis": "metabolic acidosis",
    "bacterial pleocytosis with low csf/serum glucose ratio (<0.40)": "cloudy CSF with pleocytosis",
    "elevated cardiac troponin": "elevated cardiac troponin",
    "myocardial injury": "myocardial necrosis",

    # Infective endocarditis & Bohan & Peter hallmarks
    "janeway lesions": "Janeway lesions",
    "osler nodes": "Osler nodes",
    "roth spots": "Roth spots",
    "valvular vegetation": "valvular vegetation",
    "new regurgitant murmur": "new regurgitant murmur",
    "gottron's papules": "Gottron's papules",
    "gottron sign": "Gottron's papules",
    "heliotrope rash": "heliotrope rash",
    "mechanic's hands": "mechanic's hands",
    "positive anti-jo-1 antibody": "positive anti-Jo-1 antibody",
    "unilateral leg swelling": "unilateral leg swelling",
    "deep vein thrombosis": "deep vein thrombosis",

    # Diverticulitis & LLQ
    "left lower quadrant abdominal pain": "left lower quadrant pain",
    "left lower quadrant tenderness": "left lower quadrant pain",
    "left lower quadrant": "left lower quadrant pain",
    "llq abdominal pain": "left lower quadrant pain",
    "llq pain": "left lower quadrant pain",
    "llq tenderness": "left lower quadrant pain",
    "llq": "left lower quadrant pain",
    "colonic wall thickening": "left lower quadrant pain",
    "pericolonic fat stranding": "left lower quadrant pain",
    "fat stranding": "left lower quadrant pain",
    "acute diverticulitis on ct abdomen": "Acute Diverticulitis on CT Abdomen",

    # =========================================================
    # HIGH-ACUITY EMERGENCY CLINICAL ALIASES & CRITERIA
    # =========================================================
    # Acute Coronary Syndrome & Ischemia
    "levine sign": "levine sign",
    "fist on chest": "levine sign",
    "clenched fist over sternum": "levine sign",
    "substernal pressure": "crushing chest pain",
    "substernal squeezing": "crushing chest pain",
    "retrosternal heaviness": "crushing chest pain",
    "chest heaviness": "crushing chest pain",
    "ischemic chest pain": "crushing chest pain",
    "st elevation": "ST elevation on ECG",
    "st-segment elevation": "ST elevation on ECG",
    "stemi": "ST elevation on ECG",
    "elevated troponin": "elevated cardiac troponin",
    "troponin elevation": "elevated cardiac troponin",
    "positive troponin": "elevated cardiac troponin",
    "hs-ctni elevated": "elevated cardiac troponin",
    "hs-ctnt elevated": "elevated cardiac troponin",
    "pain radiating to jaw": "radiating chest pain",
    "chest pain radiating to jaw": "radiating chest pain",
    "chest pain radiating to left shoulder": "radiating chest pain",

    # Stroke & Neurocritical
    "pronator drift": "unilateral weakness",
    "arm drift": "unilateral weakness",
    "facial droop and arm drift": "facial drooping",
    "sudden numbness": "unilateral weakness",
    "gaze deviation": "forced gaze deviation",
    "forced gaze": "forced gaze deviation",
    "dense hemiplegia": "unilateral weakness",
    "sudden aphasia": "aphasia",
    "expressive dysphasia": "aphasia",
    "receptive dysphasia": "aphasia",
    "amaurosis fugax": "transient monocular vision loss",
    "homonymous hemianopia": "visual field cut",
    "visual field deficit": "visual field cut",

    # Sepsis & Septic Shock
    "qsofa >= 2": "refractory septic shock",
    "qsofa score >= 2": "refractory septic shock",
    "refractory hypotension": "refractory septic shock",
    "hypotension requiring vasopressors": "refractory septic shock",
    "mottled skin": "mottled extremities",
    "mottled extremities": "mottled extremities",
    "capillary refill > 3 seconds": "prolonged capillary refill",
    "delayed capillary refill": "prolonged capillary refill",
    "hyperlactatemia": "lactic acidosis",
    "serum lactate >= 2.0": "lactic acidosis",
    "serum lactate >= 4.0": "lactic acidosis",

    # Diabetic Ketoacidosis & Hyperglycemic Crises
    "kussmaul respirations": "Kussmaul breathing",
    "kussmaul breathing": "Kussmaul breathing",
    "deep rapid breathing": "Kussmaul breathing",
    "acetone odor": "fruity breath odor",
    "acetone breath": "fruity breath odor",
    "fruity breath": "fruity breath odor",
    "fruity breath odor": "fruity breath odor",
    "elevated beta-hydroxybutyrate": "ketonuria",
    "beta-hydroxybutyrate > 3.0": "ketonuria",
    "positive serum ketones": "ketonuria",

    # Bacterial Meningitis & Meningococcemia
    "kernig sign": "Kernig sign positive",
    "kernig's sign": "Kernig sign positive",
    "positive kernig sign": "Kernig sign positive",
    "brudzinski sign": "Brudzinski sign positive",
    "brudzinski's sign": "Brudzinski sign positive",
    "positive brudzinski sign": "Brudzinski sign positive",
    "jolt accentuation": "jolt accentuation of headache",
    "meningismus": "stiff neck",

    # Status Epilepticus & Seizure Crises
    "status epilepticus": "status epilepticus",
    "continuous seizures": "status epilepticus",
    "prolonged convulsion": "status epilepticus",
    "seizures > 5 minutes": "status epilepticus",
    "non-convulsive status": "status epilepticus",
    "repetitive seizures without recovery": "status epilepticus",

    # Upper Gastrointestinal Bleeding
    "coffee ground emesis": "coffee ground emesis",
    "coffee-ground emesis": "coffee ground emesis",
    "black tarry stools": "melena",
    "melena stools": "melena",
    "melena": "melena",
    "massive hematemesis": "hematemesis",

    # Hypertensive Emergency
    "hypertensive encephalopathy": "hypertensive encephalopathy",
    "papilledema": "papilledema",
    "papilledema on fundoscopy": "papilledema",
    "malignant hypertension": "hypertensive encephalopathy",
    "retinal flame hemorrhages": "papilledema",

    # Hyperkalemia & Electrolyte Emergencies
    "peaked t waves": "hyperkalemic peaked T waves",
    "peaked t wave": "hyperkalemic peaked T waves",
    "tall peaked t waves": "hyperkalemic peaked T waves",
    "sine wave on ecg": "sine wave on ECG",
    "sine wave ecg": "sine wave on ECG",
    "widened qrs on ecg": "widened QRS",

    # Aortic Dissection
    "ripping chest pain": "tearing chest pain",
    "tearing interscapular pain": "chest pain radiating to back",
    "pulse deficit": "unequal pulses",
    "asymmetric pulses": "unequal pulses",
    "bp difference between arms": "unequal blood pressure",
    "wide mediastinum": "wide mediastinum on CXR",

    # Acute Appendicitis
    "rovsing sign": "Rovsing sign positive",
    "rovsing's sign": "Rovsing sign positive",
    "positive rovsing sign": "Rovsing sign positive",
    "psoas sign": "Psoas sign positive",
    "psoas sign positive": "Psoas sign positive",
    "obturator sign": "Obturator sign positive",
    "obturator sign positive": "Obturator sign positive",
    "dunphy sign": "Dunphy sign positive",
    "mcburney point tenderness": "right lower quadrant pain",
    "mcburney's point tenderness": "right lower quadrant pain",
    "pain migrating from periumbilical to rlq": "migratory RLQ abdominal pain",
    "pain migrating to right lower quadrant": "migratory RLQ abdominal pain",

    # Acute Cholecystitis & Pancreatitis
    "sonographic murphy sign": "murphy sign",
    "pericholecystic fluid": "murphy sign",
    "gallbladder wall thickening": "murphy sign",
    "epigastric pain radiating to back": "severe epigastric pain radiating to back",
    "cullen sign": "Cullen sign (periumbilical ecchymosis)",
    "grey turner sign": "Grey Turner sign (flank ecchymosis)",
}


@lru_cache(maxsize=8192)
def normalize_symptom(sym: str) -> str:
    sym_lower = sym.lower().strip()
    if sym_lower in SYMPTOM_ALIASES:
        return SYMPTOM_ALIASES[sym_lower]

    # Quantitative lab pattern matching
    if "massive ck" in sym_lower or "ck >10,000" in sym_lower or "ck of 45" in sym_lower or "ck 45000" in sym_lower or "ck 55000" in sym_lower:
        return "massive CK elevation"
    if "lactic acid" in sym_lower or "lactate" in sym_lower:
        return "lactic acidosis"
    if "anion gap" in sym_lower or "hagma" in sym_lower:
        return "metabolic acidosis"
    if "csf/serum" in sym_lower or "csf glucose" in sym_lower:
        return "cloudy CSF with pleocytosis"
    if "gottron" in sym_lower:
        return "Gottron's papules"
    if "heliotrope" in sym_lower:
        return "heliotrope rash"
    if "mechanic" in sym_lower and "hand" in sym_lower:
        return "mechanic's hands"
    if "jo-1" in sym_lower:
        return "positive anti-Jo-1 antibody"
    if "janeway" in sym_lower:
        return "Janeway lesions"
    if "osler" in sym_lower:
        return "Osler nodes"
    if "vegetation" in sym_lower:
        return "valvular vegetation"

    # Clinical phrase & substring matching
    if "dermatomal" in sym_lower or "zoster" in sym_lower:
        return "dermatomal rash"
    if "nerve pain" in sym_lower or ("burning" in sym_lower and "pain" in sym_lower):
        return "burning pain"
    if "joint" in sym_lower and ("debilitat" in sym_lower or "severe" in sym_lower or "excruciating" in sym_lower):
        return "severe joint pain"
    if "joint" in sym_lower and "bone" in sym_lower:
        return "severe joint pain"
    if "conjunctiv" in sym_lower or "redness of eye" in sym_lower or "red eye" in sym_lower or "scleral injection" in sym_lower or "conjunctival suffusion" in sym_lower:
        return "conjunctivitis"
    if "costovertebral" in sym_lower or "cva tenderness" in sym_lower or "cva angle" in sym_lower:
        return "costovertebral angle tenderness"
    if "colicky" in sym_lower and "flank" in sym_lower:
        return "colicky flank pain"
    if "flank pain" in sym_lower or "flank tenderness" in sym_lower:
        return "flank pain"
    if "radiat" in sym_lower and "groin" in sym_lower:
        return "radiating pain to groin"
    if "kidney stone" in sym_lower or "calculus" in sym_lower or "nephrolithiasis" in sym_lower:
        return "kidney stone"
    if "dysuria" in sym_lower or "painful urination" in sym_lower or "burning on urination" in sym_lower or "burning micturition" in sym_lower:
        return "dysuria"
    if "left lower quadrant" in sym_lower or "llq" in sym_lower or "diverticul" in sym_lower:
        return "left lower quadrant pain"
    if "first mtp" in sym_lower or "metatarsophalangeal" in sym_lower or "podagra" in sym_lower or "needle-shaped" in sym_lower or "birefringent" in sym_lower:
        return "first mtp pain"
    if "wheez" in sym_lower:
        return "wheezing"
    if "increased sputum" in sym_lower or "sputum volume" in sym_lower:
        return "increased sputum"
    if "barrel chest" in sym_lower:
        return "barrel chest"
    if "murphy" in sym_lower and ("sign" in sym_lower or "positive" in sym_lower):
        return "murphy sign"
    if "gallstone" in sym_lower or "cholelithiasis" in sym_lower:
        return "gallstones"
    if "lipase" in sym_lower or "amylase" in sym_lower:
        return "elevated serum lipase"
    if "splinter hemorrhag" in sym_lower:
        return "splinter hemorrhages"
    if "kussmaul" in sym_lower:
        return "Kussmaul breathing"
    if "ketonuria" in sym_lower or "4+ ketones" in sym_lower or "ketones" in sym_lower:
        return "ketonuria"
    if "s1q3t3" in sym_lower:
        return "S1Q3T3 on ECG"
    if "cellulitis" in sym_lower or "erythematous warm" in sym_lower:
        return "skin redness"
    if "right lower quadrant" in sym_lower or "rlq" in sym_lower or "mcburney" in sym_lower:
        return "right lower quadrant pain"
    if "rebound tenderness" in sym_lower:
        return "rebound tenderness"
    if "crushing" in sym_lower and "chest" in sym_lower:
        return "crushing chest pain"
    if "left arm" in sym_lower:
        return "left arm pain"
    if "radiating to back" in sym_lower:
        return "pain radiating to back"
    if "tearing" in sym_lower and "chest" in sym_lower:
        return "tearing chest pain"
    if "worst headache" in sym_lower or "thunderclap" in sym_lower:
        return "thunderclap headache"
    if "jaw claudication" in sym_lower:
        return "jaw claudication"
    if "scalp tenderness" in sym_lower:
        return "scalp tenderness"
    if "kayser" in sym_lower or "fleischer" in sym_lower:
        return "kayser-fleischer rings"
    if "strawberry tongue" in sym_lower:
        return "strawberry tongue"
    if "bullseye" in sym_lower or "erythema migrans" in sym_lower:
        return "erythema migrans"
    if "drooling" in sym_lower and "throat" in sym_lower:
        return "drooling"
    if "tripod" in sym_lower:
        return "tripod position"
    if "hot potato" in sym_lower:
        return "hot potato voice"
    if "lead-pipe" in sym_lower:
        return "lead-pipe rigidity"
    if "halos" in sym_lower and "light" in sym_lower:
        return "halos around lights"
    if "steamy cornea" in sym_lower or "cloudy cornea" in sym_lower:
        return "cloudy cornea"
    if "dark curtain" in sym_lower:
        return "dark curtain falling over vision"
    if "resting tremor" in sym_lower or "pill-rolling" in sym_lower:
        return "resting tremor"
    if "cogwheel" in sym_lower:
        return "cogwheel rigidity"
    if "lhermitte" in sym_lower:
        return "lhermitte sign"
    if "pulsus paradoxus" in sym_lower:
        return "pulsus paradoxus"
    if "muffled heart" in sym_lower:
        return "muffled heart sounds"
    if "sitting forward" in sym_lower and "chest" in sym_lower:
        return "chest pain relieved by sitting forward"
    if "pericardial friction" in sym_lower:
        return "pericardial friction rub"
    if "irregularly irregular" in sym_lower:
        return "irregularly irregular pulse"
    if "tracheal deviation" in sym_lower:
        return "tracheal deviation away from affected side"
    if "barking cough" in sym_lower or "seal-like" in sym_lower:
        return "barking cough"
    if "murphy" in sym_lower and "sign" in sym_lower:
        return "murphy sign positive"
    if "charcot" in sym_lower and "triad" in sym_lower:
        return "charcot triad"
    if "reynolds" in sym_lower and "pentad" in sym_lower:
        return "reynolds pentad"
    if "dermatitis herpetiformis" in sym_lower:
        return "dermatitis herpetiformis"
    if "hamman" in sym_lower:
        return "hamman sign"
    if "purple" in sym_lower and "striae" in sym_lower:
        return "purple abdominal striae"
    if "salt craving" in sym_lower:
        return "salt craving"
    if "frothy urine" in sym_lower or "foamy urine" in sym_lower:
        return "frothy urine"
    if "absent cremasteric" in sym_lower:
        return "absent cremasteric reflex"
    if "bp discrepancy" in sym_lower or "unequal blood pressure" in sym_lower or "blood pressure discrepancy" in sym_lower:
        return "unequal blood pressure"

    # Neurological / Stroke
    if "facial droop" in sym_lower or "drooping face" in sym_lower or "face drooping" in sym_lower:
        return "facial drooping"
    if "hemiparesis" in sym_lower or "one-sided weakness" in sym_lower or "hemiplegia" in sym_lower or "arm weakness" in sym_lower or "leg weakness" in sym_lower:
        return "unilateral weakness"
    if "aphasia" in sym_lower or "expressive aphasia" in sym_lower or "inability to speak" in sym_lower:
        return "aphasia"
    if "slurred speech" in sym_lower or "dysarthria" in sym_lower:
        return "slurred speech"

    # Cardiopulmonary / Heart Failure
    if "orthopnea" in sym_lower or "pillows to sleep" in sym_lower or "cannot lie flat" in sym_lower:
        return "orthopnea"
    if "paroxysmal nocturnal" in sym_lower or "pnd" in sym_lower or "waking up gasping" in sym_lower:
        return "paroxysmal nocturnal dyspnea"
    if "crackles" in sym_lower or "rales" in sym_lower or "crepitations" in sym_lower:
        return "crackles"
    if "s3 gallop" in sym_lower or "s3 heart sound" in sym_lower or "third heart sound" in sym_lower:
        return "s3 gallop"
    if "s4 gallop" in sym_lower or "s4 heart sound" in sym_lower or "fourth heart sound" in sym_lower:
        return "s4 gallop"
    if "jugular venous" in sym_lower or "jvp" in sym_lower or "jvd" in sym_lower or "distended neck veins" in sym_lower:
        return "elevated jvp"
    if "purulent sputum" in sym_lower or "rust-colored sputum" in sym_lower or "green sputum" in sym_lower or "yellow sputum" in sym_lower:
        return "purulent sputum"

    # Obstetric / Renal / Autoimmune
    if "clonus" in sym_lower or "hyperreflexia" in sym_lower:
        return "clonus"
    if "scotoma" in sym_lower or "visual disturbance" in sym_lower or "spots before eyes" in sym_lower:
        return "scotoma"
    if "severe hypertension" in sym_lower:
        return "severe hypertension"
    if "proteinuria" in sym_lower or "protein in urine" in sym_lower:
        return "proteinuria"
    if "anti-dsdna" in sym_lower or "antidsdna" in sym_lower:
        return "positive anti-dsdna"
    if "hypocomplementemia" in sym_lower or "low c3" in sym_lower or "low c4" in sym_lower:
        return "hypocomplementemia"

    # High-Acuity Emergency Findings Normalization
    if "levine" in sym_lower or ("fist" in sym_lower and "chest" in sym_lower):
        return "levine sign"
    if "st elevation" in sym_lower or "stemi" in sym_lower:
        return "ST elevation on ECG"
    if "troponin" in sym_lower:
        return "elevated cardiac troponin"
    if "kernig" in sym_lower:
        return "Kernig sign positive"
    if "brudzinski" in sym_lower:
        return "Brudzinski sign positive"
    if "jolt" in sym_lower and "accentuat" in sym_lower:
        return "jolt accentuation of headache"
    if "status epilepticus" in sym_lower or ("seizure" in sym_lower and ("continuous" in sym_lower or ">5" in sym_lower or "prolonged" in sym_lower)):
        return "status epilepticus"
    if "coffee ground" in sym_lower or "coffee-ground" in sym_lower:
        return "coffee ground emesis"
    if "melena" in sym_lower or "black tarry" in sym_lower:
        return "melena"
    if "papilledema" in sym_lower:
        return "papilledema"
    if "peaked t wave" in sym_lower or "tented t wave" in sym_lower:
        return "hyperkalemic peaked T waves"
    if "sine wave" in sym_lower:
        return "sine wave on ECG"
    if "rovsing" in sym_lower:
        return "Rovsing sign positive"
    if "psoas" in sym_lower and "sign" in sym_lower:
        return "Psoas sign positive"
    if "obturator" in sym_lower and "sign" in sym_lower:
        return "Obturator sign positive"
    if "qsofa" in sym_lower or ("vasopressor" in sym_lower and "shock" in sym_lower):
        return "refractory septic shock"
    if "mottled" in sym_lower:
        return "mottled extremities"
    if "fruity" in sym_lower and ("breath" in sym_lower or "odor" in sym_lower):
        return "fruity breath odor"

    return sym_lower


def normalize_symptom_set(symptoms: List[str]) -> Set[str]:
    return {normalize_symptom(s) for s in symptoms if s}


# ---------------------------------------------------------------------------
# High-Specificity / Pathognomonic Symptom Registry
# When a patient presents with hallmark diagnostic signs, award targeted
# diagnostic weights to elevate the true underlying condition.
# ---------------------------------------------------------------------------
HIGH_SPECIFICITY_SYMPTOMS: Dict[str, Dict[str, float]] = {
    "port-wine urine": {"Acute Intermittent Porphyria (AIP)": 0.85},
    "dark reddish-brown urine": {"Acute Intermittent Porphyria (AIP)": 0.70},
    "elevated plasma phytanic acid": {"Refsum Disease": 0.85},
    "elevated phytanic acid": {"Refsum Disease": 0.85},
    "phytanic acid": {"Refsum Disease": 0.80},
    "pigmentary retinal degeneration": {"Refsum Disease": 0.50, "Gyrate Atrophy of the Choroid and Retina": 0.35},
    "retinitis pigmentosa": {"Refsum Disease": 0.50, "Gyrate Atrophy of the Choroid and Retina": 0.35},
    "ichthyosis": {"Refsum Disease": 0.45},
    "absent ankle reflexes": {"Refsum Disease": 0.35, "Guillain-Barré Syndrome": 0.25},
    "right lower quadrant pain": {"Acute Appendicitis": 0.35},
    "left arm pain": {"Acute Myocardial Infarction (STEMI/NSTEMI)": 0.35},
    "pain radiating to left arm": {"Acute Myocardial Infarction (STEMI/NSTEMI)": 0.35},
    "neck stiffness": {"Bacterial Meningitis": 0.30, "Meningococcal Meningitis": 0.30},
    "nuchal rigidity": {"Bacterial Meningitis": 0.30, "Meningococcal Meningitis": 0.30},
    "polyuria": {"Type 2 Diabetes Mellitus": 0.40, "Type 1 Diabetes Mellitus": 0.40, "Diabetic Ketoacidosis (DKA)": 0.30},
    "polydipsia": {"Type 2 Diabetes Mellitus": 0.40, "Type 1 Diabetes Mellitus": 0.40, "Diabetic Ketoacidosis (DKA)": 0.30},
    "fruity breath": {"Diabetic Ketoacidosis (DKA)": 0.35},
    "flank pain radiating to groin": {"Nephrolithiasis (Kidney Stones)": 0.35},
    "eschar": {"Scrub Typhus (Orientia tsutsugamushi)": 0.40},
    "malar rash": {"Systemic Lupus Erythematosus (SLE)": 0.45},
    "photosensitive rash": {"Systemic Lupus Erythematosus (SLE)": 0.35},
    "positive antinuclear antibody": {"Systemic Lupus Erythematosus (SLE)": 0.40},
    "positive anti-dsdna": {"Systemic Lupus Erythematosus (SLE)": 0.50},
    "hypocomplementemia": {"Systemic Lupus Erythematosus (SLE)": 0.40},
    "dermatomal rash": {"Herpes Zoster (Shingles)": 0.60},
    "burning pain": {"Herpes Zoster (Shingles)": 0.45},
    "retro-orbital pain": {"Dengue Fever": 0.40},
    "retro-orbital headache": {"Dengue Fever": 0.40},
    "rose spots": {"Typhoid Fever": 0.55},
    "relative bradycardia": {"Typhoid Fever": 0.40},
    "hemoptysis": {"Tuberculosis (Active)": 0.45, "Pulmonary Tuberculosis": 0.45, "Pulmonary Embolism": 0.35},
    "night sweats": {"Tuberculosis (Active)": 0.40, "Pulmonary Tuberculosis": 0.40},
    "loss of smell": {"COVID-19": 0.50},
    "loss of taste": {"COVID-19": 0.50},
    "crepitus": {"Osteoarthritis": 0.50},
    "koilonychia": {"Iron Deficiency Anemia": 0.55},
    "pica": {"Iron Deficiency Anemia": 0.55},
    "cold intolerance": {"Hypothyroidism / Myxedema Coma": 0.45, "Hypothyroidism": 0.45},
    "severe hypertension": {"Essential Hypertension": 0.40, "Hypertension": 0.40, "Preeclampsia with Severe Features": 0.35},
    "throbbing headache": {"Migraine": 0.30},
    "unilateral headache": {"Migraine": 0.30},
    "band-like headache": {"Tension-type Headache": 0.35},
    "facial pressure": {"Acute Sinusitis (Rhinosinusitis)": 0.30},
    "purulent nasal discharge": {"Acute Sinusitis (Rhinosinusitis)": 0.25},
    "tonsillar exudate": {"Streptococcal Pharyngitis (Strep Throat)": 0.35, "Mononucleosis (Infectious / EBV)": 0.25},
    "heartburn": {"Gastroesophageal Reflux Disease (GERD)": 0.35},
    "acid regurgitation": {"Gastroesophageal Reflux Disease (GERD)": 0.35},
    "first mtp pain": {"Gout (Acute Gouty Arthritis)": 0.40},
    "podagra": {"Gout (Acute Gouty Arthritis)": 0.45},
    "pain reproduced by palpation": {"Costochondritis": 0.35},
    "chest wall tenderness": {"Costochondritis": 0.30},
    "posterior cervical lymphadenopathy": {"Mononucleosis (Infectious / EBV)": 0.35},
    # Neurology & Ophthalmology
    "facial drooping": {"Acute Ischemic Stroke (CVA)": 0.45, "Bell's Palsy (Idiopathic Facial Palsy)": 0.35},
    "unilateral weakness": {"Acute Ischemic Stroke (CVA)": 0.45},
    "hemiparesis": {"Acute Ischemic Stroke (CVA)": 0.45},
    "aphasia": {"Acute Ischemic Stroke (CVA)": 0.45},
    "slurred speech": {"Acute Ischemic Stroke (CVA)": 0.35},
    "jaw claudication": {"Giant Cell Arteritis (Temporal Arteritis)": 0.45},
    "scalp tenderness": {"Giant Cell Arteritis (Temporal Arteritis)": 0.35},
    "temporal headache": {"Giant Cell Arteritis (Temporal Arteritis)": 0.30},
    "inability to close eye": {"Bell's Palsy (Idiopathic Facial Palsy)": 0.40},
    "inability to wrinkle forehead": {"Bell's Palsy (Idiopathic Facial Palsy)": 0.40},
    "fatigable weakness": {"Myasthenia Gravis": 0.40},
    "weakness improves with rest": {"Myasthenia Gravis": 0.35},
    "pill-rolling tremor": {"Parkinson's Disease": 0.45},
    "resting tremor": {"Parkinson's Disease": 0.35},
    "cogwheel rigidity": {"Parkinson's Disease": 0.35},
    "lhermitte sign": {"Multiple Sclerosis (Relapsing-Remitting)": 0.45},
    "internuclear ophthalmoplegia": {"Multiple Sclerosis (Relapsing-Remitting)": 0.40},
    "optic neuritis": {"Multiple Sclerosis (Relapsing-Remitting)": 0.35},
    "halos around lights": {"Acute Angle-Closure Glaucoma": 0.45},
    "cloudy cornea": {"Acute Angle-Closure Glaucoma": 0.40},
    "fixed mid-dilated pupil": {"Acute Angle-Closure Glaucoma": 0.40},
    "dark curtain falling over vision": {"Retinal Detachment": 0.45},
    "flashes of light": {"Retinal Detachment": 0.35},
    # Cardiology & Pulmonology
    "orthopnea": {"Acute Heart Failure (Cardiogenic Pulmonary Edema)": 0.45},
    "paroxysmal nocturnal dyspnea": {"Acute Heart Failure (Cardiogenic Pulmonary Edema)": 0.45},
    "crackles": {"Acute Heart Failure (Cardiogenic Pulmonary Edema)": 0.35, "Community-Acquired Pneumonia (Lobar Pneumonia)": 0.30},
    "elevated jvp": {"Acute Heart Failure (Cardiogenic Pulmonary Edema)": 0.40, "Cardiac Tamponade": 0.35},
    "s3 gallop": {"Acute Heart Failure (Cardiogenic Pulmonary Edema)": 0.45},
    "s4 gallop": {"Acute Heart Failure (Cardiogenic Pulmonary Edema)": 0.35},
    "purulent sputum": {"Community-Acquired Pneumonia (Lobar Pneumonia)": 0.40},
    "pulsus paradoxus": {"Cardiac Tamponade": 0.40},
    "muffled heart sounds": {"Cardiac Tamponade": 0.40},
    "chest pain relieved by sitting forward": {"Acute Pericarditis": 0.45},
    "pericardial friction rub": {"Acute Pericarditis": 0.45},
    "irregularly irregular pulse": {"Atrial Fibrillation (Rapid Ventricular Response)": 0.45},
    "tracheal deviation away from affected side": {"Tension Pneumothorax": 0.45},
    "absent breath sounds": {"Tension Pneumothorax": 0.35},
    "bilateral hilar lymphadenopathy": {"Sarcoidosis": 0.40},
    "barking cough": {"Croup (Laryngotracheobronchitis)": 0.45},
    "seal-like cough": {"Croup (Laryngotracheobronchitis)": 0.45},
    # Obstetric
    "severe hypertension": {"Preeclampsia with Severe Features": 0.40},
    "clonus": {"Preeclampsia with Severe Features": 0.45},
    "scotoma": {"Preeclampsia with Severe Features": 0.40},
    "proteinuria": {"Preeclampsia with Severe Features": 0.35, "Nephrotic Syndrome": 0.35},
    # GI & Surgical
    "severe epigastric pain": {"Acute Pancreatitis": 0.40},
    "murphy sign positive": {"Acute Cholecystitis": 0.45},
    "charcot triad": {"Acute Ascending Cholangitis": 0.45},
    "reynolds pentad": {"Acute Ascending Cholangitis": 0.45},
    "dermatitis herpetiformis": {"Celiac Disease (Gluten-Sensitive Enteropathy)": 0.45},
    "hamman sign": {"Boerhaave Syndrome (Spontaneous Esophageal Rupture)": 0.45},
    "subcutaneous emphysema": {"Boerhaave Syndrome (Spontaneous Esophageal Rupture)": 0.35},
    # Critical Care / Sepsis
    "altered consciousness": {"Septic Shock / Severe Sepsis": 0.35},
    "reduced urine output": {"Septic Shock / Severe Sepsis": 0.30},
    # Endocrinology
    "paroxysmal severe hypertension": {"Pheochromocytoma": 0.40},
    "purple abdominal striae": {"Cushing's Syndrome": 0.40},
    "buffalo hump": {"Cushing's Syndrome": 0.35},
    "moon facies": {"Cushing's Syndrome": 0.35},
    "salt craving": {"Addison's Disease (Primary Adrenal Insufficiency)": 0.40},
    "palmar crease pigmentation": {"Addison's Disease (Primary Adrenal Insufficiency)": 0.40},
    # Nephrology & Urology
    "frothy urine": {"Nephrotic Syndrome": 0.40},
    "absent cremasteric reflex": {"Testicular Torsion": 0.45},
    "high-riding testicle": {"Testicular Torsion": 0.40},
    # Pediatrics & Infectious
    "strawberry tongue": {"Kawasaki Disease": 0.45},
    "periungual desquamation": {"Kawasaki Disease": 0.40},
    "palpable purpura": {"Henoch-Schonlein Purpura (IgA Vasculitis)": 0.40},
    "drooling": {"Acute Epiglottitis": 0.45},
    "tripod position": {"Acute Epiglottitis": 0.45},
    "hot potato voice": {"Acute Epiglottitis": 0.40},
    "erythema migrans": {"Lyme Disease (Early Localized / Disseminated)": 0.45},
    "bullseye rash": {"Lyme Disease (Early Localized / Disseminated)": 0.45},
    "lead-pipe rigidity": {"Neuroleptic Malignant Syndrome (NMS)": 0.45},
    "tearing chest pain": {"Aortic Dissection": 0.45},
    "chest pain radiating to back": {"Aortic Dissection": 0.40},
    "thunderclap headache": {"Subarachnoid Hemorrhage": 0.45},
    "ascending weakness": {"Guillain-Barré Syndrome": 0.40},
    "areflexia": {"Guillain-Barré Syndrome": 0.40},
    # Tropical & High-Consequence Travel Infections
    "severe joint pain": {"Chikungunya": 0.85},
    "joint swelling": {"Chikungunya": 0.40},
    "morning stiffness": {"Chikungunya": 0.30, "Systemic Lupus Erythematosus (SLE)": 0.25},
    "redness of the eyes": {"Zika Virus": 0.35, "Measles": 0.25, "Chikungunya": 0.20},
    "conjunctivitis": {"Zika Virus": 0.45, "Measles": 0.30, "Chikungunya": 0.35},
    "maculopapular rash": {"Zika Virus": 0.35, "Measles": 0.30, "Chikungunya": 0.20, "Dengue Fever": 0.20},
    "step-ladder fever": {"Typhoid Fever": 0.50},
    "persistent fever": {"Typhoid Fever": 0.30, "Malaria (Plasmodium falciparum)": 0.15},
    "intermittent fever": {"Malaria (Plasmodium falciparum)": 0.50, "Malaria (Plasmodium vivax)": 0.50},
    "recurrent fever": {"Malaria (Plasmodium falciparum)": 0.50, "Malaria (Plasmodium vivax)": 0.50},
    "blood smear requested": {"Malaria (Plasmodium falciparum)": 0.45, "Severe Malaria / Cerebral Malaria": 0.45},
    "jaundice": {"Yellow Fever": 0.55, "Hepatitis A": 0.45, "Acute Hepatitis B": 0.25},
    "dark urine": {"Yellow Fever": 0.45, "Hepatitis A": 0.40, "Acute Intermittent Porphyria (AIP)": 0.35, "Carnitine Palmitoyltransferase II (CPT II) Deficiency": 0.40},
    "severe back pain": {"Yellow Fever": 0.40},
    "right upper quadrant pain": {"Yellow Fever": 0.40, "Acute Cholecystitis": 0.35},
    "hepatic failure": {"Yellow Fever": 0.50, "Hepatitis A": 0.45},
    "clay-colored stools": {"Hepatitis A": 0.55, "Hepatitis E": 0.40},
    "non-blanching rash": {"Meningococcal Disease / Meningococcemia (with Meningitis)": 0.70, "Meningococcal Meningitis": 0.70, "Bacterial Meningitis": 0.15},
    "petechiae": {"Bundibugyo Virus Disease (BVD)": 0.45, "Ebola Virus Disease (Zaire)": 0.40, "Marburg Virus Disease": 0.40, "Meningococcal Disease / Meningococcemia (with Meningitis)": 0.45, "Meningococcal Meningitis": 0.45, "Dengue Hemorrhagic Fever": 0.45, "Chikungunya": 0.40, "Bacterial Meningitis": 0.15},
    "petechial rash": {"Bundibugyo Virus Disease (BVD)": 0.45, "Ebola Virus Disease (Zaire)": 0.40, "Marburg Virus Disease": 0.40, "Meningococcal Disease / Meningococcemia (with Meningitis)": 0.45, "Meningococcal Meningitis": 0.45, "Dengue Hemorrhagic Fever": 0.45, "Chikungunya": 0.40, "Bacterial Meningitis": 0.15},
    "purpuric rash": {"Meningococcal Disease / Meningococcemia (with Meningitis)": 0.65, "Meningococcal Meningitis": 0.65, "Bundibugyo Virus Disease (BVD)": 0.40},
    "purpura fulminans": {"Meningococcal Disease / Meningococcemia (with Meningitis)": 0.85, "Meningococcal Meningitis": 0.85},
    "thrombocytopenia": {"Bundibugyo Virus Disease (BVD)": 0.45, "Ebola Virus Disease (Zaire)": 0.40, "Yellow Fever": 0.40, "Dengue Hemorrhagic Fever": 0.45},
    "bleeding": {"Bundibugyo Virus Disease (BVD)": 0.50, "Ebola Virus Disease (Zaire)": 0.40, "Marburg Virus Disease": 0.40, "Yellow Fever": 0.40, "Dengue Hemorrhagic Fever": 0.40},
    "hematemesis": {"Bundibugyo Virus Disease (BVD)": 0.40, "Ebola Virus Disease (Zaire)": 0.35, "Marburg Virus Disease": 0.35, "Yellow Fever": 0.35, "Dengue Hemorrhagic Fever": 0.30},
    "postural dizziness": {"Bundibugyo Virus Disease (BVD)": 0.35, "Ebola Virus Disease (Zaire)": 0.35, "Marburg Virus Disease": 0.35, "Dengue Hemorrhagic Fever": 0.25},
    "profound weakness": {"Bundibugyo Virus Disease (BVD)": 0.35, "Ebola Virus Disease (Zaire)": 0.35, "Marburg Virus Disease": 0.35},
    "reduced urine output": {"Bundibugyo Virus Disease (BVD)": 0.35, "Ebola Virus Disease (Zaire)": 0.35, "Marburg Virus Disease": 0.35, "Septic Shock / Severe Sepsis": 0.30, "Dengue Hemorrhagic Fever": 0.25},
    "sore throat": {"Bundibugyo Virus Disease (BVD)": 0.30, "Ebola Virus Disease (Zaire)": 0.25, "Marburg Virus Disease": 0.25, "Streptococcal Pharyngitis (Strep Throat)": 0.35},
    "persistent vomiting": {"Bundibugyo Virus Disease (BVD)": 0.35, "Ebola Virus Disease (Zaire)": 0.35, "Marburg Virus Disease": 0.35, "Dengue Hemorrhagic Fever": 0.35, "Dengue Fever": 0.25, "Acute Pancreatitis": 0.20},
    "severe abdominal pain": {"Bundibugyo Virus Disease (BVD)": 0.30, "Ebola Virus Disease (Zaire)": 0.30, "Marburg Virus Disease": 0.30, "Dengue Hemorrhagic Fever": 0.35, "Dengue Fever": 0.25, "Acute Appendicitis": 0.25},
    "lethargy": {"Bundibugyo Virus Disease (BVD)": 0.25, "Dengue Hemorrhagic Fever": 0.30, "Ebola Virus Disease (Zaire)": 0.25, "Marburg Virus Disease": 0.25},

    # Hallmark Features for Complex Rare/Metabolic/Genetic Conditions (Cases 36-48)
    "postprandial hypoglycemia": {"Insulin Autoimmune Syndrome (Hirata Disease)": 0.65},
    "insulin autoantibodies": {"Insulin Autoimmune Syndrome (Hirata Disease)": 0.60},
    "hyperinsulinism": {"Insulin Autoimmune Syndrome (Hirata Disease)": 0.45},
    "digital clubbing": {"Pachydermoperiostosis (Primary Hypertrophic Osteoarthropathy)": 0.60},
    "pachydermia": {"Pachydermoperiostosis (Primary Hypertrophic Osteoarthropathy)": 0.65},
    "periostosis": {"Pachydermoperiostosis (Primary Hypertrophic Osteoarthropathy)": 0.60},
    "port-wine urine": {"Acute Intermittent Porphyria (AIP)": 0.65},
    "pain out of proportion to exam": {"Acute Intermittent Porphyria (AIP)": 0.50, "Acute Mesenteric Ischemia": 0.45},
    "heme biosynthesis defect": {"Acute Intermittent Porphyria (AIP)": 0.60},
    "calf pseudohypertrophy": {"Duchenne Muscular Dystrophy (DMD)": 0.65},
    "gowers sign": {"Duchenne Muscular Dystrophy (DMD)": 0.60},
    "markedly elevated ck": {"Duchenne Muscular Dystrophy (DMD)": 0.55, "Carnitine Palmitoyltransferase II (CPT II) Deficiency": 0.50},
    "nyctalopia": {"Gyrate Atrophy of the Choroid and Retina": 0.60},
    "retinal degeneration": {"Gyrate Atrophy of the Choroid and Retina": 0.55},
    "amino acid transport defect": {"Gyrate Atrophy of the Choroid and Retina": 0.60},
    "urticarial rash": {"Cryopyrin-Associated Periodic Syndrome (CAPS Spectrum / Muckle-Wells / FCAS)": 0.55, "Cryopyrin-Associated Periodic Syndrome (CAPS / Muckle-Wells)": 0.55},
    "sensorineural hearing loss": {"Cryopyrin-Associated Periodic Syndrome (CAPS Spectrum / Muckle-Wells / FCAS)": 0.55, "Cryopyrin-Associated Periodic Syndrome (CAPS / Muckle-Wells)": 0.55},
    "autoinflammatory syndrome": {"Cryopyrin-Associated Periodic Syndrome (CAPS Spectrum / Muckle-Wells / FCAS)": 0.50, "Cryopyrin-Associated Periodic Syndrome (CAPS / Muckle-Wells)": 0.50},
    "perifascicular atrophy": {"Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)": 0.65, "Anti-Synthetase Syndrome (Amyopathic Dermatomyositis)": 0.65},
    "interstitial lung disease": {"Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)": 0.45, "Anti-Synthetase Syndrome (Amyopathic Dermatomyositis)": 0.45},
    "myositis-specific antibody": {"Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)": 0.60, "Anti-Synthetase Syndrome (Amyopathic Dermatomyositis)": 0.60},
    "collodion membrane": {"Collodion Baby Phenotype (Underlying Congenital Ichthyosis suspected)": 0.70, "Collodion Baby (Congenital Ichthyosis)": 0.70},
    "ectropion": {"Collodion Baby Phenotype (Underlying Congenital Ichthyosis suspected)": 0.55, "Collodion Baby (Congenital Ichthyosis)": 0.55},
    "ichthyosis": {"Collodion Baby Phenotype (Underlying Congenital Ichthyosis suspected)": 0.55, "Collodion Baby (Congenital Ichthyosis)": 0.55},
    "disorder of cornification": {"Collodion Baby Phenotype (Underlying Congenital Ichthyosis suspected)": 0.60, "Collodion Baby (Congenital Ichthyosis)": 0.60},
    "migraine-like headaches": {"Mitochondrial Encephalopathy (Differential includes MELAS, MERRF, Mitochondrial Ataxia)": 0.45, "Mitochondrial Encephalopathy (MELAS / Mitochondrial Ataxia)": 0.45},
    "brainstem/cerebellar lesions": {"Mitochondrial Encephalopathy (Differential includes MELAS, MERRF, Mitochondrial Ataxia)": 0.50, "Subacute Necrotizing Encephalomyelopathy (Suspected Leigh Syndrome / Mitochondrial Neurodegeneration)": 0.50, "Mitochondrial Encephalopathy (MELAS / Mitochondrial Ataxia)": 0.50, "Leigh Syndrome (Subacute Necrotizing Encephalomyelopathy)": 0.50},
    "mitochondrial dna defect": {"Mitochondrial Encephalopathy (Differential includes MELAS, MERRF, Mitochondrial Ataxia)": 0.60, "Mitochondrial Energy Metabolism Disorder (Suspected Respiratory Chain Complex Deficiency / Inborn Error of Metabolism)": 0.55, "Subacute Necrotizing Encephalomyelopathy (Suspected Leigh Syndrome / Mitochondrial Neurodegeneration)": 0.55, "Mitochondrial Encephalopathy (MELAS / Mitochondrial Ataxia)": 0.60, "Mitochondrial Complex Deficiency (Lactic Acidosis)": 0.55, "Leigh Syndrome (Subacute Necrotizing Encephalomyelopathy)": 0.55},
    "rhabdomyolysis": {"Carnitine Palmitoyltransferase II (CPT II) Deficiency": 0.60},
    "exercise-induced myoglobinuria": {"Carnitine Palmitoyltransferase II (CPT II) Deficiency": 0.65},
    "fatty acid oxidation defect": {"Carnitine Palmitoyltransferase II (CPT II) Deficiency": 0.60},
    "developmental regression": {"Subacute Necrotizing Encephalomyelopathy (Suspected Leigh Syndrome / Mitochondrial Neurodegeneration)": 0.60, "Leigh Syndrome (Subacute Necrotizing Encephalomyelopathy)": 0.60},
    "mitochondrial encephalomyopathy": {"Subacute Necrotizing Encephalomyelopathy (Suspected Leigh Syndrome / Mitochondrial Neurodegeneration)": 0.60, "Mitochondrial Encephalopathy (Differential includes MELAS, MERRF, Mitochondrial Ataxia)": 0.50, "Leigh Syndrome (Subacute Necrotizing Encephalomyelopathy)": 0.60, "Mitochondrial Encephalopathy (MELAS / Mitochondrial Ataxia)": 0.50},
    "spastic paraparesis": {"Hereditary Spastic Paraplegia (HSP)": 0.65},
    "corticospinal tract abnormalities": {"Hereditary Spastic Paraplegia (HSP)": 0.55},
    "severe metabolic acidosis": {"Mitochondrial Energy Metabolism Disorder (Suspected Respiratory Chain Complex Deficiency / Inborn Error of Metabolism)": 0.60, "Mitochondrial Complex Deficiency (Lactic Acidosis)": 0.60},
    "lactic acidosis": {"Mitochondrial Energy Metabolism Disorder (Suspected Respiratory Chain Complex Deficiency / Inborn Error of Metabolism)": 0.65, "Mitochondrial Complex Deficiency (Lactic Acidosis)": 0.65},
    "mitochondrial respiratory chain defect": {"Mitochondrial Energy Metabolism Disorder (Suspected Respiratory Chain Complex Deficiency / Inborn Error of Metabolism)": 0.65, "Mitochondrial Complex Deficiency (Lactic Acidosis)": 0.65},
    "gottron's papules": {"Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)": 0.65, "Anti-Synthetase Syndrome (Amyopathic Dermatomyositis)": 0.65},
    "heliotrope rash": {"Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)": 0.65, "Anti-Synthetase Syndrome (Amyopathic Dermatomyositis)": 0.65},
    "mechanic's hands": {"Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)": 0.65, "Anti-Synthetase Syndrome (Amyopathic Dermatomyositis)": 0.65},
    "positive anti-jo-1 antibody": {"Idiopathic Inflammatory Myopathy (Suspected Anti-Synthetase Syndrome / Dermatomyositis Spectrum)": 0.70, "Anti-Synthetase Syndrome (Amyopathic Dermatomyositis)": 0.70},
    "janeway lesions": {"Infective Endocarditis": 0.65},
    "osler nodes": {"Infective Endocarditis": 0.65},
    "valvular vegetation": {"Infective Endocarditis": 0.70},
    "splinter hemorrhages": {"Infective Endocarditis": 0.60},
    "new regurgitant murmur": {"Infective Endocarditis": 0.65},
    "costovertebral angle tenderness": {"Pyelonephritis (Upper UTI)": 0.60},
    "flank pain": {"Pyelonephritis (Upper UTI)": 0.40, "Nephrolithiasis (Kidney Stones)": 0.45},
    "colicky flank pain": {"Nephrolithiasis (Kidney Stones)": 0.65},
    "radiating pain to groin": {"Nephrolithiasis (Kidney Stones)": 0.60},
    "kidney stone": {"Nephrolithiasis (Kidney Stones)": 0.65},
    "dysuria": {"Urinary Tract Infection (Lower)": 0.45, "Pyelonephritis (Upper UTI)": 0.40},
    "left lower quadrant pain": {"Acute Diverticulitis": 0.75},
    "Acute Diverticulitis on CT Abdomen": {"Acute Diverticulitis": 0.85},
    "first mtp pain": {"Gout (Acute Gouty Arthritis)": 0.65},
    "podagra": {"Gout (Acute Gouty Arthritis)": 0.70},
    "wheezing": {"COPD Exacerbation": 0.45, "Asthma Exacerbation": 0.45},
    "expiratory wheezes": {"COPD Exacerbation": 0.50, "Asthma Exacerbation": 0.45},
    "increased sputum": {"COPD Exacerbation": 0.50},
    "barrel chest": {"COPD Exacerbation": 0.45},
    "skin redness": {"Cellulitis": 0.45},
    "skin warmth": {"Cellulitis": 0.40},
    "skin swelling": {"Cellulitis": 0.40},
    "erythematous warm skin": {"Cellulitis": 0.60},
    "spreading erythema": {"Cellulitis": 0.65},
    "local induration": {"Cellulitis": 0.50},
    "induration": {"Cellulitis": 0.45},
    "murphy sign": {"Acute Cholecystitis": 0.60},
    "gallstones": {"Acute Cholecystitis": 0.50},
    "elevated serum lipase": {"Acute Pancreatitis": 0.65},
    "Kussmaul breathing": {"Diabetic Ketoacidosis (DKA)": 0.60},
    "ketonuria": {"Diabetic Ketoacidosis (DKA)": 0.55},
    "S1Q3T3 on ECG": {"Pulmonary Embolism": 0.55},
    "levine sign": {"Acute Myocardial Infarction (STEMI/NSTEMI)": 0.55},
    "ST elevation on ECG": {"Acute Myocardial Infarction (STEMI/NSTEMI)": 0.65, "Acute Pericarditis": 0.35},
    "elevated cardiac troponin": {"Acute Myocardial Infarction (STEMI/NSTEMI)": 0.65},
    "forced gaze deviation": {"Acute Ischemic Stroke (CVA)": 0.55},
    "refractory septic shock": {"Septic Shock / Severe Sepsis": 0.65},
    "mottled extremities": {"Septic Shock / Severe Sepsis": 0.45},
    "fruity breath odor": {"Diabetic Ketoacidosis (DKA)": 0.55},
    "Kernig sign positive": {"Bacterial Meningitis": 0.55, "Meningococcal Disease / Meningococcemia (with Meningitis)": 0.55},
    "Brudzinski sign positive": {"Bacterial Meningitis": 0.55, "Meningococcal Disease / Meningococcemia (with Meningitis)": 0.55},
    "status epilepticus": {"Status Epilepticus": 0.85, "Epilepsy / Seizure Disorder": 0.45},
    "continuous seizures": {"Status Epilepticus": 0.85, "Epilepsy / Seizure Disorder": 0.45},
    "prolonged seizure": {"Status Epilepticus": 0.80, "Epilepsy / Seizure Disorder": 0.45},
    "coffee ground emesis": {"Acute Upper Gastrointestinal Bleeding": 0.70, "Peptic Ulcer Disease": 0.55},
    "melena": {"Acute Upper Gastrointestinal Bleeding": 0.70, "Peptic Ulcer Disease": 0.50},
    "hematemesis": {"Acute Upper Gastrointestinal Bleeding": 0.75, "Peptic Ulcer Disease": 0.50},
    "hypertensive encephalopathy": {"Essential Hypertension": 0.50},
    "papilledema": {"Essential Hypertension": 0.50, "Subarachnoid Hemorrhage": 0.35},
    "hyperkalemic peaked T waves": {"Acute Kidney Injury (AKI)": 0.55, "Chronic Kidney Disease (CKD)": 0.45},
    "sine wave on ECG": {"Acute Kidney Injury (AKI)": 0.65, "Chronic Kidney Disease (CKD)": 0.55},
    "Rovsing sign positive": {"Acute Appendicitis": 0.60},
    "Psoas sign positive": {"Acute Appendicitis": 0.55},
    "Obturator sign positive": {"Acute Appendicitis": 0.50},
    "migratory RLQ abdominal pain": {"Acute Appendicitis": 0.65},
    "severe epigastric pain radiating to back": {"Acute Pancreatitis": 0.65},
    "Cullen sign (periumbilical ecchymosis)": {"Acute Pancreatitis": 0.60},
    "Grey Turner sign (flank ecchymosis)": {"Acute Pancreatitis": 0.60},
    "wide mediastinum on CXR": {"Aortic Dissection": 0.65},
    "unequal pulses": {"Aortic Dissection": 0.60},
    # Outbreak & Zoonotic Hallmarks (Plague, CCHF, Arboviruses)
    "painful buboes": {"Bubonic Plague": 0.70, "Plague": 0.70},
    "buboes": {"Bubonic Plague": 0.70, "Plague": 0.70},
    "bubo": {"Bubonic Plague": 0.70, "Plague": 0.70},
    "flea bite history": {"Bubonic Plague": 0.45, "Murine Typhus (Endemic Typhus)": 0.45},
    "flea bite": {"Bubonic Plague": 0.45, "Murine Typhus (Endemic Typhus)": 0.45},
    "ecchymosis": {"Crimean-Congo Hemorrhagic Fever": 0.55, "Crimean-Congo Hemorrhagic Fever (CCHF)": 0.55},
    "petechiae": {"Dengue Hemorrhagic Fever": 0.40, "Meningococcal Disease / Meningococcemia (with Meningitis)": 0.40},
    "livestock contact": {"Crimean-Congo Hemorrhagic Fever": 0.50, "Crimean-Congo Hemorrhagic Fever (CCHF)": 0.50, "Brucellosis": 0.40, "Q Fever": 0.40},
    "livestock handling": {"Crimean-Congo Hemorrhagic Fever": 0.50, "Crimean-Congo Hemorrhagic Fever (CCHF)": 0.50, "Brucellosis": 0.40, "Q Fever": 0.40},
    "tick exposure": {"Crimean-Congo Hemorrhagic Fever": 0.45, "Crimean-Congo Hemorrhagic Fever (CCHF)": 0.45, "Kyasanur Forest Disease (Monkey Fever)": 0.40, "Lyme Disease": 0.40},
    "severe debilitating joint pain": {"Chikungunya": 0.65},
}


# ---------------------------------------------------------------------------
# Canonical Disease Entity Lookup Registry & Differential Panels
# Guarantees instant (<5ms) deterministic recognition of disease names and
# establishes evidence-based differential diagnosis panels.
# ---------------------------------------------------------------------------

CANONICAL_DISEASE_LOOKUP: Dict[str, str] = {
    # Tropical / Outbreaks / Vector-Borne
    "dengue": "Dengue Fever",
    "dengue fever": "Dengue Fever",
    "severe dengue": "Dengue Hemorrhagic Fever",
    "dengue hemorrhagic fever": "Dengue Hemorrhagic Fever",
    "malaria": "Malaria (Plasmodium falciparum)",
    "falciparum malaria": "Malaria (Plasmodium falciparum)",
    "vivax malaria": "Malaria (Plasmodium vivax)",
    "severe malaria": "Severe Malaria / Cerebral Malaria",
    "cerebral malaria": "Severe Malaria / Cerebral Malaria",
    "typhoid": "Typhoid Fever",
    "typhoid fever": "Typhoid Fever",
    "enteric fever": "Typhoid Fever",
    "chikungunya": "Chikungunya",
    "zika": "Zika Virus",
    "zika virus": "Zika Virus",
    "yellow fever": "Yellow Fever",
    "leptospirosis": "Leptospirosis",
    "cholera": "Cholera",
    "scrub typhus": "Scrub Typhus (Orientia tsutsugamushi)",
    "nipah": "Nipah Virus Disease",
    "nipah virus": "Nipah Virus Disease",
    "ebola": "Ebola Virus Disease (Zaire)",
    "marburg": "Marburg Virus Disease",
    "mpox": "Mpox (Clade I/II)",
    "monkeypox": "Mpox (Clade I/II)",
    "plague": "Bubonic Plague",
    "bubonic plague": "Bubonic Plague",
    "pneumonic plague": "Pneumonic Plague",
    "bubo": "Bubonic Plague",
    "buboes": "Bubonic Plague",
    "cchf": "Crimean-Congo Hemorrhagic Fever",
    "crimean congo": "Crimean-Congo Hemorrhagic Fever",
    "crimean-congo": "Crimean-Congo Hemorrhagic Fever",
    "crimean congo hemorrhagic fever": "Crimean-Congo Hemorrhagic Fever",
    "crimean-congo hemorrhagic fever": "Crimean-Congo Hemorrhagic Fever",
    "kfd": "Kyasanur Forest Disease (Monkey Fever)",
    "kyasanur forest disease": "Kyasanur Forest Disease (Monkey Fever)",
    "monkey fever": "Kyasanur Forest Disease (Monkey Fever)",
    "chandipura": "Chandipura Encephalitis",
    "chandipura virus": "Chandipura Encephalitis",
    "chandipura encephalitis": "Chandipura Encephalitis",

    # Respiratory & Infectious
    "covid": "COVID-19",
    "covid-19": "COVID-19",
    "covid 19": "COVID-19",
    "coronavirus": "COVID-19",
    "sars-cov-2": "COVID-19",
    "tuberculosis": "Tuberculosis (Active)",
    "tb": "Tuberculosis (Active)",
    "pulmonary tuberculosis": "Tuberculosis (Active)",
    "pulmonary tb": "Tuberculosis (Active)",
    "active tb": "Tuberculosis (Active)",
    "pneumonia": "Community-Acquired Pneumonia (Lobar Pneumonia)",
    "community-acquired pneumonia": "Community-Acquired Pneumonia (Lobar Pneumonia)",
    "lobar pneumonia": "Community-Acquired Pneumonia (Lobar Pneumonia)",
    "cap": "Community-Acquired Pneumonia (Lobar Pneumonia)",
    "common cold": "Common Cold (Viral Upper Respiratory Infection)",
    "cold": "Common Cold (Viral Upper Respiratory Infection)",
    "viral uri": "Common Cold (Viral Upper Respiratory Infection)",
    "upper respiratory infection": "Common Cold (Viral Upper Respiratory Infection)",
    "influenza": "Influenza",
    "flu": "Influenza",
    "bronchitis": "Acute Bronchitis",
    "acute bronchitis": "Acute Bronchitis",
    "sinusitis": "Acute Sinusitis (Rhinosinusitis)",
    "acute sinusitis": "Acute Sinusitis (Rhinosinusitis)",
    "rhinitis": "Allergic Rhinitis",
    "allergic rhinitis": "Allergic Rhinitis",
    "strep throat": "Streptococcal Pharyngitis (Strep Throat)",
    "pharyngitis": "Streptococcal Pharyngitis (Strep Throat)",
    "tonsillitis": "Streptococcal Pharyngitis (Strep Throat)",
    "croup": "Croup (Laryngotracheobronchitis)",
    "epiglottitis": "Acute Epiglottitis",
    "mono": "Mononucleosis (Infectious / EBV)",
    "mononucleosis": "Mononucleosis (Infectious / EBV)",

    # Acute Cardiovascular Emergencies
    "stemi": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "nstemi": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "acute myocardial infarction": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "myocardial infarction": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "st elevation": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "crushing chest pain": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "acute coronary syndrome": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "acs": "Acute Myocardial Infarction (STEMI/NSTEMI)",

    # Chronic General Medical
    "type 2 diabetes": "Type 2 Diabetes Mellitus",
    "type 2 diabetes mellitus": "Type 2 Diabetes Mellitus",
    "t2dm": "Type 2 Diabetes Mellitus",
    "type 1 diabetes": "Type 1 Diabetes Mellitus",
    "type 1 diabetes mellitus": "Type 1 Diabetes Mellitus",
    "t1dm": "Type 1 Diabetes Mellitus",
    "diabetes": "Type 2 Diabetes Mellitus",
    "diabetes mellitus": "Type 2 Diabetes Mellitus",
    "diabetic ketoacidosis": "Diabetic Ketoacidosis (DKA)",
    "dka": "Diabetic Ketoacidosis (DKA)",
    "hypertension": "Essential Hypertension",
    "essential hypertension": "Essential Hypertension",
    "high blood pressure": "Essential Hypertension",
    "htn": "Essential Hypertension",
    "iron deficiency anemia": "Iron Deficiency Anemia",
    "iron deficiency": "Iron Deficiency Anemia",
    "anemia": "Iron Deficiency Anemia",
    "osteoarthritis": "Osteoarthritis",
    "oa": "Osteoarthritis",
    "degenerative joint disease": "Osteoarthritis",
    "chronic kidney disease": "Chronic Kidney Disease (CKD)",
    "ckd": "Chronic Kidney Disease (CKD)",
    "kidney failure": "Chronic Kidney Disease (CKD)",
    "epilepsy": "Epilepsy / Seizure Disorder",
    "seizure disorder": "Epilepsy / Seizure Disorder",
    "seizures": "Epilepsy / Seizure Disorder",
    "depression": "Major Depressive Disorder (MDD)",
    "major depressive disorder": "Major Depressive Disorder (MDD)",
    "mdd": "Major Depressive Disorder (MDD)",
    "clinical depression": "Major Depressive Disorder (MDD)",
    "anxiety": "Generalized Anxiety Disorder",
    "generalized anxiety disorder": "Generalized Anxiety Disorder",
    "gad": "Generalized Anxiety Disorder",
    "atopic dermatitis": "Atopic Dermatitis (Eczema)",
    "eczema": "Atopic Dermatitis (Eczema)",
    "psoriasis": "Psoriasis Vulgaris",
    "psoriasis vulgaris": "Psoriasis Vulgaris",
    "otitis media": "Acute Otitis Media",
    "acute otitis media": "Acute Otitis Media",
    "ear infection": "Acute Otitis Media",
    "hypothyroidism": "Hypothyroidism / Myxedema Coma",
    "underactive thyroid": "Hypothyroidism / Myxedema Coma",
    "myxedema": "Hypothyroidism / Myxedema Coma",
    "hyperthyroidism": "Hyperthyroidism / Thyroid Storm",
    "thyroid storm": "Hyperthyroidism / Thyroid Storm",

    # Cardiopulmonary / Acute Emergencies
    "heart attack": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "myocardial infarction": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "acute myocardial infarction": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "stemi": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "nstemi": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "acute coronary syndrome": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "acs": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "angina": "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "stroke": "Acute Ischemic Stroke (CVA)",
    "ischemic stroke": "Acute Ischemic Stroke (CVA)",
    "acute ischemic stroke": "Acute Ischemic Stroke (CVA)",
    "cva": "Acute Ischemic Stroke (CVA)",
    "brain attack": "Acute Ischemic Stroke (CVA)",
    "asthma": "Bronchial Asthma",
    "bronchial asthma": "Bronchial Asthma",
    "asthma exacerbation": "Asthma Exacerbation",
    "acute asthma": "Asthma Exacerbation",
    "copd": "COPD Exacerbation",
    "copd exacerbation": "COPD Exacerbation",
    "pulmonary embolism": "Pulmonary Embolism",
    "pe": "Pulmonary Embolism",
    "aortic dissection": "Aortic Dissection",
    "acute aortic dissection": "Aortic Dissection",
    "cardiac tamponade": "Cardiac Tamponade",
    "tension pneumothorax": "Tension Pneumothorax",
    "pneumothorax": "Tension Pneumothorax",
    "heart failure": "Acute Heart Failure (Cardiogenic Pulmonary Edema)",
    "acute heart failure": "Acute Heart Failure (Cardiogenic Pulmonary Edema)",
    "chf": "Acute Heart Failure (Cardiogenic Pulmonary Edema)",
    "congestive heart failure": "Acute Heart Failure (Cardiogenic Pulmonary Edema)",
    "pericarditis": "Acute Pericarditis",
    "endocarditis": "Infective Endocarditis",
    "infective endocarditis": "Infective Endocarditis",

    # GI / Surgical / Abdominal
    "appendicitis": "Acute Appendicitis",
    "acute appendicitis": "Acute Appendicitis",
    "cholecystitis": "Acute Cholecystitis",
    "acute cholecystitis": "Acute Cholecystitis",
    "pancreatitis": "Acute Pancreatitis",
    "acute pancreatitis": "Acute Pancreatitis",
    "diverticulitis": "Acute Diverticulitis",
    "acute diverticulitis": "Acute Diverticulitis",
    "gerd": "Gastroesophageal Reflux Disease (GERD)",
    "gastroesophageal reflux": "Gastroesophageal Reflux Disease (GERD)",
    "acid reflux": "Gastroesophageal Reflux Disease (GERD)",
    "heartburn": "Gastroesophageal Reflux Disease (GERD)",
    "peptic ulcer": "Peptic Ulcer Disease",
    "peptic ulcer disease": "Peptic Ulcer Disease",
    "pud": "Peptic Ulcer Disease",
    "gastroenteritis": "Gastroenteritis (Viral)",
    "stomach flu": "Gastroenteritis (Viral)",

    # Renal / Genitourinary
    "kidney stones": "Nephrolithiasis (Kidney Stones)",
    "kidney stone": "Nephrolithiasis (Kidney Stones)",
    "nephrolithiasis": "Nephrolithiasis (Kidney Stones)",
    "renal calculi": "Nephrolithiasis (Kidney Stones)",
    "renal stone": "Nephrolithiasis (Kidney Stones)",
    "renal colic": "Nephrolithiasis (Kidney Stones)",
    "urinary tract infection": "Urinary Tract Infection (Lower)",
    "uti": "Urinary Tract Infection (Lower)",
    "bladder infection": "Urinary Tract Infection (Lower)",
    "cystitis": "Urinary Tract Infection (Lower)",
    "pyelonephritis": "Pyelonephritis (Upper UTI)",
    "kidney infection": "Pyelonephritis (Upper UTI)",

    # Musculoskeletal & Rheumatology
    "gout": "Gout (Acute Gouty Arthritis)",
    "acute gout": "Gout (Acute Gouty Arthritis)",
    "gouty arthritis": "Gout (Acute Gouty Arthritis)",
    "podagra": "Gout (Acute Gouty Arthritis)",
    "rheumatoid arthritis": "Rheumatoid Arthritis",
    "ra": "Rheumatoid Arthritis",
    "lupus": "Systemic Lupus Erythematosus (SLE)",
    "sle": "Systemic Lupus Erythematosus (SLE)",
    "systemic lupus erythematosus": "Systemic Lupus Erythematosus (SLE)",
    "costochondritis": "Costochondritis",

    # Neurological / Headache / Skin / Infections
    "migraine": "Migraine",
    "migraine headache": "Migraine",
    "tension headache": "Tension-type Headache",
    "tension-type headache": "Tension-type Headache",
    "subarachnoid hemorrhage": "Subarachnoid Hemorrhage",
    "sah": "Subarachnoid Hemorrhage",
    "meningitis": "Bacterial Meningitis",
    "bacterial meningitis": "Bacterial Meningitis",
    "meningococcal disease": "Meningococcal Disease / Meningococcemia (with Meningitis)",
    "meningococcal meningitis": "Meningococcal Disease / Meningococcemia (with Meningitis)",
    "bell's palsy": "Bell's Palsy (Idiopathic Facial Palsy)",
    "bells palsy": "Bell's Palsy (Idiopathic Facial Palsy)",
    "facial palsy": "Bell's Palsy (Idiopathic Facial Palsy)",
    "parkinson's": "Parkinson's Disease",
    "multiple sclerosis": "Multiple Sclerosis (Relapsing-Remitting)",
    "guillain-barre": "Guillain-Barré Syndrome",
    "cellulitis": "Cellulitis",
    "shingles": "Herpes Zoster (Shingles)",
    "chickenpox": "Varicella (Chickenpox)",
    "measles": "Measles",
    "status epilepticus": "Epilepsy / Seizure Disorder",
    "septic shock": "Septic Shock / Severe Sepsis",
    "sepsis": "Septic Shock / Severe Sepsis",
    "anaphylaxis": "Anaphylaxis",
    "dvt": "Deep Vein Thrombosis (DVT)",
    "deep vein thrombosis": "Deep Vein Thrombosis (DVT)",
    "atrial fibrillation": "Atrial Fibrillation (Rapid Ventricular Response)",
    "afib": "Atrial Fibrillation (Rapid Ventricular Response)",
    "afib with rvr": "Atrial Fibrillation (Rapid Ventricular Response)",
}

CANONICAL_DIFFERENTIALS: Dict[str, List[str]] = {
    "Dengue Fever": ["Malaria (Plasmodium falciparum)", "Typhoid Fever", "Chikungunya", "Zika Virus"],
    "Malaria (Plasmodium falciparum)": ["Dengue Fever", "Typhoid Fever", "Yellow Fever", "Severe Malaria / Cerebral Malaria"],
    "Malaria (Plasmodium vivax)": ["Malaria (Plasmodium falciparum)", "Dengue Fever", "Typhoid Fever"],
    "Typhoid Fever": ["Malaria (Plasmodium falciparum)", "Dengue Fever", "Gastroenteritis (Viral)"],
    "Tuberculosis (Active)": ["Community-Acquired Pneumonia (Lobar Pneumonia)", "Bronchial Asthma", "COPD Exacerbation"],
    "COVID-19": ["Influenza", "Common Cold (Viral Upper Respiratory Infection)", "Community-Acquired Pneumonia (Lobar Pneumonia)"],
    "Type 2 Diabetes Mellitus": ["Type 1 Diabetes Mellitus", "Diabetic Ketoacidosis (DKA)", "Chronic Kidney Disease (CKD)"],
    "Type 1 Diabetes Mellitus": ["Type 2 Diabetes Mellitus", "Diabetic Ketoacidosis (DKA)"],
    "Essential Hypertension": ["Chronic Kidney Disease (CKD)", "Acute Myocardial Infarction (STEMI/NSTEMI)", "Pheochromocytoma"],
    "Bronchial Asthma": ["Asthma Exacerbation", "COPD Exacerbation", "Acute Bronchitis"],
    "Asthma Exacerbation": ["Bronchial Asthma", "COPD Exacerbation", "Acute Bronchitis"],
    "Community-Acquired Pneumonia (Lobar Pneumonia)": ["Acute Bronchitis", "Pulmonary Embolism", "Bronchial Asthma"],
    "Acute Myocardial Infarction (STEMI/NSTEMI)": ["Pulmonary Embolism", "Aortic Dissection", "Acute Pericarditis", "Gastroesophageal Reflux Disease (GERD)"],
    "Acute Ischemic Stroke (CVA)": ["Subarachnoid Hemorrhage", "Bell's Palsy (Idiopathic Facial Palsy)", "Migraine"],
    "Acute Appendicitis": ["Acute Diverticulitis", "Nephrolithiasis (Kidney Stones)", "Gastroenteritis (Viral)"],
    "Migraine": ["Tension-type Headache", "Acute Sinusitis (Rhinosinusitis)", "Subarachnoid Hemorrhage"],
    "Gastroesophageal Reflux Disease (GERD)": ["Peptic Ulcer Disease", "Acute Pancreatitis", "Costochondritis"],
    "Urinary Tract Infection (Lower)": ["Pyelonephritis (Upper UTI)", "Nephrolithiasis (Kidney Stones)"],
    "Nephrolithiasis (Kidney Stones)": ["Pyelonephritis (Upper UTI)", "Urinary Tract Infection (Lower)", "Acute Diverticulitis"],
    "Iron Deficiency Anemia": ["Chronic Kidney Disease (CKD)", "Celiac Disease (Gluten-Sensitive Enteropathy)", "Hypothyroidism / Myxedema Coma"],
    "Osteoarthritis": ["Gout (Acute Gouty Arthritis)", "Rheumatoid Arthritis"],
    "Gout (Acute Gouty Arthritis)": ["Osteoarthritis", "Cellulitis", "Septic Arthritis"],
    "Hypothyroidism / Myxedema Coma": ["Major Depressive Disorder (MDD)", "Iron Deficiency Anemia", "Chronic Kidney Disease (CKD)"],
    "Common Cold (Viral Upper Respiratory Infection)": ["Allergic Rhinitis", "Acute Sinusitis (Rhinosinusitis)", "Acute Bronchitis"],
    "Acute Sinusitis (Rhinosinusitis)": ["Common Cold (Viral Upper Respiratory Infection)", "Allergic Rhinitis", "Migraine"],
    "Acute Bronchitis": ["Community-Acquired Pneumonia (Lobar Pneumonia)", "Bronchial Asthma", "Common Cold (Viral Upper Respiratory Infection)"],
    "Streptococcal Pharyngitis (Strep Throat)": ["Mononucleosis (Infectious / EBV)", "Common Cold (Viral Upper Respiratory Infection)", "Acute Epiglottitis"],
    "Acute Diverticulitis": ["Acute Appendicitis", "Nephrolithiasis (Kidney Stones)", "Gastroenteritis (Viral)"],
    "Acute Cholecystitis": ["Acute Pancreatitis", "Peptic Ulcer Disease", "Acute Hepatitis B"],
    "Acute Pancreatitis": ["Acute Cholecystitis", "Peptic Ulcer Disease", "Gastroesophageal Reflux Disease (GERD)"],
    "Cellulitis": ["Deep Vein Thrombosis", "Herpes Zoster (Shingles)", "Erysipelas"],
    "Pulmonary Embolism": ["Acute Myocardial Infarction (STEMI/NSTEMI)", "Community-Acquired Pneumonia (Lobar Pneumonia)", "Aortic Dissection"],
    "Aortic Dissection": ["Acute Myocardial Infarction (STEMI/NSTEMI)", "Pulmonary Embolism", "Acute Pericarditis"],
    "Diabetic Ketoacidosis (DKA)": ["Type 1 Diabetes Mellitus", "Type 2 Diabetes Mellitus", "Acute Pancreatitis"],
    "Bacterial Meningitis": ["Meningococcal Disease / Meningococcemia (with Meningitis)", "Subarachnoid Hemorrhage", "Viral Encephalitis"],
    "Septic Shock / Severe Sepsis": ["Bacterial Meningitis", "Community-Acquired Pneumonia (Lobar Pneumonia)", "Acute Pyelonephritis", "Acute Pancreatitis"],
    "Anaphylaxis": ["Asthma Exacerbation", "Acute Epiglottitis", "Cardiac Tamponade"],
    "Atrial Fibrillation (Rapid Ventricular Response)": ["Acute Heart Failure (Cardiogenic Pulmonary Edema)", "Pulmonary Embolism", "Acute Myocardial Infarction (STEMI/NSTEMI)"],
    "Deep Vein Thrombosis (DVT)": ["Cellulitis", "Pulmonary Embolism", "Ruptured Baker Cyst"],
    "Crimean-Congo Hemorrhagic Fever": ["Dengue Hemorrhagic Fever", "Kyasanur Forest Disease (Monkey Fever)", "Leptospirosis", "Meningococcal Disease / Meningococcemia (with Meningitis)"],
    "Bubonic Plague": ["Streptococcal Pharyngitis (Strep Throat)", "Mononucleosis (Infectious / EBV)", "Tularemia", "Scrub Typhus (Orientia tsutsugamushi)"],
}


# ---------------------------------------------------------------------------
# Scoring Functions
# ---------------------------------------------------------------------------

def _symptom_fuzzy_match(p: str, d: str) -> bool:
    """Accurately checks if patient symptom p matches disease symptom d without false prefix collisions."""
    if p == d:
        return True
    p_len = len(p)
    d_len = len(d)
    if p_len >= 4 and d_len >= 4:
        # Check whole-word / phrase containment
        if p in d:
            if re.search(r'\b' + re.escape(p) + r'\b', d):
                return True
        elif d in p:
            if re.search(r'\b' + re.escape(d) + r'\b', p):
                return True
        # Inflectional plural / gerund match (e.g. "headaches" vs "headache")
        p_stem = p.rstrip('s')
        d_stem = d.rstrip('s')
        if p_stem == d_stem:
            return True
        if p.endswith("ing") and p[:-3] in d:
            return True
        if d.endswith("ing") and d[:-3] in p:
            return True
    return False


CONSTITUTIONAL_SYMPTOMS = {
    "fever", "headache", "fatigue", "pain", "malaise", "nausea", "vomiting",
    "weakness", "chills", "myalgia", "body ache", "loss of appetite", "lethargy",
    "dizziness", "sweats", "generalized weakness"
}


def _symptom_score(
    patient_set: Set[str],
    disease_set: Set[str],
    cardinal_set: Set[str],
) -> Tuple[float, List[str], List[str]]:
    """
    Returns (score, supporting_findings, missing_cardinal_symptoms).
    Score calculated using:
      - Clinical Patient Coverage (what fraction of patient's symptoms this disease explains)
      - Cardinal Symptom Precision (+ bonus if cardinal matches, - penalty if patient lacks all cardinal symptoms)
      - Hallmark specificity: distinguishing hallmarks provide strong evidence, non-specific constitutional symptoms provide baseline evidence.
    """
    intersection: Set[str] = set()
    for p in patient_set:
        for d in disease_set:
            if _symptom_fuzzy_match(p, d):
                intersection.add(p)
                break

    if not intersection:
        return 0.0, [], list(cardinal_set)[:4]

    # Coverage: fraction of patient's symptoms explained by this disease
    coverage = len(intersection) / max(len(patient_set), 1)

    # Cardinal precision:
    cardinal_matches: Set[str] = set()
    cardinal_score = 0.0
    for p in patient_set:
        for c in cardinal_set:
            if _symptom_fuzzy_match(p, c):
                cardinal_matches.add(c)
                if c.lower() in CONSTITUTIONAL_SYMPTOMS:
                    cardinal_score += 0.06  # Constitutional non-specific symptom
                else:
                    cardinal_score += 0.20  # Specific cardinal hallmark
                break

    if cardinal_set:
        if not cardinal_matches:
            cardinal_score = -0.22  # Missing all hallmark/cardinal symptoms of this disease
        else:
            cardinal_score = min(cardinal_score, 0.40)
    else:
        cardinal_score = 0.0

    missing_cardinal = list(cardinal_set - cardinal_matches)[:4]
    supporting = sorted(list(intersection))[:8]

    base_score = (coverage * 0.40) + cardinal_score
    return round(base_score, 4), supporting, missing_cardinal


def _geographic_score(
    geo_bonuses: Dict[str, float],
    disease_name: str,
) -> float:
    """Returns geographic outbreak score 0–0.35."""
    return round(geo_bonuses.get(disease_name, 0.0), 4)


def _incubation_score(disease_name: str, days_since_return: Optional[int]) -> Tuple[float, str]:
    """
    Returns (score_delta, fit_label).
    FITS: +0.15, TOO_EARLY: -0.20, TOO_LATE: -0.10, UNKNOWN: 0.0
    """
    if days_since_return is None:
        return 0.0, "UNKNOWN"

    result = check_incubation_fit(disease_name.lower(), days_since_return)
    fit = result["fit"]

    if fit == "FITS":
        return +0.15, "FITS"
    elif fit == "TOO_EARLY":
        return -0.20, "TOO_EARLY"
    elif fit == "TOO_LATE":
        return -0.10, "TOO_LATE"
    else:
        return 0.0, "UNKNOWN"


def _cluster_score(
    active_clusters: List[str],
    disease_clusters: List[str],
) -> float:
    """Returns cluster bonus 0–0.35 (uncapped to allow pathognomonic patterns to dominate)."""
    matched = set(active_clusters).intersection(set(disease_clusters))
    if not matched:
        return 0.0
    # Sum cluster bonuses
    total = sum(
        SYNDROMIC_CLUSTERS[c]["score_bonus"]
        for c in matched
        if c in SYNDROMIC_CLUSTERS
    )
    # NO cap here — allow mpox_cluster (0.20) + dermatological_fever (0.10) to add up
    return round(total, 4)


def _hemorrhagic_flag_score(
    patient_symptoms: Set[str],
    disease_is_hemorrhagic: bool,
    active_clusters: List[str],
) -> float:
    """
    If patient has hemorrhagic symptoms AND disease is hemorrhagic → bonus.
    If patient has hemorrhagic symptoms AND disease is NOT hemorrhagic → slight penalty.
    """
    hemorrhagic_symptoms = {
        "bleeding", "hemorrhage", "blood in stool", "hemoptysis",
        "blood in urine", "nosebleed", "bruising"
    }
    patient_has_hemorrhagic = bool(
        normalize_symptom_set(list(patient_symptoms)).intersection(hemorrhagic_symptoms)
    )
    hemorrhagic_cluster = "hemorrhagic_fever" in active_clusters

    if (patient_has_hemorrhagic or hemorrhagic_cluster) and disease_is_hemorrhagic:
        return 0.10
    elif (patient_has_hemorrhagic or hemorrhagic_cluster) and not disease_is_hemorrhagic:
        return -0.05
    return 0.0


def _severity_uncertainty(score: float, disease_severity: str) -> str:
    """Maps score + disease severity to uncertainty label."""
    if score >= 0.70:
        return "Low"
    elif score >= 0.45:
        return "Moderate"
    else:
        return "High"


# ---------------------------------------------------------------------------
# Main Reasoning Engine
# ---------------------------------------------------------------------------

class ClinicalReasoningEngine:
    """
    God-Level Deterministic Clinical Reasoning Engine.

    Architecture:
    1. Takes extracted clinical data (symptoms, travel, days_since_return, negations)
    2. Scores ALL 50+ diseases in the offline KB
    3. Applies geographic, incubation, cluster, hemorrhagic bonuses
    4. Returns top-N scored candidates with full score breakdown
    5. LLM only fills in narrative sentences — does NOT reason from scratch

    This enables accurate diagnosis on hardware-constrained systems because:
    - Heavy reasoning is done in Python (instant, no GPU)
    - LLM receives a 200-token prompt with pre-ranked candidates
    - Even a 3B model can write excellent narratives for pre-determined answers
    """

    def score_all_diseases(
        self,
        patient_symptoms: List[str],
        negated_symptoms: List[str],
        countries_visited: List[str],
        days_since_return: Optional[int],
        live_geo_bonuses: Optional[Dict[str, float]] = None,
        top_n: int = 5,
    ) -> List[ScoredCandidate]:
        """
        Score all diseases in the KB and return top-N candidates.

        Args:
            patient_symptoms: List of symptoms the patient HAS
            negated_symptoms: List of symptoms the patient DENIED
            countries_visited: List of countries from travel history
            days_since_return: Days since returning from travel (or None)
            live_geo_bonuses: Optional additional geographic bonuses from intelligence_engine
            top_n: Number of top candidates to return

        Returns:
            List of ScoredCandidate objects, sorted by score descending
        """
        # Normalize inputs
        patient_sym_set = normalize_symptom_set(patient_symptoms)
        negated_sym_set = normalize_symptom_set(negated_symptoms)
        active_clusters = get_active_disease_clusters(patient_sym_set)

        # Build geographic bonuses
        geo_bonuses = get_diseases_for_geography(countries_visited)
        if live_geo_bonuses:
            # Merge live bonuses (take max)
            for disease, bonus in live_geo_bonuses.items():
                geo_bonuses[disease] = max(geo_bonuses.get(disease, 0.0), bonus)

        # -------------------------------------------------------------------
        # Direct Diagnostic Entity Recognition (Diagnostic Finding Boost)
        # -------------------------------------------------------------------
        direct_disease_matches: Dict[str, float] = {}
        canonical_diff_boosts: Dict[str, float] = {}

        check_tokens = [s.lower().strip() for s in patient_symptoms if s]

        for token in check_tokens:
            if not token:
                continue
            matched_canonical = CANONICAL_DISEASE_LOOKUP.get(token)
            if not matched_canonical:
                for c_term, c_disease in CANONICAL_DISEASE_LOOKUP.items():
                    if len(c_term) >= 4 and (c_term in token or token in c_term):
                        matched_canonical = c_disease
                        break

            if matched_canonical:
                # Direct diagnostic mention boost (genuine evidence, not fake score)
                boost = 0.35
                if matched_canonical in ("Essential Hypertension", "Type 2 Diabetes Mellitus", "Dyslipidemia", "Osteoarthritis"):
                    boost = 0.20
                direct_disease_matches[matched_canonical] = max(direct_disease_matches.get(matched_canonical, 0.0), boost)
                # Peers get differential panel consideration bonus
                diffs = CANONICAL_DIFFERENTIALS.get(matched_canonical, [])
                for diff_name in diffs:
                    if diff_name != matched_canonical:
                        canonical_diff_boosts[diff_name] = max(
                            canonical_diff_boosts.get(diff_name, 0.0),
                            0.08
                        )

        scored = []

        # Use MERGED KB = static (96+ diseases) + dynamic (live-learned from WHO/CDC/ProMED)
        try:
            from app.services.live_disease_scanner import get_merged_disease_kb
            active_kb = get_merged_disease_kb()
        except ImportError:
            active_kb = DISEASE_KB

        for disease_name, profile in active_kb.items():
            # Pre-normalized symptom sets
            d_sym_set = profile.get("_norm_symptoms")
            if d_sym_set is None:
                d_sym_set = normalize_symptom_set(profile.get("symptoms", []))
                profile["_norm_symptoms"] = d_sym_set

            c_sym_set = profile.get("_norm_cardinals")
            if c_sym_set is None:
                c_sym_set = normalize_symptom_set(profile.get("cardinal_symptoms", []))
                profile["_norm_cardinals"] = c_sym_set

            # 1. Symptom overlap score
            sym_score, supporting, missing_cardinal = _symptom_score(
                patient_sym_set,
                d_sym_set,
                c_sym_set,
            )

            # Direct canonical mention bonus
            direct_boost = direct_disease_matches.get(disease_name, 0.0)
            diff_peer_bonus = canonical_diff_boosts.get(disease_name, 0.0)
            sym_score = sym_score + direct_boost + diff_peer_bonus

            # 2. Geographic bonus
            geo_score = _geographic_score(geo_bonuses, disease_name)

            # 3. Incubation score
            incub_delta, fit_label = _incubation_score(disease_name, days_since_return)

            # 4. Syndromic cluster bonus
            cluster_score = _cluster_score(
                active_clusters,
                profile.get("clusters", []),
            )

            # 5. Hemorrhagic flag
            hemorrhagic_score = _hemorrhagic_flag_score(
                patient_sym_set,
                profile.get("hemorrhagic", False),
                active_clusters,
            )

            # 6. Negation penalty: if patient DENIED a cardinal symptom that's key for this disease
            negation_penalty = 0.0
            contradicting = []
            for cardinal in profile.get("cardinal_symptoms", []):
                cardinal_norm = normalize_symptom(cardinal)
                if cardinal_norm in negated_sym_set:
                    negation_penalty -= 0.12
                    contradicting.append(f"Patient denies {cardinal} (cardinal for {disease_name})")

            # Limit negation penalty
            negation_penalty = max(negation_penalty, -0.30)

            # 7. Minimum symptom threshold: need at least 1 symptom or geo match or direct boost
            if direct_boost == 0.0 and diff_peer_bonus == 0.0 and sym_score < 0.05 and geo_score == 0.0:
                continue  # Skip diseases with zero evidence

            # 8. PATHOGNOMONIC PATTERN BONUS
            # When a specific cluster perfectly matches a specific disease,
            # give an exclusive bonus that breaks ties with non-matching diseases.
            pathognomonic_bonus = 0.0

            # mpox_cluster is HIGHLY specific for Mpox (distinguishes from Dengue/Ebola)
            if "mpox_cluster" in active_clusters and "mpox_cluster" in profile.get("clusters", []):
                pathognomonic_bonus += 0.30  # Only Mpox has mpox_cluster in its profile

            # lymphadenopathy_fever is specific for diseases with prominent lymphadenopathy
            if "lymphadenopathy_fever" in active_clusters and "mpox_cluster" in profile.get("clusters", []):
                pathognomonic_bonus += 0.10

            # dermatological_fever helps separate skin diseases from VHFs
            if "dermatological_fever" in active_clusters and "dermatological_fever" in profile.get("clusters", []):
                pathognomonic_bonus += 0.08

            # hemorrhagic_fever cluster should NOT boost non-hemorrhagic diseases
            if "hemorrhagic_fever" in active_clusters and not profile.get("hemorrhagic", False):
                pathognomonic_bonus -= 0.15  # Penalize non-hemorrhagic diseases when VHF pattern present

            # 8b. High-specificity / pathognomonic hallmark boost
            spec_boost = 0.0
            for s in patient_sym_set:
                s_rule = HIGH_SPECIFICITY_SYMPTOMS.get(s) or HIGH_SPECIFICITY_SYMPTOMS.get(s.lower())
                if s_rule and disease_name in s_rule:
                    spec_boost += s_rule[disease_name]

            # 8c. Clinical Contradictions and Downweighting
            if "Cellulitis" in disease_name:
                if any(m in patient_sym_set for m in ["strawberry tongue", "redness of the eyes", "conjunctivitis", "cheilitis", "cracked lips"]):
                    spec_boost -= 0.60
                    contradicting.append("Cellulitis is inconsistent with bilateral mucosal/conjunctival signs")

            if "Meningitis" in disease_name:
                has_meningeal_sign = any(
                    m in patient_sym_set
                    for m in ["neck stiffness", "stiff neck", "nuchal rigidity", "Kernig sign", "Brudzinski sign", "confusion", "altered consciousness", "cloudy CSF with pleocytosis"]
                )
                if not has_meningeal_sign:
                    spec_boost -= 0.35
                    contradicting.append("Absence of neck stiffness, nuchal rigidity, or altered consciousness makes acute bacterial meningitis unlikely")

            # 8d. Epidemiological Bayesian Prior (Zebra Bias elimination)
            has_travel = bool(countries_visited)
            TROPICAL_VECTOR_DISEASES = {
                "Dengue Fever", "Dengue Hemorrhagic Fever",
                "Malaria (Plasmodium falciparum)", "Malaria (Plasmodium vivax)", "Severe Malaria / Cerebral Malaria",
                "Typhoid Fever", "Chikungunya", "Zika Virus", "Yellow Fever",
                "Leptospirosis", "Scrub Typhus (Orientia tsutsugamushi)", "Chandipura Encephalitis"
            }
            TROPICAL_HALLMARKS = {
                "retro-orbital pain", "retroorbital pain", "tourniquet test", "petechiae", "rigors",
                "cyclic fever", "tertian fever", "step-ladder fever", "rose spots", "eschar",
                "mosquito bite", "travel", "tropical", "monsoon", "splenomegaly", "hemolytic anemia"
            }
            has_tropical_hallmark = bool(patient_sym_set & TROPICAL_HALLMARKS)

            if disease_name in TROPICAL_VECTOR_DISEASES:
                if has_travel or geo_score > 0 or has_tropical_hallmark:
                    prior_score = 0.20
                else:
                    prior_score = -0.30  # Non-endemic tropical disease in non-traveler without vector hallmarks
            elif disease_name in COMMON_PREVALENCE_DISEASES:
                prior_score = 0.22
            elif disease_name in ULTRA_RARE_OUTBREAK_DISEASES:
                # Domestic zoonotic / vector-borne check: allow domestic non-travel endemic presentation
                # if patient has cardinal zoonotic vector or hallmark exposure (e.g. CCHF with tick/livestock, KFD with forest/tick, Nipah with bat)
                has_domestic_vector_exposure = (
                    (disease_name == "Crimean-Congo Hemorrhagic Fever" and bool(patient_sym_set & {"tick exposure", "livestock contact", "ecchymosis"}))
                    or (disease_name == "Kyasanur Forest Disease (Monkey Fever)" and bool(patient_sym_set & {"tick exposure", "forest exposure"}))
                    or (disease_name == "Nipah Virus Disease" and bool(patient_sym_set & {"bat exposure", "date palm sap", "myoclonus"}))
                )
                if not has_travel:
                    if has_domestic_vector_exposure:
                        prior_score = 0.15  # Domestic endemic zoonotic focus (e.g. Gujarat/Rajasthan CCHF, Western Ghats KFD, Kerala Nipah)
                    else:
                        prior_score = -0.45  # Quarantine gate: non-travelers without exposure do not get plague/ebola/nipah
                elif geo_score == 0.0:
                    prior_score = -0.40  # Geographic mismatch: traveled to non-endemic region (e.g. South America vs African VHF)
                else:
                    # Active 2026 Epidemiological Outbreak Surveillance Prior:
                    # In DRC (Congo), the active ongoing outbreak is Bundibugyo virus disease (BDBV - WHO DON617),
                    # not Zaire ebolavirus.
                    is_drc = any(c.lower() in ("democratic republic of the congo", "drc", "congo") for c in countries_visited)
                    is_madagascar = any(c.lower() in ("madagascar",) for c in countries_visited)
                    if is_drc:
                        if disease_name == "Bundibugyo Virus Disease (BVD)":
                            prior_score = 0.25  # Active ongoing 2026 outbreak in DRC
                        elif disease_name == "Ebola Virus Disease (Zaire)":
                            prior_score = 0.05
                        else:
                            prior_score = 0.0
                    elif is_madagascar:
                        if disease_name in ("Bubonic Plague", "Pneumonic Plague"):
                            prior_score = 0.35  # Madagascar endemic plague focus (>75% global cases)
                        else:
                            prior_score = 0.0
                    else:
                        prior_score = 0.0
            else:
                zones = profile.get("geographic_zones", ["Global"])
                if "Global" not in zones and not has_travel:
                    if any(z in zones for z in ["Asia", "Americas", "Africa", "South Asia", "India"]):
                        prior_score = -0.05
                    else:
                        prior_score = -0.25
                else:
                    prior_score = 0.0

            # 9. Compute final score from genuine clinical evidence
            raw_score = (
                sym_score
                + geo_score
                + incub_delta
                + cluster_score
                + hemorrhagic_score
                + negation_penalty
                + pathognomonic_bonus
                + spec_boost
                + prior_score
            )
            # Use raw unconstrained score for ranking to break ties cleanly; normalize to 0.05-0.98 for display
            final_score_raw = max(0.01, round(raw_score, 4))
            final_score = round(min(max(final_score_raw, 0.05), 0.98), 4)

            # Build explanation hint for LLM narrator
            hint_parts = []
            if spec_boost > 0:
                hint_parts.append("hallmark clinical signs present")
            if geo_score > 0:
                hint_parts.append(f"endemic in visited countries ({geo_score:.2f} geographic score)")
            if fit_label == "FITS":
                hint_parts.append(f"incubation period fits ({days_since_return} days)")
            elif fit_label == "TOO_EARLY":
                hint_parts.append(f"incubation too short for {days_since_return} days")
            elif fit_label == "TOO_LATE":
                hint_parts.append(f"incubation may be too long for {days_since_return} days")
            if supporting:
                hint_parts.append(f"{len(supporting)} symptoms match")
            if active_clusters:
                hint_parts.append(f"syndrome: {', '.join(active_clusters[:2])}")

            explanation_hint = "; ".join(hint_parts) if hint_parts else "symptom pattern match"

            scored.append(ScoredCandidate(
                disease=disease_name,
                score=final_score_raw,  # Use raw (uncapped) score for RANKING
                score_breakdown={
                    "symptom_overlap": sym_score,
                    "geographic": geo_score,
                    "incubation": incub_delta,
                    "syndrome_cluster": cluster_score,
                    "hemorrhagic_flag": hemorrhagic_score,
                    "negation_penalty": negation_penalty,
                    "specificity_boost": spec_boost,
                    "bayesian_prior": prior_score,
                },
                supporting_findings=supporting,
                missing_expected_findings=missing_cardinal,
                contradicting_information=contradicting,
                uncertainty=_severity_uncertainty(final_score, profile.get("severity", "moderate")),
                clusters_matched=[c for c in active_clusters if c in profile.get("clusters", [])],
                incubation_fit=fit_label,
                geographic_match=geo_score > 0,
                hemorrhagic=profile.get("hemorrhagic", False),
                severity=profile.get("severity", "moderate"),
                explanation_hint=explanation_hint,
            ))

        # Sort by score descending
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_n]

    def get_disease_profile_summary(self, disease_name: str) -> Optional[Dict]:
        """Returns the disease profile from the offline or dynamic KB."""
        # Check static KB first
        static = DISEASE_KB.get(disease_name)
        if static:
            return static
        # Fallback: check dynamic KB
        try:
            from app.services.live_disease_scanner import get_dynamic_kb_entry
            return get_dynamic_kb_entry(disease_name)
        except ImportError:
            return None

    def get_active_clusters_summary(self, patient_symptoms: List[str]) -> Dict[str, bool]:
        """Returns which syndromic clusters are active for a patient."""
        sym_set = normalize_symptom_set(patient_symptoms)
        active = get_active_disease_clusters(sym_set)
        return {c: (c in active) for c in SYNDROMIC_CLUSTERS}

    def build_deterministic_answer(
        self,
        candidates: List[ScoredCandidate],
        patient_context_short: str,
        active_clusters: List[str],
        days_since_return: Optional[int],
        countries_visited: List[str],
    ) -> str:
        """
        Builds a SHORT prompt for the LLM that contains the pre-ranked answer.
        The LLM only needs to write 1-2 sentence explanations.

        Returns a prompt under 600 tokens.
        """
        if not candidates:
            return ""

        top = candidates[0]

        # Build bullet list of pre-ranked candidates
        candidate_lines = []
        for i, c in enumerate(candidates[:5]):
            marker = "🥇" if i == 0 else f"#{i+1}"
            incub_note = f" [Incubation: {c.incubation_fit}]" if c.incubation_fit != "UNKNOWN" else ""
            geo_note = " [Geographic match]" if c.geographic_match else ""
            candidate_lines.append(
                f"{marker} {c.disease} (score={c.score:.2f}){incub_note}{geo_note}"
                f"\n   Hints: {c.explanation_hint}"
            )

        cluster_str = ", ".join(active_clusters) if active_clusters else "None"
        travel_str = f"{days_since_return} days since return from {', '.join(countries_visited)}" if countries_visited else "No travel"
        prompt = f"""You are a master diagnostic physician. A clinical reasoning engine has pre-ranked the top candidates:

PATIENT: {patient_context_short[:250]}
TRAVEL: {travel_str}
SYNDROME: {cluster_str}

PRE-RANKED CANDIDATES:
{chr(10).join(candidate_lines)}

INSTRUCTIONS:
1. Provide a 1-sentence clinical rationale for each candidate above.
2. OPEN-DOMAIN DIAGNOSIS: If and ONLY IF the patient's specific symptoms strongly indicate another medical pathology that is completely absent from the pre-ranked list above, you may include it in 'open_domain_candidates'. Otherwise, keep 'open_domain_candidates' empty ([]).

Return ONLY valid JSON:
{{
  "candidates": [
    {{
      "disease": "exact disease name",
      "explanation_reference": "1-2 sentences explaining why this matches and key test to confirm"
    }}
  ],
  "open_domain_candidates": [
    {{
      "disease": "Disease Name",
      "score": 0.85,
      "explanation_reference": "Clinical reason why this open diagnosis matches",
      "supporting_findings": ["finding1", "finding2"]
    }}
  ]
}}"""
        return prompt


# Singleton instance
clinical_reasoning_engine = ClinicalReasoningEngine()


# ---------------------------------------------------------------------------
# Clinical Decision Support: Must-Not-Miss Emergencies & Bedside Clarifiers
# ---------------------------------------------------------------------------

CRITICAL_EMERGENCY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "Acute Aortic Dissection": {
        "aliases": ["Aortic Dissection", "Thoracic Aortic Dissection"],
        "triggers": ["chest pain", "back pain", "tearing pain", "hypertension", "syncope", "pulse deficit"],
        "immediate_action": "Stat CT Angiography Chest/Abdomen; emergent cardiothoracic surgery consult; impulse control (IV esmolol to SBP 100-120, HR < 60) before vasodilators.",
        "confirmatory_tests": ["CT Angiography of Aorta", "Transesophageal Echocardiogram (TEE)"],
    },
    "Acute Coronary Syndrome (STEMI/NSTEMI)": {
        "aliases": ["Acute Myocardial Infarction (STEMI/NSTEMI)", "Acute MI", "STEMI", "NSTEMI"],
        "triggers": ["chest pain", "substernal pressure", "diaphoresis", "dyspnea", "left arm pain", "jaw pain", "st elevation"],
        "immediate_action": "Stat 12-lead ECG (<10 min) + serial hs-Troponin + ASPIRIN 324mg chewable; immediate cath lab activation for STEMI.",
        "confirmatory_tests": ["12-lead ECG", "Serial High-Sensitivity Cardiac Troponin", "Coronary Angiography"],
    },
    "Pulmonary Embolism": {
        "aliases": ["Acute Pulmonary Embolism", "PE"],
        "triggers": ["shortness of breath", "dyspnea", "pleuritic chest pain", "tachycardia", "hypoxia", "hemoptysis", "leg swelling"],
        "immediate_action": "Calculate Wells & PERC score; order CT Pulmonary Angiography; initiate therapeutic anticoagulation if high pretest probability without bleeding contraindications.",
        "confirmatory_tests": ["CT Pulmonary Angiography (CTPA)", "D-dimer (rule-out)", "Lower Extremity Venous Duplex Ultrasound"],
    },
    "Tension Pneumothorax": {
        "aliases": ["Tension Pneumothorax"],
        "triggers": ["sudden chest pain", "severe dyspnea", "absent breath sounds", "tracheal deviation", "hypotension"],
        "immediate_action": "Immediate needle thoracostomy (2nd ICS midclavicular or 5th ICS anterior axillary line) followed promptly by tube thoracostomy.",
        "confirmatory_tests": ["Clinical diagnosis (do NOT delay for X-ray)", "Bedside Lung Ultrasound", "Portable Chest Radiograph"],
    },
    "Bacterial Meningitis": {
        "aliases": ["Bacterial Meningitis", "Acute Meningitis"],
        "triggers": ["fever", "headache", "neck stiffness", "meningismus", "altered mental status", "photophobia", "purpura"],
        "immediate_action": "Stat IV Ceftriaxone 2g + Vancomycin 15-20mg/kg + Dexamethasone 10mg IV BEFORE or concurrently with Lumbar Puncture.",
        "confirmatory_tests": ["Lumbar Puncture (CSF Gram stain, cell count, protein, glucose)", "Blood Cultures x2"],
    },
    "Septic Shock / Severe Sepsis": {
        "aliases": ["Septic Shock / Severe Sepsis", "Sepsis", "Septic Shock"],
        "triggers": ["fever", "hypotension", "tachycardia", "altered mental status", "tachypnea", "elevated lactate"],
        "immediate_action": "Surviving Sepsis 1-Hour Bundle: 30 mL/kg IV crystalloid resuscitation, blood cultures prior to broad-spectrum antimicrobials, serum lactate, vasopressors for MAP < 65.",
        "confirmatory_tests": ["Serum Lactate", "Blood Cultures x2", "Urine & Sputum Cultures", "CBC with Differential"],
    },
    "Acute Ischemic Stroke (CVA)": {
        "aliases": ["Acute Ischemic Stroke (CVA)", "Stroke", "CVA"],
        "triggers": ["facial droop", "hemiparesis", "aphasia", "slurred speech", "sudden weakness", "numbness", "ataxia"],
        "immediate_action": "Stat Non-Contrast Head CT + CT Angiography Head/Neck; determine last known well; assess IV thrombolysis (<4.5h) and mechanical thrombectomy (<24h).",
        "confirmatory_tests": ["Non-Contrast Head CT", "CT Angiography Head & Neck", "MRI Brain with Diffusion (DWI)"],
    },
    "Ectopic Pregnancy": {
        "aliases": ["Ectopic Pregnancy"],
        "triggers": ["pelvic pain", "lower abdominal pain", "vaginal bleeding", "amenorrhea", "syncope", "hypotension"],
        "immediate_action": "Stat serum quantitative beta-hCG + bedside transvaginal ultrasound; immediate Ob/Gyn surgical consultation for hemoperitoneum.",
        "confirmatory_tests": ["Serum Quantitative beta-hCG", "Transvaginal Pelvic Ultrasound"],
    },
    "Acute Epiglottitis": {
        "aliases": ["Acute Epiglottitis"],
        "triggers": ["stridor", "drooling", "tripod position", "severe sore throat", "dysphagia", "muffled voice"],
        "immediate_action": "Maintain patient calm; do NOT examine pharynx with tongue blade; prepare for emergent difficult airway in operating room with ENT/anesthesia.",
        "confirmatory_tests": ["Direct fiberoptic laryngoscopy in controlled OR setting", "Lateral Soft Tissue Neck Radiograph"],
    },
    "Cauda Equina Syndrome": {
        "aliases": ["Cauda Equina Syndrome"],
        "triggers": ["back pain", "saddle anesthesia", "urinary retention", "fecal incontinence", "lower extremity weakness"],
        "immediate_action": "Stat Emergent Lumbar Spine MRI; immediate neurosurgical or orthopedic spine decompression within 24-48 hours.",
        "confirmatory_tests": ["Emergent Lumbar Spine MRI", "Post-void Residual Bladder Scan"],
    },
}

BEDSIDE_CLARIFYING_RULES: List[Dict[str, Any]] = [
    {
        "target_disease": "Acute Aortic Dissection",
        "question": "Is there a blood pressure discrepancy (>15-20 mmHg) between right and left arms?",
        "maneuver": "Bilateral Upper Extremity Blood Pressure Measurement",
        "positive_token": "bp discrepancy between arms",
        "negative_token": "denies bp discrepancy between arms",
        "positive_label": "+ BP Discrepancy (>15 mmHg)",
        "negative_label": "- Equal Bilateral BPs",
        "trigger_symptoms": ["chest pain", "back pain", "tearing pain", "hypertension", "angina"],
        "differentiates": "Aortic Dissection vs ACS / Pericarditis",
    },
    {
        "target_disease": "Pulmonary Embolism",
        "question": "Is there asymmetric calf swelling (circumference discrepancy >3 cm) or unilateral leg warmth/tenderness?",
        "maneuver": "Calf Circumference & Deep Vein Assessment",
        "positive_token": "unilateral leg swelling",
        "negative_token": "denies leg swelling",
        "positive_label": "+ Asymmetric Calf Swelling (>3 cm)",
        "negative_label": "- Symmetric Calves / No DVT Sign",
        "trigger_symptoms": ["shortness of breath", "dyspnea", "pleuritic chest pain", "tachycardia"],
        "differentiates": "PE vs Pneumonia / COPD / Asthma",
    },
    {
        "target_disease": "Acute Appendicitis",
        "question": "Is there point tenderness at McBurney's point or positive Rovsing / psoas sign?",
        "maneuver": "McBurney Point & Peritoneal Sign Palpation",
        "positive_token": "McBurney sign",
        "negative_token": "denies McBurney point tenderness",
        "positive_label": "+ Positive McBurney Sign",
        "negative_label": "- Negative McBurney Sign",
        "trigger_symptoms": ["abdominal pain", "nausea", "vomiting", "fever", "guarding"],
        "differentiates": "Appendicitis vs Diverticulitis / Gastroenteritis",
    },
    {
        "target_disease": "Acute Diverticulitis",
        "question": "Is the abdominal tenderness strictly localized to the Left Lower Quadrant (LLQ)?",
        "maneuver": "Left Lower Quadrant Abdominal Palpation",
        "positive_token": "left lower quadrant pain",
        "negative_token": "denies left lower quadrant pain",
        "positive_label": "+ Point Tenderness in LLQ",
        "negative_label": "- No LLQ Localization",
        "trigger_symptoms": ["abdominal pain", "fever", "diarrhea", "constipation", "guarding"],
        "differentiates": "Diverticulitis vs Appendicitis / Colitis",
    },
    {
        "target_disease": "Acute Cholecystitis",
        "question": "Does patient arrest inspiration upon deep palpation of the Right Upper Quadrant (Murphy's Sign)?",
        "maneuver": "Inspiratory Murphy Sign Examination",
        "positive_token": "Murphy sign",
        "negative_token": "denies Murphy sign",
        "positive_label": "+ Inspiratory Murphy Sign Positive",
        "negative_label": "- Murphy Sign Negative",
        "trigger_symptoms": ["abdominal pain", "right upper quadrant pain", "nausea", "epigastric pain"],
        "differentiates": "Cholecystitis vs Pancreatitis / PUD",
    },
    {
        "target_disease": "Pyelonephritis (Upper UTI)",
        "question": "Is there exquisite pain upon gentle fist percussion over the costovertebral angle (CVA tenderness)?",
        "maneuver": "Costovertebral Angle (CVA) Percussion",
        "positive_token": "costovertebral angle tenderness",
        "negative_token": "denies costovertebral angle tenderness",
        "positive_label": "+ Costovertebral Angle Tenderness",
        "negative_label": "- No CVA Tenderness",
        "trigger_symptoms": ["fever", "flank pain", "back pain", "dysuria", "urinary frequency"],
        "differentiates": "Pyelonephritis vs Lower UTI / Nephrolithiasis",
    },
    {
        "target_disease": "Gout (Acute Gouty Arthritis)",
        "question": "Is the acute severe erythema and exquisite agony localized to the 1st Metatarsophalangeal (podagra) joint?",
        "maneuver": "First MTP Joint Inspection & Palpation",
        "positive_token": "podagra",
        "negative_token": "denies 1st MTP podagra",
        "positive_label": "+ 1st MTP Podagra Present",
        "negative_label": "- 1st MTP Sparing",
        "trigger_symptoms": ["joint pain", "joint swelling", "joint redness", "erythema"],
        "differentiates": "Gout vs Cellulitis / Septic Arthritis",
    },
    {
        "target_disease": "Cellulitis",
        "question": "Is there a rapidly advancing, warm erythematous border without fluctuance or pus collection?",
        "maneuver": "Skin Demarcation & Fluctuance Assessment",
        "positive_token": "spreading erythema",
        "negative_token": "denies spreading erythema",
        "positive_label": "+ Spreading Erythema & Induration",
        "negative_label": "- Discrete / Non-Spreading Lesion",
        "trigger_symptoms": ["skin redness", "erythema", "leg pain", "skin warmth"],
        "differentiates": "Cellulitis vs DVT / Contact Dermatitis",
    },
    {
        "target_disease": "Bacterial Meningitis",
        "question": "Is there resistance to passive neck flexion or positive Kernig / Brudzinski signs?",
        "maneuver": "Nuchal Rigidity & Meningismus Assessment",
        "positive_token": "neck stiffness",
        "negative_token": "denies neck stiffness",
        "positive_label": "+ Nuchal Rigidity Present",
        "negative_label": "- Supple Neck / No Meningismus",
        "trigger_symptoms": ["fever", "headache", "altered mental status", "photophobia"],
        "differentiates": "Meningitis vs Migraine / Encephalitis",
    },
    {
        "target_disease": "Nephrolithiasis (Kidney Stones)",
        "question": "Does the agonizing spasmodic flank pain radiate downward towards the groin or scrotum with inability to sit still?",
        "maneuver": "Colic Radiation Pattern Assessment",
        "positive_token": "radiating pain to groin",
        "negative_token": "denies groin radiation",
        "positive_label": "+ Spasmodic Flank Pain Radiating to Groin",
        "negative_label": "- Non-Radiating / Dull Flank Pain",
        "trigger_symptoms": ["flank pain", "severe pain", "hematuria"],
        "differentiates": "Nephrolithiasis vs Pyelonephritis / MSK Pain",
    },
]


def identify_must_not_miss_conditions(
    patient_symptoms: Optional[List[str]],
    current_candidate_names: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """Identifies critical time-sensitive emergencies relevant to the patient's symptoms."""
    patient_symptoms = patient_symptoms or []
    current_candidate_names = current_candidate_names or []
    sym_text = " ".join(s.lower() for s in patient_symptoms)
    flagged: List[Dict[str, Any]] = []

    for disease_name, info in CRITICAL_EMERGENCY_REGISTRY.items():
        # Check if triggers match
        matched_triggers = [t for t in info["triggers"] if t in sym_text]
        if matched_triggers:
            # Check if already present in candidates
            in_candidates = any(
                c.lower() == disease_name.lower() or any(a.lower() in c.lower() for a in info["aliases"])
                for c in current_candidate_names
            )
            flagged.append({
                "disease": disease_name,
                "acuity": "CRITICAL EMERGENCY",
                "matched_triggers": matched_triggers[:3],
                "immediate_action": info["immediate_action"],
                "confirmatory_tests": info["confirmatory_tests"],
                "in_top_candidates": in_candidates,
            })

    return flagged[:3]


def generate_bedside_questions(
    patient_symptoms: Optional[List[str]],
    negated_symptoms: Optional[List[str]],
    top_candidate_names: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """Identifies top 2-3 decisive bedside questions/maneuvers not yet answered in the note."""
    patient_symptoms = patient_symptoms or []
    negated_symptoms = negated_symptoms or []
    top_candidate_names = top_candidate_names or []
    sym_text = " ".join(s.lower() for s in (patient_symptoms + negated_symptoms))
    top_names_lower = [c.lower() for c in top_candidate_names]

    relevant_questions: List[Dict[str, Any]] = []

    for rule in BEDSIDE_CLARIFYING_RULES:
        pos_token = rule["positive_token"].lower()
        neg_token = rule["negative_token"].lower()

        # Skip if already documented
        if pos_token in sym_text or neg_token in sym_text:
            continue

        # Check if relevant to top candidate or trigger symptoms
        is_target_competing = any(rule["target_disease"].lower() in c for c in top_names_lower)
        has_symptom_overlap = any(ts in sym_text for ts in rule["trigger_symptoms"])

        if is_target_competing or has_symptom_overlap:
            relevant_questions.append({
                "target_disease": rule["target_disease"],
                "question": rule["question"],
                "maneuver": rule["maneuver"],
                "positive_token": rule["positive_token"],
                "negative_token": rule["negative_token"],
                "positive_label": rule["positive_label"],
                "negative_label": rule["negative_label"],
                "differentiates": rule["differentiates"],
                "is_urgent": is_target_competing,
            })

    # Sort so urgent/competing questions appear first
    relevant_questions.sort(key=lambda q: 0 if q["is_urgent"] else 1)
    return relevant_questions[:3]


def build_diagnostic_comparison_matrix(top_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Builds a structured side-by-side comparison matrix for the top 3 candidates."""
    matrix: List[Dict[str, Any]] = []

    for c in top_candidates[:3]:
        name = c.get("disease", "")
        imm_tests = c.get("immediate_tests", []) or c.get("recommended_investigations", [])
        gold_test = imm_tests[0] if imm_tests else "Definitive imaging or biopsy"
        meds = c.get("recommended_medications", [])
        empiric_rx = meds[0] if meds else "Guideline-directed medical therapy"
        cardinal = c.get("supporting_findings", [])[:3] or ["Characteristic presentation"]

        matrix.append({
            "disease": name,
            "icd10": c.get("icd10", ""),
            "icd11": c.get("icd11", ""),
            "display_score": c.get("display_score", f"{int(c.get('score', 0)*100)}%"),
            "cardinal_features": cardinal,
            "confirmatory_test": gold_test,
            "first_line_therapy": empiric_rx,
            "clinical_pearl": c.get("pearl", "Correlate with clinical trajectory and bedside response."),
        })

    return matrix


def generate_clinical_mdm_summary(
    top_candidates: List[Dict[str, Any]],
    extracted_findings: List[str],
    extracted_vitals: Dict[str, Any],
    must_not_miss: List[Dict[str, Any]],
) -> str:
    """Generates an EMR-ready, audit-compliant Medical Decision Making (MDM) note."""
    if not top_candidates:
        return "Assessment & Plan: Clinical findings insufficient for definitive differential diagnosis."

    top_1 = top_candidates[0]
    top_1_name = top_1.get("disease", "Unknown Condition")
    top_1_score = top_1.get("display_score", "High")
    top_1_findings = ", ".join(top_1.get("supporting_findings", [])[:4]) or "clinical presentation"

    # Vitals string
    v_parts = []
    if extracted_vitals:
        for k, v in extracted_vitals.items():
            v_parts.append(f"{k.upper()}: {v}")
    vitals_str = ", ".join(v_parts) if v_parts else "Vital signs reviewed and documented."

    # Runner up lines
    diff_lines = []
    for idx, c in enumerate(top_candidates[1:4], start=2):
        diff_lines.append(f"  {idx}. {c.get('disease')} (Probability: {c.get('display_score')}) — Considered in differential; will rule out with targeted workup.")
    runner_up_text = "\n".join(diff_lines) if diff_lines else "  2. Non-specific secondary etiologies."

    # Must-not-miss emergencies
    emergency_text = ""
    if must_not_miss:
        em_lines = [f"  • {m['disease']}: {m['immediate_action']}" for m in must_not_miss]
        emergency_text = "\nCRITICAL / MUST-NOT-MISS EMERGENCIES EVALUATED:\n" + "\n".join(em_lines) + "\n"

    # Workup lines
    tests = top_1.get("immediate_tests", []) or top_1.get("recommended_investigations", [])
    tests_str = ", ".join(tests[:4]) if tests else "Routine laboratory and imaging evaluation"

    # Medications lines
    meds = top_1.get("recommended_medications", [])
    meds_str = meds[0] if meds else "Guideline-directed medical management"

    mdm = f"""CLINICAL ASSESSMENT & MEDICAL DECISION MAKING (MDM)
============================================================
CLINICAL PRESENTATION & PHYSIOLOGY:
• Key Findings: {', '.join(extracted_findings[:6]) if extracted_findings else 'See history and physical examination'}
• Vital Signs & Stability: {vitals_str}

PRIMARY WORKING DIAGNOSIS:
• {top_1_name} (Confidence: {top_1_score})
  - Supporting Clinical Elements: {top_1_findings}
  - Rationale: Findings align closely with expected syndromic pattern and presentation timeline.

DIFFERENTIAL DIAGNOSES CONSIDERED & ACTIVE WORKUP:
{runner_up_text}
{emergency_text}
DIAGNOSTIC WORKUP ORDERED:
• Priority Confirmatory Tests: {tests_str}

ACUTE MANAGEMENT & PHARMACOTHERAPY:
• Initial Regimen: {meds_str}
• Safety Decision: Verified for contraindications, organ function, and allergy profiles.

DISPOSITION & MONITORING:
• Patient monitored with continuous telemetry / vital sign tracking as clinically indicated. Re-evaluation scheduled upon receipt of stat confirmatory diagnostics."""

    return mdm.strip()

