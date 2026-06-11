# -*- coding: utf-8 -*-
"""Build the KERAUNOS whitepaper PDF for Samuel Edwards."""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, KeepTogether, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = r"C:\Users\Futur\Downloads\KERAUNOS.pdf"

NAVY = HexColor("#0a0d18")
NAVY2 = HexColor("#141b30")
TEAL = HexColor("#0891b2")
TEAL_BRIGHT = HexColor("#22d3ee")
PURPLE = HexColor("#7c3aed")
VIOLET = HexColor("#a78bfa")
BODY = HexColor("#2a3245")
DIM = HexColor("#5a6a8a")
LIGHT = HexColor("#eef2fa")
ZEBRA = HexColor("#f4f7fd")
GOLD = HexColor("#b45309")

# Fonts: Segoe UI has Greek glyphs
F = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Segoe", os.path.join(F, "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Bold", os.path.join(F, "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Italic", os.path.join(F, "segoeuii.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Semi", os.path.join(F, "seguisb.ttf")))

W, H = letter

S = {}
S["body"] = ParagraphStyle("body", fontName="Segoe", fontSize=10, leading=14.6,
                           textColor=BODY, spaceAfter=7)
S["bullet"] = ParagraphStyle("bullet", parent=S["body"], leftIndent=16,
                             bulletIndent=4, spaceAfter=5)
S["h1"] = ParagraphStyle("h1", fontName="Segoe-Bold", fontSize=15.5, leading=19,
                         textColor=NAVY, spaceBefore=18, spaceAfter=2)
S["h2"] = ParagraphStyle("h2", fontName="Segoe-Semi", fontSize=11.5, leading=15,
                         textColor=TEAL, spaceBefore=10, spaceAfter=4)
S["reminder"] = ParagraphStyle("reminder", fontName="Segoe-Italic", fontSize=9.8,
                               leading=13.5, textColor=PURPLE, leftIndent=14,
                               spaceBefore=2, spaceAfter=10)
S["mathbox"] = ParagraphStyle("mathbox", fontName="Segoe", fontSize=9.6,
                              leading=13.6, textColor=BODY)
S["tbl"] = ParagraphStyle("tbl", fontName="Segoe", fontSize=9, leading=12.2,
                          textColor=BODY)
S["tblh"] = ParagraphStyle("tblh", fontName="Segoe-Semi", fontSize=9, leading=12,
                           textColor=white)
S["caption"] = ParagraphStyle("caption", fontName="Segoe-Italic", fontSize=8.4,
                              leading=11, textColor=DIM, spaceBefore=3, spaceAfter=8)
S["quote"] = ParagraphStyle("quote", fontName="Segoe-Italic", fontSize=11.5,
                            leading=16, textColor=PURPLE, alignment=TA_CENTER,
                            spaceBefore=14, spaceAfter=14)


def sect(num, title):
    return [Paragraph(f"{num}. {title}", S["h1"]),
            HRFlowable(width="100%", thickness=1.4, color=TEAL, spaceBefore=3,
                       spaceAfter=8)]


def reminder(text):
    return Paragraph(f"Reminder: {text}", S["reminder"])


def b(text):
    return Paragraph(text, S["bullet"], bulletText="●")


def p(text):
    return Paragraph(text, S["body"])


