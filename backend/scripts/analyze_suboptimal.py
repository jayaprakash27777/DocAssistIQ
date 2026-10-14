import json
import re

RESULTS_FILE = r"c:\Users\User\Downloads\DocAssistIQ\evaluation_results_100_cases.json"
TEST_FILE = r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md"

with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    results = json.load(f)

with open(TEST_FILE, "r", encoding="utf-8") as f:
    md_text = f.read()

# Map source descriptions
src_entries = re.findall(r"-\s+\*\*(S\d+)\*\*\s+[\u2013\-]\s+\[(.*?)\]\((.*?)\)", md_text)
source_map = {s[0]: {"title": s[1], "url": s[2]} for s in src_entries}

print(f"Total results: {len(results)}")
print(f"Total mapped sources: {len(source_map)}")

# Let's inspect cases that might have unexpected top predictions
# e.g., 'Heart Attack' or 'Heroin' or generic terms
unexpected = []
for r in results:
    cid = r["case_id"]
    top1 = r.get("primary_prediction", "")
    diffs = [d["disease"] for d in r.get("differentials", [])]
    findings = r.get("extracted_findings", [])
    vignette = r.get("vignette", "")
    sid = r.get("source_id", "")
    
    # Flags for unexpected / generic top1
    is_suspicious = False
    if top1 in ["Heart Attack", "Heroin", "Edema", "liver disease", "Itching", "Artritis reumatoide"]:
        is_suspicious = True
    elif "Malaria" in top1 and "malaria" not in vignette.lower() and "fever" not in [f.lower() for f in findings]:
        is_suspicious = True
        
    if is_suspicious:
        unexpected.append({
            "case_id": cid,
            "source_id": sid,
            "source_title": source_map.get(sid, {}).get("title", ""),
            "top1": top1,
            "diffs": diffs[:4],
            "findings": findings[:6],
            "vignette": vignette[:150]
        })

print(f"\nSuspicious/Suboptimal Top-1 cases identified: {len(unexpected)}")
for u in unexpected[:15]:
    print(f"Case {u['case_id']} [{u['source_id']}]: Top-1={u['top1']} | Diffs={u['diffs']} | Findings={u['findings']}")
    print(f"   Vignette: {u['vignette']}...")
    print(f"   Source info: {u['source_title']}")
