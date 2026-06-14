# BRONTE 40 km honest redesign: west portal 1,000 m, muzzle 6,200 m, grade 7.5deg.
# 30 g cargo over 40 km -> 4.85 km/s (Mach 15.3). Phase 1 = 14 km, portal 4,373 m.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
files = [os.path.join(HERE,p) for p in (
  "keraunos-v2a.html","keraunos-v2b.html",
  "2026-06-12-bronte-chimborazo-routemap.html","keraunos_pdf_build.py")]

# SPECIFIC, order-sensitive (consume multi-token strings before globals touch them)
SPEC = [
 # broken markup (backslash tags)
 ("<b>SELENE<\\b><\\td><td>Moon<\\td><td>1, Proof of concept<\\td><td>",
  "<b>SELENE</b></td><td>Moon</td><td>1, Proof of concept</td><td>"),
 ("1.47°S.<\\b>", "1.47°S.</b>"),
 # v2a full-line velocity math (line 298)
 ("294 × 21,315) = 3,540 m/s = <b>3.54 km/s</b>", "294 × 40,000) = 4,850 m/s = <b>4.85 km/s</b>"),
 ("(Mach 11.2), t = 12.0 s", "(Mach 15.3), t = 16.5 s"),
 # v2a human cell (line 306)
 ("1.12 km/s · Mach ~3.5 · 38 s", "1.53 km/s · Mach ~4.9 · 52 s"),
 # v2a muzzle wording (lines 291-292)
 ("The muzzle is set at <b>5,900 m</b> (just under 6 km, ~363 m below the 6,263 m summit) so the exit emerges\n  on the upper flank as a clean bored-tunnel mouth rather than a structure perched at the crest.",
  "The muzzle is set at <b>6,200 m</b> (near the summit, ~63 m below the 6,263 m crest) so the exit emerges\n  high on the summit cone as a clean bored-tunnel mouth, just below the crest rather than a mast perched on top."),
 # v2a table exit row (line 304)
 ("Same muzzle for both: <b>5,900 m</b> (just under 6 km), <b>12.3° east, straight</b>, ~363 m below peak elevation",
  "Same muzzle for both: <b>6,200 m</b>, <b>7.5° east, straight</b>, ~63 m below peak elevation"),
 ("adds ~12.7 km of deep tunnel", "adds ~26 km of deep tunnel"),
 # v2a sonic boom
 ("A Mach-11 body leaving the muzzle at 5,900 m is loud", "A Mach-15 body leaving the muzzle at 6,200 m is loud"),
 ("BRONTE exits at <b>Mach 11</b> and only <b>5,900 m (~6 km)</b>, ~2.7× closer to the ground and ~5× faster.",
  "BRONTE exits at <b>Mach 15</b> and only <b>6,200 m (~6.2 km)</b>, ~2.6× closer to the ground and ~7× faster."),
 ("altitude factor (16/6)<sup>3/4</sup> ≈ 2.1× · Mach factor ((11²−1)/(2²−1))<sup>1/8</sup> ≈ 1.6× ⇒ ~<b>3× Concorde</b>",
  "altitude factor (16/6.2)<sup>3/4</sup> ≈ 2.1× · Mach factor ((15.3²−1)/(2²−1))<sup>1/8</sup> ≈ 1.7× ⇒ ~<b>3.6× Concorde</b>"),
 ("⇒ order <b>5–10 psf (~250–500 Pa) near the track</b>", "⇒ order <b>6–12 psf (~300–600 Pa) near the track</b>"),
 # v2a velocity-ladder framing (309-312)
 ("<h3>Could the line go faster? The velocity ladder over a 40 km straight track</h3>\n  <p>Exit speed is set by length and g-load (v = √(2aL)), so to test how far a longer Chimborazo line could be\n  pushed, here is what it takes to reach 4, 6, and 8 km/s over a 40 km straight track, and whether the g-load\n  makes it possible.</p>",
  "<h3>Could the line go faster? The velocity ladder over the 40 km line</h3>\n  <p>The full line runs cargo at 30 g, which over 40 km is 4.85 km/s (Mach 15.3), one rung on this ladder. Exit\n  speed is set by length and g-load (v = √(2aL)); here is what dialing the same 40 km line to 4, 6, and 8 km/s\n  would take, and whether the g-load makes it possible.</p>"),
 # map full-line derivation (line 153)
 ("L = 21,315 m ⇒ 3,540 m/s", "L = 40,000 m ⇒ 4,850 m/s"),
 # map Panel C km axis (line 210): add 30 tick, even spacing for 40 km
 ('<text x="194" y="688">0</text><text x="494" y="688">10</text><text x="794" y="688">20</text>',
  '<text x="194" y="688">0</text><text x="474" y="688">10</text><text x="754" y="688">20</text><text x="1034" y="688">30</text>'),
 ("(JUST UNDER 6 km)", "(NEAR SUMMIT)"),
 ("~37,000 COIL HOOPS", "~67,000 COIL HOOPS"),
 ("(A CURVE WOULD BE 13+ g)", "(A CURVE WOULD BE 24+ g)"),
 # build-script BRONTE cover labels
 ("straight 12.3° (true 1:1)", "straight 7.5° (schematic)"),
 ("no bend (true 1:1)", "no bend (schematic)"),
]

