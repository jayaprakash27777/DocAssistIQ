import re
import json

text = open('c:/Users/User/Downloads/DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md', encoding='utf-8').read()

# Load ground truth from grade_final_benchmark.py
from scripts.grade_final_benchmark import CLINICAL_GROUND_TRUTH

cases = list(re.finditer(r'### Case\s+(\d+)[:\s]*(.*?)(?=(?:### Case\s+\d+)|\n##\s+|\Z)', text, re.DOTALL))

print(f"Comparing {len(cases)} cases...")
for c in cases:
    cid = int(c.group(1))
    vignette = c.group(2).strip()
    tag_m = re.findall(r'\[(S\d+(?:,\s*S\d+)*)\]', vignette)
    tags = tag_m[-1] if tag_m else ""
    gt = CLINICAL_GROUND_TRUTH.get(cid, {})
    gt_target = gt.get("target", "MISSING")
    
    # Print cases that might look mismatched
    print(f"Case {cid:3d} | Tag: [{tags:10s}] | GT: {gt_target:35s} | First 100 chars: {vignette[:100].replace(chr(10), ' ')}")
