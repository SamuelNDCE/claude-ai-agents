"""Inject the Rev E SELENE blueprint SVG (dark palette via scoped CSS vars)
into keraunos.html as an 'Early Concept Mock-up' section."""
import re
from pathlib import Path

mock = Path(r"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\2026-06-11-selene-track-section.html")
page = Path(r"C:\Users\Futur\Claude\Projects\PerpetualTechnologiesWebsite\keraunos.html")

html = mock.read_text(encoding="utf-8")
m = re.search(r'(<svg id="main".*?</svg>)', html, re.DOTALL)
if not m:
    raise RuntimeError("SVG not found in mockup")
svg = m.group(1).replace('<svg id="main"', '<svg id="kbp-svg"')

site = page.read_text(encoding="utf-8")
if "k-blueprint" in site:
    raise RuntimeError("Blueprint already injected")

style_add = """
    /* EARLY MOCKUP BLUEPRINT */
    .k-blueprint{
      --bg:#07090f; --grid:#12182a; --ink:#f2f5fa; --muted:#8d9ab4; --faint:#4a5570;
      --cy:#7cc8f5; --cyd:#4aa3d8; --pur:#a78bfa; --blue:#4f7bd9;
      --phA:#7cc8f5; --phB:#8b5cf6; --phC:#c8b8fd;
      --casing:#131a2c; --casingS:#42526f; --panel:#101725; --panelS:#33405c;
      --bore:#030509; --pod:#101828; --modf:#0b101c;
      --rego:#120f18; --regoS:#2c2440; --groundS:#8d9ab4;
      --cu:#8a6a42; --ag:#9aa4b8; --hast:#46587a; --g10:#a08c50;
      --senseInk:#07090f; --star:0.5;
      border:1px solid rgba(124,58,237,0.25); border-radius:12px; overflow:hidden;
      margin-top:2.5rem; background:#07090f;
    }
    .k-blueprint svg{display:block;width:100%;height:auto}
    .k-blueprint svg text{font-family:'Syne Mono',Consolas,monospace}
    .k-bp-caption{
      margin-top:0.9rem; font-family:'Syne Mono',monospace; font-size:0.68rem;
      letter-spacing:0.18em; text-transform:uppercase; color:var(--muted);
    }
    .k-bp-caption strong{color:var(--purple-l)}
  </style>"""

section = f"""
<!-- EARLY CONCEPT MOCK-UP -->
<section id="mockup" style="padding-top:0;">
  <span class="section-label">Early Concept Mock-up</span>
  <h2>A first look at one track section.<br /><span class="grad-text">Not to scale. Will change.</span></h2>
  <div class="divider"></div>
  <p class="section-sub">
    A very early concept mock-up of a single SELENE track section: an open lunar track of
    superconducting coil rings with a modular payload pod. This is a test design for
    illustration only. It is not to scale and not a final configuration.
  </p>
  <div class="k-blueprint">
{svg}
  </div>
  <p class="k-bp-caption"><strong>KER-SEL-TRK-001 REV E</strong> &middot; Very early concept mock-up &middot; Not to scale &middot; Configuration will change &middot; June 2026</p>
</section>

<!-- THREE PHASES -->"""

site = site.replace("  </style>", style_add, 1)
site = site.replace("<!-- THREE PHASES -->", section, 1)
page.write_text(site, encoding="utf-8")
print(f"Injected. New size: {page.stat().st_size} bytes")