# GLOBAL single-value replacements
GLB = [
 ("12.3°","7.5°"), ("0.2130","0.1305"),
 ("5,900","6,200"),
 ("363 m below","63 m below"), ("363 m BELOW","63 m BELOW"),
 ("1,360","1,000"), ("2,920","4,373"),
 ("21,315","39,850"), ("21.3 km","40 km"),
 ("4,540","5,200"), ("2,980","1,827"), ("13,990","14,000"),
 ("3,540","4,850"), ("3.54 km/s","4.85 km/s"),
 ("Mach 11.2","Mach 15.3"), ("MACH 11.2","MACH 15.3"), ("~11.2","~15.3"),
 ("Mach-11","Mach-15"), ("Mach 11<","Mach 15<"), ("MACH 11 FINENESS","MACH 15 FINENESS"),
 ("1.12 km/s","1.53 km/s"),
 ("Mach ~3.5","Mach ~4.9"), ("MACH ~3.5","MACH ~4.9"), ("Mach 3.5","Mach 4.9"), ("MACH 3.5","MACH 4.9"),
 ("/ 3.5 at human","/ 4.9 at human"), ("3.5 at human-rated","4.9 at human-rated"),
 ("26.1 MWh","49.0 MWh"), ("34.8 MWh","65.3 MWh"),
 ("15.6 GW","21.4 GW"), ("20.8 GW","28.5 GW"),
 ("9.40 × 10¹⁰","1.76 × 10¹¹"),
 ("12.0 s","16.5 s"),
 ("TRUE SCALE 1:1","SCHEMATIC PROFILE, VERTICAL EXAGGERATED"),
 ("(TRUE 1:1)","(SCHEMATIC, V. EXAG.)"),
 ("~35 MWh · ~$2,100","~65 MWh · ~$3,900"),
 ("~62 MWh · ~$3,700","~115 MWh · ~$6,900"),
 ("~184 MWh · ~$11,100","~346 MWh · ~$20,800"),
 ("~259 MWh · ~$15,500","~487 MWh · ~$29,200"),
 ("peaks at ~21 GW","peaks at ~29 GW"),
 ("70 m cargo shot at ~160 GW","70 m cargo shot at ~213 GW"),
 ("~259 MWh, ~90 MW of sustained generation, ~155 GW peak","~487 MWh, ~170 MW of sustained generation, ~213 GW peak"),
 ("= 125 m/s² = <b>~13 g sideways</b>","= 235 m/s² = <b>~24 g sideways</b>"),
 ("~13 g","~24 g"),
]

for path in files:
    t = open(path, encoding="utf-8").read()
    for old,new in SPEC:
        t = t.replace(old,new)
    for old,new in GLB:
        t = t.replace(old,new)
    open(path,"w",encoding="utf-8").write(t)
print("40km redesign applied")
