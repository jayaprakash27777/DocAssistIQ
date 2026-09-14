import asyncio
import sys
import os

# Add backend to path
sys.path.append(r"c:\Users\User\Downloads\DocAssistIQ\backend")

from app.services.llm_service import llm_service

async def test():
    prompt = """Analyze this data and return the JSON."""
    system_prompt = """You are an expert clinical diagnostic AI.
Return ONLY valid JSON matching this schema exactly:
{
  "candidates": [
    {
      "disease": "Asthma",
      "score": 0.9,
      "supporting_findings": ["cough"],
      "missing_expected_findings": [],
      "contradicting_information": [],
      "uncertainty": "Low",
      "explanation_reference": "Matches symptoms."
    }
  ]
}
"""
    try:
        resp = await llm_service.generate_json(prompt, system_prompt)
        print("Success!")
        print(resp)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
