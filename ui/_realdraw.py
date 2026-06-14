import gzip, os, math, subprocess
import numpy as np
T=os.environ['TEMP']; HERE=os.path.dirname(os.path.abspath(__file__))
def load(t):
    raw=gzip.open(os.path.join(T,t),'rb').read()
    d=np.frombuffer(raw,dtype='>i2').reshape(3601,3601).astype(float); d[d<-100]=np.nan; return d
W79=load('S02W079.hgt.gz'); W80=load('S02W080.hgt.gz')
def elev(lat,lon):
    dem,LL=(W79,-79.0) if lon>=-79.0 else (W80,-80.0)
    r=(-1.0-lat)*3600.0; c=(lon-LL)*3600.0
    r0,c0=int(r),int(c); fr,fc=r-r0,c-c0
    return (dem[r0,c0]*(1-fr)*(1-fc)+dem[r0+1,c0]*fr*(1-fc)+dem[r0,c0+1]*(1-fr)*fc+dem[r0+1,c0+1]*fr*fc)
KMLAT=110.57; KMLON=111.32*math.cos(math.radians(1.47))
# chosen feasible 40 km route: muzzle near (-1.464,-78.804), az 100, fire ESE
MLAT,MLON,AZ,L=-1.480,-78.804,100,38.0
th=math.radians(AZ); dlat=math.cos(th)/KMLAT; dlon=math.sin(th)/KMLON
def at(d): return elev(MLAT-(L-d)*dlat, MLON-(L-d)*dlon)   # d=0 portal .. d=L muzzle
prof=[(d, float(at(d))) for d in np.arange(0, L+5.01, 0.2)]   # +5 km east of muzzle
Pz=prof[0][1]; Mz=float(at(L))
print(f"portal {Pz:.0f} m, muzzle {Mz:.0f} m, grade {math.degrees(math.atan((Mz-Pz)/(L*1000))):.2f} deg")
# straight track portal->muzzle
def trackz(d): return Pz+(Mz-Pz)*d/L
# ---- SVG (vertical exaggeration, real terrain) ----
VBW,VBH=1600,560
x0,xpad=120,40; plotw=VBW-x0-xpad
emax=6400; emin=600
sx=plotw/(L+5)            # px per km
VEXAG=2.6
sy=sx/1000*VEXAG          # px per m (exaggerated)
ybase=VBH-70             # y at emin
X=lambda d:x0+d*sx
Y=lambda e:ybase-(e-emin)*sy
# terrain polygon
pts=" ".join(f"{X(d):.1f},{Y(z):.1f}" for d,z in prof)
terr=f'<polygon points="{X(0):.1f},{ybase:.1f} {pts} {X(prof[-1][0]):.1f},{ybase:.1f}" fill="#efe9da" stroke="#8a7f6a" stroke-width="1.4"/>'
# track split into tunnel (terrain>=track) vs viaduct (terrain<track), 0..L
segs=[];cur=None
for d,z in [(d,z) for d,z in prof if d<=L+1e-6]:
    mode='tunnel' if z>=trackz(d)+8 else ('viaduct' if z<trackz(d)-8 else 'grade')
    if cur is None or cur[0]!=mode: cur=[mode,[]]; segs.append(cur)
    cur[1].append((d,trackz(d)))
def seg_path(seg):
    mode,ps=seg
    if len(ps)<2: return ""
    d=" L ".join(f"{X(a):.1f},{Y(b):.1f}" for a,b in ps)
    if mode=='tunnel':
        return f'<path d="M {d}" fill="none" stroke="#7c3aed" stroke-width="5" stroke-dasharray="13 8"/>'
    if mode=='viaduct':
        # piers down to terrain
        piers="".join(f'<line x1="{X(a):.0f}" y1="{Y(b):.0f}" x2="{X(a):.0f}" y2="{Y(at(a)):.0f}" stroke="#b45309" stroke-width="1.2"/>' for a,b in ps[::4])
        return piers+f'<path d="M {d}" fill="none" stroke="#dc2626" stroke-width="5"/>'
    return f'<path d="M {d}" fill="none" stroke="#7c3aed" stroke-width="5"/>'
track="".join(seg_path(s) for s in segs)
# gridlines every 1000 m
grid=['<g stroke="#dbe3ee" stroke-width="1">']
for e in range(1000,6001,1000): grid.append(f'<line x1="{x0}" y1="{Y(e):.1f}" x2="{VBW-xpad}" y2="{Y(e):.1f}"/>')
grid.append('</g><g font-size="10.5" fill="#64748b" font-family="Consolas,monospace" text-anchor="end">')
for e in range(1000,6001,1000): grid.append(f'<text x="{x0-6}" y="{Y(e)+3:.1f}">{e:,} m</text>')
grid.append('</g>')
# summit marker (peak of terrain near muzzle)
sd,sz=max(((d,z) for d,z in prof if abs(d-L)<6), key=lambda p:p[1])
summit=(f'<path d="M {X(sd):.0f},{Y(sz)-2:.0f} l -6,11 l 12,0 Z" fill="#334155"/>'
        f'<text x="{X(sd):.0f}" y="{Y(sz)-8:.0f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#334155" font-family="Consolas,monospace">CHIMBORAZO 6,263 m</text>')
