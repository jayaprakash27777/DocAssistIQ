from abc import ABC, abstractmethod
from typing import List

from app.schemas.representation import ClinicalRepresentationResponse
from app.schemas.diagnosis import DifferentialDiagnosisResponse, DifferentialDiagnosisItem

from sqlalchemy.ext.asyncio import AsyncSession

class DiagnosisProvider(ABC):
    """Stable interface for diagnosis providers (Phase 34)."""
    @abstractmethod
    async def generate_differential(self, db: AsyncSession, representation: ClinicalRepresentationResponse) -> DifferentialDiagnosisResponse:
        pass

import json
from app.services.llm_service import llm_service

class OllamaDiagnosisProvider(DiagnosisProvider):
    """
    Live LLM differential diagnosis engine.
    Uses the local Ollama LLM to generate differential diagnosis based on clinical representation.
    """
    async def generate_differential(self, db: AsyncSession, representation: ClinicalRepresentationResponse) -> DifferentialDiagnosisResponse:
        missing_critical_info = []
        
        if not representation.symptoms:
            missing_critical_info.append("At least one reported symptom is required.")
            
        if not representation.duration:
            missing_critical_info.append("Duration of symptoms is missing.")
            
        if not representation.severity:
            missing_critical_info.append("Severity of symptoms is missing.")
            
        if not representation.symptoms:
            return DifferentialDiagnosisResponse(
                consultation_id=str(representation.consultation_id),
                status="INSUFFICIENT_INFO",
                message="Insufficient clinical information to generate a safe and meaningful differential diagnosis.",
                missing_critical_info=missing_critical_info,
                provider_metadata={
                    "provider": "OllamaDiagnosisProvider",
                    "version": "1.0"
                },
                top_candidates=[]
            )

        # Prepare prompt
        symptoms_str = ", ".join([f"{item.value} ({item.status})" for item in representation.symptoms])
        duration_str = ", ".join([item.value for item in representation.duration]) if representation.duration else "Unknown"
        severity_str = ", ".join([item.value for item in representation.severity]) if representation.severity else "Unknown"
        history_str = ", ".join([item.value for item in representation.history]) if representation.history else "None"
        vitals_str = ", ".join([item.value for item in representation.vitals]) if representation.vitals else "None"
        travel_history_str = ", ".join([item.value for item in representation.travel_history]) if getattr(representation, "travel_history", None) else "None"

        # PHASE 2: Retrieve RAG Context
        from app.services.rag_service import retrieve_medical_context
        
        # Build query from symptoms and travel history
        rag_query = symptoms_str
        
        live_context = ""
        if travel_history_str != "None":
            rag_query += f" travel to {travel_history_str} endemic disease outbreak"
            # Real-time fetch for CDC Travel Health Notices (Geo-Spatial Aware)
            try:
                import httpx
                import xml.etree.ElementTree as ET
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get("https://wwwnc.cdc.gov/travel/rss/notices.xml")
                    if response.status_code == 200:
                        root = ET.fromstring(response.text)
                        live_notices = []
                        for item in root.findall(".//item"):
                            title = item.find("title").text if item.find("title") is not None else ""
                            desc = item.find("description").text if item.find("description") is not None else ""
                            
                            # Basic geo-spatial pre-filtering (LLM will do the deep semantic matching)
                            # We grab all notices but format them clearly for the LLM's incubation engine.
                            live_notices.append(f"- {title}: {desc}")
                            
                        if live_notices:
                            live_context = "LIVE CDC GLOBAL OUTBREAK DATABASE:\n" + "\n".join(live_notices[:10]) + "\n\n"
            except Exception as e:
                import structlog
                structlog.get_logger(__name__).error("live_cdc_fetch_failed", error=str(e))
            
        rag_context = await retrieve_medical_context(db, rag_query, top_k=3)
        if live_context:
            rag_context = live_context + "STATIC KNOWLEDGE BASE CONTEXT:\n" + rag_context
            
        system_prompt = f"""You are a Senior Clinical Diagnostician AI and Geo-Spatial Epidemiologist.
Your task is to analyze the provided clinical representation and return a JSON list of the top 3-5 differential diagnoses.
You must be precise, medical, and evidence-based. Do NOT invent or hallucinate diseases.

## Instructions
1. Analyze the symptoms, duration, severity, vitals, and travel history.
2. Formulate 3-5 highly likely differential diagnoses.
3. For each diagnosis, explicitly list which provided findings support it, which expected findings are missing, and which findings contradict it.
4. Base your confidence score (0.0 to 1.0) strictly on clinical overlap. The most likely diagnosis should typically have a score > 0.8.
5. You MUST consider the following retrieved knowledge context (e.g. FDA drug side effects, WHO disease outbreaks).
6. **ULTRA-ADVANCED GEO-SPATIAL & INCUBATION PIPELINE**: If the patient has travel history, you MUST act as a geographic engine.
   - Match their specific countries visited against the LIVE CDC GLOBAL OUTBREAK DATABASE provided below (e.g., if they visited Brazil, you MUST map that to South America notices).
   - If there is a geographic match, mathematically cross-reference the patient's "days since return" (duration) against the standard incubation period of the endemic pathogens. If the incubation period does not fit, lower the score!

## Retrieved Context:
{rag_context}

## Output Format
Return ONLY valid JSON matching this exact schema (no markdown, no preamble):
{{
  "candidates": [
    {{
      "disease": "string (Specific medical name)",
      "score": 0.0 to 1.0,
      "supporting_findings": ["string", "string"],
      "missing_expected_findings": ["string", "string"],
      "contradicting_information": ["string"],
      "uncertainty": "Low" | "Moderate" | "High",
      "explanation_reference": "string (1-2 sentences of clinical rationale)"
    }}
  ]
}}
"""
        user_prompt = f"""Clinical Representation:
- Symptoms: {symptoms_str}
- Duration: {duration_str}
- Severity: {severity_str}
- Past Medical History: {history_str}
- Travel History: {travel_history_str}
- Vitals: {vitals_str}

Analyze this data and return the JSON.
"""
        
        try:
            response_json = await llm_service.generate_json(user_prompt, system=system_prompt)
            candidates_data = response_json.get("candidates", [])
            
            top_candidates = []
            for c in candidates_data:
                # Apply uncertainty penalty for missing severity or duration
                uncertainty = c.get("uncertainty", "Moderate")
                score = float(c.get("score", 0.0))
                explanation = c.get("explanation_reference", "")
                
                if missing_critical_info:
                    explanation += " (Note: Confidence may be impacted by missing clinical context like duration or severity.)"
                
                top_candidates.append(DifferentialDiagnosisItem(  # type: ignore
                    disease=c.get("disease", "Unknown"),
                    score=round(score, 3),
                    supporting_findings=c.get("supporting_findings", []),
                    missing_expected_findings=c.get("missing_expected_findings", []),
                    contradicting_information=c.get("contradicting_information", []),
                    uncertainty=uncertainty,
                    explanation_reference=explanation
                ))
            
            top_candidates.sort(key=lambda x: x.score, reverse=True)
            
            return DifferentialDiagnosisResponse(
                consultation_id=str(representation.consultation_id),
                status="SUCCESS",
                message=None,
                missing_critical_info=missing_critical_info,
                provider_metadata={
                    "provider": "OllamaDiagnosisProvider",
                    "version": "1.0",
                    "model": llm_service.default_model
                },
                top_candidates=top_candidates[:5]
            )
            
        except Exception as e:
            # Fallback to Baseline if LLM fails
            from structlog import get_logger
            get_logger(__name__).error("llm_diagnosis_failed", error=str(e))
            fallback_provider = BaselineDiagnosisProvider()
            return await fallback_provider.generate_differential(db, representation)



