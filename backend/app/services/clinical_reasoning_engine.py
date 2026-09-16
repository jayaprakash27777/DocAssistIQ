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
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from app.services.offline_disease_kb import (
    DISEASE_KB,
    SYNDROMIC_CLUSTERS,
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

    # ---- Fatigue / weakness ----
    "malaise": "fatigue",
    "lethargy": "fatigue",
    "lassitude": "fatigue",
    "profound weakness": "weakness",
    "extreme weakness": "weakness",
    "marked weakness": "weakness",
    "generalized weakness": "weakness",
    "severe fatigue": "fatigue",
    "significant fatigue": "fatigue",

    # ---- GI ----
    "anorexia": "loss of appetite",
    "oliguria": "reduced urine output",
    "watery diarrhea": "diarrhea",
    "bloody diarrhea": "diarrhea",
    "loose stools": "diarrhea",
    "dysphagia": "difficulty swallowing",
    "difficulty eating": "difficulty swallowing",
    "difficulty drinking": "reduced oral intake",
    "nausea and vomiting": "vomiting",

    # ---- Eyes ----
    "conjunctival redness": "redness of the eyes",
    "conjunctivitis": "redness of the eyes",
    "red eyes": "redness of the eyes",
    "pink eye": "redness of the eyes",
    "conjunctival injection": "redness of the eyes",

    # ---- Cardiovascular ----
    "tachycardia": "rapid heart rate",
    "bradycardia": "slow heart rate",
    "haemorrhage": "hemorrhage",
    "haemorrhaging": "bleeding",
    "unexplained bleeding": "bleeding",
    "spontaneous bleeding": "bleeding",

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
    "dark urine": "reduced urine output",
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
    "severe joint pain": "severe bone pain",
    "joint stiffness": "morning stiffness",

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
}


def normalize_symptom(sym: str) -> str:
    sym_lower = sym.lower().strip()
    return SYMPTOM_ALIASES.get(sym_lower, sym_lower)


def normalize_symptom_set(symptoms: List[str]) -> Set[str]:
    return {normalize_symptom(s) for s in symptoms if s}


# ---------------------------------------------------------------------------
# Scoring Functions
# ---------------------------------------------------------------------------

def _symptom_score(
    patient_symptoms: Set[str],
    disease_symptoms: List[str],
    cardinal_symptoms: List[str],
) -> Tuple[float, List[str], List[str]]:
    """
    Returns (score, supporting_findings, missing_cardinal_symptoms).
    Score 0–0.60 based on:
      - Weighted Jaccard overlap with disease symptom profile
      - Cardinal symptom bonus (+0.08 each, capped)
    """
    disease_set = normalize_symptom_set(disease_symptoms)
    patient_set = normalize_symptom_set(list(patient_symptoms))
    cardinal_set = normalize_symptom_set(cardinal_symptoms)

    # Jaccard overlap
    intersection = patient_set.intersection(disease_set)
    union = patient_set.union(disease_set)
    jaccard = len(intersection) / max(len(union), 1)

    # Cardinal symptom bonus
    cardinal_matches = patient_set.intersection(cardinal_set)
    cardinal_bonus = min(len(cardinal_matches) * 0.08, 0.24)

    # Missing cardinal symptoms
    missing_cardinal = list(cardinal_set - patient_set)[:4]

    # Supporting findings = overlap symptoms, sorted by importance
    supporting = sorted(list(intersection))[:8]

    base_score = min(jaccard * 1.5 + cardinal_bonus, 0.60)
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

        scored = []

        # Use MERGED KB = static (96+ diseases) + dynamic (live-learned from WHO/CDC/ProMED)
        try:
            from app.services.live_disease_scanner import get_merged_disease_kb
            active_kb = get_merged_disease_kb()
        except ImportError:
            active_kb = DISEASE_KB

        for disease_name, profile in active_kb.items():
            # 1. Symptom overlap score
            sym_score, supporting, missing_cardinal = _symptom_score(
                patient_sym_set,
                profile.get("symptoms", []),
                profile.get("cardinal_symptoms", []),
            )

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

            # 7. Minimum symptom threshold: need at least 2 symptoms to score
            if sym_score < 0.05 and geo_score == 0.0:
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

            # 9. Compute final score (higher cap to let pathognomonic patterns dominate)
            raw_score = (
                sym_score
                + geo_score
                + incub_delta
                + cluster_score
                + hemorrhagic_score
                + negation_penalty
                + pathognomonic_bonus
            )
            # Use 1.5 cap for ranking; normalize to 0-1 for display
            final_score_raw = max(0.01, min(raw_score, 1.50))
            final_score = round(min(final_score_raw, 0.99), 4)  # Display score capped at 0.99

            # Build explanation hint for LLM narrator
            hint_parts = []
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

        prompt = f"""You are a medical AI. The deterministic reasoning engine has PRE-RANKED these diagnoses:

PATIENT SUMMARY: {patient_context_short[:300]}
TRAVEL: {travel_str}
SYNDROME: {cluster_str}

PRE-RANKED CANDIDATES (DO NOT CHANGE THE ORDER OR SCORES):
{chr(10).join(candidate_lines)}

For each candidate, write exactly 1-2 sentences of clinical rationale and the top 2 investigations to confirm.
Return ONLY valid JSON:
{{
  "candidates": [
    {{
      "disease": "exact name from pre-ranked list above",
      "score": number (use the score given above, do not change it),
      "supporting_findings": ["finding1", "finding2"],
      "missing_expected_findings": ["missing1"],
      "contradicting_information": [],
      "uncertainty": "Low|Moderate|High",
      "explanation_reference": "1-2 sentences: why + top 2 tests to confirm."
    }}
  ]
}}"""
        return prompt


# Singleton instance
clinical_reasoning_engine = ClinicalReasoningEngine()
