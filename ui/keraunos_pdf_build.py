#!/usr/bin/env python
"""
KERAUNOS-v2.pdf builder.

Uniform A4 PORTRAIT throughout. The whitepaper (keraunos-v2a/b) prints as-is.
The two design maps are transformed into a print copy where the BIG figure
panels are placed on their own portrait page, rotated 90 deg so they stay
large (Option 3: "portrait paper, big maps on own rotated pages"). The chart
strips and text panels stay in normal portrait flow.

Order: v2a (front + Sec 0-4 + Annex notes) -> BRONTE map (Annex A)
       -> SELENE map (Annex B) -> v2b (Sec 5-12).

Mechanism: Chrome headless --print-to-pdf per HTML, merged with pypdf.
The originals stay browser-viewable; only *_print.html copies get rotation CSS.
"""
import os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")

# Print CSS injected into the map print-copies. Page content area for A4
# portrait at 9 mm margins = 192 x 279 mm. A rotated figure's long edge maps
# to the 279 mm page height; its short edge is capped to 180 mm so the heading
# also fits across the 192 mm page width.
MAP_PRINT_CSS = """
<style id="pdfprint">
.copyright { display:none; }
.annexcover { padding: 4px 6px 0; }
.annexcover .ax-letter { font-family:Consolas,monospace; font-size:13px; letter-spacing:3px;
   color:#0e7490; font-weight:700; margin:26px 0 2px; }
.annexcover .ax-title { font-size:30px; font-weight:700; letter-spacing:1px; color:#0f172a; margin:0 0 4px; }
.annexcover .ax-id { font-family:Consolas,monospace; font-size:12px; color:#64748b; margin:0 0 22px;
   border-bottom:2.5px solid #0e7490; padding-bottom:12px; }
.annexcover .ax-sub { font-size:12.5px; letter-spacing:2px; color:#7c3aed; font-weight:700;
   font-family:Consolas,monospace; margin:0 0 8px; }
.annexcover ul.ax-toc { list-style:none; padding:0; margin:0 0 22px; }
.annexcover ul.ax-toc li { font-size:13px; color:#1e293b; padding:6px 0 6px 16px;
   border-bottom:1px solid #e2e8f0; position:relative; }
.annexcover ul.ax-toc li:before { content:"▸"; color:#0e7490; position:absolute; left:0; }
.annexcover .ax-note { font-size:12px; font-style:italic; color:#92400e; background:#fffbeb;
   border-left:3px solid #d97706; padding:9px 12px; margin-top:8px; }
@media print {
  @page { size: A4 portrait; margin: 9mm; }
  .copyright { display:block; position:fixed; left:0; right:0; bottom:4mm; text-align:center;
     font-size:8px; letter-spacing:1px; color:#94a3b8; font-family:Consolas,monospace; }
  html, body { background:#fff !important; padding:0 !important; margin:0 !important; }
  .sheet { box-shadow:none !important; border:none !important; max-width:none !important;
           padding:0 !important; margin:0 !important; }
  .keep { break-inside: avoid; page-break-inside: avoid; margin-bottom:6px; }
  .keep h2.panel, h2.panel { break-after: avoid; page-break-after: avoid; }
  .stamp, .intro, .caption { break-inside: avoid; page-break-inside: avoid; }
  .caption { break-before: avoid; }
  /* a big figure on its own portrait page, rotated to fill the long edge */
  .rotpage { break-before: page; break-after: page;
             page-break-before: always; page-break-after: always;
             height: 279mm; display:flex; align-items:center; justify-content:center;
             overflow:hidden; }
  .rotbox { transform: rotate(90deg); transform-origin: center center;
            display:flex; flex-direction:column; align-items:center; }
  .rotbox h2.panel { margin:0 0 5px; font-size:16px; white-space:nowrap; text-align:center; }
  .rotbox svg, .rotbox .mapbox { width:auto; height:auto;
            max-width:279mm; max-height:178mm; display:block; }
  .rotbox .mapbox img { width:auto; height:auto; max-width:279mm; max-height:178mm; display:block; }
}
</style>
"""

def cover_html(cov):
    items = "".join(f"<li>{x}</li>" for x in cov["toc"])
    return (f'<div class="annexcover"><div class="ax-letter">ANNEX {cov["letter"]}</div>'
            f'<div class="ax-title">{cov["title"]}</div>'
            f'<div class="ax-id">{cov["id"]}</div>'
            f'<div class="ax-sub">WHAT IS INSIDE</div>'
            f'<ul class="ax-toc">{items}</ul>'
            f'<div class="ax-note">Each large panel is on its own page, rotated to read at full '
            f'size, turn the page (or your screen) a quarter-turn clockwise.</div></div>')

def transform_map(src_path, hero_idx, cover=None):
    """Wrap hero panels (by 0-based order of <h2 class="panel">) in rotated
    full-page boxes; wrap the rest in .keep. Returns path to the *_print.html."""
    html = open(src_path, encoding="utf-8").read()
    # pull caption out so it stays in normal flow at the very end
    cap = ""
    m = re.search(r'(<p class="caption">.*?</p>)', html, re.S)
    if m:
        cap = m.group(1)
        html = html.replace(cap, "")
    # split the sheet body on panel headings
    parts = re.split(r'(?=<h2 class="panel">)', html)
    # parts[0] = everything up to first panel (head, body, stamp, intro)
    head, panels = parts[0], parts[1:]
    if cover:
        head += cover_html(cover)
    # peel the document tail (</div></body></html>) off the final block
    tail = ""
    tm = re.search(r'(\s*</div>\s*</body>\s*</html>\s*)$', panels[-1], re.S)
    if tm:
        tail = tm.group(1)
        panels[-1] = panels[-1][:tm.start()]
    # big figures (rotated, one per page) first, then the upright panels packed
    # together so no short panel is stranded alone on a mostly-empty page
    heroes = [f'<div class="rotpage"><div class="rotbox">{b}</div></div>'
              for i, b in enumerate(panels) if i in hero_idx]
    keeps = [f'<div class="keep">{b}</div>'
             for i, b in enumerate(panels) if i not in hero_idx]
    new = "".join([head] + heroes + keeps + [cap, tail])
    # inject print CSS just before </head>
    new = new.replace("</head>", MAP_PRINT_CSS + "</head>", 1)
    dst = src_path.replace(".html", "_print.html")
    open(dst, "w", encoding="utf-8").write(new)
    return dst

