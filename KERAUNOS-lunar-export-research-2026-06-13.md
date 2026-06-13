---
title: KERAUNOS / SELENE — Lunar Export Feasibility Deep Research
date: 2026-06-13
project: Perpetual Technologies / KERAUNOS
type: research-report
sources: 60+ (NASA NTRS, peer-reviewed, agency, company)
confidence: High on physics/energy; Medium on economics; Low on He-3 fusion demand
---

# Can the Moon Build, Mine, and Ship to Earth via SELENE? — Deep Research Report

*Six parallel research agents · ~70 searches · ~30 deep-reads · every number tagged FACT vs ESTIMATE/COMPUTED with primary-source citations. All arithmetic re-derived and cross-checked.*

## Executive summary

1. **Launch is the easy, cheap part; everything else is hard.** The SELENE mass driver's ~0.79 kWh/kg-to-escape is *physically trivial*. The two real walls are (a) **making material worth launching** (ISRU processing costs 30–190× more energy per kg than launching it) and (b) **catching/recovering it** (re-entry carries 21× the launch energy; orbital catch is unsolved at cadence).
2. **Cislunar use beats Earth-return for essentially everything.** The peer-reviewed consensus (Crawford 2015; Metzger 2023) is that the only robust near-term lunar product is **propellant sold in cislunar space** — which doesn't even need a mass driver to Earth. Earth-return pencils out only for the very highest value density (PGMs), and even there **asteroids beat the Moon**.
3. **Helium-3 is a luxury-scarcity commodity, not a fusion-energy play.** At ~$20M/kg into the *quantum-cryogenics* market it can close as a tiny (kg/yr) business (Interlune–Bluefors, 10,000 L/yr, 2028–2037). As fusion fuel it does **not** close: there is no commercial D-He3 reactor, and the **extraction energy (≈5,000 GJ/kg, heating alone) dwarfs launch by ~10⁴×**.
4. **Lunar-made electronics: solar-grade yes, logic-chip no.** Oxygen + crude metal is mature (carbothermal TRL-6 in vacuum; H₂-reduction TRL-5). Solar cells, purified Si, and Al wiring are demonstrated **only in the lab on simulant (TRL 2–3)**. Copper is essentially absent — **aluminium is the lunar conductor** (61% IACS → 1.6× cross-section).
5. **SELENE's site is validated.** The Shackleton–de Gerlache Connecting Ridge gets **92.3% annual illumination at 2 m, 95.6% at 10 m** (Gläser 2014, LOLA/LRO), with only 3–5 day max darkness — exactly the near-continuous-solar premise.

---

## 1 · Lunar manufacture of electrical/electronic components

**Maturity (honest TRL):**
| Process | Output | TRL | Basis |
|---|---|---|---|
| Carbothermal (Sierra Space / NASA CaRD) | O₂ | **6** | Thermal-vacuum, −45→1,800 °C, on simulant |
| H₂ reduction of ilmenite | O₂ + Fe | **5** | Breadboard; low total O₂ yield (~1–5 wt%) |
| Molten Regolith Electrolysis (MRE) | O₂ + Fe/Si/Al/Ti | **3–4** | Gram-scale lab, ambient, simulant |
| FFC-Cambridge (Metalysis/ESA) | O₂ + alloy | **3–4** | 96% O₂ in 50 h @ 950 °C, simulant |
| Blue Origin "Blue Alchemist" (MRE→solar cells) | full PV chain | **~3** | Company claim: 99.999% Si, Al wire, cover glass, lab/simulant |
| Vacuum-evaporated solar-grade Si | thin-film Si | **2–3** | <1 ppm impurities measured; *below* microelectronic grade |

**Key facts:**
- Regolith is **40–45 wt% oxygen** (Apollo) — feedstock for all O₂+metal routes.
- **No source demonstrates semiconductor (logic-chip) grade Si from regolith — only solar-grade.** (Ignatiev/NASA: vacuum evaporation → <1 ppm impurities, bandgap 1.1 eV, but explicitly below microelectronic grade.)
- **Copper is essentially absent** on the Moon (sub-/low-ppm vapour-mobilized trace, not an ore). The realistic ISRU conductor is **aluminium**: σ(Al) ≈ 61% IACS of Cu, so equal-resistance Al needs **1.6× the cross-section** — fine, since Al is abundant and mass (not volume) is the constraint.
- Insulators (regolith glass, ceramics) are *easier* than conductors or semiconductors and more mature.

**Energy (note the definitional spread — flag for any physicist):** MRE specific energy is quoted from **~21 kWh/kg O₂** (isolated reactor, Schreiner model) to **~420 kWh/kg** (review pessimistic) — a ~20× spread that is *definitional* (theoretical minimum vs full reactor incl. melt heating; per-kg-O₂ vs per-kg-total-product). The most defensible **system-level** anchor is the Guerrero-Gonzalez & Zabel 2023 plant: 311 kW → 25 t metal + 23.9 t O₂/yr ⇒ **~56 kWh/kg combined product**. Silicon purification to solar grade (terrestrial Siemens benchmark **100–200 kWh/kg**) dominates the entire chain.

