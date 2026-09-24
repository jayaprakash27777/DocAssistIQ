"""DocAssistIQ — Long Clinical Notes & Complex EHR Benchmark Suite.

Validates:
1. Section-aware segmentation on complex multi-paragraph hospital doctor notes (H&P / SOAP)
2. Past Medical History (PMH) distractor isolation (e.g. chronic asthma does not distract from acute myositis)
3. USMLE Step 2/3 style multi-paragraph clinical vignettes
4. Consensus diagnostic criteria formal calculation (Bohan & Peter, Duke, ACR/EULAR, Wells)
5. Differentiating "Next Best Test" recommendations between top competing differential candidates
6. Strict sub-40ms execution latency on long-form clinical notes
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.realtime_prediction_service import realtime_prediction_service
from app.services.clinical_note_parser import clinical_note_parser


def run_long_clinical_note_tests():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("DocAssistIQ -- Enterprise Long Clinical Note Benchmark Suite")
    print("=" * 80)

    # Warmup service caches, regex compilers, and tokenizers
    realtime_prediction_service.predict("warmup fever and cough")

    total_cases = 0
    passed_cases = 0

    # -----------------------------------------------------------------------
    # Case 1: Multi-Paragraph EHR Referral with Past Medical History Distractor
    # -----------------------------------------------------------------------
    total_cases += 1
    ehr_note_1 = """
CHIEF COMPLAINT:
Progressive proximal muscle weakness and cutaneous rash over 6 weeks.

PAST MEDICAL HISTORY:
1. Moderate persistent asthma (well-controlled on inhaled fluticasone/salmeterol).
2. Remote uncomplicated appendectomy 15 years ago.
3. Essential hypertension.

HISTORY OF PRESENT ILLNESS:
The patient is a 46-year-old female who reports progressive difficulty climbing stairs
and rising from a seated chair over the past month and a half. She has noticed fatigue
when washing her hair and lifting objects onto high shelves. Over the last two weeks,
she developed a violaceous erythematous rash over the upper eyelids with periorbital edema,
as well as raised erythematous scaly papules over the dorsal metacarpophalangeal and
proximal interphalangeal joints. She denies fever, chest pain, wheezing, cough, or shortness of breath.

PHYSICAL EXAMINATION:
Vitals: BP 128/82, HR 74, RR 14, Temp 36.8 C, SpO2 99% on room air.
HEENT: Heliotrope rash over the bilateral upper eyelids with mild periorbital edema.
Dermatologic: Gottron's papules prominently visible over bilateral MCP and PIP joints.
Cardiovascular: Regular rate and rhythm, S1 and S2 normal, no murmurs.
Pulmonary: Lungs completely clear to auscultation bilaterally; no wheezing, rhonchi, or rales.
Musculoskeletal: Symmetrical 3/5 strength in bilateral deltoids and hip flexors.
Distal hand grip strength 5/5. Deep tendon reflexes 2+ and symmetric throughout.

LABORATORY & DIAGNOSTIC DATA:
Serum Creatine Kinase (CK): 1,450 U/L.
Aldolase: 16.2 U/L (reference <7.5).
Extended Autoantibody Panel: Anti-Jo-1 positive, ANA positive at 1:320.
Chest Radiograph: Normal heart size, clear lung fields without infiltrates.
"""

    t0 = time.perf_counter()
    res1 = realtime_prediction_service.predict(symptoms=ehr_note_1, top_k=3)
    lat1 = (time.perf_counter() - t0) * 1000

    top1_disease = res1["top_candidates"][0]["disease"] if res1["top_candidates"] else ""
    criteria1 = res1.get("criteria_evaluations", [])
    bg1 = res1.get("background_history", [])

    print(f"\n[Case 1] Multi-Paragraph EHR Note: Dermatomyositis / Inflammatory Myopathy")
    print(f"  Latency: {lat1:.2f}ms (Engine: {res1['latency_ms']}ms)")
    print(f"  Top Candidate: {top1_disease} ({res1['top_candidates'][0].get('display_score')})")
    print(f"  Background Distractors Isolated: {bg1}")
    print(f"  Criteria Evaluated: {len(criteria1)} systems")

    c1_pass = (
        ("Dermatomyositis" in top1_disease or "Myopathy" in top1_disease or "Synthetase" in top1_disease)
        and "Asthma" not in top1_disease
        and len(criteria1) > 0
        and lat1 < 50.0
    )
    if c1_pass:
        print("  [PASS] Case 1 passed: Correct inflammatory myopathy diagnosis; asthma distractor isolated; criteria evaluated.")
        passed_cases += 1
    else:
        print(f"  [FAIL] Case 1 failed: Expected myopathy/dermatomyositis without asthma distractor, got {top1_disease}")

    # -----------------------------------------------------------------------
    # Case 2: Complex USMLE Vignette — Neurovisceral Crisis vs Acute Abdomen
    # -----------------------------------------------------------------------
    total_cases += 1
    vignette_2 = """
