import re

text = open('c:/Users/User/Downloads/DocAssistIQ_100_Symptom_to_Disease_Test_Cases.md', encoding='utf-8').read()

# Let's inspect cases around 60-75
matches = list(re.finditer(r'### Case\s+(\d+)[:\s]*(.*?)(?=(?:### Case\s+\d+)|\Z)', text, re.DOTALL))
print(f"Found {len(matches)} cases in markdown")

for m in matches:
    cid = int(m.group(1))
    if cid in [6, 7, 22, 24, 39, 49, 56, 61, 64, 66, 71, 73, 74, 83]:
        full_block = m.group(0)
        lines = [l.strip() for l in full_block.split('\n') if l.strip()]
        print(f"*** CASE {cid} ***")
        for line in lines[:8]:
            print("  ", line)
        print()