def chrome_pdf(html_path, pdf_path):
    url = "file:///" + html_path.replace("\\", "/")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", url],
                   check=True, capture_output=True)

def merge(pdfs, out_path):
    from pypdf import PdfWriter
    w = PdfWriter()
    for p in pdfs:
        w.append(p)
    with open(out_path, "wb") as f:
        w.write(f)

BRONTE_COVER = {"letter":"B", "title":"BRONTE, Chimborazo Design Map",
    "id":"KER-BRO-TRK-001 · REV N · EARLY-VERSION TEST MOCK-UP · NOT FOR CONSTRUCTION",
    "toc":[
      "Panel A, Plan view: one line, two phases (real SRTM 30 m terrain)",
      "Panel B, Phase 1 (build first): 14 km, portal 2,920 m → tunnel muzzle 5,900 m, straight 12.3° (true 1:1)",
      "Panel C, Full line (~21.3 km growth target): single straight bored tunnel @ 12.3°, no bend (true 1:1)",
      "Panel D, Tunnel &amp; tube typical section: the 360° drive ring, wide bore for Ø3.2 m payload",
      "Panel E, External bridge section · ASTRAPE front view · ASTRAPE in the tube",
      "Charts, systems, route engineering, tunnel engineering"]}
SELENE_COVER = {"letter":"A", "title":"SELENE, South Pole Design Map",
    "id":"KER-SEL-TRK-002 · REV E · Ø3 m BORE · EARLY-VERSION TEST MOCK-UP · NOT FOR CONSTRUCTION",
    "toc":[
      "Panel A, Site: real LRO/LOLA laser topography, Shackleton / Connecting Ridge ~89.7°S",
      "Panel A2, Where on the Moon · what does not exist here · EOS-3 machine specs (Ø3 m bore)",
      "Panel B, EOS-3 open-track section: no tube, the Moon is the vacuum vessel (Ø3.0 m bore)",
      "Panel C, Side profile: the raised track on its regolith embankment (true 1:1)",
      "Panel D, Engineering charts: track length vs g, Δv destinations, ridge illumination, energy",
      "Panel E, Return missions: direct Earth entry, satellite dispenser, cislunar depot supply",
      "Panel F, Build cost summary (revised Ø3 m estimate, $2.0B–$2.5B mid-case)"]}

def split_v2a():
    """Split keraunos-v2a.html at the Section-2 boundary so each design map sits with its
    project: part A = front + Sec 0 + Sec 1 (SELENE), part B = Sec 2-4 (incl. Chimborazo).
    Merge order then interleaves: A -> SELENE map -> B -> BRONTE map -> v2b."""
    html = open(os.path.join(HERE, "keraunos-v2a.html"), encoding="utf-8").read()
    split = html.index("<!-- SECTION 2 PHYSICS -->")
    open_end = html.index("</div>", html.index('class="copyright"')) + len("</div>")
    head_open = html[:open_end]                 # <head>+styles + <body> + copyright div
    a = head_open + html[open_end:split] + "\n</body>\n</html>\n"
    b = head_open + html[split:]                # Sec 2-4 + original </body></html>
    ap = os.path.join(HERE, "keraunos-v2a_a.html"); open(ap, "w", encoding="utf-8").write(a)
    bp = os.path.join(HERE, "keraunos-v2a_b.html"); open(bp, "w", encoding="utf-8").write(b)
    return ap, bp

def main(only=None):
    a_path, b_path = split_v2a()
    jobs = {
        "v2a_a":  (a_path, None, None),
        "v2a_b":  (b_path, None, None),
        "bronte": (os.path.join(HERE, "2026-06-12-bronte-chimborazo-routemap.html"), [0,1,2,3,4], BRONTE_COVER),
        "selene": (os.path.join(HERE, "2026-06-12-selene-design-map.html"), [0,2,3,5], SELENE_COVER),
        "v2b":    (os.path.join(HERE, "keraunos-v2b.html"), None, None),
    }
    pdfs = {}
    for name, (src, hero, cover) in jobs.items():
        if only and name not in only:
            continue
        printable = transform_map(src, hero, cover) if hero is not None else src
        pdf = os.path.join(HERE, f"_{name}.pdf")
        chrome_pdf(printable, pdf)
        pdfs[name] = pdf
        print(f"  printed {name}: {pdf}")
    if only:
        return
    out = os.path.join(HERE, "KERAUNOS-v2.pdf")
    # SELENE map follows Sec 1; BRONTE map follows Sec 4
    merge([pdfs["v2a_a"], pdfs["selene"], pdfs["v2a_b"], pdfs["bronte"], pdfs["v2b"]], out)
    import shutil
    shutil.copy(out, os.path.join(DOWNLOADS, "KERAUNOS-v2.pdf"))
    print("MERGED ->", out, "and Downloads")

if __name__ == "__main__":
    main(only=sys.argv[1:] or None)
