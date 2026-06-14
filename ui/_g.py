import os
HERE = os.path.dirname(os.path.abspath(__file__))
F = {n: os.path.join(HERE, p) for n,p in {
  "a":"keraunos-v2a.html","b":"keraunos-v2b.html",
  "m":"2026-06-12-bronte-chimborazo-routemap.html","bld":"keraunos_pdf_build.py"}.items()}

# order matters for a few; list of (old,new) applied to all four files
R = [
 # grade & geometry
 ("12.3°","6.5°"), ("0.2130","0.1132"),
 # full-line length
 ("21,315","40,000"), ("21.3 km","40 km"),
 # full-line velocity (do longer/specific before bare)
 ("3,540","4,850"), ("3.54 km/s","4.85 km/s"),
 # full-line Mach
 ("Mach 11.2","Mach 15.3"), ("MACH 11.2","MACH 15.3"), ("~11.2","~15.3"),
 ("Mach-11","Mach-15"), ("Mach 11<","Mach 15<"), ("MACH 11 FINENESS","MACH 15 FINENESS"),
 # full-line human
 ("1.12 km/s","1.53 km/s"),
 ("Mach ~3.5","Mach ~4.9"), ("MACH ~3.5","MACH ~4.9"), ("Mach 3.5","Mach 4.9"), ("MACH 3.5","MACH 4.9"),
 ("/ 3.5 at human","/ 4.9 at human"), ("3.5 at human-rated","4.9 at human-rated"),
 # full-line energy / power / time
 ("26.1 MWh","49.0 MWh"), ("34.8 MWh","65.3 MWh"),
 ("15.6 GW","21.4 GW"), ("20.8 GW","28.5 GW"),
 ("9.40 × 10¹⁰","1.76 × 10¹¹"),
 ("12.0 s","16.5 s"),
 # phase-1 portal / rise / length-result
 ("2,920","4,315"), ("2,980","1,585"), ("13,990","14,000"),
 # theoretical E cargo-shot column (scales with v^2: x1.877)
 ("~35 MWh · ~$2,100","~65 MWh · ~$3,900"),
 ("~62 MWh · ~$3,700","~115 MWh · ~$6,900"),
 ("~184 MWh · ~$11,100","~346 MWh · ~$20,800"),
 ("~259 MWh · ~$15,500","~487 MWh · ~$29,200"),
 # theoretical E peak-power prose
 ("peaks at ~21 GW","peaks at ~29 GW"),
 ("70 m cargo shot at ~160 GW","70 m cargo shot at ~213 GW"),
 ("~259 MWh, ~90 MW of sustained generation, ~155 GW peak","~487 MWh, ~170 MW of sustained generation, ~213 GW peak"),
 # theoretical F "if curved" cargo example
 ("= 125 m/s² = <b>~13 g sideways</b>","= 235 m/s² = <b>~24 g sideways</b>"),
 ("~13 g","~24 g"),
]
for path in F.values():
    t = open(path, encoding="utf-8").read()
    for old,new in R:
        t = t.replace(old,new)
    open(path,"w",encoding="utf-8").write(t)
print("bulk replace done")
