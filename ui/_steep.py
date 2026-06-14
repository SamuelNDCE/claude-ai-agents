import gzip, os, math
import numpy as np
T=os.environ['TEMP']
def load(t):
    raw=gzip.open(os.path.join(T,t),'rb').read()
    d=np.frombuffer(raw,dtype='>i2').reshape(3601,3601).astype(float); d[d<-100]=np.nan; return d
W79=load('S02W079.hgt.gz'); W80=load('S02W080.hgt.gz')
def elev(lat,lon):
    dem,LL=(W79,-79.0) if lon>=-79.0 else (W80,-80.0)
    r=(-1.0-lat)*3600.0; c=(lon-LL)*3600.0
    r0,c0=int(r),int(c)
    if r0<0 or c0<0 or r0+1>3600 or c0+1>3600: return np.nan
    fr,fc=r-r0,c-c0
    return (dem[r0,c0]*(1-fr)*(1-fc)+dem[r0+1,c0]*fr*(1-fc)+dem[r0,c0+1]*(1-fr)*fc+dem[r0+1,c0+1]*fr*fc)
KMLAT=110.57; KMLON=111.32*math.cos(math.radians(1.47))
def evalline(mlat,mlon,az,L):
    th=math.radians(az); dlat=math.cos(th)/KMLAT; dlon=math.sin(th)/KMLON
    s=np.arange(0,L+1e-6,0.3)
    zz=np.array([elev(mlat-(L-d)*dlat, mlon-(L-d)*dlon) for d in s])
    if np.any(np.isnan(zz)): return None
    ze=zz[0]; zm=zz[-1]+30
    line=ze+(zm-ze)*s/L; dev=zz-line
    return ze,zm,float(dev.max()),float(-dev.min()),math.degrees(math.atan((zm-ze)/(L*1000)))
print("steepest feasible straight line per length (fill<=180 m, cut<=2600 m):")
print(" L | grade | portal | muzzle | rise | cut | fill | az | muz | exitspeed30g")
overall=None
for L in (30,34,38,42,46,50):
    best=None
    for mlat in np.arange(-1.56,-1.38,0.008):
        for mlon in np.arange(-78.90,-78.62,0.008):
            zm0=elev(mlat,mlon)
            if not(zm0==zm0) or zm0<4000: continue
            if zm0-elev(mlat,mlon+3.0/KMLON)<350: continue
            for az in (80,85,90,95,100,105):
                r=evalline(mlat,mlon,az,L)
                if r is None: continue
                ze,zm,cut,fill,grade=r
                if fill>180 or cut>2600: continue
                if best is None or grade>best[0]:
                    best=(grade,ze,zm,cut,fill,az,mlat,mlon)
    if best:
        grade,ze,zm,cut,fill,az,mlat,mlon=best
        v=math.sqrt(2*294*L*1000)
        print(f"{L:>3} | {grade:4.2f}° | {ze:6.0f} | {zm:6.0f} | {zm-ze:5.0f} | {cut:5.0f} | {fill:4.0f} | {az} | {mlat:.3f},{mlon:.3f} | {v:.0f} m/s")
        if overall is None or grade>overall[0]: overall=(grade,L,ze,zm,cut,fill,az,mlat,mlon)
print("STEEPEST:", overall)
