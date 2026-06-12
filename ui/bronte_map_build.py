import gzip, os, json, math
import numpy as np

# ---- load DEM (SRTM 1-arcsec tile S02W079: lat -2..-1, lon -79..-78) ----
p = os.path.join(os.environ['TEMP'], 'S02W079.hgt.gz')
raw = gzip.open(p, 'rb').read()
dem = np.frombuffer(raw, dtype='>i2').reshape(3601, 3601).astype(float)
dem[dem < -100] = np.nan  # voids

LAT_TOP, LON_LEFT = -1.0, -79.0
def rc(lat, lon):
    return (LAT_TOP - lat) * 3600.0, (lon - LON_LEFT) * 3600.0
def elev(lat, lon):
    r, c = rc(lat, lon)
    r0, c0 = int(r), int(c)
    fr, fc = r - r0, c - c0
    z = (dem[r0,c0]*(1-fr)*(1-fc) + dem[r0+1,c0]*fr*(1-fc)
         + dem[r0,c0+1]*(1-fr)*fc + dem[r0+1,c0+1]*fr*fc)
    return z

KMLAT, KMLON = 110.57, 111.32*math.cos(math.radians(1.45))

# ---- route scan: straight 14 km line, fire east-ish, muzzle on eastern rim ----
best = []
for rim_lat in np.arange(-1.475, -1.392, 0.004):
    # find eastern rim: easternmost lon with elev>=4350 and big drop 2.5 km east
    lon_rim = None
    for lon in np.arange(-78.70, -78.86, -0.002):
        z = elev(rim_lat, lon)
        if z >= 4350:
            zd = elev(rim_lat, lon + 2.5/KMLON)
            if z - zd >= 500:
                lon_rim = lon
                break
    if lon_rim is None:
        continue
    for az in (80, 85, 90, 95, 100):
        th = math.radians(az)
        dlat = math.cos(th)/KMLAT   # per km along fire direction
        dlon = math.sin(th)/KMLON
        m_lat, m_lon = rim_lat, lon_rim
        e_lat, e_lon = m_lat - 14*dlat, m_lon - 14*dlon
        s = np.linspace(0, 14, 141)
        zz = np.array([elev(e_lat + d*dlat*1, e_lon + d*dlon*1) for d in s])
        if np.any(np.isnan(zz)):
            continue
        z_entry, z_muz = zz[0], zz[-1] + 30  # muzzle 30 m above rim ground
        line = z_entry + (z_muz - z_entry) * s/14
        dev = zz - line   # + means terrain above track (cut/tunnel), - means below (viaduct)
        maxcut, maxfill = float(dev.max()), float(-dev.min())
        score = max(maxcut, 1.5*maxfill)
        best.append((score, maxcut, maxfill, float(z_entry), float(z_muz),
                     rim_lat, lon_rim, az, e_lat, e_lon))
best.sort()
print("top 5 routes: score maxcut maxfill z_entry z_muzzle rim_lat rim_lon az")
for b in best[:5]:
    print("  " + " ".join(f"{v:.4f}" if isinstance(v,float) else str(v) for v in b[:8]))

score, maxcut, maxfill, z_entry, z_muz, rim_lat, rim_lon, az, e_lat, e_lon = best[0]
th = math.radians(az)
dlat, dlon = math.cos(th)/KMLAT, math.sin(th)/KMLON
# full profile incl. 6 km downrange past muzzle
s = np.linspace(-0, 20, 201)
prof = []
for d in s:
    la, lo = e_lat + d*dlat, e_lon + d*dlon
    prof.append((float(d), float(elev(la, lo))))
exit_angle = math.degrees(math.atan((z_muz - z_entry)/14000))
print(f"CHOSEN: az {az} deg, entry ({e_lat:.4f},{e_lon:.4f}) {z_entry:.0f} m, "
      f"muzzle ({rim_lat:.4f},{rim_lon:.4f}) {z_muz:.0f} m, exit angle {exit_angle:.2f} deg, "
      f"maxcut {maxcut:.0f} m, maxfill {maxfill:.0f} m")
json.dump({"entry":[e_lat,e_lon,z_entry], "muzzle":[rim_lat,rim_lon,z_muz],
           "az":az, "exit_angle":exit_angle, "maxcut":maxcut, "maxfill":maxfill,
           "profile":prof},
          open(os.path.join(os.path.dirname(__file__), 'bronte_route.json'), 'w'))

# ---- map rendering ----
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap

lat0, lat1 = -1.62, -1.30          # south, north
lon0, lon1 = -78.99, -78.60
r0, c0 = rc(lat1, lon0); r1, c1 = rc(lat0, lon1)
sub = dem[int(r0):int(r1)+1, int(c0):int(c1)+1]
extent = [lon0, lon1, lat0, lat1]

terrain_cmap = LinearSegmentedColormap.from_list('andes', [
    (0.00, '#4e6b3a'), (0.18, '#6e8449'), (0.35, '#9aa05e'),
    (0.50, '#b9a878'), (0.65, '#c5ad8d'), (0.78, '#cbb9a4'),
    (0.88, '#d8cfc4'), (1.00, '#f4f1ec')])
