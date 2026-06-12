from pypdf import PdfReader
import os

r = PdfReader(r'C:\Users\Futur\Documents\AiWorkspace\Claude\tmp-doet.pdf')

def extract_pages(start, end):
    parts = []
    for i in range(start-1, end):
        t = r.pages[i].extract_text()
        if t and t.strip():
            t = t.replace('\t', ' ')
            parts.append(t)
    return '\n\n'.join(parts)

chapters = [
    ('preface',   'Preface to the Revised Edition', 13, 18),
    ('chapter-1', 'The Psychopathology of Everyday Things', 19, 51),
    ('chapter-2', 'The Psychology of Everyday Actions', 52, 84),
    ('chapter-3', 'Knowledge in the Head and in the World', 85, 125),
    ('chapter-4', 'Knowing What to Do: Constraints, Discoverability, and Feedback', 126, 160),
    ('chapter-5', 'Human Error? No, Bad Design', 161, 207),
    ('chapter-6', 'Design Thinking', 208, 242),
    ('chapter-7', 'Design in the World of Business', 243, 285),
]

vault = r'C:\Users\Futur\Documents\AiWorkspace\NeuralVault\sample-vault\wiki\sources\doet'
os.makedirs(vault, exist_ok=True)

for slug, title, start, end in chapters:
    text = extract_pages(start, end)
    fname = os.path.join(vault, f'{slug}.md')
    content = (
        f'---\n'
        f'title: "DOET — {title}"\n'
        f'type: source\n'
        f'status: evergreen\n'
        f'source: book-extract\n'
        f'book: The Design of Everyday Things\n'
        f'author: Don Norman\n'
        f'edition: Revised and Expanded 2013\n'
        f'pages: {start}-{end}\n'
        f'created: 2026-06-12\n'
        f'updated: 2026-06-12\n'
        f'tags: [book, design, ux, psychology, human-centered-design, doet, wiki/source]\n'
        f'---\n\n'
        f'# {title}\n\n'
        f'> Extracted from *The Design of Everyday Things* (revised ed., 2013) by Don Norman, pp. {start}–{end}.\n\n'
        f'{text}\n'
    )
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Saved {slug}: {len(text)} chars, pages {start}-{end}')

print('Done.')
