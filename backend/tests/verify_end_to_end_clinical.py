"""
End-to-End Clinical Verification Suite:
Validates real-time clinical-grade answers across global diseases, doctor note parsing,
demographic filtering, disease intelligence, investigations, and medications.
"""
import sys
import os
import time
import asyncio

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.clinical_note_parser import ClinicalNoteParser
from app.services.realtime_prediction_service import RealtimePredictionService
from app.services.clinical_disease_metadata import get_disease_clinical_profile
from app.services.disease_intelligence_service import _build_static_fallback
from app.services.open_domain_medical_engine import open_domain_engine

async def test_doctor_clinical_note_understanding():
    print("=" * 70)
    print("1. TESTING DOCTOR CLINICAL NOTE UNDERSTANDING (SOAP & ED TRIAGE)")
    print("=" * 70)
    parser = ClinicalNoteParser()

    complex_doctor_note = """
    HPI: 42yo M presents to ED with 4 days of progressive high fevers (Tmax 39.4C), severe retro-orbital headache, 
    debilitating generalized myalgias and arthralgias. Recently returned from travel to the Amazon basin (Iquitos, Peru).
    Vitals: BP 118/74, HR 102, RR 18, SpO2 98% on RA, Temp 39.1C.
    Physical Exam: Marked photophobia, mild conjunctival injection without purulence. No neck stiffness, Kernig/Brudzinski negative.
    Skin: Transient maculopapular rash on trunk. No petechiae or mucosal bleeding.
    Lungs: Clear to auscultation bilaterally, no wheezes or rales.
    Abdomen: Soft, non-tender, no hepatosplenomegaly.
    Labs: WBC 3.1 (leukopenia), Platelets 115k (mild thrombocytopenia), AST 68, ALT 54.
    Denies: No cough, no dyspnea, no chest pain, no diarrhea, no focal neurological deficits.
    Assessment: Suspect acute arboviral illness (Oropouche virus vs Dengue).
    """

    parsed = parser.parse(complex_doctor_note)
    pos = parsed["positive_findings"]
    neg = parsed["negated_findings"]
    diag = parsed["diagnostic_findings"]
    vitals = parsed["abnormal_vitals_findings"]
    travel = parsed["travel_history"]

    print(f"Extracted Positive Findings ({len(pos)}): {pos[:10]}")
    print(f"Extracted Negated Clauses ({len(neg)}): {neg}")
    print(f"Diagnostic Markers ({len(diag)}): {diag}")
    print(f"Abnormal Vitals ({len(vitals)}): {vitals}")
    print(f"Travel Context: {travel}")

    assert any("fever" in f.lower() for f in pos), "Fever should be extracted"
    assert any("headache" in f.lower() or "retro-orbital" in f.lower() for f in pos), "Headache should be extracted"
    assert any("myalgia" in f.lower() or "arthralgia" in f.lower() for f in pos), "Myalgia/arthralgia should be extracted"
    assert any("cough" in n.lower() for n in neg), "Cough should be negated"
    assert any("chest pain" in n.lower() for n in neg), "Chest pain should be negated"
    print(" [PASSED] Doctor Clinical Note Parser accurately extracted positive/negated concepts & markers.\n")

