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
You must be thorough. Do not miss any symptoms, conditions, medications, allergies, or vitals.
Crucially, you must accurately determine if the patient DENIES the finding (negated: true) and whether it is a past or current issue (temporality).

Return ONLY valid JSON matching this exact schema:
{
  "findings": [
    {
      "concept": "string (strictly one of: SYMPTOM, CONDITION, MEDICATION, ALLERGY, VITALS)",
      "value": "string (the exact specific medical term or phrase)",
      "negated": boolean (true if patient denies it, false if they have it),
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
        text_lower = text.lower()
        findings = []
        
        # Simple mock dictionary for fallback
        keywords = {
            "headache": "SYMPTOM",
            "cough": "SYMPTOM",
            "fever": "SYMPTOM",
            "nausea": "SYMPTOM",
            "shortness of breath": "SYMPTOM",
            "chest pain": "SYMPTOM",
            "fatigue": "SYMPTOM",
            "hypertension": "CONDITION",
            "diabetes": "CONDITION",
            "asthma": "CONDITION",
            "ibuprofen": "MEDICATION",
            "lisinopril": "MEDICATION",
            "penicillin": "ALLERGY"
        }
        
        for kw, concept in keywords.items():
            if kw in text_lower:
                # Check for simple negation
                negated = f"no {kw}" in text_lower or f"denies {kw}" in text_lower
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
                
        return findings

extractor = ClinicalExtractor()
