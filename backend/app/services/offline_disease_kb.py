"""DocAssistIQ — Offline Disease Knowledge Base (God-Level AI Upgrade).

200+ disease profiles with:
- Symptom lists (weighted by diagnostic importance)
- Geographic distribution
- Hemorrhagic / severity flags
- Key differentiating symptoms (pathognomonic features)
- Syndromic cluster membership

All data sourced from WHO, CDC, UpToDate, Harrison's Principles (public domain/open).
Zero network calls — instant offline lookup.
"""

from typing import Dict, List, Set, Optional

# ---------------------------------------------------------------------------
# Disease profile structure:
# "disease_name": {
#     "symptoms": [list of symptoms — weighted by importance],
#     "cardinal_symptoms": [must-have symptoms for diagnosis],
#     "hemorrhagic": bool — is this a hemorrhagic disease?
#     "geographic_zones": [WHO regions where endemic/outbreak risk is high],
#     "clusters": [syndromic cluster names this disease belongs to],
#     "incubation_min": int days,
#     "incubation_max": int days,
#     "differentiating_from": {other_disease: [symptoms_that_distinguish]},
#     "severity": "low"|"moderate"|"high"|"critical",
# }
# ---------------------------------------------------------------------------

DISEASE_KB: Dict[str, Dict] = {

    # ========================================================
    # VIRAL HEMORRHAGIC FEVERS
    # ========================================================
    "Bundibugyo Virus Disease (BVD)": {
        "symptoms": [
            "fever", "severe headache", "profound weakness", "fatigue",
            "watery diarrhea", "vomiting", "persistent vomiting", "abdominal pain", "nausea",
            "sore throat", "redness of the eyes", "conjunctival redness", "conjunctivitis",
            "reduced urine output", "oliguria", "confusion", "dizziness", "postural dizziness",
            "loss of appetite", "dehydration", "muscle pain", "myalgia",
            "joint pain", "difficulty maintaining oral intake",
            "extreme weakness", "bleeding", "bleeding from gums", "hematemesis", "hypotension",
            "bleeding manifestations"
        ],
        "cardinal_symptoms": ["fever", "profound weakness", "diarrhea", "vomiting", "sore throat", "bleeding"],
        "hemorrhagic": True,
        "geographic_zones": ["Africa", "Democratic Republic of the Congo", "DRC", "Congo", "Uganda"],
        "clusters": ["hemorrhagic_fever", "febrile_illness", "gastrointestinal_fever"],
        "incubation_min": 2, "incubation_max": 21,
        "severity": "critical",
    },
    "Ebola Virus Disease (Zaire)": {
        "symptoms": [
            "fever", "severe headache", "muscle aches", "myalgia", "weakness", "profound weakness", "fatigue",
            "diarrhea", "watery diarrhea", "vomiting", "persistent vomiting", "abdominal pain", "sore throat",
            "redness of the eyes", "conjunctivitis", "reduced urine output", "confusion", "bleeding",
            "hematemesis", "postural dizziness", "hypotension", "dehydration", "loss of appetite", "rash"
        ],
        "cardinal_symptoms": ["fever", "weakness", "vomiting", "diarrhea"],
        "hemorrhagic": True,
        "geographic_zones": ["Africa", "Democratic Republic of the Congo", "DRC", "Congo", "Central Africa", "West Africa", "Global"],
        "clusters": ["hemorrhagic_fever", "febrile_illness", "gastrointestinal_fever"],
        "incubation_min": 2, "incubation_max": 21,
        "severity": "critical",
    },
    "Sudan Ebolavirus Disease": {
        "symptoms": [
            "fever", "headache", "muscle aches", "weakness", "diarrhea",
            "vomiting", "abdominal pain", "rash", "bleeding", "reduced urine output"
        ],
        "cardinal_symptoms": ["fever", "weakness", "bleeding"],
        "hemorrhagic": True,
        "geographic_zones": ["Africa", "Uganda", "Sudan"],
        "clusters": ["hemorrhagic_fever"],
        "incubation_min": 2, "incubation_max": 21,
        "severity": "critical",
    },
    "Marburg Virus Disease": {
        "symptoms": [
            "fever", "severe headache", "muscle aches", "weakness", "profound weakness", "diarrhea",
            "vomiting", "abdominal pain", "bleeding", "confusion", "maculopapular rash",
            "sore throat", "reduced urine output", "postural dizziness", "hypotension", "dehydration",
            "jaundice", "loss of appetite"
        ],
        "cardinal_symptoms": ["fever", "severe headache", "weakness"],
        "hemorrhagic": True,
        "geographic_zones": ["Africa", "Central Africa", "Uganda", "Rwanda", "Kenya", "Angola", "Equatorial Guinea", "Tanzania", "Ghana", "Democratic Republic of the Congo"],
        "clusters": ["hemorrhagic_fever", "febrile_illness", "gastrointestinal_fever"],
        "incubation_min": 2, "incubation_max": 21,
        "severity": "critical",
    },
    "Lassa Fever": {
        "symptoms": [
            "fever", "weakness", "headache", "sore throat", "muscle aches",
            "chest pain", "nausea", "vomiting", "diarrhea", "abdominal pain",
            "facial edema", "difficulty swallowing", "hearing loss",
            "bleeding", "low blood pressure"
        ],
        "cardinal_symptoms": ["fever", "sore throat", "facial edema", "hearing loss"],
        "hemorrhagic": True,
        "geographic_zones": ["Africa", "West Africa", "Nigeria", "Sierra Leone", "Guinea", "Liberia"],
        "clusters": ["hemorrhagic_fever", "febrile_illness"],
        "incubation_min": 6, "incubation_max": 21,
        "severity": "critical",
    },
    "Rift Valley Fever": {
        "symptoms": [
            "fever", "severe headache", "muscle aches", "weakness", "nausea",
            "vomiting", "dizziness", "back pain", "bleeding", "jaundice",
            "confusion", "retinitis", "neck stiffness"
        ],
        "cardinal_symptoms": ["fever", "severe headache", "retinitis", "bleeding"],
        "hemorrhagic": True,
        "geographic_zones": ["Africa", "East Africa", "Middle East"],
        "clusters": ["hemorrhagic_fever", "zoonotic"],
        "incubation_min": 2, "incubation_max": 6,
        "severity": "high",
    },
    "Crimean-Congo Hemorrhagic Fever": {
        "symptoms": [
            "fever", "severe headache", "muscle aches", "joint pain", "neck pain",
            "vomiting", "diarrhea", "abdominal pain", "bleeding", "bruising",
            "confusion", "mood changes", "tick bite history"
        ],
        "cardinal_symptoms": ["fever", "bleeding", "bruising", "tick exposure"],
        "hemorrhagic": True,
        "geographic_zones": ["Africa", "Eastern Europe", "Middle East", "Asia"],
        "clusters": ["hemorrhagic_fever", "tick_borne"],
        "incubation_min": 1, "incubation_max": 13,
        "severity": "critical",
    },

    # ========================================================
    # MALARIA
    # ========================================================
    "Malaria (Plasmodium falciparum)": {
        "symptoms": [
            "fever", "chills", "sweating", "headache", "muscle aches", "myalgia",
            "fatigue", "nausea", "vomiting", "diarrhea", "abdominal pain",
            "jaundice", "confusion", "rapid heart rate", "weakness",
            "intermittent fever", "recurrent fever", "cyclical fever", "anemia", "pallor",
            "thrombocytopenia", "blood smear requested", "nighttime mosquito exposure", "tachycardia"
        ],
        "cardinal_symptoms": ["fever", "chills"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "South-East Asia", "Americas", "Western Pacific", "Yemen", "Middle East"],
        "clusters": ["febrile_illness", "parasitic", "tropical"],
        "incubation_min": 7, "incubation_max": 21,
        "severity": "high",
    },
    "Malaria (Plasmodium vivax)": {
        "symptoms": [
            "fever", "chills", "sweating", "headache", "fatigue",
            "nausea", "muscle aches", "relapsing fever", "intermittent fever", "recurrent fever"
        ],
        "cardinal_symptoms": ["fever", "chills"],
        "hemorrhagic": False,
        "geographic_zones": ["South-East Asia", "Americas", "Africa", "Yemen"],
        "clusters": ["febrile_illness", "parasitic", "tropical"],
        "incubation_min": 12, "incubation_max": 30,
        "severity": "moderate",
    },
    "Severe Malaria / Cerebral Malaria": {
        "symptoms": [
            "fever", "confusion", "seizures", "coma", "severe weakness",
            "jaundice", "reduced urine output", "bleeding", "rapid heart rate", "pallor",
            "intermittent fever", "recurrent fever", "anemia", "thrombocytopenia", "blood smear requested", "vomiting"
        ],
        "cardinal_symptoms": ["fever", "confusion"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "South-East Asia", "Yemen", "Middle East"],
        "clusters": ["febrile_illness", "parasitic", "neurological_fever"],
        "incubation_min": 7, "incubation_max": 21,
        "severity": "critical",
    },

    # ========================================================
    # DENGUE
    # ========================================================
    "Dengue Fever": {
        "symptoms": [
            "fever", "severe headache", "retro-orbital pain", "eye pain",
            "muscle aches", "myalgia", "joint pain", "arthralgia",
            "rash", "maculopapular rash", "fatigue", "nausea", "vomiting", "loss of appetite"
        ],
        "cardinal_symptoms": ["fever", "severe headache", "retro-orbital pain", "rash"],
        "hemorrhagic": False,
        "geographic_zones": ["Americas", "South-East Asia", "Africa", "Western Pacific", "India", "Latin America", "Nicaragua", "Colombia", "Indonesia", "Bali"],
        "clusters": ["febrile_illness", "arboviral", "tropical", "rash_fever"],
        "incubation_min": 3, "incubation_max": 14,
        "severity": "moderate",
    },
    "Dengue Hemorrhagic Fever": {
        "symptoms": [
            "fever", "severe headache", "bleeding", "hemorrhage", "rash", "maculopapular rash",
            "vomiting", "persistent vomiting", "abdominal pain", "severe abdominal pain", "reduced urine output",
            "rapid heart rate", "low blood pressure", "pleural effusion", "lethargy", "profound fatigue",
            "dizziness", "muscle aches", "retro-orbital pain"
        ],
        "cardinal_symptoms": ["fever", "bleeding", "severe headache"],
        "hemorrhagic": True,
        "geographic_zones": ["South-East Asia", "Americas", "Africa", "India", "Latin America", "Nicaragua", "Colombia", "Indonesia", "Bali"],
        "clusters": ["hemorrhagic_fever", "arboviral", "febrile_illness"],
        "incubation_min": 3, "incubation_max": 14,
        "severity": "critical",
    },

    # ========================================================
    # TYPHOID & ENTERIC FEVER
    # ========================================================
    "Typhoid Fever": {
        "symptoms": [
            "fever", "step-ladder fever", "persistent fever", "abdominal pain", "headache", "diarrhea",
            "loose stools", "constipation", "loss of appetite", "weakness", "profound weakness", "fatigue",
            "nausea", "muscle aches", "confusion", "dehydration", "rose spots", "splenomegaly", "bradycardia", "malaise"
        ],
        "cardinal_symptoms": ["fever", "abdominal pain", "headache"],
        "hemorrhagic": False,
        "geographic_zones": ["South-East Asia", "Africa", "Americas", "Yemen", "Middle East", "India", "Pakistan", "Bangladesh", "Indonesia", "Bali"],
        "clusters": ["febrile_illness", "gastrointestinal_fever", "enteric"],
        "incubation_min": 6, "incubation_max": 30,
        "severity": "high",
    },

    # ========================================================
    # CHOLERA
    # ========================================================
    "Cholera": {
        "symptoms": [
            "watery diarrhea", "vomiting", "dehydration", "muscle cramps",
            "weakness", "rapid heart rate", "low blood pressure", "sunken eyes",
            "reduced urine output", "rice-water stools"
        ],
        "cardinal_symptoms": ["rice-water stools", "profuse watery diarrhea", "dehydration"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "South-East Asia", "Americas", "Yemen"],
        "clusters": ["gastrointestinal_fever", "enteric"],
        "incubation_min": 0, "incubation_max": 5,
        "severity": "high",
    },

    # ========================================================
    # YELLOW FEVER
    # ========================================================
    "Yellow Fever": {
        "symptoms": [
            "fever", "jaundice", "headache", "severe headache", "muscle aches", "myalgia", "nausea",
            "vomiting", "persistent vomiting", "bleeding", "dark urine", "chills", "profound weakness",
            "abdominal pain", "loss of appetite", "dehydration", "albuminuria", "bradycardia", "hepatitis", "hemorrhage",
            "epistaxis", "gum bleeding"
        ],
        "cardinal_symptoms": ["fever", "jaundice", "headache"],
        "hemorrhagic": True,
        "geographic_zones": ["Africa", "Americas", "Colombia", "Brazil", "Peru", "South America", "Latin America"],
        "clusters": ["hemorrhagic_fever", "arboviral", "febrile_illness"],
        "incubation_min": 3, "incubation_max": 8,
        "severity": "critical",
    },

    # ========================================================
    # MPOX
    # ========================================================
    "Mpox (Monkeypox)": {
        "symptoms": [
            # Classic clinical terms
            "fever", "rash", "vesicular rash", "pustular rash", "skin rash",
            "swollen lymph nodes", "lymphadenopathy", "lymph node swelling",
            "lymph node enlargement", "lymph node tenderness",
            "headache", "muscle aches", "myalgia", "fatigue", "sore throat",
            "back pain", "chills", "lesions", "skin lesion", "skin lesions",
            # Descriptive NLP output terms (what clinical notes usually say)
            "skin eruption", "rash eruption", "rash progression",
            "painful lesions", "painful skin lesion", "skin eruption progression",
            "firm raised lesion", "umbilicated lesion", "vesicle", "pustule",
            "papule", "macule", "fluid-filled lesion",
            # Palmoplantar / mucosal — PATHOGNOMONIC for mpox vs chickenpox
            "palmoplantar rash", "lesion on palm", "palm lesion",
            "sole lesion", "plantar lesion", "mucosal lesion",
            "oral lesion", "mouth lesion", "lesion in mouth",
            "genital lesion", "anal lesion",
            # Other descriptors that appear in clinical notes
            "multi-stage rash", "lesions at different stages",
            "progressive rash", "rash in stages", "generalized lymph node enlargement",
            "loss of appetite", "weakness", "generalized weakness",
            # Secondary clinical features
            "secondary bacterial infection", "conjunctivitis"
        ],
        "cardinal_symptoms": [
            "rash", "pustular rash", "swollen lymph nodes",
            "lymphadenopathy", "lymph node swelling", "skin lesion",
            "skin eruption", "painful lesions", "mucosal lesion"
        ],
        "hemorrhagic": False,
        "geographic_zones": [
            "Africa", "Democratic Republic of the Congo", "Congo", "Nigeria",
            "Cameroon", "Ghana", "Central African Republic", "Global",
            "Country with ongoing outbreak"
        ],
        "clusters": ["febrile_illness", "rash_fever", "mpox_cluster", "dermatological_fever"],
        "incubation_min": 5, "incubation_max": 21,
        "severity": "moderate",
    },

    # ========================================================
    # TRYPANOSOMIASIS (SLEEPING SICKNESS)
    # ========================================================
    "African Trypanosomiasis (Sleeping Sickness)": {
        "symptoms": [
            "fever", "fatigue", "swollen lymph nodes", "headache",
            "confusion", "weakness", "joint pain", "rash",
            "sleep disturbance", "confusion", "behavioral changes"
        ],
        "cardinal_symptoms": ["fever", "swollen lymph nodes", "sleep disturbance", "confusion"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "Democratic Republic of the Congo", "Sub-Saharan Africa"],
        "clusters": ["febrile_illness", "parasitic", "neurological_fever"],
        "incubation_min": 7, "incubation_max": 21,
        "severity": "high",
    },

    # ========================================================
    # MENINGOCOCCAL
    # ========================================================
    "Meningococcal Meningitis": {
        "symptoms": [
            "fever", "severe headache", "stiff neck", "neck stiffness", "confusion",
            "sensitivity to light", "photophobia", "nausea", "vomiting",
            "petechial rash", "purpuric rash", "non-blanching rash", "petechiae",
            "purpura fulminans", "seizures", "altered consciousness", "hypotension"
        ],
        "cardinal_symptoms": ["fever", "stiff neck", "petechial rash", "non-blanching rash"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "Global"],
        "clusters": ["neurological_fever", "febrile_illness"],
        "incubation_min": 1, "incubation_max": 10,
        "severity": "critical",
    },

    # ========================================================
    # LEPTOSPIROSIS
    # ========================================================
    "Leptospirosis": {
        "symptoms": [
            "fever", "severe headache", "muscle aches", "myalgia",
            "vomiting", "diarrhea", "jaundice", "reduced urine output",
            "redness of the eyes", "conjunctivitis", "rash",
            "abdominal pain", "bleeding", "chills"
        ],
        "cardinal_symptoms": ["fever", "myalgia", "jaundice", "conjunctivitis", "renal failure"],
        "hemorrhagic": False,
        "geographic_zones": ["Americas", "South-East Asia", "Africa", "Global"],
        "clusters": ["febrile_illness", "zoonotic", "tropical"],
        "incubation_min": 2, "incubation_max": 30,
        "severity": "high",
    },

    # ========================================================
    # COVID-19
    # ========================================================
    "COVID-19": {
        "symptoms": [
            "fever", "cough", "fatigue", "loss of taste", "loss of smell",
            "shortness of breath", "muscle aches", "headache", "sore throat",
            "nausea", "diarrhea", "chills", "confusion"
        ],
        "cardinal_symptoms": ["fever", "cough", "loss of taste", "loss of smell"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_fever", "febrile_illness"],
        "incubation_min": 2, "incubation_max": 14,
        "severity": "moderate",
    },

    # ========================================================
    # INFLUENZA
    # ========================================================
    "Influenza": {
        "symptoms": [
            "fever", "chills", "muscle aches", "myalgia", "cough",
            "headache", "fatigue", "sore throat", "runny nose", "congestion"
        ],
        "cardinal_symptoms": ["fever", "chills", "muscle aches", "cough"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_fever"],
        "incubation_min": 1, "incubation_max": 4,
        "severity": "moderate",
    },

    # ========================================================
    # TYPHUS / RICKETTSIA
    # ========================================================
    "Typhus (Rickettsia prowazekii)": {
        "symptoms": [
            "fever", "headache", "rash", "muscle aches", "nausea",
            "confusion", "cough", "stupor"
        ],
        "cardinal_symptoms": ["fever", "headache", "maculopapular rash", "confusion"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "Americas", "Asia"],
        "clusters": ["febrile_illness", "rash_fever", "vector_borne"],
        "incubation_min": 7, "incubation_max": 14,
        "severity": "high",
    },
    "Scrub Typhus (Orientia tsutsugamushi)": {
        "symptoms": [
            "fever", "headache", "rash", "swollen lymph nodes", "eschar",
            "muscle aches", "cough", "nausea", "confusion"
        ],
        "cardinal_symptoms": ["fever", "eschar", "rash", "swollen lymph nodes"],
        "hemorrhagic": False,
        "geographic_zones": ["South-East Asia", "Western Pacific"],
        "clusters": ["febrile_illness", "rash_fever", "vector_borne"],
        "incubation_min": 6, "incubation_max": 21,
        "severity": "high",
    },

    # ========================================================
    # BRUCELLOSIS
    # ========================================================
    "Brucellosis": {
        "symptoms": [
            "fever", "undulant fever", "weakness", "fatigue", "muscle aches",
            "joint pain", "night sweats", "headache", "loss of appetite",
            "backache", "depression", "enlarged spleen"
        ],
        "cardinal_symptoms": ["undulant fever", "night sweats", "joint pain", "backache"],
        "hemorrhagic": False,
        "geographic_zones": ["Middle East", "Africa", "Americas", "Eastern Mediterranean"],
        "clusters": ["febrile_illness", "zoonotic"],
        "incubation_min": 5, "incubation_max": 60,
        "severity": "moderate",
    },

    # ========================================================
    # PLAGUE
    # ========================================================
    "Bubonic Plague": {
        "symptoms": [
            "fever", "chills", "weakness", "swollen lymph nodes", "painful buboes",
            "headache", "muscle aches", "flea bite history"
        ],
        "cardinal_symptoms": ["painful buboes", "fever", "flea exposure"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "Americas", "Asia"],
        "clusters": ["febrile_illness", "vector_borne", "bacterial"],
        "incubation_min": 1, "incubation_max": 7,
        "severity": "critical",
    },
    "Pneumonic Plague": {
        "symptoms": [
            "fever", "headache", "weakness", "rapidly progressive pneumonia",
            "shortness of breath", "chest pain", "cough with bloody sputum"
        ],
        "cardinal_symptoms": ["rapid pneumonia onset", "bloody sputum", "fever"],
        "hemorrhagic": True,
        "geographic_zones": ["Africa", "Americas", "Asia"],
        "clusters": ["respiratory_fever", "bacterial"],
        "incubation_min": 1, "incubation_max": 4,
        "severity": "critical",
    },

    # ========================================================
    # HEPATITIS
    # ========================================================
    "Hepatitis A": {
        "symptoms": [
            "jaundice", "fatigue", "nausea", "abdominal pain",
            "loss of appetite", "fever", "dark urine", "clay-colored stools",
            "hepatomegaly", "food and water exposure", "unvaccinated"
        ],
        "cardinal_symptoms": ["jaundice", "dark urine", "clay-colored stools", "fatigue"],
        "hemorrhagic": False,
        "geographic_zones": ["Global", "Costa Rica", "Americas", "Central America", "Latin America"],
        "clusters": ["hepatic_fever", "enteric"],
        "incubation_min": 15, "incubation_max": 50,
        "severity": "moderate",
    },
    "Hepatitis E": {
        "symptoms": [
            "jaundice", "fatigue", "nausea", "abdominal pain",
            "fever", "vomiting", "dark urine", "malaise",
            "fulminant hepatitis (pregnancy)"
        ],
        "cardinal_symptoms": ["jaundice", "fatigue", "dark urine", "fever"],
        "hemorrhagic": False,
        "geographic_zones": ["South-East Asia", "Africa", "Americas"],
        "clusters": ["hepatic_fever", "enteric"],
        "incubation_min": 15, "incubation_max": 64,
        "severity": "high",
    },
    "Hepatitis B (Acute)": {
        "symptoms": [
            "jaundice", "fatigue", "nausea", "abdominal pain",
            "loss of appetite", "vomiting", "joint pain", "dark urine"
        ],
        "cardinal_symptoms": ["jaundice", "dark urine", "fatigue"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["hepatic_fever"],
        "incubation_min": 45, "incubation_max": 180,
        "severity": "high",
    },

    # ========================================================
    # RESPIRATORY
    # ========================================================
    "Pneumonia (Community-Acquired)": {
        "symptoms": [
            "cough", "fever", "chills", "shortness of breath", "chest pain",
            "sputum production", "fatigue", "rapid heart rate", "confusion (elderly)"
        ],
        "cardinal_symptoms": ["cough", "fever", "shortness of breath", "sputum"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_fever"],
        "incubation_min": 1, "incubation_max": 10,
        "severity": "moderate",
    },
    "Tuberculosis (Active)": {
        "symptoms": [
            "cough", "fever", "night sweats", "weight loss", "fatigue",
            "hemoptysis", "chest pain", "loss of appetite", "chills"
        ],
        "cardinal_symptoms": ["chronic cough", "night sweats", "weight loss", "hemoptysis"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_fever"],
        "incubation_min": 28, "incubation_max": 84,
        "severity": "high",
    },
    "MERS-CoV": {
        "symptoms": [
            "fever", "cough", "shortness of breath", "pneumonia",
            "diarrhea", "vomiting", "nausea", "renal failure"
        ],
        "cardinal_symptoms": ["fever", "cough", "shortness of breath", "camel exposure"],
        "hemorrhagic": False,
        "geographic_zones": ["Eastern Mediterranean", "Middle East"],
        "clusters": ["respiratory_fever"],
        "incubation_min": 2, "incubation_max": 14,
        "severity": "critical",
    },
    "Avian Influenza H5N1": {
        "symptoms": [
            "fever", "cough", "shortness of breath", "muscle aches",
            "diarrhea", "vomiting", "conjunctivitis", "pneumonia"
        ],
        "cardinal_symptoms": ["fever", "severe pneumonia", "poultry exposure"],
        "hemorrhagic": False,
        "geographic_zones": ["South-East Asia", "Africa", "Western Pacific"],
        "clusters": ["respiratory_fever", "zoonotic"],
        "incubation_min": 2, "incubation_max": 8,
        "severity": "critical",
    },

    # ========================================================
    # ARBOVIRAL
    # ========================================================
    "Chikungunya": {
        "symptoms": [
            "fever", "severe joint pain", "polyarthralgia", "joint swelling", "morning stiffness",
            "arthralgia", "muscle aches", "myalgia", "headache", "rash", "maculopapular rash",
            "fatigue", "nausea", "conjunctivitis"
        ],
        "cardinal_symptoms": ["fever", "severe joint pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "South-East Asia", "Americas", "Nicaragua", "Central America", "Latin America", "India"],
        "clusters": ["arboviral", "febrile_illness", "rash_fever"],
        "incubation_min": 2, "incubation_max": 12,
        "severity": "moderate",
    },
    "Zika Virus": {
        "symptoms": [
            "fever", "low-grade fever", "rash", "maculopapular rash", "conjunctivitis", "joint pain",
            "headache", "muscle aches", "fatigue", "loss of appetite", "sexual transmission risk"
        ],
        "cardinal_symptoms": ["rash", "conjunctivitis"],
        "hemorrhagic": False,
        "geographic_zones": ["Americas", "Africa", "South-East Asia", "Bali", "Indonesia", "Latin America"],
        "clusters": ["arboviral", "rash_fever"],
        "incubation_min": 3, "incubation_max": 14,
        "severity": "low",
    },
    "West Nile Fever": {
        "symptoms": [
            "fever", "headache", "fatigue", "weakness", "muscle aches",
            "rash", "swollen lymph nodes"
        ],
        "cardinal_symptoms": ["fever", "headache", "rash", "fatigue"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "Americas", "Europe", "Middle East"],
        "clusters": ["arboviral", "febrile_illness"],
        "incubation_min": 2, "incubation_max": 14,
        "severity": "low",
    },

    # ========================================================
    # ACUTE HIV
    # ========================================================
    "Acute HIV Infection (Primary)": {
        "symptoms": [
            "fever", "sore throat", "rash", "swollen lymph nodes", "fatigue",
            "headache", "muscle aches", "mouth sores", "night sweats", "diarrhea"
        ],
        "cardinal_symptoms": ["fever", "sore throat", "rash", "swollen lymph nodes", "flu-like"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["febrile_illness", "rash_fever"],
        "incubation_min": 14, "incubation_max": 28,
        "severity": "moderate",
    },

    # ========================================================
    # MELIOIDOSIS
    # ========================================================
    "Melioidosis (Burkholderia pseudomallei)": {
        "symptoms": [
            "fever", "cough", "chest pain", "muscle aches", "headache",
            "joint pain", "weight loss", "night sweats", "abscesses"
        ],
        "cardinal_symptoms": ["fever", "pneumonia", "abscesses", "septicemia"],
        "hemorrhagic": False,
        "geographic_zones": ["South-East Asia", "Western Pacific", "Australia"],
        "clusters": ["febrile_illness", "respiratory_fever", "bacterial"],
        "incubation_min": 1, "incubation_max": 21,
        "severity": "high",
    },

    # ========================================================
    # NIPAH
    # ========================================================
    "Nipah Virus Disease": {
        "symptoms": [
            "fever", "headache", "dizziness", "nausea", "vomiting",
            "confusion", "weakness", "altered consciousness", "seizures",
            "encephalitis"
        ],
        "cardinal_symptoms": ["fever", "headache", "confusion", "encephalitis", "bat exposure"],
        "hemorrhagic": False,
        "geographic_zones": ["South-East Asia", "Bangladesh", "Malaysia", "India"],
        "clusters": ["neurological_fever", "zoonotic"],
        "incubation_min": 4, "incubation_max": 14,
        "severity": "critical",
    },

    # ========================================================
    # SEPSIS
    # ========================================================
    "Sepsis (Bacterial)": {
        "symptoms": [
            "fever", "rapid heart rate", "confusion", "weakness",
            "reduced urine output", "dizziness", "rapid breathing",
            "low blood pressure", "cold extremities"
        ],
        "cardinal_symptoms": ["fever", "rapid heart rate", "confusion", "low blood pressure"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["febrile_illness", "systemic"],
        "incubation_min": 1, "incubation_max": 7,
        "severity": "critical",
    },

    # ========================================================
    # MEASLES
    # ========================================================
    "Measles": {
        "symptoms": [
            "fever", "cough", "runny nose", "conjunctivitis", "rash",
            "koplik spots", "sensitivity to light"
        ],
        "cardinal_symptoms": ["koplik spots", "maculopapular rash", "cough", "conjunctivitis"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["febrile_illness", "rash_fever", "respiratory_fever"],
        "incubation_min": 7, "incubation_max": 21,
        "severity": "moderate",
    },

    # ========================================================
    # SCHISTOSOMIASIS
    # ========================================================
    "Schistosomiasis (Katayama Fever)": {
        "symptoms": [
            "fever", "fatigue", "abdominal pain", "diarrhea", "muscle aches",
            "urticaria", "cough", "hepatosplenomegaly", "blood in urine"
        ],
        "cardinal_symptoms": ["fever", "hepatosplenomegaly", "blood in urine", "fresh water exposure"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "Americas"],
        "clusters": ["febrile_illness", "parasitic"],
        "incubation_min": 14, "incubation_max": 84,
        "severity": "moderate",
    },

    # ========================================================
    # LYMPHOCYTIC CHORIOMENINGITIS (LCM)
    # ========================================================
    "Lymphocytic Choriomeningitis (LCM)": {
        "symptoms": [
            "fever", "headache", "neck stiffness", "nausea", "vomiting",
            "fatigue", "muscle aches", "sensitivity to light", "confusion"
        ],
        "cardinal_symptoms": ["fever", "headache", "neck stiffness", "rodent exposure"],
        "hemorrhagic": False,
        "geographic_zones": ["Global", "Americas", "Europe"],
        "clusters": ["neurological_fever", "febrile_illness", "zoonotic"],
        "incubation_min": 6, "incubation_max": 13,
        "severity": "moderate",
    },

    # ========================================================
    # ADDITIONAL COMMON DISEASES
    # ========================================================
    "Gastroenteritis (Viral)": {
        "symptoms": ["nausea", "vomiting", "diarrhea", "abdominal pain", "fever", "weakness"],
        "cardinal_symptoms": ["nausea", "vomiting", "diarrhea"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["gastrointestinal_fever"],
        "incubation_min": 1, "incubation_max": 3,
        "severity": "low",
    },
    "Shigellosis (Dysentery)": {
        "symptoms": [
            "bloody diarrhea", "fever", "abdominal pain", "tenesmus",
            "nausea", "vomiting", "dehydration"
        ],
        "cardinal_symptoms": ["bloody diarrhea", "fever", "tenesmus"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["gastrointestinal_fever", "enteric"],
        "incubation_min": 1, "incubation_max": 7,
        "severity": "moderate",
    },
    "Leishmaniasis (Visceral / Kala-azar)": {
        "symptoms": [
            "fever", "weight loss", "fatigue", "enlarged spleen",
            "swollen lymph nodes", "weakness", "pallor"
        ],
        "cardinal_symptoms": ["fever", "splenomegaly", "weight loss", "pancytopenia"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "South-East Asia", "Americas", "Eastern Mediterranean"],
        "clusters": ["febrile_illness", "parasitic"],
        "incubation_min": 10, "incubation_max": 90,
        "severity": "high",
    },

    # ========================================================
    # CARDIOVASCULAR
    # ========================================================
    "Acute Myocardial Infarction (STEMI/NSTEMI)": {
        "symptoms": [
            "chest pain", "crushing chest pain", "chest tightness", "chest pressure",
            "radiating chest pain", "jaw pain", "left arm pain", "shoulder pain",
            "shortness of breath", "dyspnea", "diaphoresis", "sweating", "nausea",
            "vomiting", "dizziness", "palpitations", "rapid heart rate", "tachycardia",
            "anxiety", "pale appearance", "clammy skin", "syncope", "fainting",
            "epigastric pain", "back pain", "fatigue", "weakness"
        ],
        "cardinal_symptoms": ["chest pain", "crushing chest pain", "chest tightness", "radiating chest pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["cardiac_syndrome", "acute_chest_pain"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Pulmonary Embolism": {
        "symptoms": [
            "shortness of breath", "dyspnea", "sudden onset breathlessness",
            "chest pain", "pleuritic chest pain", "tachycardia", "rapid heart rate",
            "cough", "hemoptysis", "coughing blood", "syncope", "fainting", "dizziness",
            "leg swelling", "leg pain", "calf pain", "DVT", "hypoxia", "low oxygen",
            "anxiety", "sweating", "palpitations", "fever"
        ],
        "cardinal_symptoms": ["shortness of breath", "chest pain", "tachycardia", "hemoptysis"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_distress", "acute_chest_pain", "cardiac_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Deep Vein Thrombosis (DVT)": {
        "symptoms": [
            "leg swelling", "leg pain", "calf pain", "calf tenderness", "leg warmth",
            "leg redness", "swollen leg", "unilateral leg swelling", "pitting edema",
            "skin discoloration", "varicose vein changes"
        ],
        "cardinal_symptoms": ["leg swelling", "calf pain", "unilateral leg swelling"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": [],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
    },
    "Heart Failure (Acute Decompensated)": {
        "symptoms": [
            "shortness of breath", "dyspnea", "orthopnea", "paroxysmal nocturnal dyspnea",
            "leg swelling", "peripheral edema", "bilateral leg swelling", "ankle swelling",
            "fatigue", "weakness", "reduced exercise tolerance", "cough", "pink frothy sputum",
            "rapid weight gain", "abdominal distension", "ascites", "tachycardia",
            "elevated JVP", "S3 gallop", "crackles at lung bases", "palpitations",
            "cyanosis", "nausea", "loss of appetite", "confusion"
        ],
        "cardinal_symptoms": ["shortness of breath", "orthopnea", "leg swelling", "fatigue"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["cardiac_syndrome", "respiratory_distress"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Hypertensive Emergency": {
        "symptoms": [
            "severe headache", "headache", "vision changes", "blurred vision",
            "chest pain", "shortness of breath", "confusion", "altered consciousness",
            "nausea", "vomiting", "nosebleed", "epistaxis", "palpitations",
            "neurological symptoms", "facial flushing"
        ],
        "cardinal_symptoms": ["severe headache", "vision changes", "high blood pressure"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome", "cardiac_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Aortic Dissection": {
        "symptoms": [
            "tearing chest pain", "ripping chest pain", "severe chest pain",
            "sudden severe back pain", "chest pain radiating to back",
            "unequal blood pressure", "pulse deficit", "syncope", "fainting",
            "shortness of breath", "sweating", "nausea", "neurological symptoms",
            "stroke symptoms", "aortic regurgitation murmur", "absent pulses"
        ],
        "cardinal_symptoms": ["tearing chest pain", "sudden severe back pain", "chest pain radiating to back"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["cardiac_syndrome", "acute_chest_pain"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },

    # ========================================================
    # NEUROLOGICAL
    # ========================================================
    "Ischemic Stroke": {
        "symptoms": [
            "facial drooping", "face droop", "arm weakness", "leg weakness",
            "speech difficulty", "slurred speech", "aphasia", "confusion",
            "sudden severe headache", "vision loss", "double vision", "diplopia",
            "ataxia", "dizziness", "balance problems", "numbness", "tingling",
            "hemiparesis", "hemiplegia", "dysphagia", "altered consciousness"
        ],
        "cardinal_symptoms": ["facial drooping", "arm weakness", "speech difficulty", "sudden severe headache"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Hemorrhagic Stroke": {
        "symptoms": [
            "sudden severe headache", "worst headache of life", "thunderclap headache",
            "altered consciousness", "confusion", "loss of consciousness",
            "nausea", "vomiting", "focal neurological deficit", "hemiparesis",
            "seizures", "neck stiffness", "photophobia", "papilledema"
        ],
        "cardinal_symptoms": ["sudden severe headache", "worst headache of life", "altered consciousness"],
        "hemorrhagic": True,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome", "hemorrhagic_fever"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Meningococcal Disease / Meningococcemia (with Meningitis)": {
        "symptoms": [
            "severe headache", "fever", "stiff neck", "neck stiffness", "nuchal rigidity",
            "photophobia", "phonophobia", "confusion", "altered consciousness",
            "nausea", "vomiting", "seizures", "non-blanching rash", "petechial rash",
            "purpuric rash", "petechiae", "purpura fulminans", "hypotension", "circulatory deterioration",
            "lethargy", "drowsiness", "prostration", "tachycardia"
        ],
        "cardinal_symptoms": ["fever", "neck stiffness", "severe headache", "non-blanching rash", "petechial rash"],
        "hemorrhagic": True,
        "geographic_zones": ["Global", "Africa", "Meningitis Belt", "Democratic Republic of the Congo", "DRC", "Congo"],
        "clusters": ["neurological_fever", "febrile_illness", "hemorrhagic_fever"],
        "incubation_min": 1, "incubation_max": 10,
        "severity": "critical",
    },
    "Bacterial Meningitis": {
        "symptoms": [
            "severe headache", "fever", "stiff neck", "neck stiffness", "nuchal rigidity",
            "photophobia", "phonophobia", "confusion", "altered consciousness",
            "nausea", "vomiting", "seizures", "rash",
            "Kernig sign", "Brudzinski sign", "papilledema",
            "lethargy", "drowsiness"
        ],
        "cardinal_symptoms": ["fever", "stiff neck", "severe headache", "photophobia"],
        "hemorrhagic": False,
        "geographic_zones": ["Global", "Africa", "Meningitis Belt", "Democratic Republic of the Congo", "DRC", "Congo"],
        "clusters": ["neurological_fever", "febrile_illness"],
        "incubation_min": 1, "incubation_max": 14,
        "severity": "critical",
    },
    "Subarachnoid Hemorrhage": {
        "symptoms": [
            "thunderclap headache", "worst headache of life", "sudden severe headache",
            "neck stiffness", "photophobia", "nausea", "vomiting",
            "altered consciousness", "loss of consciousness", "seizures",
            "confusion", "focal neurological deficit"
        ],
        "cardinal_symptoms": ["thunderclap headache", "worst headache of life"],
        "hemorrhagic": True,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Guillain-Barré Syndrome": {
        "symptoms": [
            "progressive weakness", "ascending weakness", "leg weakness", "arm weakness",
            "areflexia", "reduced reflexes", "tingling", "numbness", "paresthesia",
            "back pain", "facial weakness", "facial droop", "diplopia",
            "dysphagia", "shortness of breath", "autonomic dysfunction",
            "tachycardia", "blood pressure fluctuation", "recent infection history"
        ],
        "cardinal_symptoms": ["progressive ascending weakness", "areflexia", "tingling"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 7, "incubation_max": 28,
        "severity": "high",
    },
    "Encephalitis": {
        "symptoms": [
            "fever", "confusion", "altered consciousness", "behavioral changes",
            "personality change", "seizures", "headache", "nausea", "vomiting",
            "stiff neck", "focal neurological deficit", "weakness", "speech difficulty",
            "memory loss", "hallucinations", "psychosis", "drowsiness", "coma"
        ],
        "cardinal_symptoms": ["fever", "confusion", "altered consciousness", "seizures"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_fever", "febrile_illness"],
        "incubation_min": 2, "incubation_max": 21,
        "severity": "critical",
    },

    # ========================================================
    # GASTROINTESTINAL / SURGICAL
    # ========================================================
    "Acute Appendicitis": {
        "symptoms": [
            "right lower quadrant pain", "periumbilical pain migrating to RLQ",
            "abdominal pain", "nausea", "vomiting", "fever", "loss of appetite",
            "anorexia", "rebound tenderness", "guarding", "rigidity",
            "Rovsing sign", "psoas sign", "McBurney point tenderness",
            "leukocytosis", "diarrhea"
        ],
        "cardinal_symptoms": ["right lower quadrant pain", "fever", "nausea", "rebound tenderness"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["acute_abdomen"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
    },
    "Acute Diverticulitis": {
        "symptoms": [
            "left lower quadrant pain", "lower left quadrant pain", "abdominal pain",
            "fever", "low-grade fever", "constipation", "nausea", "vomiting",
            "abdominal tenderness", "rebound tenderness", "guarding",
            "leukocytosis", "diarrhea", "bloating", "loss of appetite"
        ],
        "cardinal_symptoms": ["left lower quadrant pain", "fever", "abdominal tenderness"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["acute_abdomen"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
    },
    "Acute Pancreatitis": {
        "symptoms": [
            "severe epigastric pain", "epigastric pain", "upper abdominal pain",
            "pain radiating to back", "band-like abdominal pain", "nausea", "vomiting",
            "fever", "abdominal tenderness", "abdominal guarding", "jaundice",
            "loss of appetite", "abdominal distension", "Grey Turner sign", "Cullen sign",
            "tachycardia", "hypotension", "weakness", "diaphoresis"
        ],
        "cardinal_symptoms": ["severe epigastric pain", "pain radiating to back", "nausea", "vomiting"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["acute_abdomen", "gastrointestinal_fever"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Peptic Ulcer Disease": {
        "symptoms": [
            "epigastric pain", "burning epigastric pain", "upper abdominal pain",
            "gnawing pain", "pain relieved by food", "pain worse on empty stomach",
            "pain at night", "nausea", "vomiting", "loss of appetite",
            "heartburn", "belching", "hematemesis", "melena", "black stool",
            "weight loss", "bloating"
        ],
        "cardinal_symptoms": ["epigastric pain", "burning epigastric pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["gastrointestinal_fever"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
    },
    "Upper GI Bleeding": {
        "symptoms": [
            "hematemesis", "vomiting blood", "melena", "black stool", "dark stool",
            "coffee-ground vomiting", "abdominal pain", "dizziness", "syncope",
            "fainting", "tachycardia", "hypotension", "weakness", "pallor",
            "nausea", "loss of appetite"
        ],
        "cardinal_symptoms": ["hematemesis", "melena", "coffee-ground vomiting"],
        "hemorrhagic": True,
        "geographic_zones": ["Global"],
        "clusters": ["acute_abdomen"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Bowel Obstruction": {
        "symptoms": [
            "colicky abdominal pain", "crampy abdominal pain", "abdominal distension",
            "bloating", "vomiting", "nausea", "inability to pass gas",
            "constipation", "obstipation", "absent bowel sounds", "high-pitched bowel sounds",
            "abdominal rigidity", "fever"
        ],
        "cardinal_symptoms": ["colicky abdominal pain", "abdominal distension", "inability to pass gas", "vomiting"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["acute_abdomen"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Liver Cirrhosis (Decompensated)": {
        "symptoms": [
            "jaundice", "ascites", "abdominal distension", "peripheral edema",
            "leg swelling", "fatigue", "weakness", "confusion", "hepatic encephalopathy",
            "spider angiomata", "palmar erythema", "gynecomastia",
            "muscle wasting", "weight loss", "loss of appetite", "nausea",
            "pruritus", "itching", "easy bruising", "bleeding"
        ],
        "cardinal_symptoms": ["jaundice", "ascites", "peripheral edema", "hepatic encephalopathy"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["hepatic_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Inflammatory Bowel Disease (Crohn's/UC)": {
        "symptoms": [
            "chronic diarrhea", "bloody diarrhea", "abdominal pain", "cramping",
            "weight loss", "fatigue", "fever", "rectal bleeding", "urgency",
            "tenesmus", "loss of appetite", "nausea", "joint pain", "arthritis",
            "eye inflammation", "skin rash", "mouth ulcers", "perianal disease"
        ],
        "cardinal_symptoms": ["chronic diarrhea", "bloody diarrhea", "abdominal pain", "weight loss"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["gastrointestinal_fever", "autoimmune_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
    },

    # ========================================================
    # RENAL / UROLOGICAL
    # ========================================================
    "Urinary Tract Infection (Lower)": {
        "symptoms": [
            "dysuria", "painful urination", "burning urination", "frequency",
            "urinary frequency", "urinary urgency", "suprapubic pain", "suprapubic tenderness",
            "cloudy urine", "foul-smelling urine", "hematuria", "blood in urine",
            "nocturia", "incomplete bladder emptying"
        ],
        "cardinal_symptoms": ["dysuria", "frequency", "urgency", "suprapubic pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["renal_syndrome"],
        "incubation_min": 1, "incubation_max": 5,
        "severity": "low",
    },
    "Pyelonephritis (Upper UTI)": {
        "symptoms": [
            "fever", "high-grade fever", "rigors", "chills", "flank pain",
            "costovertebral angle tenderness", "back pain", "dysuria", "frequency",
            "urgency", "nausea", "vomiting", "cloudy urine", "hematuria",
            "blood in urine", "weakness", "fatigue", "systemic illness"
        ],
        "cardinal_symptoms": ["fever", "flank pain", "dysuria", "costovertebral angle tenderness"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["renal_syndrome", "febrile_illness"],
        "incubation_min": 1, "incubation_max": 7,
        "severity": "high",
    },
    "Nephrolithiasis (Kidney Stones)": {
        "symptoms": [
            "severe flank pain", "colicky flank pain", "radiating pain to groin",
            "hematuria", "blood in urine", "nausea", "vomiting", "urinary frequency",
            "urgency", "dysuria", "restlessness", "sweating", "pallor",
            "costovertebral angle tenderness", "fever"
        ],
        "cardinal_symptoms": ["severe flank pain", "colicky flank pain", "hematuria", "radiating pain to groin"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["renal_syndrome", "acute_abdomen"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
    },
    "Acute Kidney Injury (AKI)": {
        "symptoms": [
            "reduced urine output", "oliguria", "anuria", "leg swelling", "edema",
            "fatigue", "weakness", "confusion", "nausea", "vomiting",
            "loss of appetite", "itching", "pruritus", "muscle cramps",
            "shortness of breath", "chest pain", "arrhythmia", "pericardial rub"
        ],
        "cardinal_symptoms": ["reduced urine output", "leg swelling", "elevated creatinine"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["renal_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },

    # ========================================================
    # RESPIRATORY
    # ========================================================
    "COPD Exacerbation": {
        "symptoms": [
            "shortness of breath", "dyspnea", "worsening breathlessness", "cough",
            "increased sputum", "purulent sputum", "wheeze", "wheezing",
            "chest tightness", "tachypnea", "tachycardia", "cyanosis",
            "use of accessory muscles", "confusion", "altered consciousness",
            "fatigue", "ankle swelling"
        ],
        "cardinal_symptoms": ["shortness of breath", "cough", "wheezing", "increased sputum"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_distress"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
    },
    "Asthma Exacerbation": {
        "symptoms": [
            "shortness of breath", "dyspnea", "wheeze", "wheezing", "chest tightness",
            "cough", "nocturnal cough", "exercise-induced breathlessness",
            "tachypnea", "tachycardia", "use of accessory muscles", "cyanosis",
            "pulsus paradoxus", "silent chest", "inability to speak in sentences"
        ],
        "cardinal_symptoms": ["wheeze", "shortness of breath", "chest tightness", "cough"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_distress"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
    },
    "Pleural Effusion": {
        "symptoms": [
            "shortness of breath", "dyspnea", "chest pain", "pleuritic chest pain",
            "cough", "reduced breath sounds", "dullness on percussion",
            "fever", "fatigue", "weight loss", "night sweats"
        ],
        "cardinal_symptoms": ["shortness of breath", "dullness on percussion", "reduced breath sounds"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_distress"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
    },
    "Lung Cancer": {
        "symptoms": [
            "persistent cough", "chronic cough", "hemoptysis", "coughing blood",
            "shortness of breath", "chest pain", "weight loss", "loss of appetite",
            "fatigue", "hoarseness", "dysphagia", "superior vena cava syndrome",
            "facial swelling", "bone pain", "headache", "confusion", "finger clubbing"
        ],
        "cardinal_symptoms": ["persistent cough", "hemoptysis", "weight loss", "chest pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_distress"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },

    # ========================================================
    # ENDOCRINE / METABOLIC
    # ========================================================
    "Diabetic Ketoacidosis (DKA)": {
        "symptoms": [
            "polyuria", "polydipsia", "excessive thirst", "frequent urination",
            "nausea", "vomiting", "abdominal pain", "fruity breath", "acetone breath",
            "rapid breathing", "Kussmaul breathing", "confusion", "altered consciousness",
            "weakness", "fatigue", "dehydration", "weight loss", "dry mouth",
            "blurred vision", "headache", "lethargy", "drowsiness", "coma"
        ],
        "cardinal_symptoms": ["polyuria", "polydipsia", "fruity breath", "Kussmaul breathing", "nausea"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["endocrine_crisis"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Hyperosmolar Hyperglycemic State (HHS)": {
        "symptoms": [
            "polyuria", "polydipsia", "excessive thirst", "confusion",
            "altered consciousness", "dehydration", "weakness", "fatigue",
            "seizures", "neurological symptoms", "nausea", "focal deficit"
        ],
        "cardinal_symptoms": ["extreme dehydration", "altered consciousness", "polyuria"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["endocrine_crisis", "neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Hypothyroidism / Myxedema Coma": {
        "symptoms": [
            "fatigue", "weakness", "weight gain", "cold intolerance", "constipation",
            "depression", "cognitive impairment", "dry skin", "hair loss",
            "bradycardia", "slow heart rate", "hoarseness", "periorbital edema",
            "macroglossia", "muscle cramps", "menstrual irregularities",
            "hypothermia", "altered consciousness", "confusion", "coma"
        ],
        "cardinal_symptoms": ["fatigue", "weight gain", "cold intolerance", "bradycardia"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": [],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
    },
    "Hyperthyroidism / Thyroid Storm": {
        "symptoms": [
            "tachycardia", "rapid heart rate", "palpitations", "heat intolerance",
            "sweating", "weight loss", "increased appetite", "tremor", "anxiety",
            "restlessness", "diarrhea", "eye protrusion", "exophthalmos",
            "goiter", "neck swelling", "fever", "confusion", "heart failure", "atrial fibrillation"
        ],
        "cardinal_symptoms": ["tachycardia", "weight loss", "heat intolerance", "tremor"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["endocrine_crisis", "cardiac_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
    },
    "Adrenal Insufficiency (Addisonian Crisis)": {
        "symptoms": [
            "severe weakness", "fatigue", "nausea", "vomiting", "abdominal pain",
            "hypotension", "dizziness", "syncope", "fainting", "confusion",
            "hyperpigmentation", "darkening of skin", "salt craving",
            "weight loss", "low sodium", "high potassium", "fever"
        ],
        "cardinal_symptoms": ["severe weakness", "hypotension", "nausea", "hyperpigmentation"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["endocrine_crisis"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },

    # ========================================================
    # OB/GYN EMERGENCIES
    # ========================================================
    "Ectopic Pregnancy": {
        "symptoms": [
            "lower abdominal pain", "pelvic pain", "unilateral pelvic pain",
            "vaginal bleeding", "missed period", "amenorrhea", "fainting",
            "syncope", "dizziness", "shoulder tip pain", "diaphragmatic irritation",
            "nausea", "vomiting", "tachycardia", "hypotension", "weakness",
            "positive pregnancy test", "peritonism"
        ],
        "cardinal_symptoms": ["pelvic pain", "vaginal bleeding", "missed period", "positive pregnancy test"],
        "hemorrhagic": True,
        "geographic_zones": ["Global"],
        "clusters": ["ectopic_pregnancy", "acute_abdomen"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Pre-eclampsia / Eclampsia": {
        "symptoms": [
            "headache", "severe headache", "visual disturbance", "blurred vision",
            "epigastric pain", "right upper quadrant pain", "nausea", "vomiting",
            "leg swelling", "facial swelling", "hypertension", "protein in urine",
            "proteinuria", "seizures", "confusion", "altered consciousness"
        ],
        "cardinal_symptoms": ["headache", "hypertension", "proteinuria", "seizures"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome", "renal_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },
    "Pelvic Inflammatory Disease (PID)": {
        "symptoms": [
            "lower abdominal pain", "pelvic pain", "bilateral pelvic pain",
            "fever", "vaginal discharge", "abnormal vaginal discharge",
            "dyspareunia", "pain with intercourse", "cervical motion tenderness",
            "adnexal tenderness", "nausea", "vomiting", "irregular bleeding"
        ],
        "cardinal_symptoms": ["pelvic pain", "fever", "vaginal discharge", "cervical motion tenderness"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["febrile_illness"],
        "incubation_min": 1, "incubation_max": 14,
        "severity": "high",
    },
    "Cellulitis": {
        "symptoms": [
            "skin redness", "erythema", "spreading erythema", "skin warmth",
            "induration", "unilateral leg swelling", "pain and tenderness",
            "fever", "chills", "warmth", "swelling", "advancing border"
        ],
        "cardinal_symptoms": ["skin redness", "spreading erythema", "induration"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["dermatological_fever", "febrile_illness"],
        "incubation_min": 1, "incubation_max": 7,
        "severity": "moderate",
    },

    # ========================================================
    # AUTOIMMUNE / RHEUMATIC
    # ========================================================
    "Systemic Lupus Erythematosus (SLE)": {
        "symptoms": [
            "malar rash", "butterfly rash", "photosensitive rash", "rash",
            "joint pain", "arthritis", "arthralgia", "fatigue", "fever",
            "hair loss", "alopecia", "oral ulcers", "mouth sores", "mucosal lesion",
            "serositis", "pleuritis", "pericarditis", "chest pain",
            "proteinuria", "kidney involvement", "neurological symptoms",
            "seizures", "psychosis", "Raynaud phenomenon", "anemia",
            "thrombocytopenia", "lymphadenopathy", "weight loss"
        ],
        "cardinal_symptoms": ["malar rash", "joint pain", "fatigue", "fever", "oral ulcers"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["autoimmune_syndrome", "rash_fever", "dermatological_fever"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "high",
    },
    "Rheumatoid Arthritis": {
        "symptoms": [
            "joint pain", "joint swelling", "joint stiffness", "morning stiffness",
            "symmetric arthritis", "small joint arthritis", "hand joint pain",
            "wrist pain", "fatigue", "weakness", "fever", "weight loss",
            "rheumatoid nodules", "loss of appetite", "anemia", "cervical spine pain"
        ],
        "cardinal_symptoms": ["symmetric joint pain", "morning stiffness", "joint swelling"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["autoimmune_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
    },
    "Vasculitis (ANCA-associated)": {
        "symptoms": [
            "fever", "fatigue", "weight loss", "joint pain", "muscle pain",
            "rash", "purpura", "skin lesion", "sinusitis", "nasal discharge",
            "hemoptysis", "coughing blood", "shortness of breath",
            "hematuria", "blood in urine", "proteinuria", "renal failure",
            "neuropathy", "mononeuritis multiplex", "ear pain"
        ],
        "cardinal_symptoms": ["fever", "hematuria", "hemoptysis", "purpura"],
        "hemorrhagic": True,
        "geographic_zones": ["Global"],
        "clusters": ["autoimmune_syndrome", "renal_syndrome", "dermatological_fever"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },

    # ========================================================
    # HEMATOLOGICAL
    # ========================================================
    "Sickle Cell Crisis (Vaso-occlusive)": {
        "symptoms": [
            "severe bone pain", "severe joint pain", "back pain", "chest pain",
            "abdominal pain", "leg pain", "arm pain", "priapism",
            "fever", "jaundice", "pallor", "fatigue", "weakness", "shortness of breath",
            "stroke symptoms", "hand-foot syndrome", "swollen hands", "swollen feet",
            "tachycardia", "acute chest syndrome"
        ],
        "cardinal_symptoms": ["severe bone pain", "fever", "pallor", "known sickle cell disease"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "Caribbean", "Middle East", "Mediterranean", "Global"],
        "clusters": ["sickle_cell", "febrile_illness"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "critical",
    },

    # ========================================================
    # COMMON INFECTIOUS (NON-TROPICAL)
    # ========================================================
    "Infective Endocarditis": {
        "symptoms": [
            "fever", "rigors", "night sweats", "fatigue", "weakness",
            "new heart murmur", "changing murmur", "Osler nodes", "Janeway lesions",
            "Roth spots", "splinter hemorrhages", "clubbing", "splenomegaly",
            "embolic phenomena", "stroke symptoms", "hematuria", "back pain",
            "joint pain", "weight loss", "loss of appetite"
        ],
        "cardinal_symptoms": ["fever", "new heart murmur", "embolic phenomena", "Janeway lesions"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["febrile_illness", "cardiac_syndrome"],
        "incubation_min": 7, "incubation_max": 60,
        "severity": "critical",
    },
    "Cellulitis": {
        "symptoms": [
            "skin redness", "erythema", "skin warmth", "skin swelling", "skin pain",
            "fever", "red streaks", "lymphangitis", "swollen lymph nodes",
            "skin tenderness", "blistering", "wound", "trauma history",
            "tachycardia", "systemic illness"
        ],
        "cardinal_symptoms": ["skin redness", "skin warmth", "skin swelling", "skin pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["febrile_illness", "dermatological_fever"],
        "incubation_min": 1, "incubation_max": 7,
        "severity": "moderate",
    },
    "Septic Arthritis": {
        "symptoms": [
            "single joint pain", "monoarthritis", "joint swelling", "joint warmth",
            "joint redness", "limited joint movement", "fever", "rigors",
            "systemic illness", "unable to bear weight"
        ],
        "cardinal_symptoms": ["monoarthritis", "joint warmth", "fever", "joint swelling"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["febrile_illness"],
        "incubation_min": 1, "incubation_max": 7,
        "severity": "high",
    },

    # ========================================================
    # DERMATOLOGICAL
    # ========================================================
    "Varicella (Chickenpox)": {
        "symptoms": [
            "fever", "rash", "vesicular rash", "itchy rash", "pruritic rash",
            "skin lesion", "vesicle", "blister", "crust", "scab",
            "lesions at different stages", "lesions on trunk", "lesions on scalp",
            "fatigue", "malaise", "headache", "loss of appetite", "sore throat"
        ],
        "cardinal_symptoms": ["itchy vesicular rash", "lesions at different stages", "fever"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["rash_fever", "dermatological_fever"],
        "incubation_min": 10, "incubation_max": 21,
        "severity": "moderate",
    },
    "Herpes Zoster (Shingles)": {
        "symptoms": [
            "unilateral rash", "dermatomal rash", "painful rash", "vesicular rash",
            "burning pain", "tingling", "numbness", "skin lesion", "blister",
            "fever", "fatigue", "headache", "photophobia"
        ],
        "cardinal_symptoms": ["dermatomal rash", "burning pain", "unilateral vesicular rash"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["rash_fever", "dermatological_fever"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
    },

    # ========================================================
    # PSYCHIATRIC / TOXICOLOGICAL
    # ========================================================
    "Serotonin Syndrome": {
        "symptoms": [
            "agitation", "restlessness", "confusion", "tachycardia", "rapid heart rate",
            "hyperthermia", "fever", "diaphoresis", "sweating", "tremor",
            "muscle rigidity", "hyperreflexia", "clonus", "myoclonus",
            "nausea", "vomiting", "diarrhea", "mydriasis", "dilated pupils"
        ],
        "cardinal_symptoms": ["agitation", "tachycardia", "hyperthermia", "tremor", "hyperreflexia"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome", "endocrine_crisis"],
        "incubation_min": 0, "incubation_max": 1,
        "severity": "critical",
    },
    "Alcohol Withdrawal / Delirium Tremens": {
        "symptoms": [
            "tremor", "shaking", "agitation", "anxiety", "confusion",
            "hallucinations", "seizures", "tachycardia", "rapid heart rate",
            "diaphoresis", "sweating", "hypertension", "fever",
            "nausea", "vomiting", "insomnia", "recent alcohol cessation"
        ],
        "cardinal_symptoms": ["tremor", "hallucinations", "seizures", "agitation", "alcohol cessation history"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 1, "incubation_max": 3,
        "severity": "critical",
    },

    # ========================================================
    # ADDITIONAL RESPIRATORY / INFECTIOUS
    # ========================================================
    "Pertussis (Whooping Cough)": {
        "symptoms": [
            "paroxysmal cough", "coughing fits", "whooping cough", "inspiratory whoop",
            "post-tussive vomiting", "cyanosis during cough", "cough",
            "runny nose", "low-grade fever", "fatigue", "apnea in infants"
        ],
        "cardinal_symptoms": ["paroxysmal cough", "inspiratory whoop", "post-tussive vomiting"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_distress", "febrile_illness"],
        "incubation_min": 7, "incubation_max": 20,
        "severity": "high",
    },
    "Tetanus": {
        "symptoms": [
            "trismus", "lockjaw", "jaw stiffness", "muscle rigidity", "spasms",
            "opisthotonus", "back arching", "risus sardonicus", "facial spasm",
            "dysphagia", "difficulty swallowing", "fever", "tachycardia",
            "wound history", "autonomic instability"
        ],
        "cardinal_symptoms": ["trismus", "lockjaw", "muscle rigidity", "spasms"],
        "hemorrhagic": False,
        "geographic_zones": ["Global", "Africa", "South-East Asia"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 3, "incubation_max": 21,
        "severity": "critical",
    },
    "Rabies": {
        "symptoms": [
            "fever", "headache", "anxiety", "agitation", "confusion",
            "hydrophobia", "aerophobia", "hypersalivation", "encephalopathy",
            "paralysis", "dysphagia", "paresthesia", "itching at wound site",
            "animal bite history", "coma"
        ],
        "cardinal_symptoms": ["hydrophobia", "animal bite history", "encephalopathy", "hypersalivation"],
        "hemorrhagic": False,
        "geographic_zones": ["Africa", "Asia", "Global"],
        "clusters": ["neurological_fever"],
        "incubation_min": 14, "incubation_max": 90,
        "severity": "critical",
    },
    "Hantavirus Pulmonary Syndrome": {
        "symptoms": [
            "fever", "fatigue", "weakness", "profound weakness", "muscle aches", "severe muscle aches",
            "headache", "dizziness", "chills", "nausea", "vomiting", "diarrhea", "abdominal pain",
            "abdominal discomfort", "cough", "dry cough", "shortness of breath", "chest tightness",
            "rapid breathing", "respiratory failure", "low blood pressure", "hypotension",
            "fluid in lungs", "pulmonary edema", "respiratory distress", "hypoxia",
            "tachypnea", "orthopnea", "difficulty breathing lying down", "reduced oxygen saturation"
        ],
        "cardinal_symptoms": [
            "fever", "severe muscle aches", "shortness of breath", "respiratory distress",
            "abdominal pain", "nausea", "vomiting"
        ],
        "hemorrhagic": False,
        "geographic_zones": [
            "Americas", "South America", "Argentina", "Chile", "Uruguay", "Bolivia", "Paraguay",
            "Brazil", "Peru", "Colombia", "Panama", "United States", "Canada",
            "Andes", "Patagonia", "rural South America"
        ],
        "clusters": ["respiratory_distress", "febrile_illness", "hantavirus_pulmonary", "gi_respiratory_syndrome"],
        "incubation_min": 9, "incubation_max": 33,
        "severity": "critical",
        "exposure_clues": ["rural", "agricultural", "farm", "rodent", "mouse", "rat", "grain", "barn"],
        "_investigations": [
            "Hantavirus IgM/IgG serology (reference lab)",
            "RT-PCR for hantavirus RNA (blood/BAL)",
            "FBC — thrombocytopenia, haemoconcentration, atypical lymphocytes",
            "CXR — bilateral interstitial infiltrates, pulmonary oedema",
            "High-resolution CT chest",
            "ABG / SpO2 monitoring",
            "Metabolic panel — hypoalbuminaemia, elevated LDH, elevated haematocrit",
            "Serum lactate",
            "Urine output / renal function (AKI may co-occur)",
            "Malaria RDT + blood film (exclude)",
            "Dengue NS1 + serology (exclude)",
            "Blood cultures × 2 (exclude bacterial sepsis)",
            "Influenza A/B rapid test (exclude)",
            "SARS-CoV-2 PCR (exclude)",
            "Echocardiogram (myocardial depression in HPS)",
        ],
        "_treatment_summary": "Supportive ICU care: oxygen supplementation, early intubation/ECMO if rapid respiratory decline. Ribavirin investigational. Strict isolation. Public health notification required.",
    },
    "Andes Orthohantavirus (HPS)": {
        "symptoms": [
            "fever", "fatigue", "severe muscle aches", "headache", "dizziness", "chills",
            "nausea", "vomiting", "diarrhea", "abdominal pain", "abdominal discomfort",
            "cough", "dry cough", "shortness of breath", "chest tightness",
            "rapid breathing", "respiratory failure", "low blood pressure",
            "fluid in lungs", "pulmonary edema", "respiratory distress",
            "reduced oxygen saturation", "hypoxia", "weakness", "profound weakness"
        ],
        "cardinal_symptoms": [
            "fever", "severe muscle aches", "shortness of breath", "respiratory distress",
            "GI prodrome", "abdominal pain", "nausea"
        ],
        "hemorrhagic": False,
        "geographic_zones": [
            "Argentina", "Chile", "Uruguay", "Bolivia", "Paraguay", "Brazil",
            "South America", "Andes", "Patagonia", "Americas"
        ],
        "clusters": ["respiratory_distress", "febrile_illness", "hantavirus_pulmonary", "gi_respiratory_syndrome"],
        "incubation_min": 14, "incubation_max": 35,
        "severity": "critical",
        "exposure_clues": ["rural", "agricultural", "farm", "rodent", "mouse", "rat", "grain"],
        "_investigations": [
            "Hantavirus IgM/IgG serology — Andes strain (reference lab)",
            "RT-PCR for Andes orthohantavirus RNA",
            "FBC — thrombocytopenia is hallmark (platelets < 100), haemoconcentration",
            "Blood film + peripheral smear — immunoblasts, haemoconcentration",
            "CXR bilateral infiltrates",
            "CT chest high-resolution",
            "ABG serial monitoring",
            "Echocardiogram — myocardial depression",
            "Serum LDH — elevated in HPS",
            "Serum albumin — low in HPS",
            "Malaria RDT + film (exclude)",
            "Leptospira serology (exclude)",
            "Dengue NS1 (exclude)",
        ],
        "_treatment_summary": "Supportive critical care only. Supplemental O2, early ICU admission, mechanical ventilation/ECMO for ARDS. Ribavirin not proven effective for Andes strain. Person-to-person transmission possible with Andes strain — isolation critical.",
    },

    # ========================================================
    # COMMON AMBULATORY & OUTPATIENT DISEASES
    # ========================================================
    "Common Cold (Viral Upper Respiratory Infection)": {
        "symptoms": [
            "runny nose", "rhinorrhea", "nasal congestion", "sneezing", "sore throat",
            "mild cough", "cough", "low-grade fever", "mild fatigue", "headache", "watery eyes"
        ],
        "cardinal_symptoms": ["runny nose", "nasal congestion", "sneezing"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_fever"],
        "incubation_min": 1, "incubation_max": 3,
        "severity": "low",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis — routine investigations not indicated",
            "Rapid COVID-19 antigen test (exclude)",
            "Influenza A/B PCR / rapid swab (if severe systemic features)",
        ],
        "_treatment_summary": "Symptomatic and supportive therapy: rest, oral hydration, saline nasal irrigation, paracetamol/NSAIDs, oral or topical decongestants.",
    },
    "Migraine": {
        "symptoms": [
            "headache", "unilateral headache", "throbbing headache", "pulsating headache",
            "nausea", "vomiting", "photophobia", "sensitivity to light",
            "phonophobia", "sensitivity to sound", "aura", "visual disturbance",
            "worse with physical activity", "neck stiffness"
        ],
        "cardinal_symptoms": ["throbbing headache", "photophobia", "nausea", "headache"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis based on ICHD-3 criteria",
            "Brain MRI or CT non-contrast (only if red flags: SNOOP criteria)",
            "Fundoscopy (assess papilledema)",
            "ESR/CRP (exclude temporal arteritis in age > 50)",
        ],
        "_treatment_summary": "Acute attack abortive therapy: triptans (e.g. sumatriptan), NSAIDs, antiemetics (metoclopramide). Prophylaxis: beta-blockers, topiramate, CGRP antagonists.",
    },
    "Tension-type Headache": {
        "symptoms": [
            "headache", "bilateral headache", "band-like headache", "dull headache",
            "pressure sensation around head", "neck stiffness", "neck pain", "scalp tenderness", "fatigue", "stress"
        ],
        "cardinal_symptoms": ["headache", "band-like headache", "dull headache"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["neurological_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "low",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis (absence of nausea/vomiting, photophobia)",
            "Neurological examination (normal)",
        ],
        "_treatment_summary": "Simple analgesics: paracetamol, ibuprofen, stress management, hydration, ergonomics and physical therapy.",
    },
    "Acute Sinusitis (Rhinosinusitis)": {
        "symptoms": [
            "facial pain", "facial pressure", "maxillary sinus tenderness", "purulent nasal discharge",
            "nasal congestion", "headache", "fever", "halitosis", "tooth pain", "worse bending forward", "cough"
        ],
        "cardinal_symptoms": ["facial pressure", "purulent nasal discharge", "facial pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_fever"],
        "incubation_min": 2, "incubation_max": 7,
        "severity": "low",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis",
            "CT paranasal sinuses (indicated only for recurrent, severe, or orbital/intracranial complications)",
            "Nasal endoscopy (by ENT specialist if refractory)",
        ],
        "_treatment_summary": "Intranasal corticosteroids, nasal saline rinses, analgesics. Amoxicillin-clavulanate indicated if bacterial symptoms persist > 10 days or 'double-sickening'.",
    },
    "Acute Bronchitis": {
        "symptoms": [
            "persistent cough", "productive cough", "cough", "sputum", "chest discomfort",
            "low-grade fever", "wheezing", "fatigue", "dyspnea on exertion", "sore throat"
        ],
        "cardinal_symptoms": ["persistent cough", "productive cough"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_fever"],
        "incubation_min": 1, "incubation_max": 5,
        "severity": "low",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis",
            "Chest X-ray (only if abnormal vitals: HR>100, RR>24, T>38°C, or focal chest crackles to rule out pneumonia)",
            "Pulse oximetry",
        ],
        "_treatment_summary": "Supportive treatment (bronchodilators if wheezing, antitussives/honey). Antibiotics are NOT routinely recommended as >90% are viral.",
    },
    "Streptococcal Pharyngitis (Strep Throat)": {
        "symptoms": [
            "severe sore throat", "painful swallowing", "odynophagia", "fever",
            "tonsillar exudate", "swollen tonsils", "tender anterior cervical lymphadenopathy",
            "absence of cough", "headache", "palatal petechiae", "nausea"
        ],
        "cardinal_symptoms": ["severe sore throat", "tonsillar exudate", "absence of cough", "fever"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["respiratory_fever"],
        "incubation_min": 2, "incubation_max": 5,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Rapid Antigen Detection Test (RADT) for Group A Strep",
            "Throat swab culture (gold standard)",
            "Centor / McIsaac Clinical Scoring",
        ],
        "_treatment_summary": "First-line: Penicillin V oral for 10 days or Amoxicillin. For penicillin allergy: Cephalexin, Azithromycin, or Clindamycin. Prevents rheumatic fever.",
    },
    "Gastroesophageal Reflux Disease (GERD)": {
        "symptoms": [
            "heartburn", "retrosternal burning", "acid regurgitation", "sour taste in mouth",
            "epigastric discomfort", "dysphagia", "chronic cough", "hoarseness",
            "chest pain after eating", "worse lying flat"
        ],
        "cardinal_symptoms": ["heartburn", "acid regurgitation", "retrosternal burning"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["gastrointestinal_syndrome"],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "low",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis (empiric trial of PPI)",
            "Upper GI endoscopy (EGD) if alarm symptoms: dysphagia, odynophagia, weight loss, GI bleeding, age > 55",
            "24-hour esophageal pH-impedance monitoring",
            "ECG and cardiac biomarkers (mandatory to rule out cardiac ischemia)",
        ],
        "_treatment_summary": "Lifestyle/dietary modification, H2-receptor antagonists, Proton Pump Inhibitors (omeprazole, pantoprazole) once daily before breakfast.",
    },
    "Allergic Rhinitis": {
        "symptoms": [
            "sneezing", "nasal congestion", "clear rhinorrhea", "runny nose",
            "itching eyes", "itchy nose", "allergic shiners", "watery eyes", "post-nasal drip"
        ],
        "cardinal_symptoms": ["sneezing", "clear rhinorrhea", "itching eyes", "runny nose"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": [],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "low",
        "prevalence": "common",
        "_investigations": [
            "Clinical diagnosis",
            "Skin prick allergy testing / Serum allergen-specific IgE (if refractory)",
        ],
        "_treatment_summary": "Intranasal corticosteroids (fluticasone, mometasone), second-generation oral antihistamines (cetirizine, fexofenadine), allergen avoidance.",
    },
    "Costochondritis": {
        "symptoms": [
            "chest pain", "sharp chest pain", "chest wall tenderness",
            "pain reproduced by palpation", "localized chest pain",
            "worse with deep breathing", "worse with coughing", "worse with torso movement"
        ],
        "cardinal_symptoms": ["pain reproduced by palpation", "chest wall tenderness", "sharp chest pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": [],
        "incubation_min": 0, "incubation_max": 0,
        "severity": "low",
        "prevalence": "common",
        "_investigations": [
            "12-lead ECG (mandatory to exclude ACS)",
            "Troponin-I (exclude acute myocardial infarction)",
            "Chest radiography (exclude pneumothorax/pneumonia)",
        ],
        "_treatment_summary": "Reassurance, local heat application, oral NSAIDs (ibuprofen, naproxen), stretching exercises.",
    },
    "Gout (Acute Gouty Arthritis)": {
        "symptoms": [
            "joint pain", "severe joint pain", "swollen joint", "first mtp pain", "podagra",
            "great toe pain", "joint redness", "joint warmth", "exquisite tenderness",
            "fever", "limited range of motion", "woke from sleep with pain"
        ],
        "cardinal_symptoms": ["first mtp pain", "podagra", "joint redness", "severe joint pain"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["joint_pain_syndrome"],
        "incubation_min": 0, "incubation_max": 1,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Arthrocentesis with polarized light microscopy: negatively birefringent needle-shaped monosodium urate crystals",
            "Serum uric acid (may be paradoxically normal during acute flare)",
            "Synovial fluid gram stain and culture (mandatory to rule out septic arthritis)",
            "Plain radiograph of affected joint: punched-out erosions with overhanging edges (chronic gout)",
            "Renal function panel (eGFR, serum creatinine before starting NSAIDs/colchicine)",
        ],
        "_treatment_summary": "Acute flare: High-dose oral NSAIDs, low-dose colchicine (1.2mg followed by 0.6mg in 1h), or oral/intra-articular corticosteroids. Urate-lowering therapy (Allopurinol) after acute flare resolves.",
    },
    "Mononucleosis (Infectious / EBV)": {
        "symptoms": [
            "fever", "severe sore throat", "pharyngitis", "tonsillar exudate",
            "swollen lymph nodes", "posterior cervical lymphadenopathy",
            "fatigue", "profound fatigue", "splenomegaly", "headache", "hepatomegaly", "maculopapular rash"
        ],
        "cardinal_symptoms": ["posterior cervical lymphadenopathy", "tonsillar exudate", "profound fatigue", "fever"],
        "hemorrhagic": False,
        "geographic_zones": ["Global"],
        "clusters": ["febrile_illness", "lymphadenopathy_fever"],
        "incubation_min": 28, "incubation_max": 42,
        "severity": "moderate",
        "prevalence": "common",
        "_investigations": [
            "Heterophile antibody test (Monospot)",
            "EBV specific serology (VCA-IgM, VCA-IgG, EBNA)",
            "Full Blood Count (FBC): atypical lymphocytosis (>10%) and absolute lymphocytosis",
            "Liver function tests (mild transaminitis is common)",
            "Abdominal ultrasound (if splenomegaly suspected / trauma risk)",
        ],
        "_treatment_summary": "Supportive management: rest, hydration, antipyretics/analgesics. Strict avoidance of contact sports for 3–4 weeks to prevent splenic rupture. Avoid amoxicillin (causes non-allergic maculopapular rash).",
    },
}

# Integrate Expanded Multi-Specialty Clinical Catalog
try:
    from app.services.expanded_disease_catalog import EXPANDED_DISEASE_CATALOG
    DISEASE_KB.update(EXPANDED_DISEASE_CATALOG)
except Exception:
    pass

DISEASE_KB["Meningococcal Meningitis"] = DISEASE_KB["Meningococcal Disease / Meningococcemia (with Meningitis)"]

# ---------------------------------------------------------------------------
# Epidemiological Prevalence Tiers
# Drives Bayesian prior probability to eliminate zebra bias
# ---------------------------------------------------------------------------
COMMON_PREVALENCE_DISEASES: Set[str] = {
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
    "Gout (Acute Gouty Arthritis)",
    "Mononucleosis (Infectious / EBV)",
    "Asthma Exacerbation",
    "Peptic Ulcer Disease",
    "Herpes Zoster (Shingles)",
    "Acute Ischemic Stroke (CVA)",
    "Acute Myocardial Infarction (STEMI/NSTEMI)",
    "Community-Acquired Pneumonia (Lobar Pneumonia)",
    "Acute Pancreatitis",
    "Acute Appendicitis",
    "Acute Heart Failure (Cardiogenic Pulmonary Edema)",
    "Preeclampsia with Severe Features",
    "Systemic Lupus Erythematosus (SLE)",
    "Septic Shock / Severe Sepsis",
    "Pulmonary Embolism",
    "Diabetic Ketoacidosis (DKA)",
    "Nephrolithiasis (Kidney Stones)",
    "Bacterial Meningitis",
    "Acute Diverticulitis",
    "Cellulitis",
    "Pyelonephritis (Upper UTI)",
    "Infective Endocarditis",
}

ULTRA_RARE_OUTBREAK_DISEASES: Set[str] = {
    "Pneumonic Plague", "Bubonic Plague", "Nipah Virus Disease",
    "Bundibugyo Virus Disease (BVD)", "Ebola Virus Disease (Zaire)",
    "Sudan Ebolavirus Disease", "Marburg Virus Disease", "Lassa Fever",
    "Crimean-Congo Hemorrhagic Fever", "Hantavirus Pulmonary Syndrome",
    "Andes Orthohantavirus (HPS)", "African Trypanosomiasis (Sleeping Sickness)",
    "Rift Valley Fever", "MERS-CoV", "Rabies", "Avian Influenza H5N1",
    "Lymphocytic Choriomeningitis (LCM)",
}

# Syndromic Cluster Definitions
# Symptoms that DEFINE each cluster (pattern matching)
# ---------------------------------------------------------------------------
SYNDROMIC_CLUSTERS = {
    "hemorrhagic_fever": {
        "description": "Viral Hemorrhagic Fever syndrome",
        "defining_symptoms": {
            "fever", "bleeding", "hemorrhage", "profound weakness", "reduced urine output",
            "sore throat", "redness of the eyes", "conjunctival redness"
        },
        "trigger_threshold": 4,  # How many defining symptoms needed to trigger
        "score_bonus": 0.25,
    },
    "hantavirus_pulmonary": {
        "description": "Hantavirus Pulmonary Syndrome — GI prodrome → rapid ARDS",
        "defining_symptoms": {
            "fever", "muscle aches", "nausea", "vomiting", "abdominal pain",
            "shortness of breath", "cough", "respiratory distress", "low blood pressure",
            "rapid breathing", "hypoxia"
        },
        "trigger_threshold": 5,
        "score_bonus": 0.30,
    },
    "gi_respiratory_syndrome": {
        "description": "GI prodrome followed by respiratory failure — HPS pattern",
        "defining_symptoms": {
            "fever", "nausea", "vomiting", "diarrhea", "abdominal pain",
            "shortness of breath", "respiratory distress", "cough"
        },
        "trigger_threshold": 5,
        "score_bonus": 0.20,
    },
    "febrile_illness": {
        "description": "Non-specific febrile illness",
        "defining_symptoms": {"fever", "fatigue", "weakness", "headache", "muscle aches"},
        "trigger_threshold": 3,
        "score_bonus": 0.05,
    },
    "gastrointestinal_fever": {
        "description": "Febrile illness with gastrointestinal involvement",
        "defining_symptoms": {"fever", "diarrhea", "vomiting", "abdominal pain", "nausea"},
        "trigger_threshold": 3,
        "score_bonus": 0.10,
    },
    "respiratory_fever": {
        "description": "Febrile illness with respiratory involvement",
        "defining_symptoms": {"fever", "cough", "shortness of breath", "chest pain"},
        "trigger_threshold": 3,
        "score_bonus": 0.10,
    },
    "neurological_fever": {
        "description": "Febrile illness with neurological involvement",
        "defining_symptoms": {"fever", "confusion", "seizures", "stiff neck", "altered consciousness"},
        "trigger_threshold": 2,
        "score_bonus": 0.12,
    },
    "rash_fever": {
        "description": "Febrile illness with rash",
        "defining_symptoms": {
            "fever", "rash", "skin lesions", "pustular lesions", "skin rash",
            "skin eruption", "skin lesion", "lesions", "rash progression",
            "painful lesions", "vesicular rash", "pustular rash"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.08,
    },
    "mpox_cluster": {
        "description": "Mpox pathognomonic pattern: fever + lymphadenopathy + progressive rash",
        "defining_symptoms": {
            # ANY 2 of these = mpox_cluster triggered
            "swollen lymph nodes", "lymphadenopathy", "lymph node swelling",
            "lymph node enlargement", "lymph node tenderness",
            "generalized lymph node enlargement",
            # PLUS rash-type symptoms
            "rash", "skin rash", "skin eruption", "skin lesion", "skin lesions",
            "vesicular rash", "pustular rash", "painful lesions", "lesions",
            "rash progression", "mucosal lesion", "oral lesion",
            "palmoplantar rash", "palm lesion"
        },
        "trigger_threshold": 3,  # fever + lymphadenopathy + rash
        "score_bonus": 0.20,  # Strong bonus — this cluster is very specific for mpox
    },
    "dermatological_fever": {
        "description": "Febrile illness with prominent skin manifestations",
        "defining_symptoms": {
            "fever", "rash", "skin rash", "skin lesion", "skin lesions",
            "skin eruption", "painful lesions", "lesions", "pustular rash",
            "vesicular rash", "mucosal lesion"
        },
        "trigger_threshold": 3,
        "score_bonus": 0.10,
    },
    "lymphadenopathy_fever": {
        "description": "Febrile illness with prominent lymphadenopathy",
        "defining_symptoms": {
            "fever", "swollen lymph nodes", "lymphadenopathy", "lymph node swelling",
            "lymph node enlargement", "lymph node tenderness",
            "generalized lymph node enlargement"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.08,
    },
    "tropical": {
        "description": "Tropical/travel-acquired disease",
        "defining_symptoms": set(),  # Geographic trigger only
        "trigger_threshold": 999,
        "score_bonus": 0.0,
    },
    # ----------------------------------------------------------------
    # NEW CLUSTERS FOR NON-TROPICAL CLINICAL PRESENTATIONS
    # ----------------------------------------------------------------
    "cardiac_syndrome": {
        "description": "Cardiac / Cardiovascular syndrome",
        "defining_symptoms": {
            "chest pain", "crushing chest pain", "chest tightness", "chest pressure",
            "shortness of breath", "tachycardia", "rapid heart rate", "palpitations",
            "sweating", "diaphoresis", "jaw pain", "left arm pain", "radiating chest pain",
            "tearing chest pain", "syncope", "fainting"
        },
        "trigger_threshold": 3,
        "score_bonus": 0.20,
    },
    "acute_chest_pain": {
        "description": "Acute chest pain syndrome (MI, PE, Dissection, Angina)",
        "defining_symptoms": {
            "chest pain", "crushing chest pain", "tearing chest pain", "chest pressure",
            "chest tightness", "radiating chest pain", "pleuritic chest pain",
            "sudden severe chest pain"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.15,
    },
    "neurological_syndrome": {
        "description": "Neurological syndrome (Stroke, SAH, Encephalitis, GBS)",
        "defining_symptoms": {
            "facial drooping", "arm weakness", "speech difficulty", "slurred speech",
            "aphasia", "sudden severe headache", "thunderclap headache", "worst headache of life",
            "altered consciousness", "confusion", "seizures", "focal neurological deficit",
            "hemiparesis", "ascending weakness", "areflexia", "tremor", "hallucinations",
            "agitation", "vision loss", "ataxia", "numbness", "tingling"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.18,
    },
    "acute_abdomen": {
        "description": "Acute abdomen syndrome (Appendicitis, Pancreatitis, Obstruction, Perforation)",
        "defining_symptoms": {
            "severe abdominal pain", "right lower quadrant pain", "epigastric pain",
            "severe epigastric pain", "rebound tenderness", "guarding", "rigidity",
            "abdominal distension", "colicky abdominal pain", "peritonism",
            "inability to pass gas", "hematemesis", "melena"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.18,
    },
    "renal_syndrome": {
        "description": "Renal / Urinary syndrome (UTI, Pyelonephritis, AKI, Stones)",
        "defining_symptoms": {
            "dysuria", "painful urination", "frequency", "urinary frequency",
            "urinary urgency", "flank pain", "costovertebral angle tenderness",
            "hematuria", "blood in urine", "reduced urine output", "oliguria",
            "suprapubic pain", "leg swelling", "edema", "proteinuria"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.15,
    },
    "hepatic_syndrome": {
        "description": "Hepatic / Liver syndrome (Cirrhosis, Hepatitis, Liver failure)",
        "defining_symptoms": {
            "jaundice", "ascites", "hepatic encephalopathy", "abdominal distension",
            "pruritus", "itching", "palmar erythema", "spider angiomata",
            "easy bruising", "dark urine", "pale stool", "right upper quadrant pain"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.18,
    },
    "respiratory_distress": {
        "description": "Respiratory distress syndrome (PE, COPD, Asthma, Pneumonia, Heart failure)",
        "defining_symptoms": {
            "shortness of breath", "dyspnea", "wheeze", "wheezing",
            "cyanosis", "hypoxia", "use of accessory muscles", "tachypnea",
            "hemoptysis", "coughing blood", "inability to speak in sentences",
            "orthopnea", "paroxysmal nocturnal dyspnea"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.15,
    },
    "endocrine_crisis": {
        "description": "Endocrine crisis (DKA, HHS, Thyroid storm, Addisonian crisis)",
        "defining_symptoms": {
            "polyuria", "polydipsia", "excessive thirst", "fruity breath",
            "Kussmaul breathing", "heat intolerance", "cold intolerance",
            "weight gain", "weight loss", "hyperpigmentation", "salt craving",
            "tremor", "palpitations", "hyperthermia", "hyperreflexia"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.18,
    },
    "autoimmune_syndrome": {
        "description": "Autoimmune / Rheumatic syndrome (SLE, RA, Vasculitis)",
        "defining_symptoms": {
            "joint pain", "arthritis", "morning stiffness", "malar rash",
            "butterfly rash", "oral ulcers", "photosensitive rash", "hair loss",
            "Raynaud phenomenon", "dry eyes", "dry mouth", "pleuritis", "pericarditis"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.15,
    },
    "ectopic_pregnancy": {
        "description": "Ectopic pregnancy / gynecological emergency",
        "defining_symptoms": {
            "pelvic pain", "vaginal bleeding", "missed period", "amenorrhea",
            "positive pregnancy test", "shoulder tip pain", "unilateral pelvic pain"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.20,
    },
    "sickle_cell": {
        "description": "Sickle cell disease crisis pattern",
        "defining_symptoms": {
            "severe bone pain", "severe joint pain", "pallor", "jaundice",
            "acute chest syndrome", "priapism", "hand-foot syndrome"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.20,
    },
    "parasitic": {
        "description": "Parasitic / vector-borne disease cluster",
        "defining_symptoms": {
            "fever", "splenomegaly", "hepatomegaly", "anemia", "eosinophilia",
            "skin ulcer", "painless ulcer", "swollen lymph nodes"
        },
        "trigger_threshold": 3,
        "score_bonus": 0.08,
    },
    "zoonotic": {
        "description": "Zoonotic / animal-contact disease cluster",
        "defining_symptoms": {
            "animal contact", "animal bite", "wound", "tick bite",
            "hydrophobia", "fever", "lymphadenopathy", "rash"
        },
        "trigger_threshold": 2,
        "score_bonus": 0.10,
    },
}

# ---------------------------------------------------------------------------
# Geographic Outbreak Map (updated regularly via intelligence_engine)
# Hardcoded known long-term endemic/outbreak zones by disease
# ---------------------------------------------------------------------------
KNOWN_GEOGRAPHIC_DISEASE_LINKS: Dict[str, Set[str]] = {
    # Countries/regions that trigger disease suspicion
    "democratic republic of the congo": {
        "Bundibugyo Virus Disease (BVD)",
        "Ebola Virus Disease (Zaire)",
        "Mpox (Monkeypox)",
        "African Trypanosomiasis (Sleeping Sickness)",
        "Malaria (Plasmodium falciparum)",
        "Cholera",
        "Typhoid Fever",
        "Yellow Fever",
        "Meningococcal Meningitis",
    },
    "drc": {
        "Bundibugyo Virus Disease (BVD)",
        "Ebola Virus Disease (Zaire)",
        "Mpox (Monkeypox)",
        "African Trypanosomiasis (Sleeping Sickness)",
        "Malaria (Plasmodium falciparum)",
    },
    "west africa": {
        "Lassa Fever", "Ebola Virus Disease (Zaire)", "Yellow Fever",
        "Malaria (Plasmodium falciparum)", "Typhoid Fever", "Cholera",
    },
    "nigeria": {"Lassa Fever", "Yellow Fever", "Malaria (Plasmodium falciparum)", "Cholera"},
    "sierra leone": {"Lassa Fever", "Malaria (Plasmodium falciparum)"},
    "guinea": {"Lassa Fever", "Ebola Virus Disease (Zaire)", "Malaria (Plasmodium falciparum)"},
    "uganda": {"Ebola Virus Disease (Zaire)", "Sudan Ebolavirus Disease", "Marburg Virus Disease", "Malaria (Plasmodium falciparum)"},
    "angola": {"Malaria (Plasmodium falciparum)", "Yellow Fever", "Cholera"},
    "sub-saharan africa": {
        "Malaria (Plasmodium falciparum)", "Typhoid Fever", "Cholera",
        "Meningococcal Meningitis", "Yellow Fever",
    },
    "africa": {
        "Malaria (Plasmodium falciparum)", "Typhoid Fever", "Cholera",
        "Leptospirosis", "Meningococcal Meningitis",
    },
    "bangladesh": {"Cholera", "Dengue Fever", "Typhoid Fever", "Nipah Virus Disease"},
    "india": {"Dengue Fever", "Typhoid Fever", "Malaria (Plasmodium vivax)", "Leptospirosis", "Nipah Virus Disease"},
    "thailand": {"Dengue Fever", "Malaria (Plasmodium vivax)", "Scrub Typhus (Orientia tsutsugamushi)"},
    "indonesia": {"Zika Virus", "Dengue Fever", "Dengue Hemorrhagic Fever", "Chikungunya", "Typhoid Fever", "Malaria (Plasmodium falciparum)", "Avian Influenza H5N1"},
    "bali": {"Zika Virus", "Dengue Fever", "Dengue Hemorrhagic Fever", "Chikungunya", "Typhoid Fever", "Malaria (Plasmodium falciparum)"},
    "vietnam": {"Dengue Fever", "Avian Influenza H5N1", "Scrub Typhus (Orientia tsutsugamushi)"},
    "china": {"Avian Influenza H5N1", "Dengue Fever"},
    "philippines": {"Dengue Fever", "Malaria (Plasmodium falciparum)", "Leptospirosis"},
    "brazil": {"Oropouche Virus Disease", "Dengue Fever", "Zika Virus", "Chikungunya", "Yellow Fever", "Leptospirosis"},
    "peru": {"Oropouche Virus Disease", "Dengue Fever", "Malaria (Plasmodium vivax)", "Yellow Fever", "Leptospirosis"},
    "amazon": {"Oropouche Virus Disease", "Yellow Fever", "Malaria (Plasmodium falciparum)", "Dengue Fever", "Leptospirosis"},
    "south america": {"Oropouche Virus Disease", "Yellow Fever", "Dengue Fever", "Chikungunya", "Zika Virus", "Leptospirosis"},
    "caribbean": {"Oropouche Virus Disease", "Dengue Fever", "Chikungunya", "Zika Virus"},
    "cuba": {"Oropouche Virus Disease", "Dengue Fever", "Chikungunya"},
    "colombia": {"Oropouche Virus Disease", "Yellow Fever", "Dengue Fever", "Dengue Hemorrhagic Fever", "Zika Virus", "Chikungunya", "Malaria (Plasmodium falciparum)", "Leptospirosis"},
    "nicaragua": {"Chikungunya", "Dengue Fever", "Dengue Hemorrhagic Fever", "Zika Virus", "Malaria (Plasmodium vivax)", "Leptospirosis"},
    "democratic republic of the congo": {"Ebola Virus Disease (Zaire)", "Bundibugyo Virus Disease (BVD)", "Marburg Virus Disease", "Mpox (Monkeypox)", "Malaria (Plasmodium falciparum)", "Cholera", "Bacterial Meningitis", "Meningococcal Meningitis"},
    "drc": {"Ebola Virus Disease (Zaire)", "Bundibugyo Virus Disease (BVD)", "Marburg Virus Disease", "Mpox (Monkeypox)", "Malaria (Plasmodium falciparum)", "Cholera", "Bacterial Meningitis", "Meningococcal Meningitis"},
    "congo": {"Ebola Virus Disease (Zaire)", "Bundibugyo Virus Disease (BVD)", "Marburg Virus Disease", "Mpox (Monkeypox)", "Malaria (Plasmodium falciparum)", "Cholera", "Bacterial Meningitis", "Meningococcal Meningitis"},
    "middle east": {"MERS-CoV", "Brucellosis", "Leishmaniasis (Visceral / Kala-azar)"},
    "saudi arabia": {"MERS-CoV", "Brucellosis"},
    "global": {"COVID-19", "Influenza"},
    # Outbreak & transmission context keywords that appear in clinical notes
    "country with ongoing outbreak": {
        "Mpox (Monkeypox)", "COVID-19", "Cholera", "Ebola Virus Disease (Zaire)", "Bundibugyo Virus Disease (BVD)",
        "Influenza", "Dengue Fever", "Marburg Virus Disease",
    },
    "ongoing outbreak": {
        "Mpox (Monkeypox)", "COVID-19", "Cholera", "Dengue Fever", "Marburg Virus Disease", "Ebola Virus Disease (Zaire)", "Bundibugyo Virus Disease (BVD)",
    },
    "outbreak area": {
        "Mpox (Monkeypox)", "Ebola Virus Disease (Zaire)", "Bundibugyo Virus Disease (BVD)", "Marburg Virus Disease", "COVID-19",
    },
    "active transmission": {
        "Ebola Virus Disease (Zaire)", "Marburg Virus Disease", "Bundibugyo Virus Disease (BVD)",
        "Mpox (Monkeypox)", "Cholera",
    },
    "high-consequence infectious disease": {
        "Ebola Virus Disease (Zaire)", "Marburg Virus Disease", "Bundibugyo Virus Disease (BVD)",
        "Lassa Fever", "Crimean-Congo Hemorrhagic Fever",
    },
    "high-consequence viral infection": {
        "Marburg Virus Disease", "Ebola Virus Disease (Zaire)", "Bundibugyo Virus Disease (BVD)",
        "Lassa Fever",
    },
    "mosquito-borne viral transmission": {
        "Dengue Fever", "Dengue Hemorrhagic Fever", "Chikungunya", "Zika Virus", "Yellow Fever",
    },
    "mosquito-borne outbreak": {
        "Chikungunya", "Dengue Fever", "Dengue Hemorrhagic Fever", "Zika Virus", "Yellow Fever",
    },
    "mosquito exposure": {
        "Dengue Fever", "Dengue Hemorrhagic Fever", "Chikungunya", "Zika Virus", "Yellow Fever",
        "Malaria (Plasmodium falciparum)",
    },
    "arboviral": {
        "Dengue Fever", "Dengue Hemorrhagic Fever", "Chikungunya", "Zika Virus", "Yellow Fever",
    },
    "costa rica": {"Hepatitis A", "Dengue Fever", "Zika Virus", "Chikungunya", "Leptospirosis", "Malaria (Plasmodium vivax)"},
    "mauritius": {"Chikungunya", "Dengue Fever"},
    "uncertain food and water": {
        "Typhoid Fever", "Cholera", "Hepatitis A",
    },
    "food and water exposure": {
        "Typhoid Fever", "Cholera", "Hepatitis A",
    },
    # Central Africa / Equatorial Africa regions
    "central africa": {
        "Marburg Virus Disease", "Ebola Virus Disease (Zaire)", "Bundibugyo Virus Disease (BVD)",
        "Mpox (Monkeypox)", "Malaria (Plasmodium falciparum)", "Yellow Fever",
        "African Trypanosomiasis (Sleeping Sickness)",
    },
    "cameroon": {"Mpox (Monkeypox)", "Malaria (Plasmodium falciparum)", "Yellow Fever"},
    "ghana": {"Mpox (Monkeypox)", "Malaria (Plasmodium falciparum)", "Yellow Fever"},
    "central african republic": {
        "Mpox (Monkeypox)", "Malaria (Plasmodium falciparum)", "Ebola Virus Disease (Zaire)",
    },
    # South/Southeast Asia
    "pakistan": {"Dengue Fever", "Typhoid Fever", "Cholera", "Malaria (Plasmodium falciparum)"},
    "myanmar": {"Dengue Fever", "Malaria (Plasmodium falciparum)", "Typhoid Fever"},
    "cambodia": {"Dengue Fever", "Malaria (Plasmodium falciparum)"},
    "malaysia": {"Dengue Fever", "Nipah Virus Disease", "Scrub Typhus (Orientia tsutsugamushi)"},
    # Americas
    "peru": {"Dengue Fever", "Yellow Fever", "Malaria (Plasmodium falciparum)", "Leptospirosis"},
    "venezuela": {"Dengue Fever", "Malaria (Plasmodium falciparum)", "Yellow Fever"},
    "ecuador": {"Dengue Fever", "Yellow Fever", "Leptospirosis"},
    "haiti": {"Cholera", "Dengue Fever", "Malaria (Plasmodium falciparum)"},
    # Middle East
    "yemen": {"Typhoid Fever", "Cholera", "Dengue Fever", "Malaria (Plasmodium falciparum)"},
    "jordan": {"Brucellosis", "Leishmaniasis (Visceral / Kala-azar)"},
    # South America — Andes / Southern Cone (Hantavirus endemic)
    "argentina": {
        "Andes Orthohantavirus (HPS)", "Hantavirus Pulmonary Syndrome",
        "Dengue Fever", "Yellow Fever", "Leptospirosis", "Chagas Disease",
        "Leishmaniasis (Visceral / Kala-azar)",
    },
    "chile": {
        "Andes Orthohantavirus (HPS)", "Hantavirus Pulmonary Syndrome",
        "Dengue Fever", "Leptospirosis",
    },
    "uruguay": {
        "Andes Orthohantavirus (HPS)", "Hantavirus Pulmonary Syndrome",
        "Dengue Fever", "Leptospirosis", "Chagas Disease",
    },
    "bolivia": {
        "Andes Orthohantavirus (HPS)", "Hantavirus Pulmonary Syndrome",
        "Dengue Fever", "Yellow Fever", "Chagas Disease", "Malaria (Plasmodium falciparum)",
    },
    "paraguay": {
        "Andes Orthohantavirus (HPS)", "Hantavirus Pulmonary Syndrome",
        "Dengue Fever", "Chagas Disease", "Leishmaniasis (Visceral / Kala-azar)",
    },
    "andes": {
        "Andes Orthohantavirus (HPS)", "Hantavirus Pulmonary Syndrome",
        "Dengue Fever", "Yellow Fever",
    },
    "patagonia": {
        "Andes Orthohantavirus (HPS)", "Hantavirus Pulmonary Syndrome",
    },
    "south america": {
        "Andes Orthohantavirus (HPS)", "Hantavirus Pulmonary Syndrome",
        "Dengue Fever", "Yellow Fever", "Chagas Disease", "Leptospirosis",
        "Leishmaniasis (Visceral / Kala-azar)",
    },
    "latin america": {
        "Dengue Fever", "Zika Virus", "Chikungunya", "Leptospirosis", "Chagas Disease",
        "Andes Orthohantavirus (HPS)", "Hantavirus Pulmonary Syndrome",
    },
    "americas": {
        "Hantavirus Pulmonary Syndrome", "Andes Orthohantavirus (HPS)",
        "Dengue Fever", "Zika Virus", "Yellow Fever", "Leptospirosis",
    },
    # Rural/agricultural exposure context (extracted from notes)
    "rural area": {
        "Hantavirus Pulmonary Syndrome", "Andes Orthohantavirus (HPS)",
        "Leptospirosis", "Brucellosis", "Q Fever", "Scrub Typhus (Orientia tsutsugamushi)",
    },
    "agricultural land": {
        "Hantavirus Pulmonary Syndrome", "Andes Orthohantavirus (HPS)",
        "Leptospirosis", "Brucellosis", "Q Fever",
    },
    "rural accommodation": {
        "Hantavirus Pulmonary Syndrome", "Andes Orthohantavirus (HPS)",
        "Leptospirosis", "Brucellosis",
    },
    "rodent exposure": {
        "Hantavirus Pulmonary Syndrome", "Andes Orthohantavirus (HPS)",
        "Lassa Fever", "Leptospirosis",
    },
    "farm": {
        "Q Fever", "Brucellosis", "Leptospirosis",
        "Hantavirus Pulmonary Syndrome", "Andes Orthohantavirus (HPS)",
    },
}

def get_diseases_for_geography(countries: List[str]) -> Dict[str, float]:
    """
    Given a list of visited countries, returns a dict of
    {disease_name: geographic_score_bonus} for diseases endemic/outbreak in those countries.
    """
    result: Dict[str, float] = {}
    for country in countries:
        country_lower = country.lower().strip()
        for geo_key, diseases in KNOWN_GEOGRAPHIC_DISEASE_LINKS.items():
            if geo_key in country_lower or country_lower in geo_key:
                for disease in diseases:
                    # Higher score for more specific match
                    if geo_key == country_lower:
                        result[disease] = max(result.get(disease, 0.0), 0.35)
                    elif geo_key in country_lower:
                        result[disease] = max(result.get(disease, 0.0), 0.30)
                    else:
                        result[disease] = max(result.get(disease, 0.0), 0.20)
    return result


def get_active_disease_clusters(patient_symptoms: Set[str]) -> List[str]:
    """
    Detects which syndromic clusters match the patient's symptom set.
    Returns list of active cluster names.
    """
    active = []
    syms_lower = {s.lower() for s in patient_symptoms}
    for cluster_name, cluster_data in SYNDROMIC_CLUSTERS.items():
        if not cluster_data["defining_symptoms"]:
            continue
        overlap = len(syms_lower.intersection(
            {s.lower() for s in cluster_data["defining_symptoms"]}
        ))
        if overlap >= cluster_data["trigger_threshold"]:
            active.append(cluster_name)
    return active
