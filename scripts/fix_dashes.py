# -*- coding: utf-8 -*-
"""Replace every em dash in build_keraunos_pdf.py with period/colon/comma phrasing."""
import io, sys

PATH = r"C:\Users\Futur\Documents\AiWorkspace\Claude\scripts\build_keraunos_pdf.py"

PAIRS = [
    ("SELENE — BRONTE — ARES", "SELENE · BRONTE · ARES"),
    ('f"— {doc.page - 1} —"', 'f"{doc.page - 1}"'),
    ('title="KERAUNOS — Maglev', 'title="KERAUNOS: Maglev'),
    ("three launchers — and it starts", "three launchers, and it starts"),
    ('"1 — Proof of concept"', '"1: Proof of concept"'),
    ("velocity — the demo is a working exporter", "velocity. The demo is a working exporter"),
    ('"2 — The thunder"', '"2: The thunder"'),
    ("the lightning — and you need", "the lightning, and you need"),
    ('"3 — The port"', '"3: The port"'),
    ("payloads — eventually people", "payloads, eventually people"),
    ("tonnes/year — a freight schedule", "tonnes/year: a freight schedule"),
    ("cargo</b> — 8x", "cargo</b>: 8x"),
    ("finesse — the only propellant", "finesse: the only propellant"),
    ("unlock</b> — it turns", "unlock</b>: it turns"),
    ("pedigree — and it is not", "pedigree, and it is not"),
    ("James Powell — ", "James Powell, "),
    ("maglev — and George Maise", "maglev, and George Maise"),
    ("orbital injector — ", "orbital injector: "),
    ("atmosphere — at 80 tonnes", "atmosphere. At 80 tonnes"),
    ("asset — constellation", "asset: constellation"),
    ("Transpiration cooling — the shell", "Transpiration cooling: the shell"),
    ("ZBLAN fiber — the demand is already proven:", "ZBLAN fiber (the demand is already proven):"),
    ("return pods — orbital", "return pods: orbital"),
    ("a profit — and the laser broom", "a profit, and the laser broom"),
    ("every 3 hours — ~80 tonnes/day", "every 3 hours: ~80 tonnes/day"),
    ("2025 — and is flying", "2025, and is flying"),
    ("exit seal — or the local", "exit seal, or the local"),
    ("plasma window — a magnetically", "plasma window: a magnetically"),
    ("into heat — like a Tesla", "into heat, like a Tesla"),
    ("thrown away — not the booster", "thrown away: not the booster"),
    ("The Lunar Launcher — Phase 1, The Proof of Concept",
     "The Lunar Launcher (Phase 1: The Proof of Concept)"),
    ("of track</b> — 5%", "of track</b>, 5%"),
    ("km/s — <b>above lunar", "km/s, <b>above lunar"),
    ("rocket — the last rockets", "rocket: the last rockets"),
    ("BRONTE shipments — each", "BRONTE shipments, each"),
    ("millibars — the ", "millibars: the "),
    ("the loop — ISRU", "the loop: ISRU"),
    ("km/s) — exports water", "km/s): exports water"),
    ("cargo mode — ", "cargo mode: "),
    ("goods — and eventually people", "goods, and eventually people"),
    ("ISRU — the return half", "ISRU: the return half"),
    ("continents — and it is how", "continents, and it is how"),
    ("pieces exist — ", "pieces exist. "),
    ('"nobody has assembled', '"Nobody has assembled'),
    ("apertures — scaling is", "apertures. Scaling is"),
    ("being built — for the wrong", "being built, just for the wrong"),
    ("by halves — and the", "by halves, and the"),
]

src = io.open(PATH, encoding="utf-8").read()
errors = []
for old, new in PAIRS:
    n = src.count(old)
    if n != 1:
        errors.append(f"  count={n}: {old!r}")
        continue
    src = src.replace(old, new)

if errors:
    print("MISMATCHES:")
    print("\n".join(errors))
    sys.exit(1)

remaining = src.count("—") + src.count("&mdash;")
io.open(PATH, "w", encoding="utf-8").write(src)
print(f"applied {len(PAIRS)} replacements; em dashes remaining in source: {remaining}")
