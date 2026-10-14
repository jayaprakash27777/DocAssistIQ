import sys
import os
import re

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.services.realtime_prediction_service import realtime_prediction_service

case1 = """A 29-year-old woman presents with four months of fatigue, reduced exercise tolerance, intermittent headaches, and light-headedness when standing. She reports heavy menstrual bleeding lasting eight to nine days each cycle and occasionally craving ice. Examination shows conjunctival pallor, a pulse of 102/min, and no jaundice or splenomegaly. Hemoglobin is 8.7 g/dL, mean corpuscular volume is 68 fL, and the red-cell distribution width is elevated. She eats little meat and has no reported gastrointestinal bleeding."""

res = realtime_prediction_service.predict(case1)
print("--- PREDICTION RESULT FOR CASE 1 ---")
print("Latency (ms):", res.get("latency_ms"))
print("Triage:", res.get("triage_level"))
print("Emergency:", res.get("emergency_detected"))
print("Top Predictions:")
for i, p in enumerate(res.get("predictions", [])[:5], 1):
    print(f"  {i}. {p.get('disease')} (Score: {p.get('score')}, Match: {p.get('matched_symptoms')})")
print("Bedside tests:", res.get("priority_investigations", [])[:3])
