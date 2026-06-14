# Regenerate BRONTE Panel B & C elevation profiles with COMPUTED, altitude-accurate
# geometry (true 1:1). Muzzle 6,220 m, west portal 1,000 m, P1 portal 4,393 m, 7.5deg.
import os, re, math
HERE = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(HERE, "2026-06-12-bronte-chimborazo-routemap.html")

SUMMIT = 6263; MUZ = 6220
def smoother(t):
    t = max(0.0, min(1.0, t)); return t*t*t*(t*(t*6-15)+10)

def terrain(L, portal_e):
    """surface elevation (m) vs distance-from-portal (km), 0..L+east_tail."""
    pts=[]; riseL=L-0.6
    n=140
    for i in range(n+1):
        km=riseL*i/n; t=km/riseL
        e=portal_e+(SUMMIT-portal_e)*smoother(t)+42*math.sin(km*1.3)+24*math.sin(km*0.7+1.5)
        e=min(e, SUMMIT-3)
        pts.append((km,e))
    pts.append((L-0.3, SUMMIT-4))     # summit shoulder
    pts.append((L, MUZ))              # muzzle emerges here, on the surface
    tail = L*0.22
    for i in range(1,13):             # east face drops away (fire-east corridor)
        t=i/12; km=L+tail*t
        pts.append((km, MUZ+(portal_e-900-MUZ)*t if False else MUZ-(2100)*t))
    return pts

