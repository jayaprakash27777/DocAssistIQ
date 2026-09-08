import os
import re

directory = r'c:\Users\User\Downloads\DocAssistIQ\backend\app'

count = 0
for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # replace raise NotFoundError("CODE", message) with raise NotFoundError(message, code="CODE")
            new_content, n = re.subn(
                r'raise (NotFoundError|ValidationError)\(\s*["\']([A-Z0-9_]+)["\']\s*,\s*(.*?)\)',
                r'raise \1(\3, code="\2")',  # \1 is exception, \3 is message, \2 is code
                content,
                flags=re.DOTALL
            )
            
            # handle cases where the B904 noqa is attached or we need to fix it
            # actually the DOTALL above handles multiline but it might be too greedy if there are multiple raises in one file.
            # let's be careful. Let's not use DOTALL, but rather process line by line or use a non-greedy .*?
            # DOTALL with .*? is already non-greedy.
            pass
            
            if n > 0:
                print(f'Fixed {n} in {file}')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += n

print(f'Total fixes: {count}')
