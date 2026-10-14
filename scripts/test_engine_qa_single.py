import asyncio
import sys
import time

sys.path.append("backend")

from app.services.universal_clinical_engine import answer_any_clinical_question

async def main():
    q = "What is the first-line treatment for acute pulmonary embolism?"
    t0 = time.time()
    res = await answer_any_clinical_question(q)
    print(f"Total time: {(time.time()-t0)*1000:.2f}ms")
    print(f"Engine latency: {res.get('latency_ms')}ms")

asyncio.run(main())
