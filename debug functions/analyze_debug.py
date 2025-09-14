import re
from pathlib import Path

# Count files containing debug_* function calls 
new_debug_files = []
old_debug_files = []

for py_file in Path('.').rglob('*.py'):
    if 'dist/' in str(py_file) or '__pycache__' in str(py_file):
        continue
    try:
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check for new system: debug_* function calls
        if re.search(r'debug_[a-z_]+\(', content):
            new_debug_files.append(str(py_file))
        
        # Check for old system: print(...[DEBUG])
        if re.search(r'print\([^)]*\[DEBUG\]', content):
            old_debug_files.append(str(py_file))
    except Exception:
        pass

print(f'NEW SYSTEM (debug_* functions): {len(new_debug_files)} files')
print(f'OLD SYSTEM (print [DEBUG]): {len(old_debug_files)} files')

total_files = len(set(new_debug_files + old_debug_files))
new_only = len(set(new_debug_files) - set(old_debug_files))
mixed = len(set(new_debug_files) & set(old_debug_files))
old_only = len(set(old_debug_files) - set(new_debug_files))

print(f'MIXED FILES (both systems): {mixed}')
print(f'NEW ONLY: {new_only}')
print(f'OLD ONLY: {old_only}')
print(f'TOTAL DEBUG FILES: {total_files}')

if total_files > 0:
    new_pct = (new_only + mixed) / total_files * 100
    print(f'CONVERSION RATE: {new_pct:.1f}% using new system')