import gzip, os, json, math
import numpy as np

# ---- load both SRTM tiles: S02W079 (lon -79..-78) and S02W080 (lon -80..-79) ----
def load(name):
    raw = gzip.open(os.path.join(os.environ['TEMP'], name), 'rb').read()
    d = np.frombuffer(raw, dtype='>i2').reshape(3601, 3601).astype(float)
    d[d < -100] = np.nan
    return d
T79, T80 = load('S02W079.hgt.gz'), load('S02W080.hgt.gz')
LAT_TOP = -1.0
def elev(lat, lon):
    if lon >= -79.0:
        dem, lon_left = T79, -79.0
    else:
        dem, lon_left = T80, -80.0
    r = (LAT_TOP - lat) * 3600.0
    c = (lon - lon_left) * 3600.0
    r0, c0 = int(r), int(c)
    fr, fc = r - r0, c - c0
    return (dem[r0,c0]*(1-fr)*(1-fc) + dem[r0+1,c0]*fr*(1-fc)
            + dem[r0,c0+1]*(1-fr)*fc + dem[r0+1,c0+1]*fr*fc)

KMLAT, KMLON = 110.57, 111.32*math.cos(math.radians(1.45))
S_LAT, S_LON = -1.4692, -78.8175   # Whymper summit

# ---- optimizer: straight line in vertical plane through/near the summit ----
# params: azimuth (fire direction), lateral offset at summit (km, +north), line altitude at summit station h0, slope theta
results = []
for az in (80, 85, 90, 95):
    th_az = math.radians(az)
    dlat, dlon = math.cos(th_az)/KMLAT, math.sin(th_az)/KMLON   # per km along fire dir
    plat, plon = math.cos(th_az+math.pi/2)/KMLAT, math.sin(th_az+math.pi/2)/KMLON  # perp (left of fire dir = north-ish)
    for off in (-0.5, 0.0, 0.5, 1.0):
        blat, blon = S_LAT + off*plat, S_LON + off*plon  # line passes nearest summit here (s=0)
        for h0 in (5500, 5700, 5900, 6100):
            for theta in (6.5, 7.5, 8.5, 9.5, 10.5):
                t = math.tan(math.radians(theta))*1000  # m per km
                s = np.arange(-44, 4.01, 0.2)
                terr = np.array([elev(blat + d*dlat, blon + d*dlon) for d in s])
                if np.any(np.isnan(terr)): continue
                line = h0 + t*s
                dev = line - terr   # + above ground (viaduct), - below (tunnel)
                # exit: first s>0 where line breaks out of east face
                ie = None
                for i in range(len(s)):
                    if s[i] > 0 and dev[i] >= 0:
                        ie = i; break
                if ie is None or s[ie] > 3.5: continue
                # entry: westernmost surface crossing (line at/above terrain) before going under for good
                iw = None
                for i in range(len(s)):
                    if s[i] < -18 and dev[i] >= -15:
                        iw = i; break
                if iw is None: continue
                seg = slice(iw, ie+1)
                via = dev[seg].copy(); via[via<0] = 0
                tun = -dev[seg].copy(); tun[tun<0] = 0
                maxvia, maxtun = float(via.max()), float(tun.max())
                L = (s[ie]-s[iw])
                if L < 24 or L > 42: continue
                exit_alt = float(line[ie])
                if exit_alt < 5300: continue
                # score: viaduct over 350 m heavily penalized; deep cover penalized lightly; longer track rewarded
                score = max(0, maxvia-350)*8 + maxvia + maxtun*0.35 - L*18
                results.append((score, az, off, h0, theta, float(s[iw]), float(s[ie]), L,
                                exit_alt, maxvia, maxtun, blat, blon, dlat, dlon))
results.sort()
print("top 5: score az off h0 theta s_entry s_exit L exit_alt maxvia maxtun")
for r in results[:5]:
    print("  " + " ".join(f"{v:.2f}" if isinstance(v,float) else str(v) for v in r[:11]))

