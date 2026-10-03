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

def test_emergency_medication_panels():
    # 1. Acute Coronary Syndrome
    acs = medication_provider.get_medications("Acute Coronary Syndrome")
    assert len(acs.suggestions) >= 4
    assert any("Aspirin" in s.generic_name for s in acs.suggestions)
    assert any("Ticagrelor" in s.generic_name for s in acs.suggestions)
    assert any("Heparin" in s.generic_name for s in acs.suggestions)
    assert any("Atorvastatin" in s.generic_name for s in acs.suggestions)
    for s in acs.suggestions:
        assert s.standard_reference_dosing != ""
        assert len(s.contraindications) > 0
        assert s.renal_considerations != ""
        assert s.pregnancy_lactation_considerations != ""

    # 2. Acute Ischemic Stroke
    stroke = medication_provider.get_medications("Acute Ischemic Stroke")
    assert len(stroke.suggestions) >= 2
    assert any("Tenecteplase" in s.generic_name for s in stroke.suggestions)
    assert any("Nicardipine" in s.generic_name for s in stroke.suggestions)

    # 3. Septic Shock
    sepsis = medication_provider.get_medications("Septic Shock")
    assert len(sepsis.suggestions) >= 2
    assert any("Norepinephrine" in s.generic_name for s in sepsis.suggestions)

    # 4. Diabetic Ketoacidosis
    dka = medication_provider.get_medications("Diabetic Ketoacidosis")
    assert len(dka.suggestions) >= 2
    assert any("Insulin" in s.generic_name for s in dka.suggestions)
    assert any("Potassium" in s.generic_name for s in dka.suggestions)

    # 5. Bacterial Meningitis
    meningitis = medication_provider.get_medications("Bacterial Meningitis")
    assert len(meningitis.suggestions) >= 3
    assert any("Ceftriaxone" in s.generic_name for s in meningitis.suggestions)
    assert any("Vancomycin" in s.generic_name for s in meningitis.suggestions)
    assert any("Dexamethasone" in s.generic_name for s in meningitis.suggestions)

