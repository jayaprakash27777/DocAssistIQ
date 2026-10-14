import json

with open(r"c:\Users\User\Downloads\DocAssistIQ\clinical_evaluation_graded.json", "r", encoding="utf-8") as f:
    graded = json.load(f)

with open(r"c:\Users\User\Downloads\DocAssistIQ\evaluation_results_100_cases.json", "r", encoding="utf-8") as f:
    raw_eval = {r["case_id"]: r for r in json.load(f)}

failures = [g for g in graded if not g["is_top5"]]
print(f"Total cases needing remediation / outside Top-5: {len(failures)}")

for f in failures:
    cid = f["case_id"]
    raw = raw_eval[cid]
    print(f"\n--- CASE {cid} --- Target: {f['target']} ({f['specialty']})")
    print(f"  DocAssistIQ Top-1: {f['top1']}")
    print(f"  Differentials: {f['diffs']}")
    print(f"  Extracted Findings: {raw.get('extracted_findings')}")
    print(f"  Extracted Negations: {raw.get('negated_findings')}")
    print(f"  Labs: {raw.get('labs')}")
    print(f"  Vignette snippet: {raw.get('vignette')[:180]}...")
