import fitz
m = fitz.open(r"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\KERAUNOS-v2.pdf")
print("MERGED total pages:", m.page_count)
cp = sum(1 for p in m if "Perpetual Technologies. All rights reserved" in p.get_text())
print(f"pages with copyright: {cp}/{m.page_count}")
v = fitz.open(r"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\_v2b.pdf")
for i, p in enumerate(v):
    t = p.get_text()
    if "price of scale" in t:
        end = " ".join(t.split())[-70:]
        print(f"Theoretical E on v2b idx {i}; ENDS: {end.encode('ascii','replace').decode()}")
        p.get_pixmap(dpi=115).save(rf"C:\Users\Futur\Documents\AiWorkspace\Claude\ui\_chk_E_{i}.png")