def build(L, portal_e, x0, pxkm, y0, vbw, vbh, grid, title, sub, footer,
          portal_lab, muz_lab, extra=""):
    s=pxkm/1000.0
    X=lambda km: x0+km*pxkm
    Y=lambda e: y0-e*s
    yfill=vbh-78
    surf=terrain(L, portal_e)
    sp=" L ".join(f"{X(k):.1f},{Y(e):.1f}" for k,e in surf)
    terr=(f'<path d="M {X(0):.1f},{Y(portal_e):.1f} L {sp} L {X(surf[-1][0]):.1f},{yfill:.1f} '
          f'L {X(0):.1f},{yfill:.1f} Z" fill="#efe9da" stroke="#8a7f6a" stroke-width="1.6"/>')
    # straight tunnel portal -> muzzle (true geometry)
    p0=(X(0),Y(portal_e)); p1=(X(L),Y(MUZ))
    def lerp(a,b,t): return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
    a=lerp(p0,p1,0.06); b=lerp(p0,p1,0.93)
    track=(f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{a[0]:.1f}" y2="{a[1]:.1f}" stroke="#7c3aed" stroke-width="6.5" stroke-linecap="round"/>'
           f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#7c3aed" stroke-width="6.5" stroke-dasharray="14 8" stroke-linecap="round"/>'
           f'<line x1="{b[0]:.1f}" y1="{b[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="#7c3aed" stroke-width="6.5" stroke-linecap="round"/>'
           # amber power feed parallel, offset 6px down
           f'<line x1="{p0[0]:.1f}" y1="{p0[1]+6:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]+6:.1f}" stroke="#f59e0b" stroke-width="2.4" stroke-dasharray="4 5"/>')
    # gridlines + elevation labels
    gl=['<g stroke="#dbe3ee" stroke-width="1">']
    for e in grid: gl.append(f'<line x1="{x0-4:.0f}" y1="{Y(e):.1f}" x2="{vbw-20}" y2="{Y(e):.1f}"/>')
    gl.append('</g><g font-size="10.5" fill="#64748b" class="t" text-anchor="end">')
    for e in grid: gl.append(f'<text x="{x0-10:.0f}" y="{Y(e)+3.5:.1f}">{e:,} m</text>')
    gl.append('</g>')
    grids="".join(gl)
    # altitude guide lines for portal & muzzle (dashed, to the axis)
    guides=(f'<line x1="{x0-6:.0f}" y1="{Y(portal_e):.1f}" x2="{p0[0]:.1f}" y2="{p0[1]:.1f}" stroke="#22d3ee" stroke-width="1" stroke-dasharray="3 3"/>'
            f'<line x1="{x0-6:.0f}" y1="{Y(MUZ):.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" stroke="#f43f5e" stroke-width="1" stroke-dasharray="3 3"/>')
    # summit marker
    sx=X(L-0.3); sy=Y(SUMMIT)
    summit=(f'<path d="M {sx:.0f},{sy-2:.0f} l -6,11 l 12,0 Z" fill="#334155"/>'
            f'<text x="{sx-10:.0f}" y="{sy-8:.0f}" text-anchor="end" font-size="10.5" font-weight="600" fill="#334155" class="t">CHIMBORAZO {SUMMIT:,} m</text>')
    # dots + labels
    dots=(f'<circle cx="{p0[0]:.1f}" cy="{p0[1]:.1f}" r="6" fill="#22d3ee" stroke="#0f172a" stroke-width="1.5"/>'
          f'<circle cx="{p1[0]:.1f}" cy="{p1[1]:.1f}" r="6" fill="#f43f5e" stroke="#0f172a" stroke-width="1.5"/>')
    # exit arrow (fires east)
    ex2=(p1[0]+150, p1[1]-20)
    arrow=(f'<path d="M {p1[0]:.0f},{p1[1]:.0f} L {ex2[0]:.0f},{ex2[1]:.0f}" fill="none" stroke="#0e7490" stroke-width="2.2" stroke-dasharray="8 7"/>'
           f'<path d="M {ex2[0]+12:.0f},{ex2[1]-3:.0f} l -16,-3 l 2,9 l -7,5 Z" fill="#0e7490"/>')
    midx=(p0[0]+p1[0])/2; midy=(p0[1]+p1[1])/2
    labs=(f'<text x="{p0[0]+14:.0f}" y="{p0[1]+22:.0f}" font-size="11.5" fill="#0e7490" class="t">{portal_lab}</text>'
          f'<text x="{p1[0]-8:.0f}" y="{p1[1]-30:.0f}" text-anchor="end" font-size="11.5" font-weight="700" fill="#b91c1c" class="t">{muz_lab}</text>'
          f'<text x="{p1[0]-8:.0f}" y="{p1[1]-16:.0f}" text-anchor="end" font-size="10.5" fill="#f43f5e" class="t">EXIT 7.5° EAST, FIRES OVER THE EMPTY EAST FACE</text>'
          f'<text x="{midx:.0f}" y="{midy+30:.0f}" text-anchor="middle" font-size="11" fill="#16a34a" class="t">SINGLE STRAIGHT 7.5° GRADE, NO CURVE (DASHED = BORED TUNNEL, IN THE ROCK)</text>')
    # distance axis
    da=[f'<line x1="{x0:.0f}" y1="{vbh-58}" x2="{vbw-20}" y2="{vbh-58}" stroke="#64748b" stroke-width="1.4"/>',
        '<g font-size="10" fill="#64748b" class="t" text-anchor="middle">']
    step = 2 if L<20 else 5
    k=0
    while k<=L+0.01:
        lab=f"{k:.0f}" if k<L else f"{L:.0f} km, MUZZLE"
        da.append(f'<text x="{X(k):.0f}" y="{vbh-38}">{lab}</text>'); k+=step
    da.append('</g>'); dax="".join(da)
    return (f'<svg viewBox="0 0 {vbw} {vbh}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Arial, sans-serif">'
            f'<rect x="4" y="4" width="{vbw-8}" height="{vbh-8}" fill="none" stroke="#334155" stroke-width="2"/>'
            f'<text x="{vbw//2}" y="34" text-anchor="middle" font-size="17" font-weight="700" letter-spacing="1.1">{title}</text>'
            f'<text x="{vbw//2}" y="55" text-anchor="middle" font-size="12" fill="#0e7490" class="t">{sub}</text>'
            f'{grids}{terr}{summit}{guides}{track}{arrow}{dots}{labs}{extra}{dax}'
            f'<text x="{vbw//2}" y="{vbh-14}" text-anchor="middle" font-size="11" font-weight="700" fill="#16a34a" class="t">{footer}</text></svg>')

# ---- PANEL B: Phase 1, 14 km, portal 4,393 m -> muzzle 6,220 m ----
bB = build(L=14, portal_e=4393, x0=150, pxkm=70, y0=735.4, vbw=1600, vbh=720,
   grid=[4000,4500,5000,5500,6000],
   title="PHASE 1, 14 km FIRST BUILD, A STRAIGHT BORED TUNNEL TO NEAR THE SUMMIT",
   sub="PORTAL 4,393 m · MUZZLE 6,220 m · STRAIGHT 7.5° · 30 g → 2.87 km/s (MACH 9.1) · 3 g → MACH 2.9 · v = √(2aL)",
   footer="TRUE SCALE 1:1, HORIZONTAL = VERTICAL; THE 7.5° GRADE IS SHOWN AT ITS REAL ANGLE. +1,827 m OF CLIMB OVER 14 km, NO BEND",
   portal_lab="PHASE-1 PORTAL ~4,393 m, LOAD-IN / VACUUM / SMES FARM",
   muz_lab="TUNNEL MUZZLE 6,220 m (43 m BELOW PEAK)")

