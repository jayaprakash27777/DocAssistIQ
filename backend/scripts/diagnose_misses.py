import sys
import os
import json
import re

sys.path.insert(0, os.path.abspath("backend"))

from app.services.clinical_note_parser import clinical_note_parser
from app.services.global_disease_matrix_service import global_disease_matrix_service
from app.services.bayesian_diagnostic_engine import bayesian_diagnostic_engine
from app.services.realtime_prediction_service import realtime_prediction_service

with open(r"c:\Users\User\Downloads\DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md", encoding="utf-8") as f:
    text = f.read()

cases = re.findall(r"### Case (\d+)(.*?)(?=### Case|\Z)", text, re.DOTALL)
case_dict = {int(num): content.strip() for num, content in cases}

test_cids = [5, 15, 21, 32, 36, 84, 85]
keywords = {
    5: "lupus",
    15: "leishman",
    21: "melioid",
    32: "ornithine",
    36: "neuromyelitis",
    84: "erdheim",
    85: "adrenoleuko"
}

for cid in test_cids:
    c_text = case_dict[cid]
    c_text_clean = re.sub(r"\[S\d+\]", "", c_text)
    parsed = clinical_note_parser.parse(c_text_clean)
    findings = parsed["positive_findings"]
    pred = realtime_prediction_service.predict(c_text_clean)
    top_cands = pred.get("top_candidates", [])
    top1 = top_cands[0].get("disease") if top_cands else "None"
    diffs = [d.get("disease") for d in top_cands[:5]]
    
    kw = keywords[cid]
    cands = global_disease_matrix_service.search_candidates(symptoms=findings, top_k=60)
    cand_matches = [c["disease"] for c in cands if kw in c["disease"].lower()]
    
    print(f"==================================================")
    print(f"Case {cid} | Keyword: {kw}")
    print(f"Findings ({len(findings)}): {findings}")
    print(f"Matrix Candidates with '{kw}': {cand_matches}")
    print(f"Top 1: {top1}")
    print(f"Diffs: {diffs[:5]}")
