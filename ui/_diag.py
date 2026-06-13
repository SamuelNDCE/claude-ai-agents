import fitz
m = fitz.open(r"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\KERAUNOS-v2.pdf")
want = ["PANEL B", "PANEL C", "EOS-1 PoC TRACK", "PANEL C — SIDE", "side profile", "TRACK LADDER"]
for i, p in enumerate(m):
    t = p.get_text()
    if "PANEL B — PHASE 1" in t:
        p.get_pixmap(dpi=120).save(rf"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\_d_bP B_{i}.png".replace(" ",""))
        print("BRONTE Panel B idx", i)
    if "SINGLE STRAIGHT GRADE @ 12.3°, NO BEND" in t:
        p.get_pixmap(dpi=120).save(rf"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\_d_bPC_{i}.png")
        print("BRONTE Panel C idx", i)
    if "EOS-1 PoC TRACK" in t or "REGOLITH EMBANKMENT" in t:
        p.get_pixmap(dpi=120).save(rf"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\_d_selC_{i}.png")
        print("SELENE side profile idx", i)
    if "EOS-1 SECTION" in t:
        p.get_pixmap(dpi=120).save(rf"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\_d_selB_{i}.png")
        print("SELENE ring section idx", i)
