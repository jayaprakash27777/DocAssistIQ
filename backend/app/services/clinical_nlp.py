"""DocAssistIQ — Clinical NLP Extractor (Phase 28).

Deterministic clinical information extraction using spaCy.
Focuses on explainable and testable extraction of symptoms, signs, 
medications, and conditions, with robust negation and temporality handling.
"""

import spacy
from spacy.matcher import Matcher, PhraseMatcher
from typing import List, Dict, Any
from app.services.concept_normalizer import normalizer

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Vocabularies for simple extraction
SYMPTOMS = ["fever", "chest pain", "cough", "shortness of breath", "headache", "nausea", "fatigue", "pain", "sob", "cp", "ha", "n/v"]
CONDITIONS = ["asthma", "hypertension", "diabetes", "copd", "cancer", "htn", "t2dm", "ms", "pe"]
MEDICATIONS = ["lisinopril", "albuterol", "metformin", "aspirin", "tylenol", "ibuprofen", "asa"]

# Temporality triggers
PAST_TRIGGERS = ["history", "previous", "past", "ago", "last"]
# Negation triggers
NEGATION_TRIGGERS = ["no", "not", "denies", "without", "ruled out", "zero"]

class ClinicalExtractor:
    def __init__(self):
        self.nlp = nlp
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        # Add terminology to phrase matcher
        for cat, terms in [("SYMPTOM", SYMPTOMS), ("CONDITION", CONDITIONS), ("MEDICATION", MEDICATIONS)]:
            patterns = [self.nlp.make_doc(t) for t in terms]
            self.phrase_matcher.add(cat, patterns)

    def extract(self, text: str, source_context: str = "clinical_note") -> List[Dict[str, Any]]:
        if not text:
            return []
            
        doc = self.nlp(text)
        matches = self.phrase_matcher(doc)
        
        findings = []
        # Keep track of matched tokens to avoid duplicate reporting if patterns overlap
        matched_spans = []
        
        # We sort by length descending to prefer longer matches if they overlap
        # but PhraseMatcher returns (match_id, start, end). We'll resolve overlaps simply.
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            
            # Check overlap
            overlap = False
            for (s, e) in matched_spans:
                if start >= s and start < e:
                    overlap = True
                if end > s and end <= e:
                    overlap = True
            if overlap:
                continue
            matched_spans.append((start, end))
            
            # 1. Determine Negation
            # We look in the dependency tree of the span's root, or just a sliding window backward
            negated = False
            # Check window of 3 words before the concept
            window_start = max(0, start - 4)
            pre_window = doc[window_start:start]
            
            for token in pre_window:
                if token.lower_ in NEGATION_TRIGGERS:
                    negated = True
                    break
                    
            # Check dependency specifically for verbs (e.g. "denies")
            if not negated:
                for ancestor in span.root.ancestors:
                    if ancestor.lemma_ in ["deny", "rule out", "exclude"]:
                        negated = True
                        break
                        
            # 2. Determine Temporality
            temporality = "current"
            # Check window before
            for token in pre_window:
                if token.lower_ in PAST_TRIGGERS:
                    temporality = "past"
                    break
            
            # "history of" often appears as "history" <- prep -> "of" <- pobj -> concept
            if not negated and temporality == "current":
                for ancestor in span.root.ancestors:
                    if ancestor.lower_ in PAST_TRIGGERS:
                        temporality = "past"
                        break

            # 3. Phase 29: Normalization
            raw_val = span.text.lower()
            canon, mapping_src, mapping_conf = normalizer.normalize(raw_val)

            finding = {
                "concept": label,
                "value": raw_val,
                "certainty": "high" if not negated else "high", # we are certain it is negated
                "negated": negated,
                "temporality": temporality,
                "source": source_context,
                "confidence": 0.95,  # Deterministic regex/phrase match
                "canonical_concept": canon,
                "mapping_source": mapping_src,
                "mapping_confidence": mapping_conf
            }
            findings.append(finding)
            
        return findings

extractor = ClinicalExtractor()
