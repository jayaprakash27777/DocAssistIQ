from app.schemas.medication import MedicationResponse, MedicationSuggestion
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rag_service import retrieve_medical_context
from app.services.llm_service import llm_service
import json
import structlog

log = structlog.get_logger(__name__)

class BaselineMedicationProvider:
    """Fallback fallback logic for medications."""
    KB = {
        "Asthma": [
            MedicationSuggestion(
                generic_name="Albuterol",
                indication="Bronchospasm",
                formulation="Inhaler",
                route="Inhalation",
                standard_reference_dosing="90 mcg/actuation, 2 puffs every 4-6 hours PRN",
                contraindications=["Hypersensitivity"],
                interactions=["Beta-blockers"],
                allergy_considerations="None specific",
                renal_considerations="No adjustment",
                hepatic_considerations="No adjustment",
                pregnancy_lactation_considerations="Use with caution",
                age_considerations="Pediatric dosing differs",
                monitoring_reference_information="Heart rate, potassium",
                source_evidence="Standard Baseline DB",
                safety_decision=None
            )
        ],
        "Hypertension": [
            MedicationSuggestion(
                generic_name="Lisinopril",
                indication="Hypertension",
                formulation="Tablet",
                route="Oral",
                standard_reference_dosing="10-40 mg daily",
                contraindications=["History of angioedema", "Pregnancy"],
                interactions=["Potassium supplements", "NSAIDs"],
                allergy_considerations="ACE inhibitor allergy",
                renal_considerations="Dose adjustment required in renal impairment",
                hepatic_considerations="No adjustment",
                pregnancy_lactation_considerations="Contraindicated in pregnancy",
                age_considerations="Start low in elderly",
                monitoring_reference_information="BP, BUN, Creatinine, Potassium",
                source_evidence="Standard Baseline DB",
                safety_decision=None
            )
        ],
        "COVID-19": [
            MedicationSuggestion(
                generic_name="Nirmatrelvir/Ritonavir",
                indication="Mild-to-moderate COVID-19",
                formulation="Tablet",
                route="Oral",
                standard_reference_dosing="300 mg/100 mg twice daily for 5 days",
                contraindications=["Severe renal impairment", "Severe hepatic impairment"],
                interactions=["CYP3A4 substrates (many significant drug interactions)"],
                allergy_considerations="None specific",
                renal_considerations="Dose reduction in moderate renal impairment",
                hepatic_considerations="Not recommended in severe impairment",
                pregnancy_lactation_considerations="Use if benefits outweigh risks",
                age_considerations="Not for <12 years",
                monitoring_reference_information="Drug interactions",
                source_evidence="Standard Baseline DB",
                safety_decision=None
            )
        ]
    }
    
    async def get_medications(self, disease_name: str) -> MedicationResponse:
        for key in self.KB:
            if key.lower() in disease_name.lower():
                return MedicationResponse(disease=disease_name, suggestions=self.KB[key])
        
        # Generic fallback
        return MedicationResponse(disease=disease_name, suggestions=[
            MedicationSuggestion(
                generic_name="Acetaminophen",
                indication="General pain/fever relief",
                formulation="Tablet",
                route="Oral",
                standard_reference_dosing="325-650 mg every 4-6 hours PRN",
                contraindications=["Severe hepatic impairment"],
                interactions=["Alcohol", "Warfarin"],
                allergy_considerations="None specific",
                renal_considerations="No adjustment",
                hepatic_considerations="Caution in liver disease",
                pregnancy_lactation_considerations="Generally safe",
                age_considerations="Pediatric dosing differs based on weight",
                monitoring_reference_information="LFTs if high dose",
                source_evidence="Standard Baseline DB",
                safety_decision=None
            )
        ])

class MedicationProvider:
    """
    Provides clinician-facing reference intelligence for medications based on disease (Phase 45).
    This serves strictly as reference intelligence and NOT as an automated order system.
    """

    async def get_medications(self, db: AsyncSession, disease_name: str) -> MedicationResponse:
        rag_context = await retrieve_medical_context(db, f"{disease_name} treatments", top_k=3)
        
        system_prompt = f"""You are an Expert Clinical Pharmacologist AI.
Your task is to recommend 2 to 4 safe, standard-of-care medications for the disease: '{disease_name}'.
You MUST ground your response in the retrieved FDA data (if any). Do not hallucinate dosing. 
If standard dosing varies, state typical ranges and explicitly mention 'Requires clinical correlation'.

## Retrieved FDA Context:
{rag_context}

## Output Requirements
Return ONLY valid JSON matching this exact schema:
{{
  "medications": [
    {{
      "generic_name": "string (e.g., Albuterol)",
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
      "source_evidence": "string (put 'FDA Label' here if found in context, else 'Standard Knowledge')"
    }}
  ]
}}"""
        
        try:
            user_prompt = "Generate medication suggestions based on the context. Return ONLY the JSON."
            data = await llm_service.generate_json(user_prompt, system=system_prompt)
            suggestions = []
            for item in data.get("medications", []):
                suggestions.append(MedicationSuggestion(**item, safety_decision=None))  # type: ignore
            if not suggestions:
                raise ValueError("No medications generated in JSON")
            return MedicationResponse(disease=disease_name, suggestions=suggestions)
        except Exception as e:
            log.error("llm_medication_failed", error=str(e), disease=disease_name)
            fallback = BaselineMedicationProvider()
            return await fallback.get_medications(disease_name)

medication_provider = MedicationProvider()