score, az, off, h0, theta, s_in, s_out, L, exit_alt, maxvia, maxtun, blat, blon, dlat, dlon = results[0]
t = math.tan(math.radians(theta))*1000
# full profile for drawing: s from entry-4 to exit+8
s = np.arange(s_in-4, s_out+8.01, 0.2)
prof = [(float(d), float(elev(blat+d*dlat, blon+d*dlon))) for d in s]
entry_lat, entry_lon = blat + s_in*dlat, blon + s_in*dlon
exit_lat,  exit_lon  = blat + s_out*dlat, blon + s_out*dlon
entry_alt = h0 + t*s_in
g = 9.80665
v30 = math.sqrt(2*30*g*L*1000); v10 = math.sqrt(2*10*g*L*1000); v3 = math.sqrt(2*3*g*L*1000)
Ta = 288.15-0.0065*exit_alt; a_s = math.sqrt(1.4*287.05*Ta)
print(f"CHOSEN: az {az} off {off} km h0 {h0} theta {theta} deg")
print(f"  entry ({entry_lat:.4f},{entry_lon:.4f}) {entry_alt:.0f} m  exit ({exit_lat:.4f},{exit_lon:.4f}) {exit_alt:.0f} m  L {L:.1f} km")
print(f"  maxviaduct {maxvia:.0f} m, maxcover {maxtun:.0f} m")
print(f"  30g {v30:.0f} m/s M{v30/a_s:.1f} | 10g {v10:.0f} M{v10/a_s:.1f} | 3g {v3:.0f} M{v3/a_s:.1f}")
json.dump({"az":az,"off":off,"h0":h0,"theta":theta,"s_in":s_in,"s_out":s_out,"L":L,
           "entry":[float(entry_lat),float(entry_lon),float(entry_alt)],
           "exit":[float(exit_lat),float(exit_lon),float(exit_alt)],
           "maxvia":maxvia,"maxtun":maxtun,"base":[float(blat),float(blon)],
           "dlat":float(dlat),"dlon":float(dlon),"profile":prof},
          open(os.path.join(os.path.dirname(__file__),'bronte_full_route.json'),'w'))

# ---- map ----
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects
from matplotlib.colors import LightSource, LinearSegmentedColormap

lat0, lat1 = -1.62, -1.30
lon0, lon1 = -79.30, -78.60
# stitch columns: W080 part lon -79.30..-79.0, W079 part -79.0..-78.60
r0, r1 = int((LAT_TOP-lat1)*3600), int((LAT_TOP-lat0)*3600)
cW0, cW1 = int((lon0-(-80.0))*3600), 3600
cE0, cE1 = 0, int((lon1-(-79.0))*3600)
sub = np.hstack([T80[r0:r1+1, cW0:cW1], T79[r0:r1+1, cE0:cE1+1]])
extent = [lon0, lon1, lat0, lat1]

terrain_cmap = LinearSegmentedColormap.from_list('andes', [
    (0.00,'#3f6132'),(0.15,'#5d7a40'),(0.30,'#8b9655'),(0.45,'#b2a371'),
    (0.62,'#c3ab88'),(0.76,'#cbb9a4'),(0.88,'#d8cfc4'),(1.00,'#f4f1ec')])
ls = LightSource(azdeg=315, altdeg=45)
norm_z = np.clip((sub-1200)/(6300-1200), 0, 1)
rgb = ls.shade_rgb(terrain_cmap(norm_z)[:,:,:3], sub, vert_exag=0.06, blend_mode='soft', dx=30, dy=30)
gmask = sub >= 5100
for ch, v in enumerate((0.97, 0.98, 1.0)):
    rgb[:,:,ch] = np.where(gmask, 0.25*rgb[:,:,ch]+0.75*v, rgb[:,:,ch])

fig, ax = plt.subplots(figsize=(18, 10.3), dpi=110)
ax.imshow(rgb, extent=extent, aspect=KMLAT/KMLON)
lonv = np.linspace(lon0, lon1, sub.shape[1]); latv = np.linspace(lat1, lat0, sub.shape[0])
ax.contour(lonv, latv, sub, levels=np.arange(1400,6400,200), colors='#3b3528', linewidths=0.3, alpha=0.5)
cs2 = ax.contour(lonv, latv, sub, levels=np.arange(2000,6400,1000), colors='#3b3528', linewidths=0.85, alpha=0.7)
ax.clabel(cs2, fmt='%d', fontsize=7.5)

