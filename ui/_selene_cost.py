import math

escape_v = 2385
eta = 0.84
south_pole_illum = 0.90
hours_per_year = 8760
joule_per_kwh = 3.6e6

e_escape = 0.5 * escape_v**2 / (joule_per_kwh * eta)
e_phase3 = 0.5 * 4200**2 / (joule_per_kwh * eta)
annual_mwh_per_mw = hours_per_year * south_pole_illum

print("Annual energy per installed MW:", round(annual_mwh_per_mw), "MWh/MW/yr")
print("Wall-plug energy at escape:", round(e_escape, 3), "kWh/kg")
print("Throughput per MW at escape:", round(annual_mwh_per_mw * 1000 / e_escape), "t/MW/yr")
print("Throughput per MW at 4.2 km/s:", round(annual_mwh_per_mw * 1000 / e_phase3), "t/MW/yr")
print()

shots_per_year = hours_per_year * 3600 * south_pole_illum / 10
annual_t = shots_per_year * 25.4 / 1e6
print("SJSU Phase 1b annual throughput:", round(annual_t * 1000), "t/yr,", round(shots_per_year/1e6, 2), "M shots/yr")
print()

track_len = 2900
ring_spacing = 0.6
n_rings = int(track_len / ring_spacing)
print("Stator rings (2.9 km @ 0.6 m):", n_rings)
print()

tape_cross = 4e-3 * 0.1e-3  # 4mm x 0.1mm REBCO tape cross-section m^2
rho = 6000  # kg/m^3 REBCO density
mass_per_m = rho * tape_cross  # kg per meter of tape

for bore_m in [1, 2, 3]:
    outer_r = bore_m / 2.0 + 0.35
    circ = 2 * math.pi * outer_r
    turns = 50
    tape_per_ring = circ * turns
    total_tape = tape_per_ring * n_rings
    rebco_mass = total_tape * mass_per_m
    payload_vol = math.pi * (bore_m / 2.0)**2 * 2.0  # m^3 for 2m long pod
    payload_bulk = payload_vol * 500  # kg at 500 kg/m^3

    rebco_cost_lo = total_tape * 50
    rebco_cost_hi = total_tape * 200
    rebco_delivery = rebco_mass * 2000

    print("Bore " + str(bore_m) + " m:")
    print("  Ring circumference: " + str(round(circ, 2)) + " m, tape per ring (" + str(turns) + " turns): " + str(round(tape_per_ring)) + " m")
    print("  Total REBCO tape: " + str(round(total_tape/1000)) + " km, mass: " + str(round(rebco_mass/1000, 1)) + " t")
    print("  REBCO cost @$50/m: $" + str(round(rebco_cost_lo/1e6)) + "M  @$200/m: $" + str(round(rebco_cost_hi/1e6)) + "M")
    print("  REBCO delivery @$2k/kg: $" + str(round(rebco_delivery/1e6)) + "M")
    print("  Bulk payload per shot (500 kg/m^3, 2m pod): " + str(round(payload_bulk)) + " kg")
    print()

solar_mass = 8700 * 5  # 5 kg/kW thin-film
print("Solar arrays (8.7 MW, 5 kg/kW):", round(solar_mass/1000, 1), "t")
print("Solar delivery @$2k/kg: $" + str(round(solar_mass*2000/1e6)) + "M")
print("Solar manufacture @$3/W: $" + str(round(8700*1000*3/1e6)) + "M")