## 2 · Helium-3 — the math

**Concentration (FACT, Apollo lab):** Apollo 11 soil mean **11.8 ppb** (range 9.2–17.9); global average **4.2 ± 3.4 ppb** (Fegley & Swindle 1993); best high-Ti/ilmenite mare **up to ~20–26 ppb**. ~88–90% of the He is in grains <100 µm. *No verified Chang'e ppb value is public — treat any such claim as unverified.*

**Mass balance (COMPUTED — it's just arithmetic on the grade):**
> 1 tonne = 10⁹ mg. At 10 ppb → 10 mg He-3/tonne → **10⁵ tonnes regolith per kg He-3** (100% recovery); at 80% recovery → **~1.25 × 10⁵ t/kg**. At 20 ppb → ~5 × 10⁴ t/kg.
> Cross-check (FACT): NASA M-3 miner excavates 1,258 t/h, heats the 556 t/h fines fraction, yields 33 kg He-3/yr at 10 ppb ⇒ ~1.5 × 10⁵ t excavated/kg. **Consistent.**

**Extraction energy (COMPUTED, cp ≈ 0.8 kJ/kg·K, ΔT = 670 K to reach 700 °C):**
> Heat 1 t: 0.8 × 670 × 1000 = **0.536 GJ/tonne**.
> At 10 ppb, 80% yield, **no heat recovery**: 1.25×10⁵ t × 0.536 = **~67,000 GJ/kg He-3 (≈18.6 GWh/kg)**.
> With **85% heat recovery**: ~**10,000 GJ/kg**. At 20 ppb + 85%: ~**5,000 GJ/kg**.
> Cross-check (FACT): NASA M-3 = 12.3 MW thermal at 85% recovery for 33 kg/yr ⇒ **5,289 GJ/kg** — my 20-ppb figure (5,025 GJ/kg) lands within **5%**.

**The design figures (~56–99 GJ/kg, Mark-series) are ~100× lower than the raw heating cost** *only* because they assume 85% counterflow heat recuperation **and** heat only the beneficiated <100 µm fines. Remove either assumption and the cost rises 10–60×. ⚠ A widely-cited "38 tonnes/kg" figure (Politecnico abstract) is **wrong by ~10⁴** — do not use it.

**Market & demand (the honest part):** $20M/kg is an **asking price into the quantum-cryogenics niche** (dilution refrigerators — Bluefors, Maybell), not a fusion price. **There is no fusion buyer**: no commercial D-He3 reactor exists, D-He3 is *harder* than D-T, and USGS (2022) classes lunar He-3 "inferred unrecoverable." Real near-term demand: single-digit-to-low-tens of kg/yr. Interlune–Bluefors offtake: up to **10,000 L/yr, 2028–2037, >$300M**; Interlune also owes DOE **3 L by 2029**. **Verdict: closes as a luxury commodity at kg/yr; does NOT close for fusion; the crusher is lunar earth-moving + heat, not launch.**

## 3 · Other exports

- **Water ice → propellant:** LCROSS Cabeus **5.6 ± 2.9 wt%** (single ground-truth, ±50%). Electrolysis ≈ low-tens of kWh/kg propellant (thermodynamic floor 4.4 kWh/kg H₂O). Market = **cislunar propellant depots (~$1.8B/yr), factor ≥3 transport savings — sold in space, never returned to Earth.** Pascal Lee's caution: Starship could land 100+ t of water for "10s of $M," so lunar extraction must beat that.
- **Oxygen from regolith:** three independent methods converge on **~10–35 kWh/kg O₂** (PNAS 2025: 24.3 ± 5.8 kWh/kg LOX via H₂-reduction — note: *not* MRE, often mislabeled). O₂ is ~80–89% of propellant mass; value is in-space.
- **Metals:** Fe 14–17%, Ti 5–8%, Al 10–18% — the **Moon beats asteroids for the lithophiles Ti and Al**. Value is lunar/cislunar construction, not Earth.
- **PGMs:** pristine lunar rock is barren; the enrichment is **meteoritic** (crashed-asteroid debris), modeled at **~1–5 g/t** in large impact melts — **1–2 orders below PGM asteroids (100–250 ppm)**, unproven, no assays. The lone Earth-return candidate, but **asteroids win**.

## 4 · Delivery chain — the math

**Launch (COMPUTED, 3 ways agree):** ½v² at 2.38 km/s = **2.832 MJ/kg = 0.787 kWh/kg** (ideal); ÷0.84 efficiency = **0.937 kWh/kg at the wall**. SELENE's stated 0.78 kWh/kg is the ideal escape figure — **correct.** (The "0.22 kWh/kg" in my own research brief was wrong; the right floor is 0.79.)

**Transfer:** beyond escape, reaching Earth's vicinity costs **≈0 extra Δv** — a payload at 2.38 km/s leaves the lunar SOI at ~rest and falls down Earth's well. Vis-viva from 384,400 km to a 120 km interface ⇒ **entry speed ≈ 10.99 km/s** (independently reproduces Apollo/Orion ~11.1 km/s). To capture into Earth–Moon L1/L2 instead costs ~1 km/s more (3.34–3.70 km/s total), 4–26 day TOF (JPL DESCANSO). The mass driver does ~all the work.

**Re-entry (COMPUTED + precedent):** ½ × 11,000² = **60.5 MJ/kg — 21.4× the launch energy.** Re-entry, not launch, is the dominant energy-management problem. Precedents: Stardust 12.9 km/s (fastest ever), ~1,200 W/cm², ~34 g, PICA; Apollo ~11 km/s, ~6–7 g guided (L/D 0.3) / ~36 g ballistic; Hayabusa TPS = **53% of capsule mass**. For an uncrewed 500 kg pod: **ballistic entry + parachute (Genesis/Stardust-class), ~30–34 g (fine for cargo), peak ~600–1,000 W/cm² (q∝v³ scaling), TPS ~15–35% (~100–175 kg).** Orbital catch (skyhook/HASTOL) avoids re-entry heat but needs a facility **~200× the payload mass** (~100 t for a 500 kg pod) — capital-heavy, only worth it at high cadence.

## 5 · Show-stoppers & economics (the skeptic's column)

- **Catching is harder than throwing.** A 0.1% exit-velocity error → ~±5 km after half an orbit; high-cadence capture is unsolved hardware, and impact-catching creates an orbit-sandblasting debris cloud. Each "dumb" payload realistically needs thrusters + a capture interface — i.e., becomes a small spacecraft.
- **Bootstrapping NPV is negative.** Landing costs ~**$200,000/kg**; every gram of mine/power/refinery is paid at that rate *before* any revenue, across years of zero cash flow → peer-reviewed models return **negative NPV**. (Artemis: ~$100B to date, ~8 yr late — the cost reality of even government lunar capability.)
- **Legal:** OST Article II is genuinely ambiguous for private extraction; US/Luxembourg/Artemis-Accords law is permissive enough to *enable* it in practice (China/Russia outside the Accords) → a contestation risk, not an absolute blocker. Economics is the show-stopper, not the law.

## 6 · The core tension (the number a physicist will love)

The same **10 MW** solar plant:
> **launches ~300 t/day** of raw mass (at 0.8 kWh/kg) — but
> **processes only ~10 t/day of O₂** (24 kWh/kg) or **~1.6 t/day of solar-grade Si** (150 kWh/kg).

⇒ **ISRU processing is 30× (O₂) to ~190× (solar-Si) more energy-intensive per kg than launching.** A solar-powered lunar export economy is **bottlenecked by processing energy, not launch energy.** SELENE can throw 300 t/day only if it throws *raw or lightly-processed regolith*; anything refined is gated by the processing plant, which would consume the overwhelming majority of the power.

---

## Implications for the KERAUNOS document

1. **Keep "300 t/day"** but state explicitly it is *raw/lightly-processed mass throughput*; refined exports are processing-energy-limited (~10 t/day O₂-class at 10 MW). Add the 30–190× tension as a headline insight.
2. **Temper the He-3 narrative** to: tiny luxury-commodity (quantum cryogenics, kg/yr, ~$20M/kg) that closes; **fusion is aspirational with no current buyer**; extraction energy (~5,000 GJ/kg) is the real cost, not launch. Drop any "powers civilization" framing and the "1M tonnes He-3 → energy" leap.
3. **Reframe the export thesis honestly:** the robust product is **cislunar propellant/oxygen sold in space**; Earth-return is for the highest-value-density goods only. This actually *strengthens* SELENE's "exporter from day one" claim — just to cislunar buyers, not Earth.
4. **Lunar-made hardware:** solar cells + aluminium wiring are plausible (TRL 2–3); semiconductor-grade Si and copper are not — say so.
5. **Add a math-derivation subsection** to every quantitative claim (launch energy, He-3 mass/energy balance, re-entry energy, processing tension), as requested.

## Sources (selected primary; full URLs in session log)
NASA NTRS: Olson 2021 He-3 (ASCEND); MRE deck 20090018064; H₂-reduction ISRU; Apollo TN D-5399; Stardust 20090004445; Hayabusa 20120011648. Peer-reviewed: Crawford 2015 (arXiv:1410.6865); Metzger 2023 (arXiv:2303.09011); Azami 2024 (arXiv:2408.05823); Guerrero-Gonzalez & Zabel 2023 (Acta Astronautica 203:187); Lordos 2025 (PNAS 2306146122); Gläser 2014 (Icarus 243:78); Colaprete 2010 (Science 330:463); Li & Milliken 2017 (Sci Adv); Lin 2022 (Sci Adv abl9174); precious-metal impact enrichment 2025 (Comms Earth Environ s43247-025-03046-x). Engineering/agency: SJSU Miller 2023 mass-driver thesis; O'Neill NASA SP-428 / NSS; FarView NIAC (arXiv:2404.03840); Blue Origin Blue Alchemist; Sierra Space carbothermal; ESA/Metalysis FFC; Interlune–Bluefors. Skeptics: The Space Review "helium-3 incantation"; Resilience.org; Scientific American (Pascal Lee); Moon Village Association; Handmer "How to build a lunar mass driver" (2026); SpaceNews "separating market from marketing."