def seg_pts(a, b):
    return ([blon+a*dlon, blon+b*dlon], [blat+a*dlat, blat+b*dlat])
# full line
xs, ys = seg_pts(s_in, s_out)
ax.plot(xs, ys, color='#7c3aed', lw=4.2, solid_capstyle='round', zorder=5)
ax.plot(xs, ys, color='white', lw=1.5, ls=(0,(2,3)), zorder=6)
# phase-1 (eastern 14 km) highlight
xs1, ys1 = seg_pts(s_out-14, s_out)
ax.plot(xs1, ys1, color='#f59e0b', lw=2.2, zorder=6)
# downrange
xs2, ys2 = seg_pts(s_out, s_out+8)
ax.plot(xs2, ys2, color='#0e7490', lw=2, ls='--', zorder=5)
ax.annotate('', xy=(xs2[1], ys2[1]), xytext=(xs2[0], ys2[0]),
            arrowprops=dict(arrowstyle='-|>', color='#0e7490', lw=2), zorder=6)
ax.plot(entry_lon, entry_lat, 'o', ms=10, mfc='#22d3ee', mec='#0f172a', zorder=7)
ax.plot(exit_lon, exit_lat, 'o', ms=10, mfc='#f43f5e', mec='#0f172a', zorder=7)

def label(lon, lat, txt, dx=0.004, dy=0.004, fs=11, w='bold', c='#0f172a'):
    ax.annotate(txt, (lon, lat), xytext=(lon+dx, lat+dy), fontsize=fs, fontweight=w,
                color=c, zorder=8,
                path_effects=[matplotlib.patheffects.withStroke(linewidth=2.6, foreground='white')])
label(S_LON, S_LAT, 'CHIMBORAZO 6,263 m', -0.020, -0.038, 13)
label(-78.750, -1.404, 'CARIHUAIRAZO 5,018 m', 0.004, 0.012, 10)
label(entry_lon, entry_lat, f'WEST PORTAL {entry_alt:.0f} m', -0.010, -0.026, 12, c='#055160')
label(exit_lon, exit_lat, f'EAST-FACE MUZZLE {exit_alt:.0f} m', 0.020, 0.024, 12, c='#9f1239')
label(-78.88, -1.50, 'EL ARENAL (E491, pass 4,407 m)', 0, 0, 9.5, 'normal')
label(-79.02, -1.40, 'SALINAS', 0, 0, 9.5, 'normal')
label(-79.26, -1.55, 'CHAZOJUAN VALLEYS', 0.0, 0.0, 9.5, 'normal')
label(blon+(s_out-13)*dlon, blat+(s_out-13)*dlat, 'PHASE 1 — 14 km DEMONSTRATOR', -0.030, -0.034, 10, 'bold', '#92400e')
label(xs2[1], ys2[1], 'FIRE LINE -> EAST (+465 m/s)', -0.05, 0.012, 10, 'normal', '#0e7490')
label(-78.64, -1.33, 'AMBATO 30 km NE >', 0, 0, 9.5, 'normal')
label(-78.66, -1.60, 'RIOBAMBA 25 km SE >', 0, 0, 9.5, 'normal')
sb_lon, sb_lat = -79.27, -1.612
ax.plot([sb_lon, sb_lon+10/KMLON], [sb_lat, sb_lat], color='#0f172a', lw=3)
label(sb_lon+0.02, sb_lat, '10 km', 0, 0.005, 10)
ax.annotate('N', xy=(-78.615,-1.315), xytext=(-78.615,-1.347), fontsize=14, fontweight='bold',
            ha='center', color='#0f172a',
            arrowprops=dict(arrowstyle='-|>', color='#0f172a', lw=2.4), zorder=8)
ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
ax.set_title(f'BRONTE FULL LINE — {L:.0f} km THROUGH-MOUNTAIN ALIGNMENT @ {theta}° · SRTM 30 m · EARLY CONCEPT, NOT FOR CONSTRUCTION',
             fontsize=13, fontweight='bold')
plt.tight_layout()
out = os.path.join(os.path.dirname(__file__), 'bronte-full-map.png')
plt.savefig(out, dpi=110)
print('map saved:', out)
