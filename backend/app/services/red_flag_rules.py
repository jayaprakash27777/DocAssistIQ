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

def evaluate_cauda_equina(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect Cauda Equina Syndrome (saddle anesthesia, acute retention, bilateral weakness/sciatica)."""
    has_ces = False
    is_negated = False
    ces_keywords = [
        "saddle anesthesia", "saddle numbness", "urinary retention",
        "bowel incontinence", "bladder incontinence", "loss of bowel control",
        "loss of bladder control", "bilateral sciatica", "cauda equina"
    ]
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if any(kw in val for kw in ces_keywords):
            has_ces = True
    for neg in rep.negations:
        val = neg.value.lower()
        if any(kw in val for kw in ces_keywords):
            is_negated = True
    if has_ces and not is_negated:
        return SafetyFlag(
            rule_id="RF-006",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Possible Cauda Equina Syndrome detected (saddle anesthesia, acute urinary retention, or bilateral neurological deficit). Emergency spinal MRI and urgent neurosurgical/spine consult required.",
            source="RedFlagEngine"
        )
    return None

def evaluate_thunderclap_headache(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect Thunderclap Headache / Subarachnoid Hemorrhage."""
    has_sah = False
    is_negated = False
    sah_keywords = [
        "thunderclap headache", "worst headache of life", "worst headache ever",
        "explosive headache", "sudden severe headache"
    ]
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if any(kw in val for kw in sah_keywords) or ("headache" in val and ("sudden" in val or "explosive" in val) and ("severe" in val or "10/10" in val)):
            has_sah = True
    for neg in rep.negations:
        val = neg.value.lower()
        if any(kw in val for kw in sah_keywords):
            is_negated = True
    if has_sah and not is_negated:
        return SafetyFlag(
            rule_id="RF-007",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Thunderclap or explosive onset headache detected. Evaluate immediately for subarachnoid hemorrhage (STAT non-contrast head CT and lumbar puncture if CT negative).",
            source="RedFlagEngine"
        )
    return None

def evaluate_aortic_dissection(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect acute aortic dissection (tearing or ripping chest/back pain)."""
    has_dissection = False
    is_negated = False
    dissection_keywords = [
        "tearing chest pain", "ripping chest pain", "tearing back pain",
        "ripping back pain", "interscapular tearing", "aortic dissection"
    ]
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if any(kw in val for kw in dissection_keywords) or (("chest pain" in val or "back pain" in val) and ("tearing" in val or "ripping" in val)):
            has_dissection = True
    for neg in rep.negations:
        val = neg.value.lower()
        if any(kw in val for kw in dissection_keywords):
            is_negated = True
    if has_dissection and not is_negated:
        return SafetyFlag(
            rule_id="RF-008",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Tearing or ripping chest/interscapular pain detected. Urgent evaluation for acute aortic dissection (STAT CT angiography of chest and abdomen) required.",
            source="RedFlagEngine"
        )
    return None

def evaluate_torsion(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect testicular or ovarian torsion (acute severe scrotal/adnexal pain)."""
    has_torsion = False
    is_negated = False
    torsion_keywords = [
        "testicular torsion", "severe testicular pain", "acute scrotal pain",
        "scrotal swelling with pain", "ovarian torsion", "acute adnexal pain"
    ]
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if any(kw in val for kw in torsion_keywords):
            has_torsion = True
    for neg in rep.negations:
        val = neg.value.lower()
        if any(kw in val for kw in torsion_keywords):
            is_negated = True
    if has_torsion and not is_negated:
        return SafetyFlag(
            rule_id="RF-009",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Acute scrotal or adnexal pain suspicious for testicular or ovarian torsion detected. Immediate Doppler ultrasound and emergent surgical consultation (<6h time window) required.",
            source="RedFlagEngine"
        )
    return None

def evaluate_necrotizing_fasciitis(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect necrotizing soft tissue infection (pain out of proportion, crepitus, hemorrhagic bullae)."""
    has_nec = False
    is_negated = False
    nec_keywords = [
        "necrotizing fasciitis", "pain out of proportion", "gas gangrene",
        "crepitus", "subcutaneous emphysema", "skin necrosis", "dishwater discharge"
    ]
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if any(kw in val for kw in nec_keywords):
            has_nec = True
    for neg in rep.negations:
        val = neg.value.lower()
        if any(kw in val for kw in nec_keywords):
            is_negated = True
    if has_nec and not is_negated:
        return SafetyFlag(
            rule_id="RF-010",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Signs concerning for necrotizing soft tissue infection/fasciitis detected. Immediate emergency surgical exploration/debridement and broad-spectrum IV antimicrobial coverage required.",
            source="RedFlagEngine"
        )
    return None

def evaluate_airway_compromise(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect acute airway obstruction or epiglottitis (stridor, drooling, tripoding)."""
    has_airway = False
    is_negated = False
    airway_keywords = [
        "stridor", "epiglottitis", "drooling and inability to swallow",
        "tripod position", "tripoding", "airway compromise", "choking"
    ]
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if any(kw in val for kw in airway_keywords):
            has_airway = True
    for neg in rep.negations:
        val = neg.value.lower()
        if any(kw in val for kw in airway_keywords):
            is_negated = True
    if has_airway and not is_negated:
        return SafetyFlag(
            rule_id="RF-011",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Acute stridor, tripoding, or severe upper airway compromise detected. Maintain calm, prepare for immediate emergency airway intervention (anesthesiology/ENT stat).",
            source="RedFlagEngine"
        )
    return None

def evaluate_ectopic_pregnancy(rep: ClinicalRepresentationResponse) -> SafetyFlag | None:
    """Detect ruptured ectopic pregnancy (acute pelvic pain, syncope, shoulder tip pain)."""
    has_ectopic = False
    is_negated = False
    ectopic_keywords = [
        "ectopic pregnancy", "ruptured ectopic", "shoulder tip pain with pelvic pain",
        "severe pelvic pain with syncope", "adnexal mass with severe pain"
    ]
    for symptom in rep.symptoms:
        val = symptom.value.lower()
        if any(kw in val for kw in ectopic_keywords):
            has_ectopic = True
    for neg in rep.negations:
        val = neg.value.lower()
        if any(kw in val for kw in ectopic_keywords):
            is_negated = True
    if has_ectopic and not is_negated:
        return SafetyFlag(
            rule_id="RF-012",
            rule_version="1.0.0",
            category="RED_FLAG",
            severity="CRITICAL",
            message="Severe acute pelvic pain concerning for ruptured ectopic pregnancy detected. Urgent STAT pelvic ultrasound, quantitative beta-hCG, and emergent surgical consultation required.",
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
    ),
    RedFlagRule(
        rule_id="RF-006",
        rule_version="1.0.0",
        description="Cauda Equina Syndrome Rule",
        evaluator=evaluate_cauda_equina
    ),
    RedFlagRule(
        rule_id="RF-007",
        rule_version="1.0.0",
        description="Thunderclap Headache Rule",
        evaluator=evaluate_thunderclap_headache
    ),
    RedFlagRule(
        rule_id="RF-008",
        rule_version="1.0.0",
        description="Aortic Dissection Rule",
        evaluator=evaluate_aortic_dissection
    ),
    RedFlagRule(
        rule_id="RF-009",
        rule_version="1.0.0",
        description="Testicular or Ovarian Torsion Rule",
        evaluator=evaluate_torsion
    ),
    RedFlagRule(
        rule_id="RF-010",
        rule_version="1.0.0",
        description="Necrotizing Fasciitis Rule",
        evaluator=evaluate_necrotizing_fasciitis
    ),
    RedFlagRule(
        rule_id="RF-011",
        rule_version="1.0.0",
        description="Acute Airway Compromise Rule",
        evaluator=evaluate_airway_compromise
    ),
    RedFlagRule(
        rule_id="RF-012",
        rule_version="1.0.0",
        description="Ruptured Ectopic Pregnancy Rule",
        evaluator=evaluate_ectopic_pregnancy
    ),
]

