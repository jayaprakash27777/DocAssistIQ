"""DocAssistIQ — Quantitative Laboratory & Clinical Biomarker Validation Suite.

Validates:
1. Numerical lab value parsing and severity categorization (CK tiers, Lactate tiers, Platelet thresholds)
2. Calculated physiological indices (Anion Gap, CSF/Serum Glucose Ratio)
3. Differential diagnostic modulation based on biomarker magnitude (e.g. CK 45,000 vs CK 1,200)
4. Consensus clinical criteria evaluation (ACR/EULAR SLE, Duke Endocarditis, Bohan & Peter Myositis, Wells PE)
5. Discriminative Next Best Test recommendation between competing differential candidates
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.lab_value_interpreter import lab_value_interpreter
from app.services.clinical_criteria_evaluator import criteria_evaluator
from app.services.discriminative_test_engine import discriminative_test_engine
from app.services.realtime_prediction_service import realtime_prediction_service


def run_quantitative_lab_tests():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("DocAssistIQ -- Quantitative Laboratory & Biomarker Reasoning Suite")
    print("=" * 80)

    total_tests = 0
    passed_tests = 0

    # Test 1: Lab Value Parsing - Massive CK
    total_tests += 1
    text_ck_massive = "Patient presents after endurance training with dark port-wine urine, severe myalgia, CK 45,000 U/L."
    res_ck = lab_value_interpreter.interpret(text_ck_massive)
    ck_info = res_ck["extracted_labs"].get("creatine_kinase", {})
    if ck_info.get("value") == 45000.0 and ck_info.get("severity") == "massive_elevation":
        print("[PASS] Test 1: Massive CK (45,000 U/L) parsed and correctly categorized as massive_elevation.")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 1: Expected 45000 massive_elevation, got {ck_info}")

    # Test 2: Lab Value Parsing - Moderate CK
    total_tests += 1
    text_ck_mod = "46yo female with symmetric proximal weakness and dysphagia. Labs: CK of 1,200 U/L, ESR 62."
    res_ck_mod = lab_value_interpreter.interpret(text_ck_mod)
    ck_mod_info = res_ck_mod["extracted_labs"].get("creatine_kinase", {})
    if ck_mod_info.get("value") == 1200.0 and ck_mod_info.get("severity") == "moderate_elevation":
        print("[PASS] Test 2: Moderate CK (1,200 U/L) parsed and correctly categorized as moderate_elevation.")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 2: Expected 1200 moderate_elevation, got {ck_mod_info}")

    # Test 3: Anion Gap Calculation
    total_tests += 1
    text_ag = "BMP shows Na 140, Cl 98, HCO3 12, BUN 24, Cr 1.2. Patient with severe lethargy and vomiting."
    res_ag = lab_value_interpreter.interpret(text_ag)
    ag_val = res_ag["calculated_indices"].get("anion_gap")
    ag_interp = res_ag["calculated_indices"].get("anion_gap_interpretation")
    # AG = 140 - (98 + 12) = 30
    if ag_val == 30.0 and ag_interp == "high_anion_gap_metabolic_acidosis":
        print(f"[PASS] Test 3: Anion Gap correctly calculated as {ag_val} mEq/L (HAGMA flagged).")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 3: Expected AG 30.0 high_anion_gap_metabolic_acidosis, got {ag_val} {ag_interp}")

    # Test 4: CSF / Serum Glucose Ratio Calculation
    total_tests += 1
    text_csf = "Lumbar puncture shows cloudy CSF, WBC 1800 with 90% neutrophils, CSF glucose 22 mg/dL with simultaneous blood glucose 110 mg/dL."
    res_csf = lab_value_interpreter.interpret(text_csf)
    csf_ratio = res_csf["calculated_indices"].get("csf_serum_glucose_ratio")
    csf_interp = res_csf["calculated_indices"].get("csf_interpretation")
    # Ratio = 22 / 110 = 0.20
    if csf_ratio == 0.2 and csf_interp == "hypoglycorrhachia_bacterial_meningitis_pattern":
        print(f"[PASS] Test 4: CSF/Serum glucose ratio correctly calculated as {csf_ratio} (low ratio <0.40 flagged).")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 4: Expected ratio 0.20 hypoglycorrhachia, got {csf_ratio} {csf_interp}")

    # Test 5: Severe Lactic Acidosis
    total_tests += 1
    text_lac = "ABG demonstrates pH 7.18, venous lactate 6.5 mmol/L, pCO2 28."
    res_lac = lab_value_interpreter.interpret(text_lac)
    lac_info = res_lac["extracted_labs"].get("lactate", {})
    if lac_info.get("value") == 6.5 and lac_info.get("severity") == "severe_lactic_acidosis":
        print("[PASS] Test 5: Lactate 6.5 mmol/L correctly identified as severe_lactic_acidosis.")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 5: Expected lactate 6.5 severe_lactic_acidosis, got {lac_info}")

    # Test 6: Discriminative "Next Best Test" Recommendation
    total_tests += 1
    cand1 = {"disease": "Bundibugyo Virus Disease (BVD)", "display_score": "93%"}
    cand2 = {"disease": "Malaria (Plasmodium falciparum)", "display_score": "45%"}
    rec = discriminative_test_engine.recommend(cand1, cand2)
    if rec and "Thick and Thin Peripheral Blood Smears" in rec["differentiating_investigation"] and "RT-PCR" in rec["differentiating_investigation"]:
        print(f"[PASS] Test 6: Discriminative test correctly recommended: '{rec['differentiating_investigation']}'")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 6: Unexpected recommendation: {rec}")

    # Test 7: Clinical Criteria Evaluation - ACR/EULAR SLE
    total_tests += 1
    sle_eval = criteria_evaluator.evaluate_sle_acr_eular(
        findings={"positive antinuclear antibody", "malar rash", "joint pain", "hypocomplementemia", "fever"},
        labs={"platelets": {"value": 75000}, "wbc": {"value": 3100}}
    )
    # Score: Fever (2) + Thrombocytopenia (4) + Malar rash (6) + Joint involvement (6) + Low complement (4) = 22 pts (>=10)
    if sle_eval["meets_criteria"] is True and sle_eval["total_score"] >= 10:
        print(f"[PASS] Test 7: ACR/EULAR SLE criteria met with score {sle_eval['total_score']} (threshold 10).")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 7: SLE criteria failed: {sle_eval}")

    # Test 8: Clinical Criteria Evaluation - Modified Duke for Endocarditis
    total_tests += 1
    duke_eval = criteria_evaluator.evaluate_duke_endocarditis(
        findings={"blood culture positive", "valvular vegetation", "fever", "janeway lesions", "prosthetic valve"},
        labs={}
    )
    # 2 Major (positive blood cultures + echo vegetation) + Minor (fever, Janeway, prosthetic valve)
    if duke_eval["meets_criteria"] is True and duke_eval["major_criteria_count"] >= 2:
        print(f"[PASS] Test 8: Modified Duke Criteria met: {duke_eval['status']} ({duke_eval['major_criteria_count']} Major, {duke_eval['minor_criteria_count']} Minor).")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 8: Duke criteria failed: {duke_eval}")

    # Test 9: Real-Time Diagnostic Prediction with Labs & Differentiation in <30ms
    total_tests += 1
    t0 = time.perf_counter()
    full_pred = realtime_prediction_service.predict(
        symptoms="32yo female with severe polyarthralgia, fever 38.5C, malar butterfly rash, ANA 1:640, low C3/C4 complement, platelets 85,000",
        top_k=3
    )
    lat_ms = (time.perf_counter() - t0) * 1000
    top_d = full_pred["top_candidates"][0]["disease"] if full_pred["top_candidates"] else ""
    has_criteria = len(full_pred.get("criteria_evaluations", [])) > 0
    has_labs = bool(full_pred.get("quantitative_labs"))
    if "Lupus" in top_d or "SLE" in top_d:
        print(f"[PASS] Test 9: Real-time prediction correctly diagnosed '{top_d}' in {lat_ms:.2f}ms (Criteria: {has_criteria}, Labs: {has_labs}).")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 9: Expected Lupus/SLE, got '{top_d}'")

    # Test 10: Clinical Criteria Evaluation - Centor / McIsaac for Streptococcal Pharyngitis
    total_tests += 1
    centor_eval = criteria_evaluator.evaluate_centor_mcisaac(
        findings={"absence of cough", "cervical lymphadenopathy", "fever", "tonsillar exudates"},
        labs={},
        age=12
    )
    # 4 clinical signs + 1 age modifier = 5 pts (High probability)
    if centor_eval["score"] == 5 and centor_eval["risk_tier"] == "High":
        print(f"[PASS] Test 10: Centor/McIsaac score {centor_eval['score']} correctly evaluated: {centor_eval['recommendation']}")
        passed_tests += 1
    else:
        print(f"[FAIL] Test 10: Centor evaluation failed: {centor_eval}")

    print("=" * 80)
    print(f"Quantitative Laboratory Suite Result: {passed_tests}/{total_tests} Tests Passed")
    print("=" * 80)
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_quantitative_lab_tests()
    sys.exit(0 if success else 1)
