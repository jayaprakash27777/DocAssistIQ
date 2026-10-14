import json
import re
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath("backend"))

from scripts.verified_clinical_ground_truth import CLINICAL_GROUND_TRUTH_100

RESULTS_FILE = r"c:\Users\User\Downloads\DocAssistIQ\evaluation_results_100_cases.json"
TEST_FILE = r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md"

with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    results = json.load(f)

def clean_name(s):
    return re.sub(r"[^a-zA-Z0-9]", "", str(s)).lower()

top1_count = 0
top3_count = 0
top5_count = 0
match_results = []

GENERIC_MEDICAL_STOPWORDS = {
    "acute", "chronic", "syndrome", "disease", "disorder", "infection",
    "deficiency", "crisis", "type", "mellitus", "severe", "fever",
    "secondary", "primary", "recurrent", "progressive", "mild", "systemic", "adult"
}

def matches_target(pred, targets):
    p_clean = clean_name(pred)
    if not p_clean:
        return False
    for t in targets:
        t_clean = clean_name(t)
        if not t_clean:
            continue
        # Direct exact or substring match
        if p_clean in t_clean or t_clean in p_clean:
            return True
        # Discriminative token match (excluding generic medical stopwords)
        tokens = [clean_name(w) for w in t.split() if len(w) > 3 and clean_name(w) not in GENERIC_MEDICAL_STOPWORDS]
        if tokens and any(tok in p_clean for tok in tokens):
            return True
    return False

for r in results:
    cid = r["case_id"]
    target_info = CLINICAL_GROUND_TRUTH_100.get(cid, {"target": "Unknown", "synonyms": [], "specialty": "General"})
    target = target_info["target"]
    synonyms = target_info.get("synonyms", [])
    all_valid = [target] + synonyms

    top1 = r.get("primary_prediction", "")
    diffs = [d["disease"] for d in r.get("differentials", [])]

    is_top1 = matches_target(top1, all_valid)
    is_top3 = is_top1 or any(matches_target(d, all_valid) for d in diffs[:3])
    is_top5 = is_top3 or any(matches_target(d, all_valid) for d in diffs[:5])

    if is_top1:
        top1_count += 1
    if is_top3:
        top3_count += 1
    if is_top5:
        top5_count += 1

    match_results.append({
        "case_id": cid,
        "specialty": target_info["specialty"],
        "target": target,
        "synonyms": synonyms,
        "top1": top1,
        "diffs": diffs[:5],
        "is_top1": is_top1,
        "is_top3": is_top3,
        "is_top5": is_top5,
        "findings": r.get("extracted_findings", []),
        "latency_ms": r.get("latency_ms", 0)
    })

print(f"==================================================")
print(f"--- CLINICAL BENCHMARK METRICS AFTER ENHANCEMENTS ---")
print(f"Top-1 Diagnostic Accuracy: {top1_count}/100 ({top1_count}%)")
print(f"Top-3 Differential Inclusion: {top3_count}/100 ({top3_count}%)")
print(f"Top-5 Differential Concordance: {top5_count}/100 ({top5_count}%)")
print(f"==================================================")

with open(r"c:\Users\User\Downloads\DocAssistIQ\clinical_evaluation_graded_final.json", "w", encoding="utf-8") as f:
    json.dump(match_results, f, indent=2)

misses = [m for m in match_results if not m["is_top5"]]
print(f"Total cases not in Top-5: {len(misses)}")
for m in misses:
    print(f"  Case {m['case_id']}: Target={m['target']} | Top-1={m['top1']} | Diffs={m['diffs']}")
