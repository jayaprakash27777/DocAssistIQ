import re

text = open('c:/Users/User/Downloads/DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md', encoding='utf-8').read()

# Build map of S-tags to references
ref_map = {}
for m in re.finditer(r'\*\*(S\d+)\*\*\s*[–—\-]?\s*\[(.*?)\]', text):
    ref_map[m.group(1)] = m.group(2)

print(f"Loaded {len(ref_map)} references.")

cases = list(re.finditer(r'### Case\s+(\d+)[:\s]*(.*?)(?=(?:### Case\s+\d+)|\Z)', text, re.DOTALL))
print(f"Found {len(cases)} cases.")

for c in cases[:25]:
    cid = int(c.group(1))
    c_text = c.group(2).strip()
    tags = re.findall(r'\[(S\d+(?:,\s*S\d+)*)\]', c_text)
    tag_list = []
    if tags:
        for t in tags[-1].split(','):
            tag_list.append(t.strip())
    ref_descs = [f"{t}: {ref_map.get(t, 'Unknown')}" for t in tag_list]
    print(f"Case {cid:2d} | Tags: {tag_list} | Ref: {ref_descs}")
