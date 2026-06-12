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
@media print {
  @page { size: A4 portrait; margin: 9mm; }
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

def transform_map(src_path, hero_idx):
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
    out = [head]
    for i, blk in enumerate(panels):
        # the last block may carry the trailing </div></body></html>; peel it
        tail = ""
        tm = re.search(r'(\s*</div>\s*</body>\s*</html>\s*)$', blk, re.S)
        if tm:
            tail = tm.group(1)
            blk = blk[:tm.start()]
        if i in hero_idx:
            out.append(f'<div class="rotpage"><div class="rotbox">{blk}</div></div>')
        else:
            out.append(f'<div class="keep">{blk}</div>')
        if tail:
            out.append(cap + tail)
    new = "".join(out)
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

def main(only=None):
    jobs = {
        "v2a":    (os.path.join(HERE, "keraunos-v2a.html"), None),
        "bronte": (os.path.join(HERE, "2026-06-12-bronte-chimborazo-routemap.html"), [0,1,2,3,4]),
        "selene": (os.path.join(HERE, "2026-06-12-selene-design-map.html"), [0,2,3]),
        "v2b":    (os.path.join(HERE, "keraunos-v2b.html"), None),
    }
    pdfs = {}
    for name, (src, hero) in jobs.items():
        if only and name not in only:
            continue
        printable = transform_map(src, hero) if hero is not None else src
        pdf = os.path.join(HERE, f"_{name}.pdf")
        chrome_pdf(printable, pdf)
        pdfs[name] = pdf
        print(f"  printed {name}: {pdf}")
    if only:
        return
    out = os.path.join(HERE, "KERAUNOS-v2.pdf")
    merge([pdfs["v2a"], pdfs["bronte"], pdfs["selene"], pdfs["v2b"]], out)
    import shutil
    shutil.copy(out, os.path.join(DOWNLOADS, "KERAUNOS-v2.pdf"))
    print("MERGED ->", out, "and Downloads")

if __name__ == "__main__":
    main(only=sys.argv[1:] or None)
