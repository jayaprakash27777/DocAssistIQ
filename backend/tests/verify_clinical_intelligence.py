import asyncio
from app.services.disease_intelligence_service import _build_static_fallback
from app.services.investigation_service import investigation_provider
from app.services.medication_service import medication_provider
from app.services.diagnosis_provider import BaselineDiagnosisProvider, _enrich_candidate_actions
from app.schemas.representation import ClinicalRepresentationResponse, RepresentationItem

def test_static_and_providers():
    test_diseases = [
        "Malaria", "Dengue", "Acute Appendicitis", "Diabetic Ketoacidosis",
        "ST-Elevation Myocardial Infarction", "COVID-19", "Acute Ischemic Stroke",
        "Septic Shock", "Asthma Exacerbation", "Acute Pancreatitis", "Gout",
        "Pulmonary Embolism", "Acute Angle-Closure Glaucoma", "Anaphylaxis"
    ]

    print(f"Testing {len(test_diseases)} key clinical diseases:\n")

    for d in test_diseases:
        fallback = _build_static_fallback(d, None, [], None, "")
        invs = investigation_provider.get_investigations(d)
        meds = medication_provider.get_medications(d)
        enriched = _enrich_candidate_actions(d)

        assert fallback.get("summary") and fallback["summary"] != "No summary available.", f"Summary missing for {d}"
        assert len(fallback.get("investigations", [])) >= 2, f"Investigations missing for {d}"
        assert len(fallback.get("medications", [])) >= 1, f"Medications missing for {d}"
        assert len(invs.suggestions) >= 2, f"Investigation suggestions empty for {d}"
        assert len(meds.suggestions) >= 1, f"Medication suggestions empty for {d}"
        assert len(enriched["immediate_tests"]) >= 1 or len(enriched["recommended_investigations"]) >= 1, f"Enriched tests empty for {d}"
        assert len(enriched["recommended_medications"]) >= 1, f"Enriched meds empty for {d}"

        # Ensure no Ebola VHF investigations for non-VHF diseases
        if d not in ["Sudan Ebolavirus Disease", "Marburg Virus Disease", "Lassa Fever"]:
            assert not any("ebola" in inv.lower() or "marburg" in inv.lower() for inv in fallback["investigations"]), f"Erroneous VHF tests in {d}"

        print(f"[{d}] - PASSED")
        print(f"  Summary: {fallback['summary'][:70]}...")
        print(f"  First-Line Tx: {fallback['first_line_treatment']}")
        print(f"  Investigations ({len(fallback['investigations'])}): {fallback['investigations'][:2]}")
        print(f"  Medications ({len(fallback['medications'])}): {fallback['medications'][:2]}")
        print(f"  Medication Suggestion: {meds.suggestions[0].generic_name} | {meds.suggestions[0].standard_reference_dosing[:60] if meds.suggestions[0].standard_reference_dosing else 'N/A'}")
        print()

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_static_and_providers()