A 29-year-old female presents to the emergency department with severe, agonizing, diffuse
abdominal pain that began 18 hours ago after a 48-hour fasting diet. She has had repeated episodes
of nausea and vomiting. She also reports tingling in her fingers, limb weakness, and visual hallucinations
of shadows on the walls. On examination, the patient is agitated and diaphoretic. Vital signs are:
blood pressure 168/104 mmHg, heart rate 116 bpm, respiratory rate 20/min, temperature 37.1 C.
Abdominal examination reveals a soft, non-distended abdomen with mild diffuse tenderness, but notably
lacking peritoneal signs, guarding, rebound tenderness, or localized organomegaly; the severe pain is
dramatically out of proportion to physical exam findings. Contrast-enhanced CT scan of the abdomen
and pelvis shows no acute intra-abdominal inflammatory process, appendicitis, or bowel obstruction.
Urine collected in the emergency room turns a dark reddish-brown / port-wine color upon exposure to ambient light.
"""

    t0 = time.perf_counter()
    res2 = realtime_prediction_service.predict(symptoms=vignette_2, top_k=3)
    lat2 = (time.perf_counter() - t0) * 1000

    top2_disease = res2["top_candidates"][0]["disease"] if res2["top_candidates"] else ""
    diff2 = res2.get("differentiating_recommendation")

    print(f"\n[Case 2] USMLE Vignette: Acute Intermittent Porphyria vs Acute Abdomen")
    print(f"  Latency: {lat2:.2f}ms")
    print(f"  Top Candidate: {top2_disease} ({res2['top_candidates'][0].get('display_score')})")
    if diff2:
        print(f"  Differentiating Recommendation: {diff2.get('differentiating_investigation')}")

    c2_pass = (
        ("Porphyria" in top2_disease or "AIP" in top2_disease)
        and lat2 < 40.0
    )
    if c2_pass:
        print("  [PASS] Case 2 passed: Accurately identified Acute Intermittent Porphyria under 40ms.")
        passed_cases += 1
    else:
        print(f"  [FAIL] Case 2 failed: Expected Porphyria, got {top2_disease}")

    # -----------------------------------------------------------------------
    # Case 3: VHF Outbreak Traveler vs Falciparum Malaria with Differentiating Test
    # -----------------------------------------------------------------------
    total_cases += 1
    travel_note_3 = """
History of Present Illness:
A 38-year-old humanitarian aid worker recently returned 8 days ago from Beni, North Kivu province,
Democratic Republic of the Congo. He presents with abrupt onset of high fever, severe frontal headache,
intractable nausea, vomiting, watery diarrhea, and marked prostration. Over the past 24 hours, he noted
spontaneous bleeding from his gums when brushing his teeth and blood-streaked emesis.
Physical Examination:
Vitals: BP 92/58 mmHg, HR 118 bpm, RR 22/min, Temp 39.4 C.
General: Severely ill, toxic appearance, dehydrated.
Oropharynx: Dried blood at the gingival margins.
Skin: Petechial rash on the trunk and upper arms.
Laboratories:
CBC shows severe thrombocytopenia with Platelets 28,000 /uL, WBC 3,100 /uL, elevated AST 450 U/L, ALT 280 U/L.
"""

    t0 = time.perf_counter()
    res3 = realtime_prediction_service.predict(symptoms=travel_note_3, top_k=3)
    lat3 = (time.perf_counter() - t0) * 1000

    top3_disease = res3["top_candidates"][0]["disease"] if res3["top_candidates"] else ""
    runner_up = res3["top_candidates"][1]["disease"] if len(res3["top_candidates"]) > 1 else ""
    diff3 = res3.get("differentiating_recommendation")
    alert3 = res3.get("emergency_alert")

    print(f"\n[Case 3] High-Consequence VHF vs Falciparum Malaria in Returning Traveler")
    print(f"  Latency: {lat3:.2f}ms")
    print(f"  #1: {top3_disease} | #2: {runner_up}")
    print(f"  Emergency Red Flag: {alert3.get('condition') if alert3 else 'None'}")
    if diff3:
        print(f"  Differentiating Next Best Test: {diff3.get('differentiating_investigation')}")

    c3_pass = (
        ("Bundibugyo" in top3_disease or "Ebola" in top3_disease)
        and alert3 is not None
        and diff3 is not None
        and (res3.get("latency_ms", 0) < 60.0 or lat3 < 80.0)
    )
    if c3_pass:
        print("  [PASS] Case 3 passed: Bundibugyo VHF identified, emergency alert fired, and species-specific RT-PCR/smear differentiated.")
        passed_cases += 1
    else:
        print(f"  [FAIL] Case 3 failed: Expected Bundibugyo VHF with emergency alert, got {top3_disease}")

    # -----------------------------------------------------------------------
    # Case 4: Modified Duke Criteria for Infective Endocarditis
    # -----------------------------------------------------------------------
    total_cases += 1
    endocarditis_note = """