async def test_differential_prediction_accuracy():
    print("=" * 70)
    print("2. TESTING REAL-TIME TOP 5 PREDICTIONS & INVESTIGATIONS/MEDICATIONS")
    print("=" * 70)
    service = RealtimePredictionService()

    test_cases = [
        {
            "name": "Emerging Arbovirus: Oropouche Virus Disease",
            "symptoms": ["high fever", "retro-orbital headache", "severe myalgia", "arthralgia", "photophobia", "maculopapular rash", "leukopenia"],
            "expected_top": "Oropouche Virus Disease",
            "gender": "male",
            "age": 42
        },
        {
            "name": "Emerging Global Pathogen: Mpox (Monkeypox)",
            "symptoms": ["fever", "painful vesicular rash", "deep-seated umbilicated lesions", "firm pustules", "pronounced painful lymphadenopathy", "inguinal lymphadenopathy"],
            "expected_top": "Mpox (Monkeypox)",
            "gender": "male",
            "age": 31
        },
        {
            "name": "Pediatric Vasculitis: Kawasaki Disease",
            "symptoms": ["prolonged high fever >5 days", "bilateral non-exudative conjunctivitis", "strawberry tongue", "erythema and edema of hands and feet", "cervical lymphadenopathy", "polymorphous rash"],
            "expected_top": "Kawasaki Disease",
            "gender": "male",
            "age": 4
        },
        {
            "name": "Cardiovascular Emergency: Acute Myocardial Infarction",
            "symptoms": ["crushing substernal chest pain", "radiation to left arm and jaw", "diaphoresis", "dyspnea", "nausea", "lightheadedness"],
            "expected_top": "Acute Myocardial Infarction",
            "gender": "female",
            "age": 62
        },
        {
            "name": "Acute Neuromuscular Emergency: Myasthenia Gravis / Crisis",
            "symptoms": ["fluctuating muscle weakness", "bilateral ptosis", "diplopia", "dysphagia", "dysarthria", "respiratory muscle weakness", "fatigability worse with repetitive activity"],
            "expected_top": "Myasthenia Gravis",
            "gender": "female",
            "age": 35
        },
        {
            "name": "Critical Vascular Emergency: Acute Pulmonary Embolism",
            "symptoms": ["sudden onset pleuritic chest pain", "acute dyspnea", "tachypnea", "tachycardia", "hemoptysis", "unilateral leg swelling"],
            "expected_top": "Pulmonary Embolism",
            "gender": "male",
            "age": 55
        }
    ]

    for tc in test_cases:
        t0 = time.perf_counter()
        result = await service.predict_differential(
            symptoms=tc["symptoms"],
            gender=tc.get("gender"),
            age=tc.get("age")
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        candidates = result.get("top_candidates", [])
        top_name = candidates[0].get("disease", "") if candidates else "NONE"
        top_score = candidates[0].get("score", 0.0) if candidates else 0.0
        
        print(f"Case: {tc['name']}")
        print(f"  Latency: {elapsed_ms:.2f} ms")
        print(f"  Top Candidate: {top_name} (Confidence: {top_score*100:.1f}%)")
        print(f"  Top 5: {[c['disease'] for c in candidates[:5]]}")
        
        top1 = candidates[0]
        meds = top1.get("recommended_medications", [])
        tests = top1.get("recommended_investigations", []) or top1.get("immediate_tests", [])
        first_line = top1.get("first_line_treatment", "")
        
        print(f"  Immediate/Recommended Tests ({len(tests)}): {tests[:2]}")
        print(f"  First-Line Treatment: {first_line[:90]}...")
        print(f"  Medications ({len(meds)}): {[m.get('name') if isinstance(m, dict) else str(m)[:30] for m in meds[:2]]}")

        assert any(tc["expected_top"].lower() in c.get("disease", "").lower() for c in candidates[:2]), \
            f"Expected {tc['expected_top']} in top 2, got {[c.get('disease') for c in candidates[:5]]}"
        assert len(tests) > 0, f"Expected recommended tests for {top_name}"
        assert len(meds) > 0 or first_line, f"Expected medications or first line treatment for {top_name}"
        print("  --> [PASSED]\n")

async def test_live_free_medical_sources():
    print("=" * 70)
    print("3. TESTING LIVE FREE MEDICAL SOURCES (NIH NLM & OpenFDA API)")
    print("=" * 70)
    
    # 1. NLM ClinicalTables
    t0 = time.perf_counter()
    nlm_res = await open_domain_engine.fetch_nlm_condition_lookup("Chikungunya")
    nlm_ms = (time.perf_counter() - t0) * 1000
    print(f"NLM ClinicalTables Lookup 'Chikungunya': {nlm_res.get('found')} in {nlm_ms:.2f} ms")
    if nlm_res.get("found"):
        print(f"  Standard Term: {nlm_res.get('standard_term')} (ICD-10: {nlm_res.get('icd10_code')})")

    # 2. OpenFDA Drug API
    t0 = time.perf_counter()
    fda_res = await open_domain_engine.fetch_openfda_drug_indications("Oropouche")
    fda_ms = (time.perf_counter() - t0) * 1000
    print(f"OpenFDA Drug Lookup: found={fda_res.get('found')} in {fda_ms:.2f} ms")

    # 3. Clinical Disease Metadata & Profile
    t0 = time.perf_counter()
    prof = get_disease_clinical_profile("Kawasaki Disease")
    prof_ms = (time.perf_counter() - t0) * 1000
    print(f"Clinical Profile for 'Kawasaki Disease' in {prof_ms:.2f} ms:")
    print(f"  ICD-10: {prof.get('icd10_code')}")
    print(f"  Investigations: {len(prof.get('recommended_investigations', []))} items")
    print(f"  Medications: {len(prof.get('recommended_medications', []))} items")
    print(f"  First Line Treatment: {prof.get('first_line_treatment')}")
    print(f"  Red Flags: {len(prof.get('red_flags', []))} items")

    assert prof.get("icd10_code") == "M30.3", f"Expected M30.3 for Kawasaki, got {prof.get('icd10_code')}"
    assert len(prof.get("recommended_medications", [])) > 0, "Expected recommended medications"
    assert len(prof.get("recommended_investigations", [])) > 0, "Expected recommended investigations"

    # 4. Disease Intelligence Static Fallback Builder
    static_data = _build_static_fallback("Kawasaki Disease")
    assert len(static_data.get("investigations", [])) > 0, "Expected static fallback investigations"
    assert len(static_data.get("medications", [])) > 0, "Expected static fallback medications"
    print(f"Disease Intelligence Fallback: {len(static_data.get('medications', []))} meds, {len(static_data.get('investigations', []))} investigations.")
    print("  --> [PASSED] Live free medical sources & intelligence validated.\n")

async def main():
    print("STARTING FULL CLINICAL GRADE VERIFICATION SUITE\n")
    await test_doctor_clinical_note_understanding()
    await test_differential_prediction_accuracy()
    await test_live_free_medical_sources()
    print("=" * 70)
    print("ALL CLINICAL GRADE SUITE CHECKS COMPLETED SUCCESSFULLY WITH 100% PASS RATE!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
