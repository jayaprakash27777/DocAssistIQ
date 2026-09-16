"""Comprehensive dual test: DRC/BVD case + Mpox case."""
import sys
sys.path.insert(0, '.')

from app.services.clinical_reasoning_engine import clinical_reasoning_engine, normalize_symptom

# =====================================================================
# TEST 1: DRC / Bundibugyo Virus Disease (Previous case — must still pass)
# =====================================================================
print("=" * 65)
print("TEST 1: DRC / BVD CASE (Should be BVD #1)")
print("=" * 65)

bvd_symptoms = [
    'Fever', 'Profound Weakness', 'Diarrhea', 'Watery Diarrhea', 'Vomiting',
    'Abdominal Pain', 'Sore Throat', 'Redness Of The Eyes', 'Loss Of Appetite',
    'Dizziness', 'Confusion', 'Reduced Urine Output', 'Nausea', 'Fatigue',
    'Muscle Pain', 'Joint Pain', 'Dehydration'
]

bvd_candidates = clinical_reasoning_engine.score_all_diseases(
    patient_symptoms=bvd_symptoms,
    negated_symptoms=[],
    countries_visited=['Democratic Republic of the Congo', 'Congo'],
    days_since_return=8,
    top_n=5,
)

for i, c in enumerate(bvd_candidates):
    print(str(i+1) + ". " + c.disease + " score=" + str(round(c.score, 3)))

bvd_ok = 'bundibugyo' in bvd_candidates[0].disease.lower()
print("BVD #1: " + str(bvd_ok) + " PASS" if bvd_ok else "BVD #1: FAIL")

# =====================================================================
# TEST 2: MPOX CASE (New test — what the AI was getting WRONG)
# =====================================================================
print()
print("=" * 65)
print("TEST 2: MPOX CASE (Should be Mpox #1)")
print("=" * 65)

# Simulate what NLP extracts from the clinical notes
# (as close to real NLP output as possible)
mpox_symptoms_npl_style = [
    'Fever', 'Fatigue', 'Headache', 'Generalized body aches', 'Loss of appetite',
    # Key dermatological findings
    'Lymph node swelling', 'Lymph node enlargement',  # <- NLP output
    'Skin eruption',                                    # <- NLP output for "rash"
    'Skin lesion',                                      # <- NLP output
    'Painful lesions',                                  # <- NLP output
    'Rash progression',                                 # <- NLP output
    'Weakness', 'Tenderness',
]

# Check normalization
print("Normalization check:")
for s in ['skin eruption', 'lymph node swelling', 'lymph node enlargement',
          'painful lesions', 'rash progression', 'generalized body aches']:
    normalized = normalize_symptom(s)
    print("  '" + s + "' -> '" + normalized + "'")

print()

mpox_candidates = clinical_reasoning_engine.score_all_diseases(
    patient_symptoms=mpox_symptoms_npl_style,
    negated_symptoms=[],
    countries_visited=['Country with ongoing outbreak'],
    days_since_return=6,
    top_n=7,
)

print("TOP 7 CANDIDATES:")
for i, c in enumerate(mpox_candidates):
    print(str(i+1) + ". " + c.disease + " score=" + str(round(c.score, 3)) +
          " | clusters=" + str(c.clusters_matched) + " | geo=" + str(c.geographic_match))

mpox_rank = None
for i, c in enumerate(mpox_candidates):
    if 'mpox' in c.disease.lower() or 'monkeypox' in c.disease.lower():
        mpox_rank = i + 1
        break

print()
print("Mpox rank: " + str(mpox_rank) + " (should be 1)")

# =====================================================================
# TEST 3: MPOX with richer clinical vocabulary (as described in the case)
# =====================================================================
print()
print("=" * 65)
print("TEST 3: MPOX with full clinical vocabulary")
print("=" * 65)

mpox_symptoms_rich = [
    'Fever', 'Fatigue', 'Headache', 'Body aches', 'Loss of appetite',
    'Swollen lymph nodes', 'Lymphadenopathy',
    'Rash', 'Skin lesion', 'Pustular rash', 'Vesicular rash',
    'Mucosal lesion', 'Palmoplantar rash',
    'Sore throat', 'Weakness',
]

mpox_rich_candidates = clinical_reasoning_engine.score_all_diseases(
    patient_symptoms=mpox_symptoms_rich,
    negated_symptoms=[],
    countries_visited=['Country with ongoing outbreak'],
    days_since_return=6,
    top_n=5,
)

print("TOP 5 (rich vocab):")
for i, c in enumerate(mpox_rich_candidates):
    print(str(i+1) + ". " + c.disease + " score=" + str(round(c.score, 3)))

mpox_rich_rank = next((i+1 for i, c in enumerate(mpox_rich_candidates)
                        if 'mpox' in c.disease.lower()), None)
print("Mpox rank (rich): " + str(mpox_rich_rank) + " (should be 1)")

# =====================================================================
# FINAL VERDICT
# =====================================================================
print()
print("=" * 65)
print("FINAL VERDICT")
print("=" * 65)
test1 = bvd_ok
test2 = mpox_rank is not None and mpox_rank <= 2
test3 = mpox_rich_rank is not None and mpox_rich_rank == 1

print("Test 1 (BVD #1):", "PASS" if test1 else "FAIL")
print("Test 2 (Mpox NLP-style, top 2):", "PASS" if test2 else "FAIL")
print("Test 3 (Mpox rich vocab, #1):", "PASS" if test3 else "FAIL")
print()
if test1 and test2 and test3:
    print(">>> ALL TESTS PASS - God-Level AI working correctly!")
else:
    print(">>> PARTIAL PASS - Check scores above")
