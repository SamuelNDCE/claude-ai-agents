"""Restore v2a + v2b to the original 21.3 km design, then strip em-dashes."""
import subprocess, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def git_show(commit, path):
    result = subprocess.run(
        ['git', 'show', f'{commit}:{path}'],
        cwd=ROOT, capture_output=True
    )
    return result.stdout.decode('utf-8', errors='replace')

def strip_em_dashes(text):
    # Replace em-dash (U+2014) with comma, normalizing surrounding whitespace
    text = re.sub(r'\s*—\s*', ', ', text)
    return text

# Commit hash that has the original 21.3 km design (pre-all-changes)
ORIG = '944d2cc'

files = ['ui/keraunos-v2a.html', 'ui/keraunos-v2b.html']

for rel in files:
    print(f'Restoring {rel} from {ORIG}...')
    content = git_show(ORIG, rel)
    em_count_before = content.count('—')
    content = strip_em_dashes(content)
    em_count_after = content.count('—')
    dest = os.path.join(ROOT, rel.replace('/', os.sep))
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  em-dashes: {em_count_before} -> {em_count_after}  (wrote {len(content):,} chars)')

print('Done. Both files restored to 21.3 km / 5,900 m / 12.3 deg design, em-dashes removed.')
