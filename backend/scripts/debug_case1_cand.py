import sys
import os
import json
sys.path.insert(0, os.path.abspath("backend"))
from app.services.realtime_prediction_service import realtime_prediction_service

case1 = """A 29-year-old woman presents with four months of fatigue, reduced exercise tolerance, intermittent headaches, and light-headedness when standing. She reports heavy menstrual bleeding lasting eight to nine days each cycle and occasionally craving ice. Examination shows conjunctival pallor, a pulse of 102/min, and no jaundice or splenomegaly. Hemoglobin is 8.7 g/dL, mean corpuscular volume is 68 fL, and the red-cell distribution width is elevated. She eats little meat and has no reported gastrointestinal bleeding."""

res = realtime_prediction_service.predict(case1)
for i, c in enumerate(res.get("top_candidates", []), 1):
    print(f"Candidate {i}: {c.get('disease')}")
    print(f"  Score: {c.get('score')}")
    print(f"  Post-test prob: {c.get('post_test_probability')}")
    print(f"  Pre-test prob: {c.get('pre_test_probability')}")
    print(f"  LR+: {c.get('positive_likelihood_ratio')}")
    print(f"  Matched symptoms: {c.get('supporting_findings')}")
    print(f"  ICD10: {c.get('icd10')}")
    print(f"  ICD11: {c.get('icd11')}")
    print(f"  Discriminative tests: {c.get('discriminative_tests')}")
