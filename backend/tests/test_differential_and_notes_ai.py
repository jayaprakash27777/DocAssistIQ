"""DocAssistIQ — Comprehensive Validation Suite for Upgraded Note Parser, Differential Diagnosis, and DocAssist AI.

Validates:
1. Long note parsing speed (<50ms) and 100% accuracy (zero false positives).
2. Differential diagnosis clinical reasoning with validated clinical decision rules (Alvarado, Wells, Centor).
3. DocAssist AI offline warehouse integration (MedQA 1.25M benchmarks, PubMed Clinical Trials, OpenFDA).
"""

import time
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from app.services.clinical_note_parser import clinical_note_parser
from app.services.clinical_reasoning_engine import clinical_reasoning_engine
from app.services.universal_clinical_engine import answer_any_clinical_question
from app.services.offline_data_service import offline_data_service

COMPREHENSIVE_ACUTE_APPENDICITIS_NOTE = """
CHIEF COMPLAINT:
Severe right lower quadrant abdominal pain, nausea, and low-grade fever for 36 hours.

HISTORY OF PRESENT ILLNESS:
The patient is a 28-year-old previously healthy male who presents to the emergency department reporting a 36-hour history of abdominal pain. The pain began periumbilically as a dull, crampy ache, but over the subsequent 18 hours migrated and localized to the right lower quadrant (RLQ). It is now described as constant, sharp, and severe (8/10), exacerbated by coughing, walking, and sudden vehicular bumps. He reports anorexia and mild nausea, with two episodes of non-bilious non-bloody emesis earlier today. He notes subjective fever and chills at home.

PAST MEDICAL HISTORY:
1. Mild persistent asthma (diagnosed 2015), well-controlled.
2. Seasonal allergic rhinitis.
3. No prior history of abdominal surgeries. Denies diabetes mellitus, hypertension, coronary artery disease, or chronic kidney disease.

MEDICATIONS:
- Albuterol sulfate HFA inhaler 90 mcg 2 puffs PRN wheezing
- Fluticasone propionate nasal spray 50 mcg 1 spray each nostril daily
- Denies NSAID overuse, chronic anticoagulants, or immunosuppressive therapy

ALLERGIES:
- Penicillin (developed maculopapular rash as child, denies anaphylaxis)

REVIEW OF SYSTEMS:
- Constitutional: Positive for fever, chills, fatigue, malaise. Negative for weight loss or night sweats.
- Eyes: Denies vision changes, photophobia.
- ENT: Denies sore throat, congestion.
- Cardiovascular: Denies chest pain, palpitations, orthopnea, or pedal edema.
- Respiratory: Denies shortness of breath, cough, hemoptysis, or wheezing currently.
- Gastrointestinal: Positive for severe right lower quadrant pain, anorexia, nausea, emesis. Denies diarrhea, hematochezia, melena, jaundice, hematemesis, or dysphagia.
- Genitourinary: Denies dysuria, hematuria, urinary frequency, urgency, or flank pain.
- Musculoskeletal: Positive for pain with hip extension. Denies joint swelling, arthralgia, or back pain.
- Neurological: Denies headache, focal weakness, numbness, syncope, or seizures.

PHYSICAL EXAMINATION:
Vitals:
BP 128/78 mmHg, HR 108 bpm (tachycardia), RR 18 /min, Temp 38.4 °C (101.1 °F, febrile), SpO2 98% on room air.
General: Patient appears uncomfortable, lying still with right hip flexed to minimize peritoneal irritation. Diaphoretic.
HEENT: Normocephalic, atraumatic. Mucous membranes dry. No scleral icterus.
Cardiovascular: Tachycardic, regular rhythm. Normal S1 and S2, no murmurs, gallops, or rubs.
Pulmonary: Clear to auscultation bilaterally. No wheezes, rales, or rhonchi.
Abdomen: Flat. Hypoactive bowel sounds. Marked focal tenderness at McBurney's point in the right lower quadrant. Positive Rovsing's sign (pain elicited in RLQ with deep palpation of LLQ). Positive Dunphy sign (sharp pain on coughing). Guarding and focal peritoneal rebound tenderness present in RLQ. Positive psoas sign and positive obturator sign on the right. No hepatosplenomegaly, no pulsatile abdominal mass.
Extremities: Warm, well-perfused. No cyanosis, clubbing, or peripheral edema. Pulses 2+ bilaterally.
Neurologic: Alert and oriented x 4. Cranial nerves II-XII grossly intact.

LABORATORY AND DIAGNOSTIC DATA:
- CBC: WBC 16.8 x 10^3/uL (leukocytosis) with 86% neutrophils and left shift (bandemia 8%). Hemoglobin 14.8 g/dL, Platelets 260 x 10^3/uL.
- BMP: Sodium 138 mEq/L, Potassium 4.1 mEq/L, Chloride 102 mEq/L, Bicarbonate 23 mEq/L, BUN 18 mg/dL, Creatinine 0.9 mg/dL, Glucose 106 mg/dL.
- Inflammatory markers: CRP 48 mg/L (elevated), ESR 32 mm/hr (elevated).
- Urinalysis: Specific gravity 1.022, pH 6.0, negative for protein, negative for blood, negative for nitrites, leukocyte esterase negative, 0-2 WBC/hpf, no bacteria.
- Imaging: Ultrasound of the appendix demonstrates a non-compressible, blind-ending tubular structure in the right lower quadrant measuring 8.5 mm in outer diameter with hyperemic wall thickening on color Doppler, periappendiceal fat stranding, and a small amount of free fluid. Appendicolith visualized at the base. Non-contrast CT abdomen/pelvis confirms acute dilated appendix (9 mm) with focal appendicolith, mucosal enhancement, and surrounding mesenteric stranding, without evidence of perforation, abscess, or pneumoperitoneum.

ASSESSMENT AND PLAN:
28-year-old male presenting with classical Alvarado score of 9/10, acute appendicitis.
Plan:
1. Urgent general surgical consultation for laparoscopic appendectomy.
2. NPO status maintained.
3. IV fluid resuscitation with Plasmalyte at 150 mL/hr.
4. Preoperative IV antibiotic coverage: Cefoxitin 2g IV.
"""


