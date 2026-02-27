import os, glob, re

target = 'http://localhost:8000'
replacement = "${import.meta.env.VITE_API_URL || 'http://localhost:8000'}"

for filepath in glob.glob('web/src/**/*.jsx', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if target in content:
        # Regex to match strings starting with target
        # Handles single, double, or backticks
        new_content = re.sub(
            r'([\'\"\`])' + target + r'(.*?)\1',
            r'`' + replacement + r'\2`',
            content
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated {filepath}')
