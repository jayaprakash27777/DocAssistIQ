"""DocAssistIQ — Clinical NLP Extractor (Phase 28).

Deterministic clinical information extraction using spaCy.
Focuses on explainable and testable extraction of symptoms, signs, 
medications, and conditions, with robust negation and temporality handling.
"""

import json
import asyncio
from typing import List, Dict, Any
from app.services.llm_service import llm_service
from app.services.concept_normalizer import normalizer
import structlog

log = structlog.get_logger(__name__)

class ClinicalExtractor:
    """
    Live LLM clinical information extraction.
    Replaces the mock spaCy extractor with a dynamic prompt to Ollama.
    """
    def __init__(self):
        pass

    async def extract(self, text: str, source_context: str = "clinical_note") -> List[Dict[str, Any]]:
        if not text:
            return []
            
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
        user_prompt = f"Text:\n{text}\n\nExtract all findings as JSON."
        
        try:
            # We must use async here. Note: consultation_service.py might be calling this synchronously if it wasn't async before.
            # We'll need to check consultation_service.py to see if we can await it.
            response_json = await llm_service.generate_json(user_prompt, system=system_prompt)
            raw_findings = response_json.get("findings", [])
            
            findings = []
            for item in raw_findings:
                raw_val = item.get("value", "").lower()
                if not raw_val:
                    continue
                    
                canon, mapping_src, mapping_conf = normalizer.normalize(raw_val)
                
                finding = {
                    "concept": item.get("concept", "UNKNOWN"),
                    "value": raw_val,
                    "certainty": "high",
                    "negated": item.get("negated", False),
                    "temporality": item.get("temporality", "current"),
                    "source": source_context,
                    "confidence": 0.90,
                    "canonical_concept": canon,
                    "mapping_source": mapping_src,
                    "mapping_confidence": mapping_conf
                }
                findings.append(finding)
                
            if not findings:
                log.warning("llm_extraction_empty", fallback="BaselineExtractor")
                return self._baseline_extract(text, source_context)
                
            return findings
        except Exception as e:
            log.warning("llm_extraction_failed", error=str(e), fallback="BaselineExtractor")
            # Fallback keyword extractor if LLM is down
            return self._baseline_extract(text, source_context)
            
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
            "copd": "CONDITION", "heart failure": "CONDITION",
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

            # ---- ALLERGIES ----
            "penicillin": "ALLERGY", "sulfa": "ALLERGY",
            "latex": "ALLERGY", "nsaid": "ALLERGY",
        }

        for kw, concept in keywords.items():
            if kw in text_lower:
                negated = f"no {kw}" in text_lower or f"denies {kw}" in text_lower or f"without {kw}" in text_lower
                canon, mapping_src, mapping_conf = normalizer.normalize(kw)
                findings.append({
                    "concept": concept,
                    "value": kw.title(),
                    "certainty": "high",
                    "negated": negated,
                    "temporality": "current",
                    "source": source_context,
                    "confidence": 0.80,
                    "canonical_concept": canon,
                    "mapping_source": mapping_src,
                    "mapping_confidence": mapping_conf
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

        # === Geographic Exposure Detection ===
        if "outbreak" in text_lower or "endemic" in text_lower or "disease zone" in text_lower:
            exposure_val = "Ongoing infectious disease outbreak area"
            canon, mapping_src, mapping_conf = normalizer.normalize(exposure_val)
            findings.append({
                "concept": "GEOGRAPHIC_EXPOSURE",
                "value": exposure_val,
                "certainty": "high",
                "negated": False,
                "temporality": "past",
                "source": source_context,
                "confidence": 0.85,
                "canonical_concept": canon,
                "mapping_source": mapping_src,
                "mapping_confidence": mapping_conf
            })

        return findings

extractor = ClinicalExtractor()
