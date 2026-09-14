import structlog
from typing import List
from app.schemas.polypharmacy import PolypharmacyRequest, PolypharmacyResponse, InteractionDetail
from app.services.llm_service import llm_service

log = structlog.get_logger(__name__)

class PolypharmacySimulator:
    """Service to evaluate complex drug-drug interactions using LLM."""

    async def simulate(self, proposed_meds: List[str], current_meds: List[str]) -> PolypharmacyResponse:
        system_prompt = """You are an Expert Clinical Pharmacologist and Pharmacogenomics AI.
Your task is to evaluate the safety and potential interactions of a polypharmacy regimen.
You are given a list of the patient's CURRENT medications and a list of PROPOSED medications to be added.

Analyze for:
1. Drug-Drug Interactions (Pharmacokinetic: CYP450 enzyme induction/inhibition).
2. Pharmacodynamic interactions (e.g., additive QT prolongation, serotonin syndrome risk, additive CNS depression).
3. Contraindications.

## Output Requirements
Return ONLY valid JSON matching this exact schema:
{
  "interactions": [
    {
      "severity": "CRITICAL" | "WARNING" | "MINOR" | "SAFE",
      "drugs_involved": ["Drug A", "Drug B"],
      "mechanism": "string (e.g., CYP3A4 inhibition)",
      "clinical_effect": "string",
      "recommendation": "string"
    }
  ],
  "summary_assessment": "string (Overall safety profile and main concerns)",
  "is_safe": boolean (True if no CRITICAL interactions)
}
If there are no interactions, return an empty interactions array and is_safe = true.
"""

        user_prompt = f"""
CURRENT MEDICATIONS: {', '.join(current_meds) if current_meds else 'None'}
PROPOSED MEDICATIONS: {', '.join(proposed_meds) if proposed_meds else 'None'}

Generate the interaction report as JSON.
"""

        try:
            log.info("simulating_polypharmacy", proposed=proposed_meds, current=current_meds)
            data = await llm_service.generate_json(user_prompt, system=system_prompt)
            
            interactions = []
            for item in data.get("interactions", []):
                interactions.append(InteractionDetail(**item))
                
            return PolypharmacyResponse(
                interactions=interactions,
                summary_assessment=data.get("summary_assessment", "Safety analysis completed."),
                is_safe=data.get("is_safe", True)
            )
        except Exception as e:
            log.error("polypharmacy_simulation_failed", error=str(e))
            # Fallback to safe response or raise error
            raise ValueError(f"Failed to generate simulation: {str(e)}")

polypharmacy_simulator = PolypharmacySimulator()
