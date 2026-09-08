from app.services.medication_service import medication_provider

def test_medications_found():
    res = medication_provider.get_medications("Asthma")
    assert res.disease.lower() == "asthma"
    assert len(res.suggestions) > 0
    
    # Check that generic names are present
    assert any(s.generic_name.startswith("Albuterol") for s in res.suggestions)
    
    # Check standard fields are populated
    first = res.suggestions[0]
    assert first.standard_reference_dosing != ""
    assert first.contraindications is not None
    assert first.allergy_considerations != ""

def test_medications_not_found():
    res = medication_provider.get_medications("UnknownDisease")
    assert res.disease == "UnknownDisease"
    assert len(res.suggestions) == 0

def test_medications_case_insensitive():
    res = medication_provider.get_medications("pNeUmOnIa")
    assert len(res.suggestions) > 0
    assert any(s.generic_name == "Amoxicillin" for s in res.suggestions)
