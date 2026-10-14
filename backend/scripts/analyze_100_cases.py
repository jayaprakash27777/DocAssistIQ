import json
import os
import re

RESULTS_FILE = r"c:\Users\User\Downloads\DocAssistIQ\evaluation_results_100_cases.json"
TEST_FILE = r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md"

with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    results = json.load(f)

with open(TEST_FILE, "r", encoding="utf-8") as f:
    md_text = f.read()

# Extract source descriptions
sources = dict(re.findall(r"-\s+\*\*(S\d+)\*\*\s+[\u2013\-]\s+\[(.*?)\]\((.*?)\)", md_text))

print(f"Loaded {len(results)} evaluated cases.")
print(f"Loaded {len(sources)} source descriptions.")

# Let's inspect each case: case_id, vignette snippet, primary prediction, differentials, and findings
for r in results:
    cid = r["case_id"]
    sid = r.get("source_id", "")
    src_title = sources.get(sid, "N/A")
    primary = r.get("primary_prediction")
    diffs = [d["disease"] for d in r.get("differentials", [])]
    findings = r.get("extracted_findings", [])
    vignette = r.get("vignette", "")[:120].replace("\n", " ")
    print(f"Case {cid:3d} [{sid:4s}] | Top-1: {primary:<35} | Diffs: {', '.join(diffs[:3])} | Findings: {findings[:4]}")
