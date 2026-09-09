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
            
        system_prompt = """You are a medical data extraction AI.
Extract all clinical findings (symptoms, conditions, medications, allergies, vitals) from the text.
Return ONLY valid JSON matching this schema exactly:
{
  "findings": [
    {
      "concept": "string (SYMPTOM, CONDITION, MEDICATION, ALLERGY, VITALS)",
      "value": "string (the exact words from text)",
      "negated": boolean,
      "temporality": "string (current, past)"
    }
  ]
}
"""
        user_prompt = f"Text:\n{text}\n\nExtract findings as JSON."
        
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
                
            return findings
        except Exception as e:
            log.error("llm_extraction_failed", error=str(e))
            return []

extractor = ClinicalExtractor()
