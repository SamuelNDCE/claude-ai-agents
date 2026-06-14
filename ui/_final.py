# Lock BRONTE to the terrain-real steepest 38 km route and redraw Panels B & C from SRTM.
import gzip, os, math, re
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); T=os.environ['TEMP']
V2A=os.path.join(HERE,"keraunos-v2a.html"); V2B=os.path.join(HERE,"keraunos-v2b.html")
MAP=os.path.join(HERE,"2026-06-12-bronte-chimborazo-routemap.html"); BLD=os.path.join(HERE,"keraunos_pdf_build.py")

# ---------- real terrain ----------
def load(t):
    raw=gzip.open(os.path.join(T,t),'rb').read()
    d=np.frombuffer(raw,dtype='>i2').reshape(3601,3601).astype(float); d[d<-100]=np.nan; return d
W79=load('S02W079.hgt.gz'); W80=load('S02W080.hgt.gz')
def elev(lat,lon):
    dem,LL=(W79,-79.0) if lon>=-79.0 else (W80,-80.0)
    r=(-1.0-lat)*3600.0; c=(lon-LL)*3600.0; r0,c0=int(r),int(c); fr,fc=r-r0,c-c0
    return (dem[r0,c0]*(1-fr)*(1-fc)+dem[r0+1,c0]*fr*(1-fc)+dem[r0,c0+1]*(1-fr)*fc+dem[r0+1,c0+1]*fr*fc)
KMLAT=110.57; KMLON=111.32*math.cos(math.radians(1.47))
MLAT,MLON,AZ,L=-1.480,-78.804,100,38.0
th=math.radians(AZ); dlat=math.cos(th)/KMLAT; dlon=math.sin(th)/KMLON
def gz(d): return float(elev(MLAT-(L-d)*dlat, MLON-(L-d)*dlon))  # d=0 west portal..38 muzzle
Pz, Mz = gz(0.0), gz(L)
def trackz(d): return Pz+(Mz-Pz)*d/L