# dots + altitude guides
P=(X(0),Y(Pz)); M=(X(L),Y(Mz))
dots=(f'<line x1="{x0}" y1="{P[1]:.1f}" x2="{P[0]:.1f}" y2="{P[1]:.1f}" stroke="#22d3ee" stroke-width="1" stroke-dasharray="3 3"/>'
      f'<line x1="{x0}" y1="{M[1]:.1f}" x2="{M[0]:.1f}" y2="{M[1]:.1f}" stroke="#f43f5e" stroke-width="1" stroke-dasharray="3 3"/>'
      f'<circle cx="{P[0]:.1f}" cy="{P[1]:.1f}" r="6" fill="#22d3ee" stroke="#0f172a" stroke-width="1.5"/>'
      f'<circle cx="{M[0]:.1f}" cy="{M[1]:.1f}" r="6" fill="#f43f5e" stroke="#0f172a" stroke-width="1.5"/>')
# fire-east arrow
arr=(f'<path d="M {M[0]:.0f},{M[1]:.0f} L {M[0]+150:.0f},{M[1]-26:.0f}" fill="none" stroke="#0e7490" stroke-width="2.2" stroke-dasharray="8 7"/>'
     f'<path d="M {M[0]+162:.0f},{M[1]-30:.0f} l -16,-2 l 2,9 l -7,5 Z" fill="#0e7490"/>')
labs=(f'<text x="{P[0]+12:.0f}" y="{P[1]+20:.0f}" font-size="11.5" fill="#0e7490" font-family="Consolas,monospace">WEST PORTAL {Pz:.0f} m</text>'
      f'<text x="{M[0]-10:.0f}" y="{M[1]-26:.0f}" text-anchor="end" font-size="11.5" font-weight="700" fill="#b91c1c" font-family="Consolas,monospace">MUZZLE {Mz:.0f} m ({6263-int(round(Mz))} m BELOW PEAK)</text>'
      f'<text x="{M[0]-10:.0f}" y="{M[1]-12:.0f}" text-anchor="end" font-size="10" fill="#0e7490" font-family="Consolas,monospace">FIRES EAST OVER THE EASTERN DROP</text>'
      f'<text x="{X(L*0.42):.0f}" y="{Y(trackz(L*0.42))+34:.0f}" font-size="11" fill="#7c3aed" font-family="Consolas,monospace">DASHED PURPLE = DEEP BORED TUNNEL (UP TO ~1.5 km COVER)</text>'
      f'<text x="{X(L*0.42):.0f}" y="{Y(trackz(L*0.42))+50:.0f}" font-size="11" fill="#dc2626" font-family="Consolas,monospace">SOLID RED = ELEVATED VIADUCT (≤ ~160 m) WHERE THE LINE CROSSES VALLEYS</text>')
# distance axis
da=[f'<line x1="{x0}" y1="{ybase+18:.0f}" x2="{VBW-xpad}" y2="{ybase+18:.0f}" stroke="#64748b" stroke-width="1.3"/>',
    '<g font-size="10" fill="#64748b" font-family="Consolas,monospace" text-anchor="middle">']
for k in range(0,int(L)+5+1,5):
    lab=f"{k}" if k!=int(L) else f"{int(L)} km, MUZZLE"
    da.append(f'<text x="{X(k):.0f}" y="{ybase+34:.0f}">{lab}</text>')
da.append('</g>')
svg=(f'<svg viewBox="0 0 {VBW} {VBH}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI,Arial,sans-serif">'
 f'<rect x="4" y="4" width="{VBW-8}" height="{VBH-8}" fill="none" stroke="#334155" stroke-width="2"/>'
 f'<text x="{VBW//2}" y="32" text-anchor="middle" font-size="16" font-weight="700">CHIMBORAZO FULL LINE, REAL SRTM 30 m TERRAIN ALONG THE FIRE LINE (AZ {AZ}°, EAST)</text>'
 f'<text x="{VBW//2}" y="51" text-anchor="middle" font-size="11.5" fill="#0e7490" font-family="Consolas,monospace">WEST PORTAL {Pz:.0f} m -> MUZZLE {Mz:.0f} m OVER {int(L)} km, STRAIGHT {math.degrees(math.atan((Mz-Pz)/(L*1000))):.1f}deg, VERTICAL EXAGGERATION {VEXAG}x</text>'
 f'{"".join(grid)}{terr}{track}{summit}{dots}{arr}{labs}{"".join(da)}'
 f'<text x="{VBW//2}" y="{VBH-12}" text-anchor="middle" font-size="10.5" fill="#16a34a" font-family="Consolas,monospace">TERRAIN IS REAL SRTM DATA; A STRAIGHT LINE CANNOT REACH THE 6,263 m SUMMIT WITHOUT A ~1.1 km VIADUCT, SO THE MUZZLE TOPS OUT ON THE UPPER FLANK</text></svg>')
open(os.path.join(HERE,"_realC.html"),"w",encoding="utf-8").write(
 f'<!doctype html><meta charset=utf-8><style>html,body{{margin:0;background:#fff}}svg{{width:1600px;height:auto;display:block}}</style>{svg}')
subprocess.run([r"C:\Program Files\Google\Chrome\Application\chrome.exe","--headless=new","--disable-gpu","--hide-scrollbars",
  f"--screenshot={os.path.join(HERE,'_realC.png')}","--window-size=1600,560","file:///"+os.path.join(HERE,"_realC.html").replace(os.sep,'/')],check=True,capture_output=True)
print("rendered _realC.png")
