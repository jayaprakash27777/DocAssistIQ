import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.infrastructure.ai.factory import get_generation_provider, get_embedding_provider
from app.infrastructure.ai.interfaces import GenerationRequest

async def test_ai():
    print("Testing Embedding Provider...")
    embedder = get_embedding_provider()
    vec = await embedder.embed("Patient with acute dyspnea and fever")
    print(f"Embedding success! Length: {len(vec)}")

    print("Testing Generation Provider (JSON mode)...")
    gen = get_generation_provider()
    req = GenerationRequest(
        prompt="Patient reports severe chest pain radiating to left jaw.",
        system_prompt="You are a medical AI. Respond ONLY with valid JSON: {\"summary\": \"...\"}",
        json_schema={"type": "object"}
    )
    res = await gen.generate(req)
    print(f"Generation success! Response:\n{res.text}")

asyncio.run(test_ai())
