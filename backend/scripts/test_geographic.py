import sys, os
sys.path.insert(0, os.path.abspath("."))

from app.services.offline_disease_kb import get_diseases_for_geography
from app.services.clinical_reasoning_engine import clinical_reasoning_engine

print("=== TEST 1: GEOGRAPHIC BONUSES BY COUNTRY ===")
for country in ["Thailand", "Uganda", "Brazil", "Nigeria", "India"]:
    bonuses = get_diseases_for_geography([country])
    top_boosted = sorted(bonuses.items(), key=lambda x: x[1], reverse=True)[:4]
    print(f"{country}: {top_boosted}")

print("\n=== TEST 2: IMPACT OF GEOGRAPHY ON DIFFERENTIAL DIAGNOSIS ===")
symptoms = ["fever", "headache", "joint pain", "rash"]

res_no_travel = clinical_reasoning_engine.score_all_diseases(
    patient_symptoms=symptoms,
    negated_symptoms=[],
    countries_visited=[],
    days_since_return=None,
    top_n=3
)
print("Without Travel:")
for c in res_no_travel:
    print(f"  {c.disease}: score={c.score:.3f}, geo_match={c.geographic_match}, geo_score={c.score_breakdown.get('geographic', 0)}")

res_brazil = clinical_reasoning_engine.score_all_diseases(
    patient_symptoms=symptoms,
    negated_symptoms=[],
    countries_visited=["Brazil"],
    days_since_return=5,
    top_n=3
)
print("\nWith Travel to Brazil (5 days ago):")
for c in res_brazil:
    print(f"  {c.disease}: score={c.score:.3f}, geo_match={c.geographic_match}, geo_score={c.score_breakdown.get('geographic', 0)}")

res_uganda = clinical_reasoning_engine.score_all_diseases(
    patient_symptoms=["fever", "headache", "bleeding"],
    negated_symptoms=[],
    countries_visited=["Uganda"],
    days_since_return=6,
    top_n=3
)
print("\nWith Travel to Uganda (6 days ago + bleeding):")
for c in res_uganda:
    print(f"  {c.disease}: score={c.score:.3f}, geo_match={c.geographic_match}, geo_score={c.score_breakdown.get('geographic', 0)}")
