import re
import sys
import os
import json

sys.path.insert(0, os.path.abspath("backend"))

from scripts.verified_clinical_ground_truth import CLINICAL_GROUND_TRUTH_100
from app.services.clinical_note_parser import clinical_note_parser
from app.services.realtime_prediction_service import realtime_prediction_service
from app.services.global_disease_matrix_service import global_disease_matrix_service
from app.services.master_disease_catalog import master_disease_catalog

RESULTS_FILE = r"c:\Users\User\Downloads\DocAssistIQ\evaluation_results_100_cases.json"
TEST_FILE = r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md"

with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    results = json.load(f)

with open(TEST_FILE, "r", encoding="utf-8") as f:
    cases_text = f.read()

cases_raw = dict(re.findall(r"###\s+Case\s+(\d+)\s*\n(.*?)(?=(?:###\s+Case\s+\d+)|\n##\s+|\Z)", cases_text, re.DOTALL))

with open(r"c:\Users\User\Downloads\DocAssistIQ\clinical_evaluation_graded_final.json", "r", encoding="utf-8") as f:
    graded = json.load(f)

misses = [g for g in graded if not g["is_top5"]]
print(f"Total misses to diagnose: {len(misses)}")

for m in misses[10:]:
    cid = m["case_id"]
    target = m["target"]
    syns = m["synonyms"]
    vig = cases_raw.get(str(cid), "").strip()
    p = clinical_note_parser.parse(vig)
    pos = p.get("positive_findings", [])
    
    # Check catalog search
    cat_hits = master_disease_catalog.match_symptoms(pos, top_k=20)
    cat_names = [h["disease"] for h in cat_hits]
    
    # Check if target is in cat_names
    target_in_cat = any(target.lower() in cn.lower() or any(s.lower() in cn.lower() for s in syns) for cn in cat_names)
    
    print(f"\nCase {cid} ({m['specialty']}): Target='{target}'")
    print(f"  Vignette snippet: {vig[:120]}...")
    print(f"  Parsed findings: {pos}")
    print(f"  Top-1 returned: '{m['top1']}' | Diffs: {m['diffs'][:3]}")
    print(f"  Target in top 20 catalog hits: {target_in_cat} (Top 5 cat hits: {cat_names[:5]})")
