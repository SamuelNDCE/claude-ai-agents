import os
HERE=os.path.dirname(os.path.abspath(__file__))
files=[os.path.join(HERE,p) for p in ("keraunos-v2a.html","keraunos-v2b.html",
  "2026-06-12-bronte-chimborazo-routemap.html","keraunos_pdf_build.py")]
R=[("6,200","6,220"),("4,373","4,393"),("63 m below","43 m below"),
   ("63 m BELOW","43 m BELOW"),("5,200","5,220"),("39,850","40,000")]
for p in files:
    t=open(p,encoding="utf-8").read()
    for a,b in R: t=t.replace(a,b)
    open(p,"w",encoding="utf-8").write(t)
print("muzzle raised to 6,220 (text)")
