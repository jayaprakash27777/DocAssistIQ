import asyncio
import sys
import time

sys.path.append("backend")

from app.services.universal_clinical_engine import answer_any_clinical_question

async def main():
    test_queries = [
        "What is the first-line treatment for acute pulmonary embolism?",
        "What are the diagnostic criteria for diabetic ketoacidosis?",
        "What is the empiric antibiotic regimen for community-acquired pneumonia?",
        "What is the antidote for acetaminophen overdose?",
        "What is the CURB-65 score for a 70 year old patient?",
    ]

    print("=== COLD RUN (OFFLINE WAREHOUSE FAST-PATH) ===")
    for q in test_queries:
        t0 = time.time()
        res = await answer_any_clinical_question(q)
        lat = (time.time() - t0) * 1000
        print(f"\n[QUERY]: {q}")
        print(f"Latency: {lat:.2f}ms (Engine reported: {res.get('latency_ms')}ms)")
        print(f"Model: {res.get('model_used')}")
        print(f"Confidence: {res.get('confidence_score')}")
        print(f"Citations ({len(res.get('citations', []))}): {[c.get('source_name') for c in res.get('citations', [])[:2]]}")
        ans_preview = res.get('answer', '')[:200].replace('\n', ' ')
        print(f"Answer: {ans_preview}...")

    print("\n\n=== WARM RUN (IN-MEMORY CACHE) ===")
    for q in test_queries:
        t0 = time.time()
        res = await answer_any_clinical_question(q)
        lat = (time.time() - t0) * 1000
        print(f"[WARM] Latency: {lat:.3f}ms | {q[:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
