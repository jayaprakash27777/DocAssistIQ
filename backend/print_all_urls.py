import re
import json

text = open('c:/Users/User/Downloads/DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md', encoding='utf-8').read()

ref_map = {}
for m in re.finditer(r'\*\*(S\d+)\*\*\s*[–—\-]?\s*\[(.*?)\]\((.*?)\)', text):
    ref_map[m.group(1)] = {"desc": m.group(2), "url": m.group(3)}

cases = list(re.finditer(r'### Case\s+(\d+)[:\s]*(.*?)(?=(?:### Case\s+\d+)|\n##\s+|\Z)', text, re.DOTALL))

for c in cases[:48]:
    cid = int(c.group(1))
    v = c.group(2).strip()
    tag_m = re.findall(r'\[(S\d+(?:,\s*S\d+)*)\]', v)
    tags = [t.strip() for t in tag_m[-1].split(',')] if tag_m else []
    urls = [ref_map.get(t, {}).get("url", "") for t in tags]
    descs = [ref_map.get(t, {}).get("desc", "") for t in tags]
    print(f"Case {cid:3d}: tags={tags} urls={urls} descs={descs}")
