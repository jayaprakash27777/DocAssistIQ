import re

with open('src/lib/api.ts', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines):
    if '/api/v1' in line and '${BASE_URL}' not in line and 'BASE_URL' not in line:
        # e.g., authedFetch<DatasetResponse[]>(`/api/v1/datasets`);
        # Replace the opening quote with a backtick, add ${BASE_URL}, replace closing quote with backtick
        # The regex matches an opening quote, /api/v1, then anything up to the same matching quote.
        new_line = re.sub(r'([\'\"\`])/api/v1(.*?)\1', r'`${BASE_URL}/api/v1\2`', line)
        lines[i] = new_line
        
# also fix //
content = '\n'.join(lines)
content = content.replace("sources//verify", "sources/${id}/verify")
content = content.replace("jobs//review", "jobs/${id}/review")
content = content.replace("knowledge///review", "knowledge/${entity_type}/${id}/review")
content = content.replace("evaluations//", "evaluations/${id}/")
content = content.replace("experiments//", "experiments/${id}/")
content = content.replace("consent//revoke", "consent/${userId}/revoke")
content = content.replace("consent//", "consent/${userId}/")


with open('src/lib/api.ts', 'w', encoding='utf-8') as f:
    f.write(content)
