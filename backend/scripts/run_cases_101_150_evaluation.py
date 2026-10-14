import sys
import os
import re
import json
import time
import traceback

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath("backend"))

from app.services.realtime_prediction_service import realtime_prediction_service

BACKUP_FILE = r"C:\Users\User\AppData\Roaming\Antigravity IDE\Backups\948871aef134a1508654cd6b153ece61\file\27df0914"
DISK_FILE = r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md"
OUTPUT_FILE = r"c:\Users\User\Downloads\DocAssistIQ\evaluation_results_cases_101_150.json"

# Read test text
text = ""
if os.path.exists(BACKUP_FILE):
    with open(BACKUP_FILE, "r", encoding="utf-8", errors="ignore") as f:
        cand_text = f.read()
        if "150" in cand_text:
            text = cand_text
            print(f"Loaded test cases from active editor buffer ({BACKUP_FILE}).")

if not text and os.path.exists(DISK_FILE):
    with open(DISK_FILE, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
        print(f"Loaded test cases from disk file ({DISK_FILE}).")

# Regex to match all cases 101 to 150
pattern = re.compile(r"(?:###\s+)?Case\s+(\d+)\s*\n(.*?)(?=(?:(?:###\s+)?Case\s+\d+)|\n##\s+|\Z)", re.DOTALL)
cases_all = pattern.findall(text)

cases_101_150 = []
for num_str, content in cases_all:
    num = int(num_str)
    if 101 <= num <= 150:
        cases_101_150.append((num, content.strip()))

print(f"Loaded {len(cases_101_150)} cases to evaluate (Cases 101 to 150).")

all_results = []
total_start = time.perf_counter()

for idx, (case_num, content_clean) in enumerate(cases_101_150, 1):
    source_match = re.search(r"\[(S\d+)\]\s*$", content_clean)
    source_id = source_match.group(1) if source_match else ""
    text_to_test = re.sub(r"\[S\d+\]\s*$", "", content_clean).strip()

    t0 = time.perf_counter()
    try:
        res = realtime_prediction_service.predict(text_to_test)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        top_cands = res.get("top_candidates", []) or []
        primary = top_cands[0].get("disease") if top_cands else "None"
        primary_score = top_cands[0].get("score") if top_cands else 0.0
        primary_prob = top_cands[0].get("post_test_probability") if top_cands else 0.0
        primary_icd10 = top_cands[0].get("icd10") if top_cands else ""

        differentials = []
        for c in top_cands[:5]:
            differentials.append({
                "disease": c.get("disease"),
                "score": c.get("score"),
                "post_test_probability": c.get("post_test_probability"),
                "pre_test_probability": c.get("pre_test_probability"),
                "likelihood_ratio": c.get("positive_likelihood_ratio"),
                "icd10": c.get("icd10"),
                "icd11": c.get("icd11"),
                "supporting_findings": c.get("supporting_findings", [])
            })

        disc_tests = []
        for dt in (res.get("discriminative_tests") or []):
            disc_tests.append(dt.get("test_name") if isinstance(dt, dict) else str(dt))
        if not disc_tests and top_cands and top_cands[0].get("discriminative_tests"):
            for dt in top_cands[0].get("discriminative_tests", [])[:3]:
                disc_tests.append(dt.get("test_name") if isinstance(dt, dict) else str(dt))

        case_record = {
            "case_id": case_num,
            "source_id": source_id,
            "vignette": text_to_test,
            "extracted_findings": res.get("extracted_findings", []),
            "negated_findings": res.get("negated_findings", []),
            "vitals": res.get("extracted_vitals", {}),
            "labs": res.get("quantitative_labs", {}),
            "primary_prediction": primary,
            "primary_score": primary_score,
            "primary_prob": primary_prob,
            "primary_icd10": primary_icd10,
            "differentials": differentials,
            "emergency_alert": bool(res.get("emergency_alert")),
            "triage_level": res.get("triage_level"),
            "outbreak_detected": bool(res.get("outbreak_detected")),
            "outbreak_summary": res.get("outbreak_summary"),
            "discriminative_tests": disc_tests[:3],
            "differentiating_recommendation": res.get("differentiating_recommendation"),
            "latency_ms": elapsed_ms,
            "status": "COMPLETED"
        }
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        print(f"Error evaluating Case {case_num}: {e}")
        traceback.print_exc()
        case_record = {
            "case_id": case_num,
            "source_id": source_id,
            "vignette": text_to_test,
            "extracted_findings": [],
            "negated_findings": [],
            "vitals": {},
            "labs": {},
            "primary_prediction": "ERROR",
            "primary_score": 0.0,
            "primary_prob": 0.0,
            "primary_icd10": "",
            "differentials": [],
            "emergency_alert": False,
            "triage_level": "UNKNOWN",
            "outbreak_detected": False,
            "outbreak_summary": None,
            "discriminative_tests": [],
            "differentiating_recommendation": None,
            "latency_ms": elapsed_ms,
            "status": f"ERROR: {str(e)}"
        }

    all_results.append(case_record)
    print(f"[{idx}/50] Case {case_num} ({source_id}) -> Top: '{case_record['primary_prediction']}' (prob: {case_record['primary_prob']}, latency: {elapsed_ms}ms)")

total_elapsed = round(time.perf_counter() - total_start, 2)
print(f"\nCompleted evaluation of all {len(all_results)} cases in {total_elapsed} seconds.")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f"Results successfully written to {OUTPUT_FILE}")
