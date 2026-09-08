import re

with open("src/lib/api.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Replace ${BASE_URL}/... with `${BASE_URL}/...`
# We look for \$\{BASE_URL\}[^,\)\n]+
# and wrap it in backticks IF it's not already.

def replacer(match):
    matched_str = match.group(0)
    # Check if preceded by backtick in the original content... actually regex is easier.
    return matched_str

# Regex to find unquoted ${BASE_URL}...
# We want to match: any space/bracket/paren, then ${BASE_URL}...
# and replace it.
content = re.sub(r'(?<!`)\$\{BASE_URL\}([^,\)\n\s]+)', r'`${BASE_URL}\1`', content)

# There are also some corrupted URLs like //verify instead of /${id}/verify
content = content.replace("sources//verify", "sources/${id}/verify")
content = content.replace("jobs//review", "jobs/${id}/review")
content = content.replace("knowledge///review", "knowledge/${entity_type}/${id}/review")

with open("src/lib/api.ts", "w", encoding="utf-8") as f:
    f.write(content)