class BaselineDiagnosisProvider(DiagnosisProvider):
    """
    Transparent, baseline differential diagnosis engine (Phase 33).
    Uses a simple weighted overlap algorithm against an internal Knowledge Matrix.
    """
    
    KB = {
        "Asthma": ["cough", "shortness of breath", "wheezing", "chest tightness"],
        "Hypertension": ["headache", "shortness of breath", "nosebleed", "dizziness"],
        "Diabetes Type 2": ["increased thirst", "frequent urination", "increased hunger", "fatigue", "blurred vision"],
        "COPD": ["shortness of breath", "wheezing", "chest tightness", "chronic cough"],
        "Pneumonia": ["cough", "fever", "chills", "shortness of breath", "chest pain"],
        "COVID-19": ["fever", "cough", "fatigue", "loss of taste", "loss of smell", "shortness of breath"],
        "Pulmonary Embolism": ["shortness of breath", "chest pain", "cough", "rapid heart rate"],
        "Migraine": ["headache", "nausea", "sensitivity to light", "sensitivity to sound"],
        "Gastroenteritis": ["nausea", "vomiting", "diarrhea", "abdominal pain", "fever"],
        "Influenza": ["fever", "chills", "muscle aches", "cough", "congestion", "runny nose", "headache", "fatigue"]
    }

    async def generate_differential(self, db: AsyncSession, representation: ClinicalRepresentationResponse) -> DifferentialDiagnosisResponse:
        missing_critical_info = []
        
        if not representation.symptoms:
            missing_critical_info.append("At least one reported symptom is required.")
            
        if not representation.duration:
            missing_critical_info.append("Duration of symptoms is missing.")
            
        if not representation.severity:
            missing_critical_info.append("Severity of symptoms is missing.")
            
        if not representation.symptoms:
            # We absolutely cannot proceed without symptoms
            return DifferentialDiagnosisResponse(
                consultation_id=str(representation.consultation_id),
                status="INSUFFICIENT_INFO",
                message="Insufficient clinical information to generate a safe and meaningful differential diagnosis.",
                missing_critical_info=missing_critical_info,
                provider_metadata={
                    "provider": "BaselineDiagnosisProvider",
                    "version": "1.0"
                },
                top_candidates=[]
            )

        rep_symptoms = set(item.value.lower() for item in representation.symptoms)
        rep_negations = set(item.value.lower() for item in representation.negations)
        
        candidates = []
        
        for disease, expected_symptoms in self.KB.items():
            expected_set = set(s.lower() for s in expected_symptoms)
            
            supporting = list(expected_set.intersection(rep_symptoms))
            missing = list(expected_set - rep_symptoms - rep_negations)
            contradictions = list(expected_set.intersection(rep_negations))
            
            union_len = len(expected_set.union(rep_symptoms))
            if union_len == 0:
                score = 0.0
            else:
                score = len(supporting) / union_len
            
            score -= (len(contradictions) * 0.2)
            
            if score > 0 or len(supporting) > 0:
                explanation = f"Matched {len(supporting)} findings. "
                if contradictions:
                    explanation += f"Penalized for {len(contradictions)} contradictions. "
                
                # Apply uncertainty penalty for missing severity or duration
                uncertainty = "High" if len(supporting) <= 1 else "Moderate" if score < 0.5 else "Low"
                if missing_critical_info:
                    score *= 0.8  # Penalty for missing core info
                    uncertainty = "High"
                    explanation += " Confidence reduced due to missing clinical context (duration/severity)."
                
                candidates.append(DifferentialDiagnosisItem(  # type: ignore
                    disease=disease,
                    score=round(score, 3),
                    supporting_findings=supporting,
                    missing_expected_findings=missing,
                    contradicting_information=contradictions,
                    uncertainty=uncertainty,
                    explanation_reference=explanation.strip()
                ))
        
        candidates.sort(key=lambda x: x.score, reverse=True)
        top_5 = candidates[:5]
        
        return DifferentialDiagnosisResponse(
            consultation_id=str(representation.consultation_id),
            status="SUCCESS",
            message=None,
            missing_critical_info=missing_critical_info,
            provider_metadata={
                "provider": "BaselineDiagnosisProvider",
                "version": "1.0",
                "algorithm": "Jaccard-like overlap with contradiction penalty",
                "kb_size": len(self.KB)
            },
            top_candidates=top_5
        )
