import json

data = json.load(open('evaluation_results_100_cases.json', encoding='utf-8'))
case_ids = [6, 7, 22, 24, 39, 49, 56, 61, 64, 66, 71, 73, 74, 83]

for item in data:
    if item.get('case_id') in case_ids:
        print(f"=== Case {item.get('case_id')} ===")
        print("Vignette:", item.get('vignette', '')[:300])
        print("Extracted findings:", item.get('extracted_findings'))
        print("Primary:", item.get('primary_prediction'))
        diffs = item.get('differentials', [])
        print("Differentials:", [d.get('disease_name') for d in diffs[:5]])
        print()
