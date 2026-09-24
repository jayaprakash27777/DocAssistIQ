"""DocAssistIQ — Real-Time Prediction & Universal Any-Disease Verification Script."""

import time
from app.services.realtime_prediction_service import realtime_prediction_service

cases = [
    ("Acute Appendicitis", "periumbilical pain migrating to right lower quadrant, nausea, vomiting, fever, rebound tenderness at McBurney point"),
    ("Acute MI", "central crushing chest pain, radiating to left arm, diaphoresis, shortness of breath"),
    ("Aortic Dissection", "sudden severe tearing chest pain radiating to back between shoulder blades, bp discrepancy between arms"),
    ("Gout", "acute severe joint pain in great toe, podagra, first mtp pain, redness, swelling"),
    ("Temporal Arteritis", "severe temporal headache, jaw claudication, scalp tenderness, blurred vision"),
    ("Kawasaki Disease", "high fever for 6 days, strawberry tongue, bilateral conjunctivitis, cracked red lips, swollen hands"),
    ("Epiglottitis", "severe sore throat, difficulty swallowing, drooling, tripod position, inspiratory stridor"),
    ("Wilson Disease (Open-Domain)", "kayser-fleischer rings, copper accumulation, asterixis, jaundice, tremor"),
    ("Addison Disease", "chronic profound fatigue, hyperpigmentation of palmar creases, salt craving, orthostatic hypotension"),
    ("Bacterial Meningitis", "high fever, severe headache, neck stiffness, nuchal rigidity, photophobia, confusion"),
    ("Subarachnoid Hemorrhage", "sudden worst headache of life, thunderclap headache, meningismus, nausea"),
    ("Anaphylaxis", "facial swelling, lip swelling, angioedema, hives, stridor, wheezing, hypotension after bee sting"),
    ("Tension Pneumothorax", "sudden sharp pleuritic chest pain, severe shortness of breath, tracheal deviation away from affected side, absent breath sounds"),
    ("Lyme Disease", "expanding bullseye rash, erythema migrans, tick bite history, fever, fatigue"),
]

passed = 0
for expected, query in cases:
    res = realtime_prediction_service.predict(query)
    top = res["top_candidates"][0] if res["top_candidates"] else None
    top_name = top["disease"] if top else "None"
    top_pct = top["display_score"] if top else "0%"
    triage = top["triage"] if top else "N/A"
    alert = res["emergency_alert"]["condition"] if res["emergency_alert"] else "None"
    
    # Check if expected is in predicted disease name
    is_match = any(word.lower() in top_name.lower() for word in expected.split()[:2])
    if is_match:
        passed += 1
        status = "PASSED"
    else:
        status = "FAILED"
        
    print(f"[{status}] Latency: {res['latency_ms']}ms | Expected: {expected}")
    print(f"   -> Top 1: {top_name} ({top_pct}) [Triage: {triage}] | Emergency Alert: {alert}")

print(f"\n==============================================")
print(f"Total: {passed}/{len(cases)} cases passed (Accuracy: {round(passed/len(cases)*100, 1)}%)")
