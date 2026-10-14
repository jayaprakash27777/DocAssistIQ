import asyncio
import sys
import time

sys.path.append("backend")

from app.services.offline_data_service import offline_data_service

async def test_parallel():
    q = "acute pulmonary embolism"
    t0 = time.time()
    f1 = asyncio.to_thread(offline_data_service.search_statpearls_monographs, q, 1)
    f2 = asyncio.to_thread(offline_data_service.search_medquad_qa, q, 2)
    r1, r2 = await asyncio.gather(f1, f2)
    print(f"Parallel cold time: {(time.time()-t0)*1000:.2f}ms")
    print(f"StatPearls: {len(r1)}, MedQuAD: {len(r2)}")

asyncio.run(test_parallel())
