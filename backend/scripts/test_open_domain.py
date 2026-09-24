import sys
import os
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.llm_service import llm_service

async def test():
    prompt = """Patient presentation:
A 45-year-old male presents with sudden-onset excruciating pain, redness, and swelling in the first metatarsophalangeal (MTP) joint of the right great toe that woke him from sleep. Denies trauma. History of alcohol consumption and steak dinner last night.

Suggest top 3 differential diagnoses with scores (0.0 to 1.0) and brief clinical rationale as JSON:
{"candidates": [{"disease": "name", "score": 0.95, "rationale": "reason"}]}"""

    print("[*] Testing open-domain clinical prediction with ii-medical:8b...")
    start = time.time()
    res = await llm_service.generate_json(prompt, system="You are an expert clinical diagnostic physician. Output valid JSON only.")
    duration = time.time() - start
    print(f"[+] Completed in {duration:.2f}s")
    print("[+] Result:", res)

if __name__ == "__main__":
    asyncio.run(test())
