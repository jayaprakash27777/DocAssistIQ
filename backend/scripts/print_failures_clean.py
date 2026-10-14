import json

with open(r"c:\Users\User\Downloads\DocAssistIQ\clinical_evaluation_graded.json", "r", encoding="utf-8") as f:
    graded = json.load(f)
with open(r"c:\Users\User\Downloads\DocAssistIQ\evaluation_results_100_cases.json", "r", encoding="utf-8") as f:
    raw_eval = {r["case_id"]: r for r in json.load(f)}

failures = [g for g in graded if not g["is_top5"]]
print(f"Total outside Top-5: {len(failures)}")
for f in failures[:15]:
    cid = f["case_id"]
    raw = raw_eval[cid]
    print(f"Case {cid}: Target={f['target']} | DocAssistIQ Top-1={f['top1']} | Diffs={f['diffs'][:3]}")
    print(f"   Findings: {raw.get('extracted_findings', [])}")
    print(f"   Vignette: {raw.get('vignette')[:140]}...")
