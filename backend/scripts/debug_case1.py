import sys
import os
sys.path.insert(0, os.path.abspath("backend"))
from app.services.realtime_prediction_service import realtime_prediction_service

case1 = """A 29-year-old woman presents with four months of fatigue, reduced exercise tolerance, intermittent headaches, and light-headedness when standing. She reports heavy menstrual bleeding lasting eight to nine days each cycle and occasionally craving ice. Examination shows conjunctival pallor, a pulse of 102/min, and no jaundice or splenomegaly. Hemoglobin is 8.7 g/dL, mean corpuscular volume is 68 fL, and the red-cell distribution width is elevated. She eats little meat and has no reported gastrointestinal bleeding."""

res = realtime_prediction_service.predict(case1)
print("=== TOP CANDIDATES ===")
for i, c in enumerate(res.get("top_candidates", []), 1):
    print(f"{i}. {c.get('disease')} | Score: {c.get('score')} | Match: {c.get('supporting_findings')} | Conf: {c.get('confidence_score')}")

print("\n=== RARE / OPEN DOMAIN DIFFERENTIALS ===")
for r in res.get("rare_disease_differentials", []):
    print(f"  {r.get('disease')} (ICD10: {r.get('icd10')})")

print("\n=== COMPARISON MATRIX ===")
for m in res.get("comparison_matrix", []):
    print(f"  {m.get('disease')} - score: {m.get('display_score')}")
