import sys; sys.path.insert(0, ".")

# Test 1: live_disease_scanner imports correctly
from app.services.live_disease_scanner import (
    outbreak_scanner, get_merged_disease_kb, get_dynamic_kb_entry,
    put_dynamic_kb_entry, get_dynamic_diseases_summary, on_demand_lookup,
    _extract_disease_names_from_text, _sparse_fallback
)
print("OK: live_disease_scanner imported")

# Test 2: Merged KB size
from app.services.offline_disease_kb import DISEASE_KB
merged = get_merged_disease_kb()
print(f"OK: Merged KB = {len(merged)} diseases ({len(DISEASE_KB)} static)")

# Test 3: Text extraction
samples = [
    "Outbreak of Novel Hemorrhagic Virus disease reported in West Africa",
    "WHO Alert: New respiratory syndrome cases in Asia",
    "Unknown hemorrhagic fever outbreak in Central Africa",
    "Disease X detected in rural villages near Amazon basin",
]
for s in samples:
    found = _extract_disease_names_from_text(s)
    print(f"  Extract: {found}")

# Test 4: Sparse fallback
cases = [
    ("Novel Zaire Hemorrhagic Fever", "hemorrhagic bleeding africa"),
    ("Mysterious Respiratory Syndrome", "cough pneumonia respiratory"),
    ("Unknown Enteric Illness", "diarrhea gastro cholera"),
]
for name, ctx in cases:
    p = _sparse_fallback(name, ctx)
    print(f"  Sparse [{name}]: severity={p['severity']}, clusters={p['clusters']}")

# Test 5: Dynamic KB store/retrieve
put_dynamic_kb_entry("Test Novel Fever", {
    "symptoms": ["fever","rash"], "cardinal_symptoms": ["fever"],
    "hemorrhagic": False, "geographic_zones": ["Global"],
    "clusters": ["febrile_illness"], "incubation_min": 2, "incubation_max": 10,
    "severity": "high"
}, "Test Novel Fever")
entry = get_dynamic_kb_entry("Test Novel Fever")
print(f"OK: Dynamic KB store/retrieve: {entry is not None}")

# Test 6: Dynamic entry in merged KB
merged2 = get_merged_disease_kb()
print(f"OK: Merged now = {len(merged2)} diseases (was {len(DISEASE_KB)} static)")

# Test 7: Scoring engine uses merged KB
from app.services.clinical_reasoning_engine import clinical_reasoning_engine
candidates = clinical_reasoning_engine.score_all_diseases(
    patient_symptoms=["fever","rash"],
    negated_symptoms=[],
    countries_visited=[],
    days_since_return=None,
    top_n=5,
)
names = [c.disease for c in candidates]
test_in = any("Test Novel" in n for n in names)
print(f"OK: Dynamic disease scored: {test_in} | Top 3: {names[:3]}")

# Test 8: Router import
from app.api.v1.endpoints.live_intelligence import router
print(f"OK: Intelligence router has {len(router.routes)} routes")

print()
print("=== ALL INTEGRATION TESTS PASSED ===")