def panel(d0,d1,vbw,vbh,title,sub,notes_html,footer,portal_lab,muz_lab,is_full,track_d0=0.0):
    prof=[(d, gz(d)) for d in np.arange(d0, d1+1e-6, 0.2)]
    emin=(min(z for _,z in prof)//500)*500-200
    emax=6400
    x0,xr,ytop,ybot=120,vbw-40,150,vbh-66
    sx=(xr-x0)/(d1-d0)
    sy=(ybot-ytop)/(emax-emin)
    vex=sy/(sx/1000.0)
    X=lambda d:x0+(d-d0)*sx; Y=lambda e:ybot-(e-emin)*sy
    # gridlines
    g=['<g stroke="#dbe3ee" stroke-width="1">']
    levels=[e for e in range(1000,6001,1000) if emin<=e<=emax]
    for e in levels: g.append(f'<line x1="{x0}" y1="{Y(e):.1f}" x2="{xr}" y2="{Y(e):.1f}"/>')
    g.append('</g><g font-size="10.5" fill="#64748b" font-family="Consolas,monospace" text-anchor="end">')
    for e in levels: g.append(f'<text x="{x0-6}" y="{Y(e)+3:.1f}">{e:,} m</text>')
    g.append('</g>')
    # real terrain polygon
    pp=" ".join(f"{X(d):.1f},{Y(z):.1f}" for d,z in prof)
    terr=f'<polygon points="{X(d0):.1f},{ybot:.1f} {pp} {X(d1):.1f},{ybot:.1f}" fill="#efe9da" stroke="#8a7f6a" stroke-width="1.4"/>'
    # track split tunnel/viaduct/grade between portal(0) and muzzle(L), clipped to [d0,d1]
    segs=[];cur=None
    for d,z in [(d,z) for d,z in prof if track_d0-1e-6<=d<=L+1e-6]:
        tz=trackz(d); mode='tunnel' if z>=tz+10 else('viaduct' if z<tz-10 else 'grade')
        if cur is None or cur[0]!=mode: cur=[mode,[]]; segs.append(cur)
        cur[1].append((d,tz))
    tk=[]
    for mode,ps in segs:
        if len(ps)<2: continue
        dd=" L ".join(f"{X(a):.1f},{Y(b):.1f}" for a,b in ps)
        if mode=='tunnel': tk.append(f'<path d="M {dd}" fill="none" stroke="#7c3aed" stroke-width="5.5" stroke-dasharray="13 8"/>')
        elif mode=='viaduct':
            tk.append("".join(f'<line x1="{X(a):.0f}" y1="{Y(b):.0f}" x2="{X(a):.0f}" y2="{Y(gz(a)):.0f}" stroke="#b45309" stroke-width="1.1"/>' for a,b in ps[::3]))
            tk.append(f'<path d="M {dd}" fill="none" stroke="#dc2626" stroke-width="5.5"/>')
        else: tk.append(f'<path d="M {dd}" fill="none" stroke="#7c3aed" stroke-width="5.5"/>')
    # amber power feed along the whole track in view
    pv=[(d,trackz(d)) for d,_ in prof if track_d0-1e-6<=d<=L+1e-6]
    if len(pv)>1: tk.append('<path d="M '+" L ".join(f"{X(a):.1f},{Y(b)+6:.1f}" for a,b in pv)+'" fill="none" stroke="#f59e0b" stroke-width="2.2" stroke-dasharray="4 5"/>')
    track="".join(tk)
    # summit marker (terrain peak in view)
    sd,sz=max(prof,key=lambda p:p[1]); summit=""
    if sz>6000:
        summit=(f'<path d="M {X(sd):.0f},{Y(sz)-2:.0f} l -6,11 l 12,0 Z" fill="#334155"/>'
                f'<text x="{X(sd):.0f}" y="{Y(sz)-8:.0f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#334155" font-family="Consolas,monospace">CHIMBORAZO 6,263 m</text>')
    # dots + guides
    P=(X(track_d0),Y(trackz(track_d0))); M=(X(min(d1,L)),Y(trackz(min(d1,L))))
    dots=(f'<line x1="{x0}" y1="{P[1]:.1f}" x2="{P[0]:.1f}" y2="{P[1]:.1f}" stroke="#22d3ee" stroke-width="1" stroke-dasharray="3 3"/>'
          f'<line x1="{x0}" y1="{M[1]:.1f}" x2="{M[0]:.1f}" y2="{M[1]:.1f}" stroke="#f43f5e" stroke-width="1" stroke-dasharray="3 3"/>'
          f'<circle cx="{P[0]:.1f}" cy="{P[1]:.1f}" r="6" fill="#22d3ee" stroke="#0f172a" stroke-width="1.5"/>'
          f'<circle cx="{M[0]:.1f}" cy="{M[1]:.1f}" r="6" fill="#f43f5e" stroke="#0f172a" stroke-width="1.5"/>')
    arr=(f'<path d="M {M[0]:.0f},{M[1]:.0f} L {M[0]+140:.0f},{M[1]-24:.0f}" fill="none" stroke="#0e7490" stroke-width="2.2" stroke-dasharray="8 7"/>'
         f'<path d="M {M[0]+152:.0f},{M[1]-28:.0f} l -16,-2 l 2,9 l -7,5 Z" fill="#0e7490"/>')
    labs=(f'<text x="{P[0]+12:.0f}" y="{P[1]+20:.0f}" font-size="11.5" fill="#0e7490" font-family="Consolas,monospace">{portal_lab}</text>'
          f'<text x="{M[0]-10:.0f}" y="{M[1]-26:.0f}" text-anchor="end" font-size="11.5" font-weight="700" fill="#b91c1c" font-family="Consolas,monospace">{muz_lab}</text>'
          f'<text x="{M[0]-10:.0f}" y="{M[1]-12:.0f}" text-anchor="end" font-size="10" fill="#0e7490" font-family="Consolas,monospace">FIRES EAST, 6.3° OVER THE EASTERN DROP</text>'
          f'<text x="{X((d0+min(d1,L))/2):.0f}" y="{Y(trackz((d0+min(d1,L))/2))+30:.0f}" text-anchor="middle" font-size="10.5" fill="#7c3aed" font-family="Consolas,monospace">DASHED = DEEP BORED TUNNEL · RED = VIADUCT WHERE THE LINE CROSSES A VALLEY</text>')
    da=[f'<line x1="{x0}" y1="{ybot+16:.0f}" x2="{xr}" y2="{ybot+16:.0f}" stroke="#64748b" stroke-width="1.3"/>','<g font-size="10" fill="#64748b" font-family="Consolas,monospace" text-anchor="middle">']
    maxd=L-track_d0; step=2 if maxd<20 else 5; dist=0
    while dist < maxd-1.5:
        da.append(f'<text x="{X(track_d0+dist):.0f}" y="{ybot+32:.0f}">{int(dist)}</text>'); dist+=step
    da.append(f'<text x="{X(L):.0f}" y="{ybot+32:.0f}">{int(round(maxd))} km, MUZZLE</text>')
    da.append('</g>')
    return (f'<svg viewBox="0 0 {vbw} {vbh}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI,Arial,sans-serif">'
            f'<rect x="4" y="4" width="{vbw-8}" height="{vbh-8}" fill="none" stroke="#334155" stroke-width="2"/>'
            f'<text x="{vbw//2}" y="34" text-anchor="middle" font-size="16" font-weight="700">{title}</text>'
            f'<text x="{vbw//2}" y="54" text-anchor="middle" font-size="11.5" fill="#0e7490" font-family="Consolas,monospace">{sub}</text>'
            f'{notes_html}{"".join(g)}{terr}{track}{summit}{dots}{arr}{labs}{"".join(da)}'
            f'<text x="{vbw//2}" y="{vbh-12}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#16a34a" font-family="Consolas,monospace">{footer}  ·  VERTICAL EXAGGERATION {vex:.1f}×</text></svg>')

notesC=('<g><rect x="86" y="74" width="540" height="64" fill="#fffbeb" stroke="#d97706"/>'
 '<text x="100" y="94" font-size="11" font-weight="700" fill="#92400e" font-family="Consolas,monospace">TERRAIN-LIMITED DESIGN (REAL SRTM 30 m)</text>'
 '<text x="100" y="111" font-size="10.3" fill="#92400e" font-family="Consolas,monospace">A STRAIGHT LINE CANNOT REACH THE 6,263 m SUMMIT (NEEDS A ~1.1 km VIADUCT).</text>'
 '<text x="100" y="127" font-size="10.3" fill="#92400e" font-family="Consolas,monospace">STEEPEST FEASIBLE 38 km LINE TOPS OUT AT 5,327 m, 936 m BELOW THE PEAK.</text></g>'
 '<g><rect x="1090" y="74" width="430" height="116" fill="#fbfcfe" stroke="#94a3b8"/>'
 '<text x="1104" y="93" font-size="11" font-weight="700" fill="#0e7490" font-family="Consolas,monospace">PERFORMANCE, 15 t · MAX 20 t</text>'
 '<g font-size="10.4" fill="#334155" font-family="Consolas,monospace">'
 '<text x="1104" y="111">FULL (38 km), 30 g → 4.73 km/s · MACH 15.0</text>'
 '<text x="1104" y="127">FULL, 3 g HUMAN → 1.49 km/s · MACH 4.7</text>'
 '<text x="1104" y="143">PHASE 1 (14 km), 30 g → 2.87 km/s · MACH 9.1</text>'
 '<text x="1104" y="159">L=38,000 m, a=294 m/s² ⇒ 4,730 m/s, t=16.1 s</text>'
 '<text x="1104" y="178" fill="#64748b">ENERGY 15 t: 46.6 MWh · PEAK 20.8 GW · LATERAL g: 0</text></g></g>')

bC=panel(0.0, L+4.0, 1600, 790,
  "CHIMBORAZO FULL LINE — REAL SRTM 30 m TERRAIN ALONG THE FIRE LINE",
  "WEST PORTAL 1,109 m → MUZZLE 5,327 m OVER 38 km · STRAIGHT 6.3° · FIRES EAST (AZ 100°)",
  notesC,
  "REAL TERRAIN; STEEPEST FEASIBLE STRAIGHT LINE IN THE 30–50 km RANGE",
  "WEST PORTAL 1,109 m, CHAZOJUÁN","MUZZLE 5,327 m (936 m BELOW PEAK)", True)
td0B=(3791-Pz)/(Mz-Pz)*L
bB=panel(td0B-1.5, L+3.0, 1600, 720,
  "PHASE 1, UPPER 14 km — REAL SRTM 30 m TERRAIN (BUILD FIRST)",
  "PORTAL 3,791 m → MUZZLE 5,327 m OVER 14 km · STRAIGHT 6.3° · 30 g → 2.87 km/s (MACH 9.1)",
  "","REAL TERRAIN; THE UPPER 14 km OF THE FULL LINE, BORED-TUNNEL FIRST BUILD",
  "PHASE-1 PORTAL 3,791 m","MUZZLE 5,327 m", False, track_d0=td0B)

# ---------- number cascade ----------
SPEC_V2A=[
 ('The muzzle is set at <b>6,220 m</b> (near the summit, ~43 m below the 6,263 m crest) so the exit emerges\n  high on the summit cone as a clean bored-tunnel mouth, just below the crest rather than a mast perched on top.',
  'The muzzle is set at <b>5,327 m</b> on the upper eastern flank, <b>936 m below the 6,263 m summit</b>. This is the highest a\n  straight 38 km line can reach on the real SRTM terrain: a straight line cannot meet the summit without a kilometre-tall viaduct\n  over the lower flank, so the muzzle exits where the line surfaces on the upper cone and fires east over the drop.'),
 ('Straight track at fixed exit angle θ = 7.5° (sin 7.5° = 0.1305):  L = Δh / sin θ',
  'Straight track at fixed exit angle θ = 6.3° (sin 6.3° = 0.1097):  L = Δh / sin θ'),
 ('Phase 1:   L = (6,220 − 4,393) / 0.1305 = 1,827 / 0.1305 = <b>14,000 m ≈ 14.0 km</b>',
  'Phase 1:   L = (5,327 − 3,791) / 0.1097 = 1,536 / 0.1097 = <b>14,000 m ≈ 14.0 km</b>'),
 ('Full line: L = (6,220 − 1,000) / 0.1305 = 5,220 / 0.1305 = <b>40,000 m ≈ 40 km</b>',
  'Full line: L = (5,327 − 1,109) / 0.1097 = 4,218 / 0.1097 = <b>38,450 m ≈ 38 km</b>'),
 ('Full line: v = √(2 × 294 × 40,000) = 4,850 m/s = <b>4.85 km/s</b>  (Mach 15.3), t = 16.5 s',
  'Full line: v = √(2 × 294 × 38,000) = 4,730 m/s = <b>4.73 km/s</b>  (Mach 15.0), t = 16.1 s'),
 ('½ × 15,000 × 4,850² = 1.76 × 10¹¹ J = <b>49.0 MWh</b>',
  '½ × 15,000 × 4,730² = 1.68 × 10¹¹ J = <b>46.6 MWh</b>'),
 ('<tr><td>Length @ 7.5°</td><td><b>14 km</b> (portal ~4,393 m, lower eastern flank)</td><td><b>~40 km</b> (west portal ~1,000 m, Chazojuán valleys)</td></tr>',
  '<tr><td>Length @ 6.3°</td><td><b>14 km</b> (portal ~3,791 m, upper flank)</td><td><b>~38 km</b> (west portal ~1,109 m, Chazojuán valleys)</td></tr>'),
 ('adds ~26 km of deep tunnel down the western slope','adds ~24 km of deep tunnel down the western slope'),
 ('Same muzzle for both: <b>6,220 m</b>, <b>7.5° east, straight</b>, ~43 m below peak elevation',
  'Same muzzle for both: <b>5,327 m</b>, <b>6.3° east, straight</b>, ~936 m below peak elevation'),
 ('4.85 km/s · <b>Mach ~15.3</b> · 16.5 s','4.73 km/s · <b>Mach ~15.0</b> · 16.1 s'),
 ('1.53 km/s · Mach ~4.9 · 52 s','1.49 km/s · Mach ~4.7 · 51 s'),
 ('49.0 MWh · 21.4 GW peak','46.6 MWh · 20.8 GW peak'),
 # spec table
 ('14 km, portal ~4,393 m','14 km, portal ~3,791 m'),
 ('Tunnel muzzle 6,220 m, 7.5° east','Tunnel muzzle 5,327 m, 6.3° east'),
 ('Single straight 7.5° grade, no curve at all; ~43 m below peak elevation',
  'Single straight 6.3° grade, no curve; ~936 m below peak (summit unreachable on a straight line)'),
 ('ρ ≈ 54% SL (p ≈ 47%)','ρ ≈ 53% SL (p ≈ 48%)'),
 ('Full ~40 km straight line later: Mach 15.3 cargo / 4.9 at human-rated 3 g',
  'Full ~38 km straight line later: Mach 15.0 cargo / 4.7 at human-rated 3 g'),
 # velocity ladder -> 38 km
 ('The velocity ladder over the 40 km line','The velocity ladder over the 38 km line'),
 ('which over 40 km is 4.85 km/s (Mach 15.3)','which over 38 km is 4.73 km/s (Mach 15.0)'),
 ('here is what dialing the same 40 km line','here is what dialing the same 38 km line'),
 ('Over L = 40 km:  a = v²/2L','Over L = 38 km:  a = v²/2L'),
 ('4 km/s: a = 4,000²/(2·40,000) = 200 m/s² = <b>20.4 g</b> · t = 20 s · F = 3.0 MN · E = 33 MWh',
  '4 km/s: a = 4,000²/(2·38,000) = 211 m/s² = <b>21.5 g</b> · t = 19 s · F = 3.2 MN · E = 33 MWh'),
 ('6 km/s: a = 6,000²/80,000 = 450 m/s² = <b>45.9 g</b> · t = 13.3 s · F = 6.8 MN · E = 75 MWh',
  '6 km/s: a = 6,000²/76,000 = 474 m/s² = <b>48.3 g</b> · t = 12.7 s · F = 7.1 MN · E = 75 MWh'),
 ('8 km/s: a = 8,000²/80,000 = 800 m/s² = <b>81.5 g</b> · t = 10 s · F = 12.0 MN · E = 133 MWh',
  '8 km/s: a = 8,000²/76,000 = 842 m/s² = <b>85.8 g</b> · t = 9.5 s · F = 12.6 MN · E = 133 MWh'),
 ('<tr><th>Target exit (over 40 km)</th>','<tr><th>Target exit (over 38 km)</th>'),
 ('<tr><td><b>4 km/s</b></td><td>20.4 g</td><td>20 s</td><td>3.0 MN</td>','<tr><td><b>4 km/s</b></td><td>21.5 g</td><td>19 s</td><td>3.2 MN</td>'),
 ('<tr><td><b>6 km/s</b></td><td>45.9 g</td><td>13.3 s</td><td>6.8 MN</td>','<tr><td><b>6 km/s</b></td><td>48.3 g</td><td>12.7 s</td><td>7.1 MN</td>'),
 ('<tr><td><b>8 km/s ≈ orbital</b></td><td>81.5 g</td><td>10 s</td><td>12.0 MN</td>','<tr><td><b>8 km/s ≈ orbital</b></td><td>85.8 g</td><td>9.5 s</td><td>12.6 MN</td>'),
 ('at 81 g (well inside','at 86 g (well inside'),
 # sonic boom -> muzzle 5,327
 ('A Mach-15 body leaving the muzzle at 6,220 m is loud','A Mach-15 body leaving the muzzle at 5,327 m is loud'),
 ('BRONTE exits at <b>Mach 15</b> and only <b>6,220 m (~6.2 km)</b>, ~2.6× closer to the ground and ~7× faster.',
  'BRONTE exits at <b>Mach 15</b> and only <b>5,327 m (~5.3 km)</b>, ~3.0× closer to the ground and ~7.5× faster.'),
 ('altitude factor (16/6.2)<sup>3/4</sup> ≈ 2.1× · Mach factor ((15.3²−1)/(2²−1))<sup>1/8</sup> ≈ 1.7× ⇒ ~<b>3.6× Concorde</b>',
  'altitude factor (16/5.3)<sup>3/4</sup> ≈ 2.3× · Mach factor ((15²−1)/(2²−1))<sup>1/8</sup> ≈ 1.7× ⇒ ~<b>4× Concorde</b>'),
 ('⇒ order <b>6–12 psf (~300–600 Pa) near the track</b>','⇒ order <b>8–14 psf (~400–700 Pa) near the track</b>'),
 ('fires Mach-7-class test articles from 6,220 m','fires Mach-7-class test articles from 5,327 m'),
]
# globals for v2b + map(non-panel) + build (panels in map get regenerated after)
GLB=[
 ("Mach 15.3","Mach 15.0"),("MACH 15.3","MACH 15.0"),("~15.3","~15.0"),
 ("4.85 km/s","4.73 km/s"),("1.53 km/s","1.49 km/s"),
 ("Mach ~4.9","Mach ~4.7"),("MACH ~4.9","MACH ~4.7"),("Mach 4.9","Mach 4.7"),("MACH 4.9","MACH 4.7"),
 ("49.0 MWh","46.6 MWh"),("65.3 MWh","62.1 MWh"),("21.4 GW","20.8 GW"),("28.5 GW","27.8 GW"),
 ("6,220","5,327"),("7.5°","6.3°"),
 ("portal ~1,000 m","portal ~1,109 m"),("PORTAL ~1,000 m","PORTAL ~1,109 m"),
 ("1,000 m (CHAZOJUÁN)","1,109 m (CHAZOJUÁN)"),("1,000 m (Chazojuán)","1,109 m (Chazojuán)"),
 ("~40 km","~38 km"),("40 km","38 km"),("(40 km)","(38 km)"),
 ("4,393","3,791"),("43 m below","936 m below"),("43 m BELOW","936 m BELOW"),
 ("16.5 s","16.1 s"),
]
for path,specs in ((V2A,SPEC_V2A),(V2B,[]),(MAP,[]),(BLD,[])):
    t=open(path,encoding="utf-8").read()
    for a,b in specs: t=t.replace(a,b)
    for a,b in GLB: t=t.replace(a,b)
    open(path,"w",encoding="utf-8").write(t)

# ---------- splice new panels into the map ----------
t=open(MAP,encoding="utf-8").read()
blkB='<h2 class="panel">PANEL B, PHASE 1 (BUILD FIRST): UPPER 14 km, PORTAL 3,791 m → MUZZLE 5,327 m, STRAIGHT 6.3° (REAL SRTM TERRAIN)</h2>\n'+bB+'\n\n'
blkC='<h2 class="panel">PANEL C, FULL LINE (THE GROWTH TARGET): 38 km, PORTAL 1,109 m → MUZZLE 5,327 m, STRAIGHT 6.3° (REAL SRTM TERRAIN)</h2>\n'+bC+'\n\n'
t=re.sub(r'<h2 class="panel">PANEL B,.*?(?=<h2 class="panel">PANEL C,)', blkB, t, count=1, flags=re.S)
t=re.sub(r'<h2 class="panel">PANEL C,.*?(?=<h2 class="panel">PANEL D,)', blkC, t, count=1, flags=re.S)
open(MAP,"w",encoding="utf-8").write(t)
print(f"DONE. portal {Pz:.0f} m, muzzle {Mz:.0f} m, grade {math.degrees(math.atan((Mz-Pz)/(L*1000))):.2f} deg, panels redrawn")
