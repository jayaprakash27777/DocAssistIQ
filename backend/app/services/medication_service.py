from app.schemas.medication import MedicationResponse, MedicationSuggestion

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rag_service import retrieve_medical_context
from app.services.llm_service import llm_service
import json

class MedicationProvider:
    """
    Provides clinician-facing reference intelligence for medications based on disease (Phase 45).
    This serves strictly as reference intelligence and NOT as an automated order system.
    """

    async def get_medications(self, db: AsyncSession, disease_name: str) -> MedicationResponse:
        rag_context = await retrieve_medical_context(db, f"{disease_name} treatments", top_k=3)
        
        system_prompt = f"""You are a clinical pharmacologist AI.
You must recommend safe medications for the disease: '{disease_name}'.
You MUST ground your response in the following retrieved FDA data. Do not hallucinate dosing.

FDA Context:
{rag_context}

Return ONLY valid JSON matching this exact schema:
{{
  "medications": [
    {{
      "generic_name": "string",
      "indication": "string",
      "formulation": "string",
      "route": "string",
      "standard_reference_dosing": "string",
      "contraindications": ["string"],
      "interactions": ["string"],
      "allergy_considerations": "string",
      "renal_considerations": "string",
      "hepatic_considerations": "string",
      "pregnancy_lactation_considerations": "string",
      "age_considerations": "string",
      "monitoring_reference_information": "string",
      "source_evidence": "string (put 'FDA Label' here if found in context)"
    }}
  ]
}}"""
        
        try:
            from app.infrastructure.ai.interfaces import GenerationRequest
            req = GenerationRequest(prompt="Generate medication suggestions based on the context.", system_prompt=system_prompt)
            result = await llm_service.generate_json(req)
            data = json.loads(result.text)
            suggestions = []
            for item in data.get("medications", []):
                suggestions.append(MedicationSuggestion(**item))
            return MedicationResponse(disease=disease_name, suggestions=suggestions)
        except Exception as e:
            import structlog
            structlog.get_logger(__name__).error("llm_medication_failed", error=str(e))
            return MedicationResponse(disease=disease_name, suggestions=[])

medication_provider = MedicationProvider()
