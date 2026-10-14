import sys
import os
import time
import asyncio

backend_path = r"c:\Users\User\Downloads\DocAssistIQ\backend"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.disease_intelligence_service import generate_disease_intelligence
from app.services.investigation_service import investigation_provider
from app.services.medication_service import medication_provider
from app.services.realtime_prediction_service import realtime_prediction_service

async def bench():
    print("=== BENCHMARKING SERVICES ===")
    
    # 1. Disease Intelligence
    t0 = time.perf_counter()
    try:
        d_intel = await asyncio.wait_for(generate_disease_intelligence(None, "Dengue Fever"), timeout=10.0)
        t1 = time.perf_counter()
        print(f"Disease Intelligence ('Dengue Fever'): {(t1-t0)*1000:.2f} ms")
    except Exception as e:
        t1 = time.perf_counter()
        print(f"Disease Intelligence FAILED in {(t1-t0)*1000:.2f} ms: {e}")

    # 2. Suggested Investigations
    t0 = time.perf_counter()
    try:
        invs = await asyncio.wait_for(investigation_provider._get_investigations_async(None, "Dengue Fever", None), timeout=10.0)
        t1 = time.perf_counter()
        print(f"Suggested Investigations ('Dengue Fever'): {(t1-t0)*1000:.2f} ms | Found: {len(invs.suggestions)}")
    except Exception as e:
        t1 = time.perf_counter()
        print(f"Suggested Investigations FAILED in {(t1-t0)*1000:.2f} ms: {e}")

    # 3. Medications
    t0 = time.perf_counter()
    try:
        meds = await asyncio.wait_for(medication_provider._get_medications_async(None, "Dengue Fever"), timeout=10.0)
        t1 = time.perf_counter()
        print(f"Medications ('Dengue Fever'): {(t1-t0)*1000:.2f} ms | Found: {len(meds.suggestions)}")
    except Exception as e:
        t1 = time.perf_counter()
        print(f"Medications FAILED in {(t1-t0)*1000:.2f} ms: {e}")

    # 4. Realtime Differential Diagnosis
    t0 = time.perf_counter()
    diff = realtime_prediction_service.predict(symptoms="high fever, retro-orbital headache, rash, thrombocytopenia", top_k=5)
    t1 = time.perf_counter()
    print(f"Realtime Differential Diagnosis: {(t1-t0)*1000:.2f} ms | Top: {diff['top_candidates'][0]['disease']} ({diff['top_candidates'][0]['display_score']})")

if __name__ == "__main__":
    asyncio.run(bench())