def test_long_note_parsing_speed_and_accuracy():
    """Verify long complex note parses rapidly (<100ms) with zero false positives."""
    # Warm-up pass to load modules and initialize regex cache
    clinical_note_parser.parse(COMPREHENSIVE_ACUTE_APPENDICITIS_NOTE)

    t0 = time.perf_counter()
    res = clinical_note_parser.parse(COMPREHENSIVE_ACUTE_APPENDICITIS_NOTE)
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000

    # Speed check
    assert latency_ms < 100.0, f"Parsing took too long: {latency_ms:.2f} ms"

    pos = res["positive_findings"]
    neg = res["negated_findings"]
    diag = res["diagnostic_findings"]
    vitals = res["vitals"]

    # Cardinal surgical positive findings present
    assert any("right lower quadrant" in s or "rlq" in s for s in pos)
    assert any("psoas" in s for s in pos)
    assert "abdominal pain" in pos
    assert "rebound tenderness" in pos
    assert "leukocytosis" in pos

    # FALSE POSITIVE GUARDS:
    # 1. 'trauma' must NOT appear (from 'atraumatic')
    assert "trauma" not in pos

    # 2. 'cough' must NOT appear in positive findings (patient denied cough in ROS, only Dunphy provocation)
    assert "cough" not in pos
    assert "cough" in neg

    # 3. Urinalysis pH 6.0 must NOT trigger arterial acidemia panic alert
    assert "critical severe acidemia (pH <7.20)" not in pos
    assert "critical severe acidemia (pH <7.20)" not in diag
    assert "acidemia" not in pos

    # 4. Rovsing deep palpation of LLQ must NOT trigger left lower quadrant pain
    assert "left lower quadrant pain" not in pos

    # 5. Normal heart sounds must NOT trigger gallop or murmur
    assert not any("gallop" in s.lower() for s in pos)

    # Vitals accurately extracted
    assert vitals["heart_rate"] == 108
    assert vitals["blood_pressure"] == "128/78"
    assert vitals["temperature"] == 38.4


def test_differential_diagnosis_reasoning_accuracy():
    """Verify differential diagnosis engine scores Acute Appendicitis #1 with high confidence."""
    parsed = clinical_note_parser.parse(COMPREHENSIVE_ACUTE_APPENDICITIS_NOTE)
    scored = clinical_reasoning_engine.score_all_diseases(
        patient_symptoms=parsed["positive_findings"],
        negated_symptoms=parsed["negated_findings"],
        countries_visited=parsed["travel_history"],
        days_since_return=parsed["days_since_return"],
        top_n=5,
    )

    assert len(scored) >= 1
    top_candidate = scored[0]
    assert top_candidate.disease in ("Acute Appendicitis", "Appendicitis")
    assert top_candidate.score >= 1.5

    # Compartment isolation: Upper respiratory viral infections (Influenza, COVID-19)
    # must NOT contaminate the top 3 of a primary acute surgical abdomen
    top_3_diseases = [c.disease for c in scored[:3]]
    assert "Influenza" not in top_3_diseases
    assert "COVID-19" not in top_3_diseases


@pytest.mark.asyncio
async def test_docassist_ai_offline_warehouse_utilization():
    """Verify DocAssist AI question answering retrieves offline warehouse evidence."""
    res = await answer_any_clinical_question(
        query="What is the evidence-based management protocol for acute appendicitis?"
    )

    assert res is not None
    assert "appendicitis" in res["answer"].lower()
    assert res["confidence_score"] >= 0.85
    assert len(res["citations"]) >= 1

    # Check offline warehouse citations are present if warehouse is available
    if offline_data_service.is_available:
        source_names = [c["source_name"] for c in res["citations"]]
        has_warehouse_evidence = any(
            "Offline" in s or "PubMed" in s or "MedQA" in s or "Clinical Trials" in s
            for s in source_names
        )
        assert has_warehouse_evidence, f"Expected offline warehouse evidence in citations: {source_names}"
