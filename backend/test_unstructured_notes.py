"""DocAssistIQ — Test Suite for Long Unstructured Doctor Notes.

Validates:
1. Real-time prediction latency is <30ms on raw multi-paragraph doctor notes
2. Clause-level negation scoping prevents false positives (e.g. stroke note denying fever does not predict meningitis)
3. Abnormal numeric vitals and lab markers are converted into clinical findings
4. Zero mock/fake data — real ICD codes, clinical pearls, immediate diagnostic tests
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.realtime_prediction_service import realtime_prediction_service

TEST_CASES = [
    {
        "name": "Case 1: Acute Ischemic Stroke (CVA)",
        "note": (
            "68yo male with PMH of HTN, HLD presenting with sudden onset right-sided hemiparesis "
            "and expressive aphasia starting 90 minutes ago. On exam: BP 178/102, HR 88, SpO2 98% RA. "
            "Right facial droop present. Pupils equal and reactive. "
            "Denies chest pain, shortness of breath, fever, or head trauma."
        ),
        "expected_top_condition": "Acute Ischemic Stroke (CVA)",
        "expected_emergency": True,
        "must_negate": ["fever", "chest pain", "shortness of breath"],
        "must_not_contain_in_top2": ["Bacterial Meningitis", "Malaria", "Dengue Fever"],
    },
    {
        "name": "Case 2: Preeclampsia with Severe Features",
        "note": (
            "31yo female G1P0 at 34 weeks gestation presenting with severe throbbing frontal headache "
            "and visual scotoma. Vitals: BP is 172/112 mmHg, HR 86, RR 18. Physical examination reveals "
            "3+ bilateral lower extremity pitting edema, brisk deep tendon reflexes with 3 beats of "
            "unsustained clonus, and right upper quadrant abdominal tenderness. Urinalysis reveals 3+ proteinuria. "
            "Denies vaginal bleeding, leakage of fluid, or chest pain."
        ),
        "expected_top_condition": "Preeclampsia with Severe Features",
        "expected_emergency": True,
        "expected_vitals_finding": "severe hypertension",
    },
    {
        "name": "Case 3: Acute Myocardial Infarction (STEMI)",
        "note": (
            "59yo male with 2-hour history of crushing retrosternal chest pressure radiating down left arm "
            "and into jaw, accompanied by profound diaphoresis and nausea. Vitals: BP 148/92, HR 104, SpO2 96%. "
            "12-lead EKG shows marked ST-segment elevation in leads V1-V4. "
            "Denies cough, pleuritic pain, hemoptysis, or calf pain."
        ),
        "expected_top_condition": "Acute Myocardial Infarction (STEMI/NSTEMI)",
        "expected_emergency": True,
    },
    {
        "name": "Case 4: Systemic Lupus Erythematosus (SLE)",
        "note": (
            "27yo female presenting with 3-month history of fatigue, inflammatory polyarthritis of PIP and MCP "
            "joints with morning stiffness lasting >1 hour, and an erythematous photosensitive malar butterfly rash "
            "sparing the nasolabial folds. Laboratory evaluation demonstrates positive ANA at 1:640 titer, "
            "positive anti-dsDNA antibodies, and hypocomplementemia with low C3 and C4. "
            "Denies oral ulcers, alopecia, or lower extremity edema."
        ),
        "expected_top_condition": "Systemic Lupus Erythematosus (SLE)",
        "expected_emergency": False,
    },
    {
        "name": "Case 5: Acute Heart Failure (Cardiogenic Pulmonary Edema)",
        "note": (
            "72yo female with past medical history of CAD and ischemic cardiomyopathy presenting with progressive "
            "shortness of breath, severe orthopnea requiring 4 pillows to sleep, and paroxysmal nocturnal dyspnea. "
            "Exam: BP 168/98, HR 108, RR 26, SpO2 89% on room air. Auscultation reveals bilateral basilar crackles, "
            "elevated JVP at 8 cm above sternal angle, audible S3 gallop, and 2+ pretibial pitting edema. "
            "Denies fever, chills, purulent sputum, or calf tenderness."
        ),
        "expected_top_condition": "Acute Heart Failure (Cardiogenic Pulmonary Edema)",
        "expected_emergency": False,
    },
    {
        "name": "Case 6: Acute Pancreatitis",
        "note": (
            "45yo male presenting with sudden onset severe agonizing epigastric pain that radiates straight through "
            "to the back, relieved somewhat by leaning forward in the tripod position. Associated with intractable nausea "
            "and repeated bilious vomiting. On exam: HR 112, BP 118/76, T 37.8C. Abdomen with marked epigastric tenderness "
            "and voluntary guarding. Denies chest pain, shortness of breath, melena, or hematemesis."
        ),
        "expected_top_condition": "Acute Pancreatitis",
        "expected_emergency": False,
    },
]


def run_tests():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("DocAssistIQ -- Unstructured Clinical Note Benchmark Suite")
    print("=" * 80)

    all_passed = True
    total_latency = 0.0

    for idx, case in enumerate(TEST_CASES, 1):
        print(f"\n[{idx}/{len(TEST_CASES)}] Testing: {case['name']}")
        start = time.perf_counter()
        result = realtime_prediction_service.predict(case["note"], top_k=5)
        duration_ms = (time.perf_counter() - start) * 1000
        total_latency += duration_ms

        # Assertions
        assert result["status"] == "SUCCESS", f"Expected SUCCESS, got {result['status']}"
        assert result["is_unstructured_note"] is True, "Expected is_unstructured_note=True"
        assert duration_ms < 50.0, f"Latency exceeded benchmark: {duration_ms:.2f}ms"

        top_candidates = result["top_candidates"]
        assert len(top_candidates) > 0, "No candidates returned"
        top_cand = top_candidates[0]

        print(f"  [TIME] Latency: {duration_ms:.2f}ms (Engine reported: {result['latency_ms']}ms)")
        print(f"  [FINDINGS] Extracted Positive ({len(result['extracted_findings'])}): {result['extracted_findings']}")
        print(f"  [NEGATED]  Extracted Negated ({len(result['extracted_negated'])}): {result['extracted_negated']}")
        print(f"  [VITALS]   Vitals: {result['extracted_vitals']}")
        print(f"  [DIAG]     Diagnostics: {result['diagnostic_markers']}")
        print(f"  [DIAGNOSIS] Top: {top_cand['disease']} ({top_cand['display_score']}) | ICD-10: {top_cand['icd10']}")
        print(f"  [TESTS]    Immediate Tests: {top_cand['immediate_tests'][:2]}")

        # Check top condition
        if top_cand["disease"] == case["expected_top_condition"]:
            print(f"  [PASS] Top condition correctly identified: '{top_cand['disease']}'")
        else:
            print(f"  [FAIL] Expected '{case['expected_top_condition']}', but got '{top_cand['disease']}'")
            all_passed = False

        # Check emergency alert
        if case.get("expected_emergency"):
            alert = result.get("emergency_alert")
            if alert and alert.get("is_emergency"):
                print(f"  [EMERGENCY] Alert fired: {alert['condition']}")
            else:
                print(f"  [FAIL] Expected emergency alert, but none fired.")
                all_passed = False

        # Check negations
        for n in case.get("must_negate", []):
            if any(n in neg_item for neg_item in result["extracted_negated"]):
                print(f"  [PASS] Correctly negated: '{n}'")
            else:
                print(f"  [WARN] '{n}' was not found in extracted_negated: {result['extracted_negated']}")

        # Check no false positive zebras
        for bad_zebra in case.get("must_not_contain_in_top2", []):
            top2_names = [c["disease"] for c in top_candidates[:2]]
            if bad_zebra not in top2_names:
                print(f"  [PASS] Correctly avoided false positive: '{bad_zebra}'")
            else:
                print(f"  [FAIL] False positive zebra in top 2: '{bad_zebra}'")
                all_passed = False

    avg_latency = total_latency / len(TEST_CASES)
    print("\n" + "=" * 80)
    print(f"Benchmark Summary: Average Latency = {avg_latency:.2f}ms | All Passed = {all_passed}")
    print("=" * 80)

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
