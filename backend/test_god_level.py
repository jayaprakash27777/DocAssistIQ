import sys, asyncio
sys.path.insert(0, '.')

from app.services.clinical_reasoning_engine import (
    clinical_reasoning_engine,
    normalize_symptom_set,
)
from app.services.offline_disease_kb import (
    get_diseases_for_geography,
    get_active_disease_clusters,
)

patient_symptoms = [
    'Fever', 'Profound Weakness', 'Diarrhea', 'Watery Diarrhea', 'Vomiting',
    'Abdominal Pain', 'Sore Throat', 'Redness Of The Eyes', 'Loss Of Appetite',
    'Dizziness', 'Confusion', 'Reduced Urine Output', 'Nausea', 'Fatigue',
    'Muscle Pain', 'Joint Pain', 'Dehydration'
]

negated_symptoms = []
countries_visited = ['Democratic Republic of the Congo', 'Congo']
days_since_return = 8

print("=== GOD-LEVEL DETERMINISTIC DIAGNOSIS TEST ===")
print("Patient: 34yo male, returned from DRC 8 days ago")
print()

geo_bonuses = get_diseases_for_geography(countries_visited)
print("Top geographic bonuses:")
for k, v in sorted(geo_bonuses.items(), key=lambda x: -x[1])[:5]:
    print("  " + k + ": +" + str(round(v, 2)))
print()

sym_set = normalize_symptom_set(patient_symptoms)
clusters = get_active_disease_clusters(sym_set)
print("Active syndromic clusters:", clusters)
print()

candidates = clinical_reasoning_engine.score_all_diseases(
    patient_symptoms=patient_symptoms,
    negated_symptoms=negated_symptoms,
    countries_visited=countries_visited,
    days_since_return=days_since_return,
    top_n=7,
)

print("=== TOP 7 DIFFERENTIAL DIAGNOSES ===")
medals = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th']
for i, c in enumerate(candidates):
    print(medals[i] + " " + c.disease + "  (score=" + str(round(c.score, 3)) + ")")
    sb = c.score_breakdown
    breakdown = (
        "sym=" + str(round(sb["symptom_overlap"], 3)) +
        " geo=" + str(round(sb["geographic"], 3)) +
        " incub=" + str(round(sb["incubation"], 3)) +
        " cluster=" + str(round(sb["syndrome_cluster"], 3))
    )
    print("   Breakdown: " + breakdown)
    print("   Incubation: " + c.incubation_fit + " | Geo: " + str(c.geographic_match) + " | Hemorrhagic: " + str(c.hemorrhagic))
    print("   Supporting: " + str(c.supporting_findings[:4]))
    print("   Uncertainty: " + c.uncertainty)
    print()

top = candidates[0]
bvd_in_top3 = any('bundibugyo' in c.disease.lower() or 'bvd' in c.disease.lower() for c in candidates[:3])
ebola_in_top3 = any('ebola' in c.disease.lower() for c in candidates[:3])
lcm_in_top5 = any('lymphocytic' in c.disease.lower() for c in candidates[:5])

print("=== VERIFICATION ===")
print("BVD in top 3: " + str(bvd_in_top3) + " (should be True)")
print("Ebola in top 3: " + str(ebola_in_top3) + " (should be True)")
print("LCM in top 5: " + str(lcm_in_top5) + " (should be False)")
print("Top disease: " + top.disease)
print("Top score: " + str(round(top.score, 3)) + " (should be > 0.70)")
print()

if bvd_in_top3 and top.score > 0.70 and not lcm_in_top5:
    print(">>> PASS - God-Level AI working correctly!")
else:
    print(">>> PARTIAL - check scores")
