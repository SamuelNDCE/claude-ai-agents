"""Extract the SVG from the SELENE track mockup HTML and convert to PNG for PDF embedding."""
import re
from pathlib import Path
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import io

html_path = Path(r"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\2026-06-11-selene-track-section.html")
svg_path  = Path(r"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\selene-track-section.svg")
png_path  = Path(r"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\selene-track-section.png")

# Extract SVG from HTML
html = html_path.read_text(encoding="utf-8")
m = re.search(r'(<svg\b.*?</svg>)', html, re.DOTALL)
if not m:
    raise RuntimeError("SVG block not found in HTML")

# Write standalone SVG (svglib reads from file)
svg_path.write_text(m.group(1), encoding="utf-8")
print(f"SVG extracted: {svg_path}")

# Convert to reportlab Drawing then render to PNG
drawing = svg2rlg(str(svg_path))
if drawing is None:
    raise RuntimeError("svglib could not parse the SVG")

print(f"Drawing size: {drawing.width:.0f} x {drawing.height:.0f} pt")

# Scale to 1400x720 output pixels
scale_x = 1400 / drawing.width
scale_y = 720  / drawing.height
scale   = min(scale_x, scale_y)
drawing.width  *= scale
drawing.height *= scale
drawing.transform = (scale, 0, 0, scale, 0, 0)

renderPM.drawToFile(drawing, str(png_path), fmt="PNG", bg=0x080c18)
print(f"PNG written: {png_path}  ({png_path.stat().st_size / 1024:.1f} KB)")