ls = LightSource(azdeg=315, altdeg=45)
norm_z = np.clip((sub - 2600)/(6300-2600), 0, 1)
rgb = ls.shade_rgb(terrain_cmap(norm_z)[:,:,:3], sub, vert_exag=0.08,
                   blend_mode='soft', dx=30, dy=30)
# glacier above 5100 m -> white tint
gmask = sub >= 5100
for ch, v in enumerate((0.97, 0.98, 1.0)):
    rgb[:,:,ch] = np.where(gmask, 0.25*rgb[:,:,ch] + 0.75*v, rgb[:,:,ch])

fig, ax = plt.subplots(figsize=(16, 12.8), dpi=110)
ax.imshow(rgb, extent=extent, aspect=KMLAT/KMLON)
cs = ax.contour(np.linspace(lon0, lon1, sub.shape[1]),
                np.linspace(lat1, lat0, sub.shape[0]),
                sub, levels=np.arange(2800, 6400, 200),
                colors='#3b3528', linewidths=0.35, alpha=0.55)
cs2 = ax.contour(np.linspace(lon0, lon1, sub.shape[1]),
                 np.linspace(lat1, lat0, sub.shape[0]),
                 sub, levels=np.arange(3000, 6400, 1000),
                 colors='#3b3528', linewidths=0.9, alpha=0.7)
ax.clabel(cs2, fmt='%d', fontsize=8)

# route line + downrange
lats = [e_lat + d*dlat for d in (0, 14)]
lons = [e_lon + d*dlon for d in (0, 14)]
ax.plot(lons, lats, color='#7c3aed', lw=4.5, solid_capstyle='round', zorder=5)
ax.plot(lons, lats, color='white', lw=1.6, ls=(0,(2,3)), zorder=6)
dr_lat = [rim_lat + d*dlat for d in (0, 7)]
dr_lon = [rim_lon + d*dlon for d in (0, 7)]
ax.plot(dr_lon, dr_lat, color='#0e7490', lw=2, ls='--', zorder=5)
ax.annotate('', xy=(dr_lon[1], dr_lat[1]), xytext=(dr_lon[0], dr_lat[0]),
            arrowprops=dict(arrowstyle='-|>', color='#0e7490', lw=2), zorder=6)
ax.plot(e_lon, e_lat, 'o', ms=11, mfc='#22d3ee', mec='#0f172a', zorder=7)
ax.plot(rim_lon, rim_lat, 'o', ms=11, mfc='#f43f5e', mec='#0f172a', zorder=7)

def label(lon, lat, txt, dx=0.004, dy=0.004, fs=11, w='bold', c='#0f172a'):
    ax.annotate(txt, (lon, lat), xytext=(lon+dx, lat+dy), fontsize=fs,
                fontweight=w, color=c, zorder=8,
                path_effects=[matplotlib.patheffects.withStroke(linewidth=2.6, foreground='white')])
import matplotlib.patheffects
label(-78.817, -1.469, 'CHIMBORAZO 6,263 m', 0.006, -0.012, 13)
label(-78.750, -1.404, 'CARIHUAIRAZO 5,018 m', 0.004, 0.016, 11)
label(e_lon, e_lat, f'ENTRY PORTAL {z_entry:.0f} m', -0.062, -0.018, 12, c='#055160')
label(rim_lon, rim_lat, f'MUZZLE {z_muz:.0f} m (RIM)', -0.012, -0.028, 12, c='#9f1239')
label(-78.88, -1.50, 'EL ARENAL\n(road E491, pass 4,407 m)', 0.0, 0.0, 10, 'normal')
label(-78.79, -1.435, 'ABRASPUNGO CORRIDOR', 0.0, 0.0, 10, 'normal')
label(-78.64, -1.33, 'AMBATO 30 km NE >', 0, 0, 10, 'normal')
label(-78.66, -1.60, 'RIOBAMBA 25 km SE >', 0, 0, 10, 'normal')
label(-78.97, -1.59, '< GUARANDA 22 km SW', 0, 0, 10, 'normal')
label(rim_lon+0.045, rim_lat-0.014, 'FIRE LINE -> EAST (+465 m/s)', 0, 0, 10, 'normal', '#0e7490')

# scale bar + north arrow
sb_lon = -78.97; sb_lat = -1.615
ax.plot([sb_lon, sb_lon + 5/KMLON], [sb_lat, sb_lat], color='#0f172a', lw=3)
label(sb_lon+0.005, sb_lat, '5 km', 0, 0.004, 10)
ax.annotate('N', xy=(-78.615, -1.315), xytext=(-78.615, -1.345), fontsize=14,
            fontweight='bold', ha='center', color='#0f172a',
            arrowprops=dict(arrowstyle='-|>', color='#0f172a', lw=2.4), zorder=8)

ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
ax.set_title('BRONTE-D ROUTE — CHIMBORAZO MASSIF — SRTM 30 m TERRAIN, CONTOURS 200 m'
             '  ·  EARLY CONCEPT, NOT FOR CONSTRUCTION', fontsize=13, fontweight='bold')
out = os.path.join(os.path.dirname(__file__), 'bronte-chimborazo-map.png')
plt.tight_layout()
plt.savefig(out, dpi=110)
print('map saved:', out)
