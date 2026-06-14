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
    r0,c0=int(r),int(c); fr,fc=r-r0,c-c0
    if r0<0 or c0<0 or r0+1>3600 or c0+1>3600: return np.nan
    return (dem[r0,c0]*(1-fr)*(1-fc)+dem[r0+1,c0]*fr*(1-fc)+dem[r0,c0+1]*(1-fr)*fc+dem[r0+1,c0+1]*fr*fc)
KMLAT=110.57; KMLON=111.32*math.cos(math.radians(1.47))

def evalline(m_lat,m_lon,az,L,muz_extra=30):
    th=math.radians(az); dlat=math.cos(th)/KMLAT; dlon=math.sin(th)/KMLON
    e_lat=m_lat-L*dlat; e_lon=m_lon-L*dlon
    s=np.arange(0,L+1e-6,0.2)
    zz=np.array([elev(e_lat+d*dlat,e_lon+d*dlon) for d in s])
    if np.any(np.isnan(zz)): return None
    z_entry=zz[0]; z_muz=zz[-1]+muz_extra
    line=z_entry+(z_muz-z_entry)*s/L
    dev=zz-line
    return z_entry,z_muz,float(dev.max()),float(-dev.min()),math.degrees(math.atan((z_muz-z_entry)/(L*1000)))

# scan muzzle points that fire east over a drop; maximize muzzle alt & length with feasible fill
print("L_km | best muzzle | portal | grade | maxCUT(tunnel) | maxFILL(viaduct) | az | muz_lat,lon")
for L in (14,20,26,32,38,40):
    best=None
    for mlat in np.arange(-1.56,-1.38,0.006):
        for mlon in np.arange(-78.90,-78.62,0.006):
            zm=elev(mlat,mlon)
            if not (zm==zm) or zm<4200: continue
            zeast=elev(mlat,mlon+3.0/KMLON)        # 3 km east
            if zm-zeast<400: continue              # need an eastern drop to fire over
            for az in (80,85,90,95,100):
                r=evalline(mlat,mlon,az,L)
                if r is None: continue
                z_entry,z_muz,cut,fill,grade=r
                if fill>180: continue              # only hard limit: viaduct<=180m (tunnels can be deep)
                key=(z_muz, -fill)
                if best is None or key>best[0]:
                    best=(key,z_entry,z_muz,cut,fill,grade,az,mlat,mlon)
    if best:
        _,ze,zm,cut,fill,grade,az,mlat,mlon=best
        print(f"{L:>4} | {zm:8.0f} | {ze:6.0f} | {grade:4.2f}° | {cut:6.0f} m | {fill:6.0f} m | {az} | {mlat:.3f},{mlon:.3f}")
    else:
        print(f"{L:>4} | none feasible (fill<=180 m, cut<=1600 m)")