# ---- PANEL C: full line, 40 km, west portal 1,000 m -> muzzle 6,220 m ----
notesC=('<g><rect x="86" y="74" width="560" height="150" fill="#fbfcfe" stroke="#94a3b8"/>'
 '<text x="100" y="94" font-size="11.5" font-weight="700" fill="#0e7490" class="t">GENERAL NOTES</text>'
 '<g font-size="10.5" fill="#334155" class="t">'
 '<text x="100" y="112">1. A HIGH-SPEED TRACK CANNOT CURVE: ONE STRAIGHT LINE AT 7.5°.</text>'
 '<text x="100" y="128">   NO CURVE ⇒ ZERO LATERAL g (A CURVE WOULD BE 24+ g).</text>'
 '<text x="100" y="146">2. WHY ALTITUDE: EXIT AIR @ 6,220 m IS ρ ≈ 53% SL. HIGHER MEANS A</text>'
 '<text x="100" y="160">   WEAKER GROUND BOOM, LESS DRAG, LESS HEATING.</text>'
 '<text x="100" y="178" fill="#9f1239">3. WEST DEEP TUNNEL ~26 km, COVER ≤ ~880 m (GOTTHARD: 2,300 m).</text>'
 '<text x="100" y="194">4. FIRES EAST OVER THE EMPTY AMAZON-FACING FACE: +465 m/s FREE.</text>'
 '<text x="100" y="212" fill="#64748b">5. CABLE GALLERY + 20 K / 80 K CRYO HEADERS RUN THE INVERT, FULL LENGTH.</text>'
 '</g></g>'
 '<g><rect x="1118" y="74" width="404" height="158" fill="#fbfcfe" stroke="#94a3b8"/>'
 '<text x="1132" y="94" font-size="11.5" font-weight="700" fill="#0e7490" class="t">PERFORMANCE, 15 t · MAX 20 t</text>'
 '<g font-size="10.8" fill="#334155" class="t">'
 '<text x="1132" y="113">FULL (40 km), 30 g → 4.85 km/s · MACH 15.3</text>'
 '<text x="1132" y="130">FULL, 3 g HUMAN → 1.53 km/s · MACH 4.9</text>'
 '<text x="1132" y="147">PHASE 1 (14 km), 30 g → 2.87 km/s · MACH 9.1</text>'
 '<text x="1132" y="166" fill="#64748b">LATERAL g: 0 (STRAIGHT). v = √(2aL)</text>'
 '<text x="1132" y="183">L = 40,000 m, a = 294 m/s² ⇒ 4,850 m/s, t = 16.5 s</text>'
 '<text x="1132" y="202">ENERGY/SHOT 15 t: 49.0 MWh · PEAK 21.4 GW</text>'
 '<text x="1132" y="221" fill="#64748b">AT 20 t: 5.9 MN · 65.3 MWh · 28.5 GW</text>'
 '</g></g>')
bC = build(L=40, portal_e=1000, x0=150, pxkm=28, y0=648, vbw=1600, vbh=790,
   grid=[1000,2000,3000,4000,5000,6000],
   title="FULL LINE, WEST VALLEYS → STRAIGHT BORED TUNNEL @ 7.5° → MUZZLE 6,220 m",
   sub="WEST PORTAL ~1,000 m (CHAZOJUÁN) · MUZZLE 6,220 m (43 m BELOW THE 6,263 m PEAK) · EXIT 7.5° EAST · TRUE SCALE 1:1",
   footer="TRUE SCALE 1:1, HORIZONTAL = VERTICAL; THE 7.5° GRADE IS SHOWN AT ITS REAL ANGLE. +5,220 m OF CLIMB OVER 40 km, NO CURVE",
   portal_lab="WEST PORTAL ~1,000 m, CHAZOJUÁN",
   muz_lab="TUNNEL MUZZLE 6,220 m (43 m BELOW PEAK)",
   extra=notesC)

t=open(MAP, encoding="utf-8").read()
blkB='<h2 class="panel">PANEL B, PHASE 1 (BUILD FIRST): 14 km, PORTAL 4,393 m → TUNNEL MUZZLE 6,220 m, STRAIGHT 7.5° (TRUE SCALE 1:1)</h2>\n'+bB+'\n\n'
blkC='<h2 class="panel">PANEL C, FULL LINE (THE GROWTH TARGET): ~40 km, STRAIGHT BORED TUNNEL @ 7.5°, NO BEND (TRUE SCALE 1:1)</h2>\n'+bC+'\n\n'
t2=re.sub(r'<h2 class="panel">PANEL B,.*?(?=<h2 class="panel">PANEL C,)', blkB, t, count=1, flags=re.S)
t2=re.sub(r'<h2 class="panel">PANEL C,.*?(?=<h2 class="panel">PANEL D,)', blkC, t2, count=1, flags=re.S)
assert t2!=t and "PANEL B" in t2 and "PANEL D" in t2, "regex replace failed"
open(MAP,"w",encoding="utf-8").write(t2)
print("panels regenerated; B and C replaced")
