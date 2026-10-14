import re
import json

text = open('c:/Users/User/Downloads/DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md', encoding='utf-8').read()

ref_map = {}
for m in re.finditer(r'\*\*(S\d+)\*\*\s*[–—\-]?\s*\[(.*?)\]\((.*?)\)', text):
    ref_map[m.group(1)] = {"desc": m.group(2), "url": m.group(3)}

cases = list(re.finditer(r'### Case\s+(\d+)[:\s]*(.*?)(?=(?:### Case\s+\d+)|\n##\s+|\Z)', text, re.DOTALL))

print(f"Total cases: {len(cases)}")
verified_cases = []

for c in cases:
    cid = int(c.group(1))
    v = c.group(2).strip()
    tag_m = re.findall(r'\[(S\d+(?:,\s*S\d+)*)\]', v)
    tags = [t.strip() for t in tag_m[-1].split(',')] if tag_m else []
    ref_info = [ref_map.get(t, {}) for t in tags]
    
    verified_cases.append({
        "case_id": cid,
        "tags": tags,
        "ref_info": ref_info,
        "vignette": v
    })

print(f"Loaded {len(verified_cases)} cases with references.")
