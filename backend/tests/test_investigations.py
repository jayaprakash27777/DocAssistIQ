from app.services.investigation_service import investigation_provider

def test_investigations_found():
    res = investigation_provider.get_investigations("Asthma")
    assert res.disease.lower() == "asthma"
    assert len(res.suggestions) > 0
    
    # check that we have a high priority suggestion
    assert any(s.priority == "HIGH PRIORITY" for s in res.suggestions)

def test_investigations_not_found():
    res = investigation_provider.get_investigations("UnknownDisease")
    assert res.disease == "UnknownDisease"
    assert len(res.suggestions) == 0

def test_investigations_case_insensitive():
    res = investigation_provider.get_investigations("pNeUmOnIa")
    assert len(res.suggestions) > 0
    assert any(s.name == "Chest X-Ray (PA and Lateral)" for s in res.suggestions)
