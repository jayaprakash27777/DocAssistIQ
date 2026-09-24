import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio, time
from app.infrastructure.ai.factory import get_generation_provider
from app.infrastructure.ai.interfaces import GenerationRequest

async def bench():
    provider = get_generation_provider()
    req = GenerationRequest(
        prompt="58yo male with acute crushing chest pain radiating to left arm. Vitals: BP 155/95, HR 102. Generate a concise JSON clinical summary.",
        system_prompt="You are a clinical AI. Output JSON only: {\"chief_complaint\": \"\", \"hpi\": \"\", \"vitals\": \"\", \"differential\": \"\", \"plan\": \"\"}. Be concise and high-yield.",
        json_schema={"type": "object"},
        max_tokens=300
    )
    t0 = time.time()
    res = await provider.generate(req, timeout=120.0)
    dur = time.time() - t0
    print(f"Generated {len(res.text)} chars in {dur:.2f}s!")
    print(res.text)

asyncio.run(bench())
