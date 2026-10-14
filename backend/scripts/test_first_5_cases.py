import sys
import os
import re
import json
import time

sys.path.insert(0, os.path.abspath("backend"))

from app.services.realtime_prediction_service import realtime_prediction_service
from app.services.clinical_note_parser import clinical_note_parser

# Read the test cases file
TEST_FILE = r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md"

with open(TEST_FILE, "r", encoding="utf-8") as f:
    text = f.read()

cases_raw = re.findall(r"###\s+Case\s+(\d+)\s*\n(.*?)(?=(?:###\s+Case\s+\d+)|\n##\s+|\Z)", text, re.DOTALL)
print(f"Parsed {len(cases_raw)} test cases from markdown.")

results = []
for num_str, content in cases_raw[:5]:
    case_num = int(num_str)
    content_clean = content.strip()
    
    # Extract source tag e.g. [S90]
    source_match = re.search(r"\[(S\d+)\]\s*$", content_clean)
    source_id = source_match.group(1) if source_match else ""
    text_to_test = re.sub(r"\[S\d+\]\s*$", "", content_clean).strip()

    t0 = time.perf_counter()
    res = realtime_prediction_service.predict(text_to_test)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    top_cands = res.get("top_candidates", []) or []
    primary = top_cands[0].get("disease") if top_cands else "None"
    top_diffs = [c.get("disease") for c in top_cands[:5]]

    print(f"\n--- CASE {case_num} ({source_id}) --- [{elapsed_ms} ms]")
    print(f"Query findings: {res.get('extracted_findings', [])}")
    print(f"Primary: {primary}")
    print(f"Differentials: {top_diffs}")
    print(f"Emergency Alert: {res.get('emergency_alert')}")

print("\nSmoke test for first 5 cases passed successfully.")
