import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio, time, json
from app.infrastructure.ai.factory import get_generation_provider
from app.infrastructure.ai.interfaces import GenerationRequest

CONCISE_PROMPT = """You are a Senior Consultant Physician AI at an academic medical center.
Generate a structured, professional clinical note matching the exact JSON schema provided.

## STANDARDS:
1. Format: Output ONLY valid JSON matching the schema — no markdown, no preamble.
2. Concise & High-Yield: 1-2 focused sentences per section. Pertinent positives and negatives.
3. Vitals: Extracted vitals (BP, HR, RR, Temp, SpO2) or "Not documented".
4. HPI: Chronological summary of onset, radiation, associated symptoms.
5. ROS: Pertinent systems.
6. Differential: Top 2-3 diagnoses with brief clinical rationale.
7. Assessment & Plan: Leave blank.

Schema:
{
  "chief_complaint": "",
  "hpi": "",
  "vitals": "",
  "review_of_systems": "",
  "past_medical_history": "",
  "surgical_history": "",
  "medications": "",
  "allergies": "",
  "family_history": "",
  "social_history": "",
  "physical_examination": "",
  "investigations": "",
  "differential_diagnosis": "",
  "assessment": "",
  "plan": "",
  "follow_up_plan": "",
  "safety_net": ""
}"""

async def bench():
    provider = get_generation_provider()
    req = GenerationRequest(
        prompt="58yo male presents with 2 hours of substernal crushing chest pain radiating to left jaw, diaphoresis, nausea. BP 155/95, HR 102.",
        system_prompt=CONCISE_PROMPT,
        json_schema={"type": "object"},
        max_tokens=450
    )
    t0 = time.time()
    res = await provider.generate(req, timeout=120.0)
    dur = time.time() - t0
    print(f"Generated 16-section note in {dur:.2f}s!")
    data = json.loads(res.text)
    print("Parsed JSON keys:", len(data))
    print("Chief complaint:", data.get("chief_complaint"))
    print("Differential:", data.get("differential_diagnosis"))
    print("Safety net:", data.get("safety_net"))

asyncio.run(bench())
