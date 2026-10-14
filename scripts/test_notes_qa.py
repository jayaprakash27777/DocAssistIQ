import asyncio
import sys
import time

sys.path.append("backend")

from app.services.doctor_notes_qa_service import doctor_notes_qa_service

async def main():
    notes = """
    Patient: John Doe, 58M.
    Chief Complaint: Retrosternal crushing chest pain radiating to left jaw for 2 hours, diaphoresis.
    Vitals: BP 85/55 mmHg, HR 112 bpm, SpO2 93% on room air, RR 24.
    ECG: Marked ST elevations in leads II, III, aVF. ST depressions in I, aVL.
    History: Type 2 Diabetes, Hypertension.
    Current Meds: Metformin 500mg, Lisinopril 10mg.
    Allergies: Penicillin (hives).
    """

    queries = [
        "What is the patient's blood pressure and heart rate?",
        "What are the patient's current medications and allergies?",
        "What is the primary diagnosis and emergency protocol?",
        "What is the first-line treatment for acute pulmonary embolism?",
    ]

    print("=== COLD RUN ===")
    for q in queries:
        t0 = time.time()
        res = await doctor_notes_qa_service.answer_question(query=q, notes_text=notes)
        lat = (time.time() - t0) * 1000
        print(f"\n[Q]: {q}")
        print(f"Latency: {lat:.2f}ms (Engine reported: {res.get('latency_ms')}ms)")
        print(f"Model: {res.get('model_used')}")
        print(f"Confidence: {res.get('confidence_score')}")
        ans_preview = res.get('answer', '')[:160].replace('\n', ' ').encode('ascii', 'ignore').decode('ascii')
        print(f"Answer: {ans_preview}...")

    print("\n\n=== WARM RUN (CACHE) ===")
    for q in queries:
        t0 = time.time()
        res = await doctor_notes_qa_service.answer_question(query=q, notes_text=notes)
        lat = (time.time() - t0) * 1000
        print(f"[WARM] Latency: {lat:.3f}ms | {q[:45]}...")

if __name__ == "__main__":
    asyncio.run(main())
