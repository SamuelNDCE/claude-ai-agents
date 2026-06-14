import gzip, os, math, json
import numpy as np
T=os.environ['TEMP']
def load(tile, lon_left):
    raw=gzip.open(os.path.join(T,tile),'rb').read()
    d=np.frombuffer(raw,dtype='>i2').reshape(3601,3601).astype(float)
    d[d<-100]=np.nan
    return d, lon_left
W79=load('S02W079.hgt.gz',-79.0)   # lon -79..-78
W80=load('S02W080.hgt.gz',-80.0)   # lon -80..-79
LAT_TOP=-1.0
def elev(lat,lon):
    dem,LL=(W79 if lon>=-79.0 else W80)
    r=(LAT_TOP-lat)*3600.0; c=(lon-LL)*3600.0
    r0,c0=int(r),int(c); fr,fc=r-r0,c-c0
    return (dem[r0,c0]*(1-fr)*(1-fc)+dem[r0+1,c0]*fr*(1-fc)
            +dem[r0,c0+1]*(1-fr)*fc+dem[r0+1,c0+1]*fr*fc)
KMLAT=110.57; KMLON=111.32*math.cos(math.radians(1.47))
SUM_LAT,SUM_LON=-1.4692,-78.8175
print("summit DEM elev:", round(float(elev(SUM_LAT,SUM_LON))))
# fire EAST (az90): travel +lon. track extends WEST of muzzle. muzzle at summit lon.
# sample from 45 km west of summit to 6 km east of summit, same lat
prof=[]
for d in np.arange(-45.0, 6.01, 0.25):   # d = km east of summit (negative = west)
    lon=SUM_LON + d/KMLON
    prof.append((round(float(d),2), round(float(elev(SUM_LAT,lon)),1)))
# distance west to reach 1000 m
west=[(d,z) for d,z in prof if d<0]
hit1000=next((d for d,z in sorted(west) if z<=1000), None)
print("elev 40 km W:", dict(prof)[-40.0], " 35kmW:", dict(prof)[-35.0],
      " 30kmW:", dict(prof)[-30.0], " 20kmW:", dict(prof)[-20.0], " 10kmW:", dict(prof)[-10.0])
print("first point <=1000 m going west at d(km)=", hit1000)
# straight tunnel from portal(40 km W) to muzzle near summit(6220), cut/fill
P_d,P_z=-40.0, dict(prof)[-40.0]
M_d,M_z=0.0, 6220.0
L=(M_d-P_d)   # km
line=lambda d: P_z+(M_z-P_z)*(d-P_d)/(M_d-P_d)
seg=[(d,z) for d,z in prof if P_d<=d<=M_d]
dev=[z-line(d) for d,z in seg]   # +terrain above track(tunnel/cut), -below(viaduct)
print(f"40km line portal {P_z:.0f} m -> muzzle 6220 m, grade {math.degrees(math.atan((M_z-P_z)/40000)):.2f} deg")
print(f"  max CUT (terrain above track): {max(dev):.0f} m   max FILL (track above ground): {-min(dev):.0f} m")
json.dump({"profile":prof,"summit":round(float(elev(SUM_LAT,SUM_LON)))},
          open(os.path.join(os.path.dirname(__file__),'_realprofile.json'),'w'))
print("profile points:", len(prof), "-> _realprofile.json")