def mathbox(rows):
    """rows: list of (formula, explanation)"""
    data = [[Paragraph(f"<font face='Segoe-Semi' color='#0891b2'>{f}</font>",
                       S["mathbox"]),
             Paragraph(e, S["mathbox"])] for f, e in rows]
    t = Table(data, colWidths=[2.15 * inch, 4.45 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.8, HexColor("#c7d4ec")),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, HexColor("#d8e2f3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return KeepTogether([t])


def styled_table(header, rows, widths, highlight_row=None):
    data = [[Paragraph(h, S["tblh"]) for h in header]]
    for r in rows:
        data.append([Paragraph(c, S["tbl"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.8, HexColor("#c7d4ec")),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, HexColor("#d8e2f3")),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    if highlight_row is not None:
        style.append(("BACKGROUND", (0, highlight_row), (-1, highlight_row),
                      HexColor("#e6f7fb")))
    t.setStyle(TableStyle(style))
    return t


def draw_gates(c):
    """KERAUNOS logo badge: accelerator coil gates ascending, payload exiting."""
    # badge card: near-black, compact
    bx0, by0 = W / 2 - 2.25 * inch, H - 3.4 * inch
    bw, bh = 4.5 * inch, 2.05 * inch
    c.setFillColor(HexColor("#070a13"))
    c.setStrokeColorRGB(0.13, 0.83, 0.93, alpha=0.3)
    c.setLineWidth(1)
    c.roundRect(bx0, by0, bw, bh, 14, stroke=1, fill=1)
    # rings, centered as a composition inside the badge
    n = 8
    x0, y0 = W / 2 - 1.5 * inch, H - 2.75 * inch
    x1, y1 = W / 2 + 1.2 * inch, H - 1.95 * inch
    c.saveState()
    c.setDash(2, 5)
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.45, 0.65, 0.75, alpha=0.25)
    c.line(x0 - 0.1 * inch, y0 - 0.04 * inch, x1 + 0.38 * inch, y1 + 0.12 * inch)
    c.restoreState()
    for i in range(n):
        t = i / (n - 1)
        cx = x0 + (x1 - x0) * t
        cy = y0 + (y1 - y0) * t
        hh = 0.30 * inch               # all rings the same size
        hw = hh * 0.30                 # narrow ellipse, seen edge-on
        base = 0.30 + 0.65 * t         # brightness ramps along the track
        c.saveState()
        c.translate(cx, cy)
        c.rotate(18)                   # perpendicular to the ascending track
        for lw, ga in ((5.5, 0.10), (3.5, 0.18), (2.1, 0.38), (1.1, 1.0)):
            c.setLineWidth(lw)
            c.setStrokeColorRGB(0.13, 0.83, 0.93, alpha=ga * base)
            c.ellipse(-hw, -hh, hw, hh, stroke=1, fill=0)
        c.restoreState()
    # the payload, clear of the muzzle
    c.setFillColorRGB(0.13, 0.83, 0.93, alpha=0.95)
    c.circle(x1 + 0.3 * inch, y1 + 0.1 * inch, 2.6, stroke=0, fill=1)
    # wordmark inside the badge
    c.setFillColor(TEAL_BRIGHT)
    c.setFont("Segoe-Semi", 10.5)
    c.drawCentredString(W / 2, by0 + 0.2 * inch, "Κ Ε Ρ Α Υ Ν Ο Σ")


def cover(c, doc):
    c.saveState()
    c.setFillColor(HexColor("#05070e"))
    c.rect(0, 0, W, H, stroke=0, fill=1)
    # subtle star field
    import random
    rng = random.Random(7)
    for _ in range(90):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(0.3, 1.1)
        c.setFillColorRGB(1, 1, 1, alpha=rng.uniform(0.15, 0.55))
        c.circle(x, y, r, stroke=0, fill=1)
    # accelerator gates
    draw_gates(c)
    # title
    c.setFillColor(white)
    c.setFont("Segoe-Bold", 56)
    c.drawCentredString(W / 2, H - 4.85 * inch, "KERAUNOS")
    c.setFillColor(VIOLET)
    c.setFont("Segoe", 15)
    c.drawCentredString(W / 2, H - 5.35 * inch, "The Thunderbolt of Zeus, Industrialized")
    # rule
    c.setStrokeColor(PURPLE)
    c.setLineWidth(1.2)
    c.line(W / 2 - 1.6 * inch, H - 5.62 * inch, W / 2 + 1.6 * inch, H - 5.62 * inch)
    c.setFillColor(HexColor("#9fb0d0"))
    c.setFont("Segoe", 12.5)
    c.drawCentredString(W / 2, H - 6.0 * inch, "Maglev Space Launch System  ·  SELENE · BRONTE · ARES")
    c.setFont("Segoe", 10.5)
    c.setFillColor(HexColor("#7e8db0"))
    c.setFillColor(white)
    c.setFont("Segoe-Semi", 13)
    c.drawCentredString(W / 2, 1.55 * inch, "Samuel Edwards")
    c.setFillColor(HexColor("#7e8db0"))
    c.setFont("Segoe", 10)
    c.drawCentredString(W / 2, 1.32 * inch, "June 2026  ·  Concept Whitepaper")
    c.restoreState()


def later(c, doc):
    c.saveState()
    # header rule
    c.setStrokeColor(TEAL)
    c.setLineWidth(0.8)
    c.line(0.85 * inch, H - 0.62 * inch, W - 0.85 * inch, H - 0.62 * inch)
    c.setFont("Segoe-Semi", 7.6)
    c.setFillColor(DIM)
    c.drawString(0.85 * inch, H - 0.55 * inch, "KERAUNOS  ·  MAGLEV SPACE LAUNCH SYSTEM")
    c.drawRightString(W - 0.85 * inch, H - 0.55 * inch, "SAMUEL EDWARDS")
    # footer
    c.setFont("Segoe", 8)
    c.drawCentredString(W / 2, 0.5 * inch, f"{doc.page - 1}")
    c.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=letter,
                        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                        topMargin=0.95 * inch, bottomMargin=0.8 * inch,
                        title="KERAUNOS: Maglev Space Launch System",
                        author="Samuel Edwards")

E = []  # story

# ---- cover is drawn by callback; first flowable forces page 1 to exist
E.append(Spacer(1, 1))
E.append(PageBreak())

# ---- EXECUTIVE SUMMARY ----
E += sect("0", "Executive Summary")
E.append(p("KERAUNOS is a family of electromagnetic mass launchers, and the core bet is "
           "deliberately simple: a maglev rail on an airless world needs no vacuum tube, "
           "no plasma window, and no heat shield, and the solar system is full of airless "
           "worlds. Earth, with its thick atmosphere, is the hardest place in the system "
           "to build one. So the program starts on the Moon, where the machine is native, "
           "and proves the hardware as a repeatable kit. The full 1,000 km Earth injector "
           "(8 km/s on grid electricity, a plasma window at a mountain exit, a kick motor "
           "at apogee) is the long-horizon prize at the end of that road, not the opening "
           "move. Wherever it stands, the launcher never leaves the ground, never gets "
           "rebuilt, and earns between launches."))
E.append(p("Three named launchers come first. After them, the same kit is meant to be "
           "stamped onto every useful airless rock in the system."))
E.append(KeepTogether([styled_table(
    ["Launcher", "Body", "Phase", "Character"],
    [["<b>SELENE</b>", "Moon", "1: Proof of concept",
      "No atmosphere: no tube, no plasma window, no aero-shell. The starter track is "
      "single-digit km: at 100 g, ~2.9 km throws dumb cargo clear off the Moon."],
     ["<b>BRONTE</b>", "Earth", "2: The thunder",
      "A 10-20 km demonstrator near-term. The full 1,000 km injector is the long-horizon "
      "prize, built only once the vacuum-world fleet has proven the hardware and the "
      "economics."],
     ["<b>ARES</b>", "Mars", "3: The port",
      "0.6% atmosphere makes the tube featherweight. ARES is the return half of the "
      "settlement economy."]],
    [1.0 * inch, 0.7 * inch, 1.55 * inch, 3.35 * inch])]))
E.append(Spacer(1, 6))
E.append(Paragraph("Specifications by launcher", S["h2"]))
E.append(p("Each launcher gets its own table below so there is no ambiguity about which "
           "body a number belongs to. BRONTE (Earth) is the flagship and gets the deepest "
           "treatment, then SELENE (Moon), then ARES (Mars)."))

E.append(KeepTogether([Paragraph("BRONTE: Earth (the hardest site, and the endgame)", S["h2"]),
                       styled_table(
    ["Parameter", "Value", "Notes"],
    [["Role", "Primary orbital injector",
      "\"The thunder.\" Earth is the hardest site in the system; these are the full "
      "machine's target figures, not a near-term commitment"],
     ["Track length", "1,000 km vacuum tube",
      "Tube length is the unlock: it buys the gentle g-load"],
     ["Exit velocity", "4-8 km/s",
      "Mach 12.7-25.3 at the 6 km exit, where the speed of sound is ~316 m/s"],
     ["Acceleration", "3.3 g constant (32 m/s<super>2</super>)",
      "a = v<super>2</super>/2L. Only 0.8 g if run to 4 km/s. StarTram needed 30 g"],
     ["Time on track", "250 s (4 min 10 s)",
      "t = v/a at full 8 km/s"],
     ["Energy per kg", "8.9 kWh ($0.53 at $0.06/kWh)",
      "E = &frac12;v<super>2</super> = 32 MJ/kg. Everything above this is amortization"],
     ["Drive power (10 t pod)", "1.28 GW average, 2.56 GW peak",
      "320 GJ per launch over 250 s; peak P = m&middot;a&middot;v at the muzzle"],
     ["Onboard kick", "0.5-1 km/s at apogee",
      "20% propellant at Isp 350 s buys ~0.77 km/s: the claims are consistent"],
     ["Exit altitude", "~6,000 m mountain face",
      "Air density there is ~55% of sea level, cutting peak drag and heating nearly in half"],
     ["Cadence", "One 10 t pod every 3 hours",
      "80 t/day, ~29,000 t/year: a freight schedule, not a launch manifest"],
     ["Cost to LEO", "$20-250/kg, toward $5/kg",
      "vs Falcon 9 ~$2,720/kg customer price; skyhook phase pushes toward $5"],
     ["Demonstrator first", "10-20 km track",
      "Mach 2-3 at 3 g human-rated; 2.4-3.4 km/s (Mach 7-10) at 30 g cargo mode"]],
    [1.45 * inch, 1.85 * inch, 3.3 * inch]),
                       Paragraph("All derived values from a = v&sup2;/2L, t = v/a, "
                                 "E = &frac12;v&sup2;, P = m&middot;a&middot;v, with "
                                 "g = 9.81 m/s&sup2;.", S["caption"])]))

E.append(KeepTogether([Paragraph("SELENE: Moon (Phase 1 proof of concept)", S["h2"]),
                       styled_table(
    ["Parameter", "Value", "Notes"],
    [["Role", "Proof of concept + mass exporter",
      "Water ice, oxygen, shielding mass to cislunar buyers"],
     ["Atmosphere", "None",
      "No tube, no plasma window, no aero-shell, no blast shutters. The track is the launcher"],
     ["Starter track (PoC)", "1-3 km at 50-100 g, dumb cargo",
      "At 100 g: 1.5 km reaches orbit speed (1.7 km/s), ~2.9 km clears escape "
      "(2.38 km/s) in a 2.4 s ride. Water, regolith, and metal don't mind the g"],
     ["Cargo track (growth)", "10-12 km at 30 g",
      "2.43-2.66 km/s for hardened payloads, escape with margin; 8 s ride"],
     ["Passenger track (later)", "~50 km at 3 g",
      "Low lunar orbit speed (~1.7 km/s) in a 58 s run; ~96 km version reaches escape"],
     ["Energy per kg", "0.40 kWh (orbit), 0.79 kWh (escape)",
      "Roughly 1/20th of the Earth launch energy"],
     ["Throw to Earth orbit", "~2.4 km/s from the lunar surface",
      "vs 9.4+ km/s from Earth's surface: the Moon wins on every kg that can start there"]],
    [1.45 * inch, 1.95 * inch, 3.2 * inch])]))

E.append(KeepTogether([Paragraph("ARES: Mars (Phase 3 frontier port)", S["h2"]),
                       styled_table(
    ["Parameter", "Value", "Notes"],
    [["Role", "Export port for the Mars economy",
      "ISRU propellant, samples, manufactured goods"],
     ["Atmosphere", "~6 mbar (0.6% of Earth)",
      "Featherweight tube; the plasma window's job is 99.4% done by the planet"],
     ["Track (orbit)", "~180 km at 3.3 g",
      "Low Mars orbit speed (~3.4 km/s) in a 105 s run"],
     ["Track (escape)", "~390 km at 3.3 g",
      "Mars escape (~5.0 km/s) in a 155 s run"],
     ["Energy per kg", "1.6 kWh (orbit), 3.5 kWh (escape)",
      "Between Moon and Earth in scale, far easier than Earth in engineering"],
     ["Staging", "Phobos and Deimos",
      "Catch points and depots; SEP tugs handle the interplanetary cruise"]],
    [1.45 * inch, 1.95 * inch, 3.2 * inch])]))
E.append(Spacer(1, 6))

# ---- 1. PHYSICS & PRICE ----
E += sect("1", "The Physics &amp; Price: Breaking the Rocket Equation")
E.append(reminder("We aren't \"improving\" rockets; we are removing the \"Stage 0\" fuel "
                  "penalty. Efficiency comes from the ground infrastructure, not the craft."))
E.append(b("<b>The Mass Fraction Flip:</b> a normal rocket is 90% fuel / 10% cargo. A "
           "KERAUNOS pod is 20% fuel (for the final kick only) / <b>80% cargo</b>. That "
           "is 8x more payload per launched tonne."))
E.append(b("<b>The Kick Motor:</b> even an 8 km/s ground launch is sub-orbital; without a "
           "circularization burn at apogee the pod hits the ocean. A small restartable "
           "motor supplies roughly 0.5-1 km/s of circularization and trim (a 20% "
           "propellant fraction at Isp 350 s buys ~0.77 km/s). It is the only propellant "
           "on board."))
E.append(b("<b>The Breakaway Aero-Shell:</b> the pod rides inside a sacrificial hypersonic "
           "shroud shaped with NASA X-59 pressure-distribution data. It eats the tube-to-air "
           "transition, then jettisons at 30-40 km, shedding dead thermal mass before the "
           "orbital burn."))
E.append(b("<b>The Mountain Muzzle (new):</b> the tube exits at roughly 6,000 m altitude "
           "on a mountain face, where air density is ~55% of sea level, cutting peak drag "
           "and heating nearly in half during the worst milliseconds of the flight. "
           "Non-negotiable at Mach 12+, and it matches the StarTram reference design "
           "(exit at 4,000-8,000 m)."))
E.append(Spacer(1, 4))
E.append(Paragraph("The arithmetic that carries the whole pitch", S["h2"]))
E.append(mathbox([
    ("E = ½v² = 32 MJ/kg",
     "8.9 kWh per kilogram at 8 km/s. At $0.06/kWh that is <b>$0.53 of electricity per "
     "kg</b> to orbital velocity. Everything above that price is hardware amortization, "
     "not physics."),
    ("a = v² / 2L = 3.3 g",
     "A 1,000 km tube reaches 8 km/s at just <b>3.3 g</b> (0.8 g at 4 km/s). The leading "
     "academic design, StarTram Gen-1, accepted a punishing 30 g cargo-only profile "
     "because its tube was ~130 km. <b>Tube length is the unlock</b>: it turns a cargo "
     "cannon into a universal launcher."),
]))
E.append(Spacer(1, 8))
E.append(KeepTogether([
    Paragraph("Comparative launch costs (per kg to LEO)", S["h2"]),
    styled_table(
    ["Launch system", "Cost per kg", "Economic bottleneck"],
    [["Space Shuttle", "$54,500", "Hand-built, massive refurbishment"],
     ["SpaceX Falcon 9", "~$2,720 price / ~$630 internal", "Fuel costs + expended hardware"],
     ["SpaceX Starship (projected)", "$100-$1,000", "Limit of chemical fuel energy density"],
     ["<b>KERAUNOS</b>", "<b>$20-$250</b>", "Electricity is ~$0.53/kg; price is amortization"],
     ["<b>KERAUNOS + skyhook</b>", "<b>toward $5</b>", "Kick-motor fuel drops toward zero"]],
    [1.9 * inch, 1.95 * inch, 2.75 * inch], highlight_row=4),
    Paragraph("Falcon 9 figures: customer price vs estimated internal cost. Starship "
              "range reflects near-term reuse assumptions.", S["caption"]),
]))

# ---- 2. PRIOR ART ----
E += sect("2", "Prior Art &amp; The Gap: Everyone Is Pointing at This, Nobody Is Building It")
E.append(reminder("KERAUNOS is not science fiction without a pedigree, and it is not a "
                  "\"me too.\""))
E.append(b("<b>StarTram proved the physics on paper (2008-2010).</b> James Powell, "
           "co-inventor of superconducting maglev, and George Maise projected $30-43/kg "
           "to orbit. But their Gen-1 was 30 g, cargo-only, from a ~130 km tube: credible "
           "physics, brutal payload constraints."))
E.append(b("<b>China is proving the intent in hardware (target 2028).</b> Galactic Energy, "
           "CASIC, and the Ziyang (Sichuan) government are building an electromagnetic "
           "launch verification platform that accelerates a conventional rocket to roughly "
           "Mach 1.6 before ignition. That is a faster runway, not an orbital injector: "
           "the rocket still carries the rocket equation on its back."))
E.append(b("<b>The gap KERAUNOS fills:</b> everyone is fighting the launcher's worst "
           "case. China is racing for an Earth assist; StarTram stayed a paper about an "
           "Earth tube. Nobody is productizing the launcher where it is native: airless "
           "worlds, where the tube, the plasma window, and the heat shield simply do not "
           "exist. KERAUNOS starts there and treats the full-length Earth tube as the "
           "prize at the end of the road, not the ante. And because the major players are "
           "already hitting the efficiency wall of hybrid designs, they are primed to "
           "accept the vacuum-world kit as the logical evolution of their own research."))

# ---- 3. GEOPOLITICS ----
E += sect("3", "The Geopolitical Superpower Race")
E.append(reminder("The nation that builds this first becomes the \"Space Panama Canal,\" "
                  "controlling the world's most valuable logistics route."))
E.append(b("<b>The Sovereign Monopoly:</b> the host nation stops paying for space and "
           "starts charging the rest of the world. As space sovereignty becomes a global "
           "priority, every other country becomes a customer of the superior infrastructure."))
E.append(b("<b>Strategic Land Grab:</b> secure the best orbital slots and lunar water-ice "
           "territories before anyone else can even clear the atmosphere. At 80 tonnes a "
           "day, occupation is a logistics fact, not a treaty argument."))
E.append(b("<b>The deterrence dividend:</b> a launcher that can place 29,000 tonnes a year "
           "into orbit is also the ultimate space-resilience asset, able to replenish a "
           "constellation in hours instead of months."))

# ---- 4. RISK ----
E += sect("4", "Risk Assessment: The Fail-Safe Protocols")
E.append(reminder("High speed in a tube is high stakes. We need a fail-safe for every "
                  "millisecond."))
E.append(KeepTogether([styled_table(
    ["Failure", "Consequence", "Countermeasure"],
    [["Aero-shell fails to jettison at Mach 12+",
      "Dead mass prevents orbit",
      "Triple-redundant cold-gas thrusters on the shell halves force separation"],
     ["Tube vacuum breach",
      "Incoming air hits the craft like a physical hammer",
      "Automated blast shutters every 1 km isolate the breach; air propagates at "
      "~0.34 km/s, so a 1 km section caps the spoiled vacuum to hours of re-pumping"],
     ["Thermal runaway at exit (2,000&deg;C+ leading edge)",
      "Shell ablation, payload loss",
      "Transpiration cooling: the shell \"sweats\" liquid nitrogen through porous ceramics"],
     ["Plasma window failure",
      "Atmospheric backflow into the tube",
      "Blast shutters close as the physical backup"],
     ["Launch abort",
      "Stranded kinetic energy, overspeed risk",
      "Regenerative magnetic braking pumps the energy back into the storage rings"]],
    [1.85 * inch, 1.8 * inch, 2.95 * inch])]))
E.append(Paragraph("The honest hard parts", S["h2"]))
E.append(p("Fail-safes handle the failures we can name. These are the open problems that "
           "decide whether KERAUNOS gets built at all, and pretending otherwise would be "
           "salesmanship:"))
E.append(b("<b>Plasma window scale-up.</b> Demonstrated at centimeters, needed at meters. "
           "This is the program's single biggest physics-to-engineering jump, and it gets "
           "the first R&amp;D dollar."))
E.append(b("<b>The tube is the price tag.</b> Nobody has published a credible cost per "
           "kilometer for 1,000 km of vacuum-rated superconducting track. The $20-250/kg "
           "range lives or dies on that number, not on the physics."))
E.append(b("<b>SELENE's first bill is a rocket bill.</b> The starter track's coils, power "
           "plant, and radiators still ride to the Moon on somebody else's launcher at "
           "today's prices. The proof of concept has to be light enough to afford."))
E.append(b("<b>Catching is harder than throwing.</b> Cislunar catch points for high-g "
           "pellets exist on paper only. Until a tug catches the first pod, the export "
           "revenue is theoretical."))

# ---- 5. INDUSTRIES ----
E += sect("5", "New Industries &amp; Orbital Manufacturing")
E.append(reminder("Focus on gravity-sensitive production. Gravity is the impurity we are "
                  "deleting."))
E.append(b("<b>ZBLAN fiber (the demand is already proven):</b> microgravity-drawn fluoride "
           "glass with up to 100x lower theoretical signal loss than silica. In Feb-Mar "
           "2024, Flawless Photonics drew <b>~12 km of ZBLAN on the ISS</b>, with "
           "repeatable 700 m runs and 1,141 m in a single day (the previous record was "
           "25 m). The factory customers are queueing; they are waiting on freight prices."))
E.append(b("<b>Organ factories:</b> 3D-printed hearts and lungs that collapse under their "
           "own weight in 1 g. KERAUNOS's cadence enables daily return pods: orbital "
           "bioprinting becomes a medical logistics business, not a stunt."))
E.append(b("<b>Debris salvage:</b> thousands of tonnes of refined aerospace-grade alloys "
           "already orbit overhead as junk. At KERAUNOS freight prices, salvage tugs turn "
           "a profit, and the laser broom (Section 9) keeps the lane clean as a side "
           "effect."))

# ---- 6. DEEP SPACE ----
E += sect("6", "Deep Space Supply Lines (Moon &amp; Mars)")
E.append(reminder("KERAUNOS is the cargo train for the Solar System."))
E.append(b("<b>The Pellet System:</b> fire 10-tonne pods of \"dumb\" cargo (water, food, "
           "shielding, propellant) every 3 hours, which adds up to ~80 tonnes a day and "
           "~29,000 tonnes a year."))
E.append(b("<b>The SEP Tug:</b> solar-electric tugs catch the pods in LEO and slow-drift "
           "them to the Moon or Mars. Chemical speed for people, electric efficiency for "
           "cargo."))
E.append(b("<b>Asteroid mining:</b> with launch cost no longer the gate, near-Earth "
           "asteroid platinum-group recovery finally closes its business case."))

# ---- 7. QUESST ----
E += sect("7", "The Quesst Connection: Aero-Data Application")
E.append(reminder("X-59 flew on Oct 28, 2025, and is flying supersonic shockwave-tailoring "
                  "test points as of mid-2026. The aero-shell's blueprint is being written "
                  "right now."))
E.append(b("<b>Data-driven design:</b> the aero-shell isn't a plane; it's a high-hypersonic "
           "shield. X-59's pressure-distribution data ensures the Mach 12 exit doesn't "
           "shatter the tube's exit seal, or the local windows."))
E.append(b("<b>External Vision (XVS):</b> because the shell is a solid thermal shield, the "
           "craft uses NASA's flight-proven XVS camera-to-monitor system instead of "
           "windows, which would melt at launch."))

# ---- 8. MHD ----
E += sect("8", "The MHD \"Invisible Door\" (Vacuum Maintenance)")
E.append(reminder("You can't have a physical door at the end of a Mach 12 tube; it would be "
                  "obliterated. We need a seal made of energy."))
E.append(b("<b>The problem:</b> keeping a 1,000 km vacuum tube sealed while a projectile "
           "exits at 4-8 km/s, without letting air rush back in."))
E.append(b("<b>The solution:</b> an MHD plasma window, a magnetically confined plug of "
           "ionized gas that behaves like a solid wall to the outside atmosphere but is "
           "transparent to the projectile."))
E.append(b("<b>This is real, patented technology:</b> invented by Ady Hershcovitch at "
           "Brookhaven National Laboratory (patented 1995) and demonstrated holding up to "
           "~9 atmospheres; used today for non-vacuum electron-beam welding. The honest "
           "engineering frontier: it has been demonstrated at centimeter-scale apertures, "
           "and scaling to pod diameter is the program's flagship R&amp;D work package."))
E.append(b("<b>Safety:</b> if the window fails, the Section 4 blast shutters are the "
           "physical backup."))

# ---- 9 POWER TAP + 10 DEBRIS ----
E += sect("9", "The Superconducting \"Power Tap\"")
E.append(reminder("You don't just need speed; you need to manage the massive energy return."))
E.append(b("<b>Regenerative braking:</b> an aborted launch pumps the craft's kinetic energy "
           "back into the superconducting storage rings instead of into heat, like a Tesla "
           "the size of a province."))
E.append(b("<b>Quench protection:</b> varistor networks prevent magnet quench, sustaining "
           "100+ launch cycles per day without overheating the track."))
E.append(b("<b>The energy loop:</b> the launcher doubles as a grid-scale battery, soaking "
           "surplus solar and wind by day and selling stability services between launch "
           "windows. <b>The track earns money even when nothing is flying.</b>"))

E += sect("10", "Real-Time Orbital Debris \"Sweeping\"")
E.append(reminder("High-frequency launch is only possible if the highway is clear."))
E.append(b("<b>The problem:</b> launching every 3 hours raises the odds of meeting Kessler "
           "Syndrome debris."))
E.append(b("<b>The Laser Broom:</b> the same power plant that feeds the track drives ground "
           "lasers that nudge small debris off the launch corridor minutes before exit."))
E.append(b("<b>Automated routing:</b> AI-planned kick-motor burns keep pods out of orbits "
           "occupied by high-risk debris clusters."))

# ---- 11 SKYHOOK + 12 SHELLS ----
E += sect("11", "The \"Space Elevator\" Lite (Tether Points)")
E.append(reminder("KERAUNOS isn't the end goal; it's the anchor for the next phase."))
E.append(b("<b>Orbital hooks:</b> once the system is firing 80% cargo loads daily, a "
           "non-rotating skyhook catches pods at altitude and flings them moonward."))
E.append(b("<b>Efficiency:</b> kick-motor fuel drops toward zero, and cost per kg falls "
           "from $20 toward <b>$5</b>."))

E += sect("12", "Post-Launch Aero-Shell Logistics")
E.append(reminder("Don't waste the hardware that got you through the atmosphere."))
E.append(b("<b>The recovery corridor:</b> breakaway shells fall on hyper-predictable paths "
           "computed from the X-59 dataset."))
E.append(b("<b>Circular economy:</b> autonomous seafaring drones wait in the drop zone, "
           "catch the shells, re-coat the transpiration layer, and have them back in the "
           "tube within 48 hours. Nothing is thrown away: not the booster (there isn't "
           "one), not the shell, not even an aborted launch's kinetic energy."))

# ---- 13. SELENE ----
E += sect("13", "SELENE: The Lunar Launcher (Phase 1: The Proof of Concept)")
E.append(reminder("The Moon is the easiest place in the solar system to build a KERAUNOS. "
                  "No air means no tube."))
E.append(b("<b>Delete the hard parts:</b> no atmosphere means no vacuum tube, no plasma "
           "window, no aero-shell, no blast shutters, no transpiration cooling. The track "
           "IS the launcher, laid directly on the regolith. Every hard engineering problem "
           "from the Earth machine simply does not exist on the Moon."))
E.append(mathbox([
    ("Orbit: ~1.7 km/s &rarr; ~50 km of track",
     "At a gentle 3 g, low lunar orbit velocity needs roughly <b>50 km of track</b>, 5% "
     "of the Earth system. Lunar escape (2.38 km/s) needs ~96 km."),
    ("Moon &rarr; Earth orbit: ~2.4 km/s",
     "Versus 9.4+ km/s from Earth's surface. Once SELENE exists, <b>the Moon undercuts "
     "Earth for every kilogram that doesn't have to start on Earth</b>: water, oxygen, "
     "shielding mass, structural metal."),
]))
E.append(b("<b>Validated pedigree:</b> Gerard O'Neill's lunar mass-driver studies (NASA "
           "Ames / Princeton, 1970s) worked this physics out fifty years ago. What was "
           "missing was a cheap way to ship the hardware. That is exactly what the Earth "
           "KERAUNOS provides."))
E.append(b("<b>The proof of concept pays for itself, and it is tiny:</b> the starter "
           "track is 1-3 km, about the length of an airport runway. Dumb cargo (water, "
           "regolith, metal billets) doesn't mind high g, so at 100 g a 1.5 km track "
           "reaches lunar orbit speed (1.7 km/s) and <b>2.9 km clears escape velocity "
           "(2.38 km/s)</b> in a 2.4-second ride. The very first SELENE segment is not a "
           "demo: it is a working exporter, throwing water ice and regolith to cislunar "
           "catch points from day one. Initial hardware arrives by heavy-lift rocket: the "
           "last rockets the program ever needs to buy."))
E.append(b("<b>Then growth by ladder:</b> the starter track stretches to a 10-12 km, "
           "30 g line for hardened payloads (2.43-2.66 km/s, escape with margin), and "
           "later to a ~50 km, 3 g human-rated track for passengers. Each step is built "
           "from SELENE's own export revenue and, later, BRONTE shipments whose 10-tonne "
           "pods carry coil segments, radiators, and solar arrays."))
E.append(b("<b>Exports:</b> Shackleton-region water ice as propellant, LOX cracked from "
           "regolith, and raw shielding mass for stations and ships. Power from solar "
           "arrays at the Peaks of Eternal Light or compact fission. SELENE turns the Moon "
           "from a destination into <b>the quarry of cislunar space</b>."))

# ---- 14. ARES ----
E += sect("14", "ARES: The Mars Launcher")
E.append(reminder("Mars' atmosphere is 0.6% of Earth's. The hard parts of the Earth machine "
                  "become easy there."))
E.append(b("<b>A featherweight tube:</b> ambient pressure on Mars is ~6 millibars, so the "
           "tube only holds back 0.6% of the pressure the Earth tube fights, the plasma "
           "window's job is 99.4% done by the planet, and exit heating is a fraction of "
           "the Earth case. Dust storms are the main environmental design driver."))
E.append(mathbox([
    ("Orbit: ~3.4 km/s &rarr; ~180 km of track",
     "At 3.3 g, low Mars orbit needs roughly <b>180 km of track</b>; Mars escape "
     "(5.0 km/s) needs ~390 km. Between the Moon and Earth in scale, far easier than "
     "Earth in engineering."),
    ("Phobos &amp; Deimos: free staging depots",
     "ARES throws cargo to Phobos-orbit catch points, where SEP tugs and fuel depots "
     "handle the interplanetary cruise. Mars' moons are the warehouse district."),
]))
E.append(b("<b>Why it matters:</b> every Mars settlement plan dies on the cost of the "
           "return trip. ARES closes the loop: ISRU propellant (Sabatier methane, LOX), "
           "return samples, and eventually manufactured exports ride to orbit on "
           "electricity. <b>ARES turns Mars from a destination into a port.</b>"))
E.append(b("<b>Sequencing:</b> ARES is the final node. SELENE proves the machine in hard "
           "vacuum, BRONTE masters the atmosphere problem on Earth, and ARES inherits a "
           "mature hardware standard delivered by the pellet pipeline."))

# ---- 15. BUILD ORDER ----
E += sect("15", "The Build Order: Moon First")
E.append(reminder("The lightning flashes before the thunder is heard. SELENE launches "
                  "silently in vacuum before BRONTE shakes the air on Earth."))
E.append(KeepTogether([styled_table(
    ["Phase", "System", "What gets built", "What it proves / earns"],
    [["1", "<b>SELENE PoC</b> (Moon)",
      "1-3 km surface track, 50-100 g dumb-cargo mode, no tube",
      "~2.9 km at 100 g clears lunar escape (2.38 km/s): exports water ice and "
      "regolith to cislunar buyers from day one. Lowest-risk version of the machine: "
      "the atmosphere problems don't exist. Stretches to 10-12 km (30 g cargo), then "
      "~50 km (3 g, passengers) later."],
     ["2", "<b>BRONTE demo</b> (Earth)",
      "10-20 km track, vacuum tube, plasma window, mountain exit",
      "Mach 2-3 in 3 g human-rated mode; 2.4-3.4 km/s (Mach 7-10) in 30 g cargo mode: "
      "a hypersonic testbed beyond anything flying, and well past China's Mach 1.6 "
      "target for 2028. Validates the tube, the window, and the shell in atmosphere."],
     ["3", "<b>BRONTE full</b> (Earth)",
      "1,000 km tube, 8 km/s, 3.3 g",
      "$20-250/kg to LEO at one pod every 3 hours. The Space Panama Canal opens."],
     ["4", "<b>ARES</b> (Mars)",
      "~180 km track, featherweight tube",
      "Mars becomes a port; the freight triangle closes."]],
    [0.55 * inch, 1.5 * inch, 2.05 * inch, 2.5 * inch])]))
E.append(Paragraph("Why Moon-first works: the proof of concept is 300x shorter than the "
                   "full Earth machine, skips every atmosphere subsystem, and generates "
                   "revenue immediately. SELENE de-risks the magnets and mass-catch "
                   "logistics while BRONTE's demo de-risks the atmosphere tech in "
                   "parallel.", S["caption"]))

# ---- 16. TRIANGLE ----
E += sect("16", "The Interplanetary Freight Triangle")
E.append(reminder("Three launchers, one standard. The marginal cost of moving a kilogram "
                  "anywhere becomes electricity."))
E.append(KeepTogether([styled_table(
    ["Node", "Role", "Throws"],
    [["<b>BRONTE</b> (Earth)", "The forge", "Industry: machines, electronics, precision "
      "goods, and eventually people, at 3.3 g"],
     ["<b>SELENE</b> (Moon)", "The quarry", "Mass: water, oxygen, shielding, structural "
      "metal at ~2.4 km/s to anywhere in cislunar space"],
     ["<b>ARES</b> (Mars)", "The frontier port", "Propellant, samples, and exports from "
      "ISRU: the return half of the settlement economy"]],
    [1.55 * inch, 1.3 * inch, 3.75 * inch])]))
E.append(Spacer(1, 6))
E.append(b("<b>SEP tugs ride the lanes between nodes.</b> Chemical fuel is burned only for "
           "final kicks and landings; everything else is electromagnetic launch and "
           "electric cruise."))
E.append(b("<b>Each node builds the next.</b> Rockets ship SELENE's first coils; SELENE's "
           "exports help build out BRONTE; BRONTE's pellet pipeline delivers ARES; every "
           "new node makes the next one cheaper. This is how railroads conquered "
           "continents, and it is how KERAUNOS conquers the solar system."))
E.append(Paragraph("“Zeus didn't ship his thunderbolts on rockets.”", S["quote"]))

# ---- 17. EVIDENCE ----
E += sect("17", "The Evidence Ledger: Zero New Physics")
E.append(reminder("Every subsystem has flown, fired, or been patented. The pieces exist. "
                  "Nobody has assembled them. That is the entire opportunity."))
E.append(KeepTogether([styled_table(
    ["Building block", "Status (verified June 2026)"],
    [["NASA X-59 shockwave tailoring",
      "First flight Oct 28, 2025 (67 min, Palmdale). Flying supersonic test points as of "
      "Apr-May 2026. XVS camera-vision system flight-proven."],
     ["MHD plasma window",
      "Invented by A. Hershcovitch, Brookhaven National Lab; patented 1995. Holds up to "
      "~9 atm. In industrial use for non-vacuum e-beam welding. Demonstrated at cm-scale "
      "apertures. Scaling is the R&amp;D centerpiece."],
     ["Superconducting maglev",
      "603 km/h crewed rail record (JR Central, 2015). Commercial maglev operating in "
      "China today."],
     ["Electromagnetic launch assist",
      "Galactic Energy + CASIC + Ziyang government verification platform targeting 2028 "
      "(~Mach 1.6 assist). The supply chain is being built, just for the wrong finish line."],
     ["Full-scale maglev launch studies",
      "StarTram (Powell &amp; Maise, IEEE 2008-2010): $30-43/kg projected at 30 g over "
      "~130 km, mountain exit at 4,000-8,000 m."],
     ["Lunar mass driver",
      "G. O'Neill mass-driver studies, NASA Ames / Princeton, 1970s. Physics settled for "
      "half a century."],
     ["Orbital manufacturing demand",
      "Flawless Photonics: ~12 km of ZBLAN fiber drawn on ISS, Feb-Mar 2024; repeatable "
      "700 m runs; 1,141 m in one day vs prior 25 m record."],
     ["Launch market baseline",
      "Falcon 9 ~$2,720/kg customer price (~$630/kg internal); Starship targeting "
      "&lt;$100/kg, $250-600/kg realistic near-term."]],
    [2.0 * inch, 4.6 * inch])]))
E.append(Spacer(1, 10))
E.append(p("<b>KERAUNOS requires zero new physics.</b> It requires the decision to build "
           "the full-length track everyone else keeps approaching by halves, and the "
           "nation or company that makes that decision first owns the freight standard of "
           "the solar system: Earth, Moon, and Mars."))

doc.build(E, onFirstPage=cover, onLaterPages=later)
print("OK:", OUT)
