"""DocAssistIQ — Concept Normalizer (Phase 29).

Maps raw clinical text to verified canonical concepts.
Refuses to map ambiguous terms (e.g., 'MS').
"""

import structlog
from typing import Optional, Tuple

log = structlog.get_logger(__name__)

# Verified mappings dictionary
# In a full production system, this would be backed by UMLS/SNOMED API
# Here it is a deterministic JSON-like structure
VERIFIED_MAPPINGS = {
    # Conditions
    "htn": "hypertension",
    "high blood pressure": "hypertension",
    "t2dm": "type 2 diabetes mellitus",
    "type 2 diabetes": "type 2 diabetes mellitus",
    "copd": "chronic obstructive pulmonary disease",
    "asthma": "asthma",
    
    # Symptoms
    "sob": "shortness of breath",
    "breathless": "shortness of breath",
    "dyspnea": "shortness of breath",
    "ha": "headache",
    "head ache": "headache",
    "cp": "chest pain",
    "chest tightness": "chest pain",
    "n/v": "nausea and vomiting",
    "nausea": "nausea",
    "fatigue": "fatigue",
    "tiredness": "fatigue",
    "fever": "fever",
    "high temp": "fever",
    "high temperature": "fever",
    
    # Medications
    "asa": "aspirin",
    "tylenol": "acetaminophen",
    "paracetamol": "acetaminophen",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
}

# Ambiguous mappings that must be explicitly rejected
AMBIGUOUS_TERMS = {
    "ms": ["multiple sclerosis", "mitral stenosis", "morphine sulfate"],
    "pe": ["pulmonary embolism", "physical examination"],
    "ca": ["cancer", "calcium", "cardiac arrest"],
    "hr": ["heart rate", "hour"],
    "mi": ["myocardial infarction", "mitral incompetence"]
}

class ConceptNormalizer:
    
    def __init__(self):
        self.source = "internal_dict"
        self.confidence = 0.95

    def normalize(self, raw_value: str) -> Tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Attempts to normalize a raw clinical string.
        Returns: (canonical_concept, mapping_source, mapping_confidence)
        Returns (None, None, None) if ambiguous or unknown.
        """
        if not raw_value:
            return None, None, None
            
        term = raw_value.strip().lower()
        
        # 1. Guard: Explicit rejection of ambiguous terms
        if term in AMBIGUOUS_TERMS:
            log.info("concept_normalizer_rejected_ambiguous", raw_term=term)
            return None, None, None
            
        # 2. Check verified mappings
        if term in VERIFIED_MAPPINGS:
            canonical = VERIFIED_MAPPINGS[term]
            return canonical, self.source, self.confidence
            
        # 3. Pass-through for terms already in canonical form
        canonical_values = set(VERIFIED_MAPPINGS.values())
        if term in canonical_values:
            return term, self.source, self.confidence
            
        return None, None, None

normalizer = ConceptNormalizer()
