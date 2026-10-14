import re

text = open('c:/Users/User/Downloads/DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md', encoding='utf-8').read()

# Look for table or source list
tags = ['S95', 'S96', 'S36', 'S07', 'S25', 'S111', 'S15', 'S55', 'S58', 'S61', 'S108', 'S117', 'S68', 'S69', 'S13', 'S78']

for t in tags:
    m = re.search(rf'\[{t}\][\s:–-]+(.*?)(?=\n\[|\Z)', text)
    if m:
        print(f"[{t}]: {m.group(1).strip()[:100]}")
    else:
        # try markdown table or other format
        m2 = re.search(rf'\|\s*{t}\s*\|(.*?)\n', text)
        if m2:
            print(f"| {t} |: {m2.group(1).strip()[:100]}")
        else:
            print(f"[{t}]: Not found directly")
