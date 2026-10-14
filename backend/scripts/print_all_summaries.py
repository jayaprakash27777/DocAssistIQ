import json
import re

RESULTS_FILE = r"c:\Users\User\Downloads\DocAssistIQ\evaluation_results_100_cases.json"
TEST_FILE = r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md"

with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    results = json.load(f)

with open(TEST_FILE, "r", encoding="utf-8") as f:
    md_text = f.read()

idx = md_text.find("## Source register")
lines = md_text[idx:].split("\n")
source_map = {}
for line in lines:
    m = re.search(r"\*\*(S\d+)\*\*.*?\[(.*?)\]\((.*?)\)", line)
    if m:
        source_map[m.group(1)] = {"title": m.group(2), "url": m.group(3)}

for r in results:
    cid = r["case_id"]
    sid = r.get("source_id", "")
    src = source_map.get(sid, {})
    top1 = r.get("primary_prediction")
    diffs = [d["disease"] for d in r.get("differentials", [])]
    findings = r.get("extracted_findings", [])
    vignette = r.get("vignette", "")
    
    # Print clean summary line
    print(f"CASE {cid:03d} [{sid:4s}] | Top-1: {top1} | Diffs: {diffs[:4]}")
