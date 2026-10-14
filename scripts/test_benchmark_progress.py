import sys
import time

sys.path.append("backend")

from benchmark_clinical_cases import clinical_cases
from app.services.realtime_prediction_service import realtime_prediction_service

print(f"Total benchmark cases: {len(clinical_cases)}")
successes = []
failures = []

for i, (query, expected) in enumerate(clinical_cases):
    t0 = time.time()
    res = realtime_prediction_service.predict(query)
    cands = res.get("top_candidates", [])
    top3 = [c["disease"] for c in cands[:3]]
    lat = (time.time() - t0) * 1000
    matched = any(any(e.lower() in d.lower() for d in top3) for e in expected)
    if matched:
        successes.append(query)
        print(f"[{i+1}/{len(clinical_cases)}] PASS ({lat:.1f}ms): '{query[:35]}' -> {top3[0] if top3 else None}")
    else:
        failures.append((query, expected, top3))
        print(f"[{i+1}/{len(clinical_cases)}] FAIL ({lat:.1f}ms): '{query[:35]}' -> Expected: {expected}, Got: {top3}")

print(f"\nFINAL RESULT: {len(successes)}/{len(clinical_cases)} passed, {len(failures)} failed.")