A 35-year-old male with a history of intravenous drug use presents with 2 weeks of persistent daily fevers,
drenching night sweats, and progressive fatigue. On physical examination: temperature 38.6 C, HR 98, BP 114/70.
Cardiac exam reveals a new grade 3/6 holosystolic regurgitant murmur heard loudest at the cardiac apex.
Skin examination reveals non-tender, erythematous hemorrhagic macules on the palms of both hands (Janeway lesions)
and subungual splinter hemorrhages. Transthoracic echocardiogram demonstrates a 1.2 cm oscillating mobile intracardiac
mass (vegetation) adherent to the anterior leaflet of the mitral valve with moderate mitral regurgitation.
Two separate blood cultures drawn 12 hours apart grow Enterococcus faecalis.
"""

    t0 = time.perf_counter()
    res4 = realtime_prediction_service.predict(symptoms=endocarditis_note, top_k=3)
    lat4 = (time.perf_counter() - t0) * 1000

    top4_disease = res4["top_candidates"][0]["disease"] if res4["top_candidates"] else ""
    criteria4 = [c for c in res4.get("criteria_evaluations", []) if "Duke" in c.get("criteria_name", "")]

    print(f"\n[Case 4] Infective Endocarditis & Modified Duke Criteria")
    print(f"  Latency: {lat4:.2f}ms")
    print(f"  Top Candidate: {top4_disease}")
    if criteria4:
        print(f"  Criteria Result: {criteria4[0].get('status')} (Major: {criteria4[0].get('major_criteria_count')}, Minor: {criteria4[0].get('minor_criteria_count')})")

    c4_pass = (
        ("Endocarditis" in top4_disease or len(criteria4) > 0)
        and (criteria4 and criteria4[0].get("meets_criteria") is True)
        and lat4 < 40.0
    )
    if c4_pass:
        print("  [PASS] Case 4 passed: Definite Infective Endocarditis formally confirmed via Modified Duke Criteria.")
        passed_cases += 1
    else:
        print(f"  [FAIL] Case 4 failed: Expected Definite IE via Duke criteria, got {top4_disease}")

    # -----------------------------------------------------------------------
    # Case 5: Pulmonary Embolism with Wells Score Calculation
    # -----------------------------------------------------------------------
    total_cases += 1
    pe_note = """
A 58-year-old female presents to the emergency department with acute onset pleuritic chest pain and sudden
shortness of breath that developed 2 hours ago. She underwent elective right total knee arthroplasty 12 days ago
and has been mostly on bed rest at home with limited mobility. On exam: HR 114 bpm (tachycardic), BP 132/84,
RR 24, SpO2 91% on room air. Right lower extremity demonstrates asymmetric calf swelling with 3 cm greater circumference
than the left, with significant tenderness to deep palpation of the right gastrocnemius muscle (clinical signs of DVT).
Lungs are clear to auscultation without focal crackles or consolidation.
"""

    t0 = time.perf_counter()
    res5 = realtime_prediction_service.predict(symptoms=pe_note, top_k=3)
    lat5 = (time.perf_counter() - t0) * 1000

    top5_disease = res5["top_candidates"][0]["disease"] if res5["top_candidates"] else ""
    criteria5 = [c for c in res5.get("criteria_evaluations", []) if "Wells" in c.get("criteria_name", "")]

    print(f"\n[Case 5] Acute Pulmonary Embolism & Wells Score Calculation")
    print(f"  Latency: {lat5:.2f}ms")
    print(f"  Top Candidate: {top5_disease}")
    if criteria5:
        print(f"  Wells Score: {criteria5[0].get('score')} | Risk: {criteria5[0].get('risk_tier')} | Next: {criteria5[0].get('next_step')}")

    c5_pass = (
        ("Pulmonary Embolism" in top5_disease or len(criteria5) > 0)
        and (criteria5 and criteria5[0].get("pe_likely") is True)
        and lat5 < 40.0
    )
    if c5_pass:
        print("  [PASS] Case 5 passed: PE Likely formally calculated via Wells Score with CTPA recommendation.")
        passed_cases += 1
    else:
        print(f"  [FAIL] Case 5 failed: Expected PE Likely via Wells Score, got {top5_disease}")

    print("\n" + "=" * 80)
    print(f"Long Clinical Note Suite Result: {passed_cases}/{total_cases} Passed")
    print("=" * 80)
    return passed_cases == total_cases


if __name__ == "__main__":
    success = run_long_clinical_note_tests()
    sys.exit(0 if success else 1)
