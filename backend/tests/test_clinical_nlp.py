"""Tests for Phase 28: Clinical NLP Extraction."""

import pytest
from app.services.clinical_nlp import extractor

def test_basic_extraction():
    text = "Patient presents with fever and fatigue."
    findings = extractor.extract(text)
    assert len(findings) == 2
    concepts = {f["value"] for f in findings}
    assert "fever" in concepts
    assert "fatigue" in concepts
    
    # Check defaults
    for f in findings:
        assert f["negated"] is False
        assert f["temporality"] == "current"


def test_negation():
    text = "Patient denies chest pain and has no fever."
    findings = extractor.extract(text)
    assert len(findings) == 2
    for f in findings:
        assert f["negated"] is True
        assert f["temporality"] == "current"


def test_temporality():
    text = "History of asthma and previous episode of cough."
    findings = extractor.extract(text)
    
    asthma = next((f for f in findings if f["value"] == "asthma"), None)
    assert asthma is not None
    assert asthma["temporality"] == "past"
    assert asthma["negated"] is False
    
    cough = next((f for f in findings if f["value"] == "cough"), None)
    assert cough is not None
    assert cough["temporality"] == "past"
    assert cough["negated"] is False


def test_adversarial_combinations():
    text = "Patient has no history of diabetes."
    findings = extractor.extract(text)
    assert len(findings) == 1
    diabetes = findings[0]
    assert diabetes["value"] == "diabetes"
    assert diabetes["negated"] is True
    # Either past or current is fine here depending on how strict the rule is,
    # but "history" usually forces temporality="past".
    assert diabetes["temporality"] == "past"


def test_conflicting_statements():
    text = "Patient complains of headache. Denies headache."
    findings = extractor.extract(text)
    assert len(findings) == 2
    
    h1 = findings[0]
    assert h1["negated"] is False
    
    h2 = findings[1]
    assert h2["negated"] is True


def test_abbreviations_and_casing():
    text = "Patient has COPD and takes Tylenol."
    findings = extractor.extract(text)
    assert len(findings) == 2
    concepts = {f["concept"] for f in findings}
    assert "CONDITION" in concepts
    assert "MEDICATION" in concepts
