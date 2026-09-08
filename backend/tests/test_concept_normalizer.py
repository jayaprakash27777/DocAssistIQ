"""Tests for Phase 29: Clinical Concept Normalization."""

import pytest
from app.services.concept_normalizer import ConceptNormalizer

def test_concept_normalization():
    normalizer = ConceptNormalizer()
    
    # 1. Test basic synonyms & abbreviations
    canon, src, conf = normalizer.normalize("htn")
    assert canon == "hypertension"
    assert src == "internal_dict"
    assert conf == 0.95
    
    canon, src, conf = normalizer.normalize("SOB")
    assert canon == "shortness of breath"
    
    canon, src, conf = normalizer.normalize("high blood pressure")
    assert canon == "hypertension"
    
    # 2. Test pass-through of already canonical terms
    canon, src, conf = normalizer.normalize("asthma")
    assert canon == "asthma"
    assert src == "internal_dict"
    
    # 3. Test explicit rejection of ambiguous terms
    canon, src, conf = normalizer.normalize("ms")
    assert canon is None
    assert src is None
    assert conf is None
    
    canon, src, conf = normalizer.normalize("pe")
    assert canon is None
    
    # 4. Test unknown terms
    canon, src, conf = normalizer.normalize("random weird symptom")
    assert canon is None
