from typing import List, Callable
from pydantic import BaseModel
from app.schemas.safety import SafetyFlag
from app.schemas.representation import ClinicalRepresentationResponse

class RedFlagRule(BaseModel):
    rule_id: str
    rule_version: str
    description: str
    evaluator: Callable[[ClinicalRepresentationResponse], SafetyFlag | None]


def evaluate_chest_pain(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect severe or crushing chest pain, avoiding negatives or mild cases."""
    has_chest_pain = False
    is_severe = False
    is_negated = False
    
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if "chest pain" in val or "chest pressure" in val or "chest tightness" in val:
            has_chest_pain = True
            if "severe" in val or "crushing" in val or "10/10" in val:
                is_severe = True
                
    for neg in rep.negations:
        val = neg.value.lower()
        if "chest pain" in val or "chest pressure" in val:
            is_negated = True
            
    if has_chest_pain and is_severe and not is_negated:
        return SafetyFlag(
            rule_id="RF-001",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Severe or crushing chest pain detected. Evaluate for acute coronary syndrome or pulmonary embolism immediately.",
            source="RedFlagEngine"
        )
    return None

def evaluate_breathing_difficulty(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect severe breathing difficulty / shortness of breath."""
    has_sob = False
    is_severe = False
    is_negated = False
    
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if "shortness of breath" in val or "dyspnea" in val or "difficulty breathing" in val:
            has_sob = True
            if "severe" in val or "gasping" in val or "unable to speak" in val:
                is_severe = True
                
    for neg in rep.negations:
        val = neg.value.lower()
        if "shortness of breath" in val or "dyspnea" in val:
            is_negated = True
            
    if has_sob and is_severe and not is_negated:
        return SafetyFlag(
            rule_id="RF-002",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Severe breathing difficulty detected. Evaluate for airway compromise, severe asthma exacerbation, or hypoxia.",
            source="RedFlagEngine"
        )
    return None

def evaluate_stroke_symptoms(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect sudden weakness, facial droop, or sudden speech changes."""
    has_stroke_signs = False
    is_negated = False
    
    stroke_keywords = ["facial droop", "sudden weakness", "slurred speech", "hemiparesis"]
    
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if any(kw in val for kw in stroke_keywords):
            has_stroke_signs = True
            
    for neg in rep.negations:
        val = neg.value.lower()
        if any(kw in val for kw in stroke_keywords):
            is_negated = True
            
    if has_stroke_signs and not is_negated:
        return SafetyFlag(
            rule_id="RF-003",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Stroke-like symptoms (weakness, facial droop, or speech changes) detected. Immediate neurological evaluation required.",
            source="RedFlagEngine"
        )
    return None

def evaluate_anaphylaxis(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect anaphylaxis-like symptoms (throat swelling + hives)."""
    has_airway_swelling = False
    has_hives = False
    is_negated = False
    
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if "throat swelling" in val or "swelling of tongue" in val:
            has_airway_swelling = True
        if "hives" in val or "urticaria" in val or "widespread rash" in val:
            has_hives = True
            
    for neg in rep.negations:
        val = neg.value.lower()
        if "swelling" in val or "hives" in val or "anaphylaxis" in val:
            is_negated = True
            
    if has_airway_swelling and has_hives and not is_negated:
        return SafetyFlag(
            rule_id="RF-004",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Possible anaphylaxis detected (airway swelling with hives). Immediate epinephrine and emergency intervention may be needed.",
            source="RedFlagEngine"
        )
    return None

def evaluate_altered_consciousness(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect altered mental status or unconsciousness."""
    has_ams = False
    is_negated = False
    
    ams_keywords = ["unconscious", "unresponsive", "altered mental status", "severe confusion", "cannot wake up"]
    
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if any(kw in val for kw in ams_keywords):
            has_ams = True
            
    for neg in rep.negations:
        val = neg.value.lower()
        if any(kw in val for kw in ams_keywords):
            is_negated = True
            
    if has_ams and not is_negated:
        return SafetyFlag(
            rule_id="RF-005",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Altered consciousness or unresponsiveness detected. Requires immediate life support and neurological assessment.",
            source="RedFlagEngine"
        )
    return None

# The master list of versioned red-flag rules
RED_FLAG_RULES = [
    RedFlagRule(
        rule_id="RF-001",
        rule_version="1.0.0",
        description="Severe Chest Pain Rule",
        evaluator=evaluate_chest_pain
    ),
    RedFlagRule(
        rule_id="RF-002",
        rule_version="1.0.0",
        description="Severe Breathing Difficulty Rule",
        evaluator=evaluate_breathing_difficulty
    ),
    RedFlagRule(
        rule_id="RF-003",
        rule_version="1.0.0",
        description="Stroke Symptoms Rule",
        evaluator=evaluate_stroke_symptoms
    ),
    RedFlagRule(
        rule_id="RF-004",
        rule_version="1.0.0",
        description="Anaphylaxis Rule",
        evaluator=evaluate_anaphylaxis
    ),
    RedFlagRule(
        rule_id="RF-005",
        rule_version="1.0.0",
        description="Altered Consciousness Rule",
        evaluator=evaluate_altered_consciousness
    )
]
