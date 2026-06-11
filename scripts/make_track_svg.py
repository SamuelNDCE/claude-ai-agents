"""Extract the SELENE track SVG from the mockup HTML and write a standalone
light-mode SVG with literal colors for PDF embedding (svglib can't resolve CSS vars).
Also swaps non-Latin-1 glyphs that reportlab's base fonts can't render."""
import re
from pathlib import Path

html_path = Path(r"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\2026-06-11-selene-track-section.html")
svg_path  = Path(r"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\selene-track-section.svg")

LIGHT = {
    "--bg": "#ffffff", "--grid": "#e8ecf4", "--ink": "#16192a",
    "--muted": "#4a5568", "--faint": "#8a94a8",
    "--cy": "#0284c7", "--cyd": "#0369a1", "--pur": "#6d28d9", "--blue": "#1e3a8a",
    "--phA": "#0284c7", "--phB": "#6d28d9", "--phC": "#8b5cf6",
    "--casing": "#eef1f8", "--casingS": "#64748b",
    "--panel": "#f4f6fb", "--panelS": "#c3ccdd",
    "--bore": "#e9edf5", "--pod": "#eef2f9", "--modf": "#e2e8f2",
    "--rego": "#f0ebe2", "--regoS": "#c9c0ae", "--groundS": "#4a5568",
    "--cu": "#b07c4a", "--ag": "#94a3b8", "--hast": "#64748b", "--g10": "#a16207",
    "--senseInk": "#ffffff",
}

GLYPHS = {
    "⚠ ": "",      # warning sign (banner)
    "⚠": "",
    "τ": "tau",    # Greek tau
    "∅": "Ø", # empty set -> Latin-1 O-slash
    "′": "'",      # prime
    "–": "-",      # en dash
    "›": ">",      # single right angle quote
    "≤": "<=",
    "≈": "~",
    "⋅": "-",
    "→": "->",
}

html = html_path.read_text(encoding="utf-8")
m = re.search(r'(<svg id="main".*?</svg>)', html, re.DOTALL)
if not m:
    raise RuntimeError("SVG block not found")
svg = m.group(1)

# stars: hide in light mode
svg = svg.replace('style="opacity:var(--star)"', 'opacity="0"')

# substitute CSS vars with literals
for var, color in LIGHT.items():
    svg = svg.replace(f"var({var})", color)

if "var(--" in svg:
    leftover = sorted(set(re.findall(r"var\(--[a-zA-Z]+\)", svg)))
    raise RuntimeError(f"Unsubstituted vars remain: {leftover}")

# glyph safety for reportlab base fonts
for bad, good in GLYPHS.items():
    svg = svg.replace(bad, good)

svg_path.write_text(svg, encoding="utf-8")
print(f"Written {svg_path} ({svg_path.stat().st_size} bytes)")

# verify svglib can parse it
from svglib.svglib import svg2rlg
d = svg2rlg(str(svg_path))
if d is None:
    raise RuntimeError("svglib failed to parse")
print(f"svglib OK: {d.width:.0f} x {d.height:.0f}")
