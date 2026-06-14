"""Restore keraunos_pdf_build.py to original 21.3 km values."""
import subprocess, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ORIG = '944d2cc'

result = subprocess.run(
    ['git', 'show', f'{ORIG}:ui/keraunos_pdf_build.py'],
    cwd=ROOT, capture_output=True
)
content = result.stdout.decode('utf-8', errors='replace')

# Strip any remaining em-dashes just in case
content = re.sub(r'\s*—\s*', ', ', content)

dest = os.path.join(ROOT, 'ui', 'keraunos_pdf_build.py')
with open(dest, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Restored keraunos_pdf_build.py from {ORIG} ({len(content):,} chars)')
print('em-dashes remaining:', content.count('—'))
