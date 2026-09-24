"""Prototype test for improved clinical precision scoring."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.offline_disease_kb import DISEASE_KB
from app.services.clinical_reasoning_engine import (
    normalize_symptom,
    normalize_symptom_set,
    get_active_disease_clusters,
    get_diseases_for_geography,
    check_incubation_fit,
)

# Prevalence tiers
COMMON_DISEASES = {
    "Common Cold (Viral Upper Respiratory Infection)",
    "Influenza",
    "COVID-19",
    "Migraine",
    "Tension-type Headache",
    "Acute Sinusitis (Rhinosinusitis)",
    "Acute Bronchitis",
    "Streptococcal Pharyngitis (Strep Throat)",
    "Gastroenteritis (Viral)",
    "Gastroesophageal Reflux Disease (GERD)",
    "Urinary Tract Infection (Lower)",
    "Allergic Rhinitis",
    "Costochondritis",
    "Asthma Exacerbation",
    "Peptic Ulcer Disease",
    "Herpes Zoster (Shingles)",
}

ULTRA_RARE_OUTBREAK = {
    "Pneumonic Plague", "Bubonic Plague", "Nipah Virus Disease",
    "Bundibugyo Virus Disease (BVD)", "Ebola Virus Disease (Zaire)",
    "Sudan Ebolavirus Disease", "Marburg Virus Disease", "Lassa Fever",
    "Crimean-Congo Hemorrhagic Fever", "Hantavirus Pulmonary Syndrome",
    "Andes Orthohantavirus (HPS)", "African Trypanosomiasis (Sleeping Sickness)",
    "Rift Valley Fever", "MERS-CoV", "Rabies", "Avian Influenza H5N1",
    "Lymphocytic Choriomeningitis (LCM)",
}

HIGH_SPECIFICITY_SYMPTOMS = {
    "right lower quadrant pain": {"Acute Appendicitis": 0.35},
    "left arm pain": {"Acute Myocardial Infarction (STEMI/NSTEMI)": 0.35},
    "pain radiating to left arm": {"Acute Myocardial Infarction (STEMI/NSTEMI)": 0.35},
    "neck stiffness": {"Bacterial Meningitis": 0.30, "Meningococcal Meningitis": 0.30},
    "nuchal rigidity": {"Bacterial Meningitis": 0.30, "Meningococcal Meningitis": 0.30},
    "polyuria": {"Diabetic Ketoacidosis (DKA)": 0.30},
    "polydipsia": {"Diabetic Ketoacidosis (DKA)": 0.30},
    "fruity breath": {"Diabetic Ketoacidosis (DKA)": 0.35},
    "flank pain radiating to groin": {"Nephrolithiasis (Kidney Stones)": 0.35},
    "eschar": {"Scrub Typhus (Orientia tsutsugamushi)": 0.40},
    "malar rash": {"Systemic Lupus Erythematosus (SLE)": 0.35},
    "dermatomal rash": {"Herpes Zoster (Shingles)": 0.35},
    "retro-orbital pain": {"Dengue Fever": 0.30},
    "retro-orbital headache": {"Dengue Fever": 0.30},
    "throbbing headache": {"Migraine": 0.30},
    "unilateral headache": {"Migraine": 0.30},
    "band-like headache": {"Tension-type Headache": 0.35},
    "facial pressure": {"Acute Sinusitis (Rhinosinusitis)": 0.30},
    "purulent nasal discharge": {"Acute Sinusitis (Rhinosinusitis)": 0.25},
    "tonsillar exudate": {"Streptococcal Pharyngitis (Strep Throat)": 0.35},
    "heartburn": {"Gastroesophageal Reflux Disease (GERD)": 0.35},
    "acid regurgitation": {"Gastroesophageal Reflux Disease (GERD)": 0.35},
}


def score_patient(patient_symptoms, negated_symptoms=None, countries_visited=None, days_since_return=None):
    if negated_symptoms is None:
        negated_symptoms = []
    if countries_visited is None:
        countries_visited = []

    patient_set = normalize_symptom_set(patient_symptoms)
    negated_set = normalize_symptom_set(negated_symptoms)
    has_travel = bool(countries_visited)
    geo_bonuses = get_diseases_for_geography(countries_visited)

    results = []

    # Temporary: add new common diseases if not in KB
    test_kb = dict(DISEASE_KB)
    if "Migraine" not in test_kb:
        test_kb["Migraine"] = {
            "symptoms": ["headache", "throbbing headache", "unilateral headache", "nausea", "vomiting", "photophobia", "sensitivity to light", "phonophobia", "sensitivity to sound", "aura"],
            "cardinal_symptoms": ["throbbing headache", "photophobia", "nausea", "headache"],
            "hemorrhagic": False,
            "geographic_zones": ["Global"],
            "clusters": ["neurological_syndrome"],
            "severity": "moderate"
        }
    if "Common Cold (Viral Upper Respiratory Infection)" not in test_kb:
        test_kb["Common Cold (Viral Upper Respiratory Infection)"] = {
            "symptoms": ["runny nose", "nasal congestion", "sneezing", "sore throat", "cough", "low-grade fever", "fatigue", "headache"],
            "cardinal_symptoms": ["runny nose", "nasal congestion", "sneezing"],
            "hemorrhagic": False,
            "geographic_zones": ["Global"],
            "clusters": ["respiratory_fever"],
            "severity": "low"
        }
    if "Tension-type Headache" not in test_kb:
        test_kb["Tension-type Headache"] = {
            "symptoms": ["headache", "bilateral headache", "band-like headache", "dull headache", "neck pain", "fatigue"],
            "cardinal_symptoms": ["headache", "band-like headache", "dull headache"],
            "hemorrhagic": False,
            "geographic_zones": ["Global"],
            "clusters": [],
            "severity": "low"
        }

    for disease, profile in test_kb.items():
        disease_syms = normalize_symptom_set(profile.get("symptoms", []))
        cardinal_syms = normalize_symptom_set(profile.get("cardinal_symptoms", []))

        # 1. Patient coverage
        intersection = patient_set.intersection(disease_syms)
        if not intersection:
            continue

        coverage = len(intersection) / max(len(patient_set), 1)

        # 2. Cardinal precision
        cardinal_matches = patient_set.intersection(cardinal_syms)
        if cardinal_syms:
            if not cardinal_matches:
                cardinal_score = -0.20  # Missing all cardinal symptoms!
            else:
                cardinal_score = min(len(cardinal_matches) * 0.10, 0.25)
        else:
            cardinal_score = 0.0

        # 3. Pathognomonic / High-Specificity Boost
        spec_boost = 0.0
        for s in patient_set:
            if s in HIGH_SPECIFICITY_SYMPTOMS and disease in HIGH_SPECIFICITY_SYMPTOMS[s]:
                spec_boost += HIGH_SPECIFICITY_SYMPTOMS[s][disease]

        # 4. Prevalence / Prior
        if disease in COMMON_DISEASES:
            prior_score = 0.22
        elif disease in ULTRA_RARE_OUTBREAK:
            if not has_travel:
                prior_score = -0.45  # Quarantine penalty for rare exotic diseases in non-travelers
            else:
                prior_score = 0.0
        else:
            # Endemic tropical without travel
            zones = profile.get("geographic_zones", ["Global"])
            if "Global" not in zones and not has_travel:
                prior_score = -0.30
            else:
                prior_score = 0.0

        # 5. Geographic score
        geo_score = geo_bonuses.get(disease, 0.0)

        # 6. Negation penalty
        neg_penalty = 0.0
        for c in cardinal_syms:
            if c in negated_set:
                neg_penalty -= 0.25

        raw = (coverage * 0.45) + cardinal_score + spec_boost + prior_score + geo_score + neg_penalty
        final = round(max(0.01, min(raw, 0.99)), 3)

        results.append((disease, final, sorted(list(intersection))))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:5]


print("=== CASE 1: [headache, fever] (No travel) ===")
for d, score, supp in score_patient(["headache", "fever"]):
    print(f"  {d:45s} | Score: {score:.3f} | Matches: {supp}")

print("\n=== CASE 2: Cardiac [chest pain, shortness of breath, diaphoresis, pain radiating to left arm] ===")
for d, score, supp in score_patient(["chest pain", "shortness of breath", "sweating", "pain radiating to left arm"]):
    print(f"  {d:45s} | Score: {score:.3f} | Matches: {supp}")

print("\n=== CASE 3: GI [right lower quadrant pain, fever, nausea, vomiting, loss of appetite] ===")
for d, score, supp in score_patient(["right lower quadrant pain", "fever", "nausea", "vomiting", "loss of appetite"]):
    print(f"  {d:45s} | Score: {score:.3f} | Matches: {supp}")

print("\n=== CASE 4: Tropical [fever, retro-orbital pain, rash, muscle aches] (Travel to Thailand) ===")
for d, score, supp in score_patient(["fever", "retro-orbital pain", "rash", "muscle aches"], countries_visited=["Thailand"]):
    print(f"  {d:45s} | Score: {score:.3f} | Matches: {supp}")
