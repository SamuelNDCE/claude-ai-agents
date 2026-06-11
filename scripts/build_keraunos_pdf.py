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

NAVY  = HexColor("#0a0d18")
NAVY2 = HexColor("#141b30")
TEAL  = HexColor("#0891b2")
TEAL_BRIGHT = HexColor("#22d3ee")
PURPLE = HexColor("#7c3aed")
VIOLET = HexColor("#a78bfa")
BODY  = HexColor("#2a3245")
DIM   = HexColor("#5a6a8a")
LIGHT = HexColor("#eef2fa")
ZEBRA = HexColor("#f4f7fd")

F = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Segoe",        os.path.join(F, "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Bold",   os.path.join(F, "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Italic", os.path.join(F, "segoeuii.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Semi",   os.path.join(F, "seguisb.ttf")))
pdfmetrics.registerFontFamily("Segoe", normal="Segoe", bold="Segoe-Bold",
                               italic="Segoe-Italic", boldItalic="Segoe-Bold")

W, H = letter

S = {}
S["body"]    = ParagraphStyle("body", fontName="Segoe", fontSize=10.5, leading=16.0,
                               textColor=BODY, spaceAfter=9)
S["bullet"]  = ParagraphStyle("bullet", parent=S["body"], leftIndent=18,
                               bulletIndent=5, spaceAfter=7)
S["h1"]      = ParagraphStyle("h1", fontName="Segoe-Bold", fontSize=15.5, leading=19,
                               textColor=NAVY, spaceBefore=22, spaceAfter=3)
S["h2"]      = ParagraphStyle("h2", fontName="Segoe-Semi", fontSize=12, leading=16,
                               textColor=TEAL, spaceBefore=14, spaceAfter=6)
S["reminder"]= ParagraphStyle("reminder", fontName="Segoe-Italic", fontSize=10,
                               leading=14.5, textColor=PURPLE, leftIndent=14,
                               spaceBefore=3, spaceAfter=12)
S["mathbox"] = ParagraphStyle("mathbox", fontName="Segoe", fontSize=10,
                               leading=14.5, textColor=BODY)
S["tbl"]     = ParagraphStyle("tbl", fontName="Segoe", fontSize=9.2, leading=13,
                               textColor=BODY)
S["tblh"]    = ParagraphStyle("tblh", fontName="Segoe-Semi", fontSize=9.2, leading=13,
                               textColor=white)
S["caption"] = ParagraphStyle("caption", fontName="Segoe-Italic", fontSize=8.6,
                               leading=12, textColor=DIM, spaceBefore=4, spaceAfter=10)
S["quote"]   = ParagraphStyle("quote", fontName="Segoe-Italic", fontSize=12,
                               leading=17, textColor=PURPLE, alignment=TA_CENTER,
                               spaceBefore=16, spaceAfter=16)


def sect(num, title):
    return [Paragraph(f"{num}. {title}", S["h1"]),
            HRFlowable(width="100%", thickness=1.4, color=TEAL,
                       spaceBefore=4, spaceAfter=12)]

def reminder(text):
    return Paragraph(text, S["reminder"])

def b(text):
    return Paragraph(text, S["bullet"], bulletText="●")

def p(text):
    return Paragraph(text, S["body"])

def mathbox(rows):
    data = [[Paragraph(f"<font face='Segoe-Semi' color='#0891b2'>{f}</font>",
                       S["mathbox"]),
             Paragraph(e, S["mathbox"])] for f, e in rows]
    t = Table(data, colWidths=[2.15*inch, 4.45*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT),
        ("BOX",           (0,0), (-1,-1), 0.8, HexColor("#c7d4ec")),
        ("LINEBELOW",     (0,0), (-1,-2), 0.5, HexColor("#d8e2f3")),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 9),
        ("LEFTPADDING",   (0,0), (-1,-1), 11),
        ("RIGHTPADDING",  (0,0), (-1,-1), 11),
    ]))
    return KeepTogether([t])

def styled_table(header, rows, widths, highlight_row=None):
    data = [[Paragraph(h, S["tblh"]) for h in header]]
    for r in rows:
        data.append([Paragraph(c, S["tbl"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND",    (0,0), (-1,0),  NAVY2),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 9),
        ("RIGHTPADDING",  (0,0), (-1,-1), 9),
        ("BOX",           (0,0), (-1,-1), 0.8, HexColor("#c7d4ec")),
        ("LINEBELOW",     (0,0), (-1,-2), 0.5, HexColor("#d8e2f3")),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0,i), (-1,i), ZEBRA))
    if highlight_row is not None:
        style.append(("BACKGROUND", (0,highlight_row), (-1,highlight_row),
                      HexColor("#e6f7fb")))
    t.setStyle(TableStyle(style))
    return t

def draw_gates(c):
    """Kept for reference; not called from cover."""
    pass

def cover(c, doc):
    c.saveState()
    c.setFillColor(white)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Segoe-Bold", 56)
    c.drawCentredString(W/2, H - 4.85*inch, "KERAUNOS")
    c.setFillColor(VIOLET)
    c.setFont("Segoe", 15)
    c.drawCentredString(W/2, H - 5.35*inch, "The Thunderbolt of Zeus, Industrialized")
    c.setStrokeColor(PURPLE)
    c.setLineWidth(1.2)
    c.line(W/2 - 1.6*inch, H - 5.62*inch, W/2 + 1.6*inch, H - 5.62*inch)
    c.setFillColor(DIM)
    c.setFont("Segoe", 12.5)
    c.drawCentredString(W/2, H - 6.0*inch,
                        "Maglev Space Launch System  ·  SELENE · BRONTE · ARES")
    c.setFillColor(NAVY)
    c.setFont("Segoe-Semi", 13)
    c.drawCentredString(W/2, 1.55*inch, "Samuel Edwards")
    c.setFillColor(DIM)
    c.setFont("Segoe", 10)
    c.drawCentredString(W/2, 1.32*inch, "June 2026  ·  Concept Whitepaper")
    c.restoreState()

def later(c, doc):
    c.saveState()
    c.setStrokeColor(TEAL)
    c.setLineWidth(0.8)
    c.line(0.95*inch, H - 0.62*inch, W - 0.95*inch, H - 0.62*inch)
    c.setFont("Segoe-Semi", 7.6)
    c.setFillColor(DIM)
    c.drawString(0.95*inch, H - 0.55*inch,
                 "KERAUNOS  ·  MAGLEV SPACE LAUNCH SYSTEM")
    c.drawRightString(W - 0.95*inch, H - 0.55*inch, "SAMUEL EDWARDS")
    c.setFont("Segoe", 8)
    c.drawCentredString(W/2, 0.5*inch, f"{doc.page - 1}")
    c.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=letter,
                        leftMargin=0.95*inch, rightMargin=0.95*inch,
                        topMargin=1.0*inch,  bottomMargin=0.85*inch,
                        title="KERAUNOS: Maglev Space Launch System",
                        author="Samuel Edwards")

E = []
E.append(Spacer(1, 1))
E.append(PageBreak())

# ===== 0. EXECUTIVE SUMMARY =====
E += sect("0", "Executive Summary")
E.append(p(
    "Earth, with its thick atmosphere, is the hardest body in the system to launch from "
    "electromagnetically. So the program starts on the Moon, where the machine is "
    "native, and works outward from there. The full Earth injector is the long-horizon "
    "prize. It is not the opening move."
))
E.append(KeepTogether([styled_table(
    ["Launcher", "Body", "Phase", "Character"],
    [
        ["<b>SELENE</b>", "Moon",  "1: Proof of concept",
         "No atmosphere: no tube, no plasma window, no aero-shell. The starter track is "
         "1-3 km. At 100 g, 2.9 km clears lunar escape in 2.4 seconds. Water, regolith, "
         "and metal don't mind the g-load. First segment isn't a demo: it's a working "
         "exporter from day one."],
        ["<b>BRONTE</b>", "Earth", "2: The Chimborazo Project",
         "A 10-20 km evacuated track exiting at <b>6,263 m on the equator</b>: "
         "Chimborazo, Ecuador. Proves the tube, plasma window, and aero-shell at 10% "
         "scale. DoD hypersonic test contracts pay for it."],
        ["<b>ARES</b>",   "Mars",  "3: The port",
         "Mars atmosphere is 0.6% of Earth's. The tube is featherweight. ARES closes "
         "the return-trip problem every Mars settlement plan dies on."],
    ],
    [1.0*inch, 0.7*inch, 1.55*inch, 3.35*inch])]))
E.append(Spacer(1, 6))

E.append(KeepTogether([Paragraph("SELENE: Moon (Phase 1)", S["h2"]),
    styled_table(
    ["Parameter", "Value", "Notes"],
    [
        ["Track (PoC)",        "1-3 km, 50-100 g",
         "At 100 g: 1.5 km = orbit speed (1.7 km/s); 2.9 km = escape (2.38 km/s) in 2.4 s"],
        ["Track (cargo)",      "10-12 km, 30 g",
         "2.43-2.66 km/s; escape with margin; 8 s ride"],
        ["Track (passengers)", "~50 km, 3 g",
         "1.7 km/s to low lunar orbit in 58 s"],
        ["Energy per kg",      "0.40 kWh orbit / 0.79 kWh escape",
         "Roughly 1/20th of Earth launch energy"],
        ["Atmosphere",         "None",
         "No tube. No plasma window. No aero-shell. The track is the launcher."],
        ["Cooling",            "Passive at south pole",
         "Ambient ~90K is just below YBCO's 92K critical temperature: no active cryogenics"],
    ],
    [1.45*inch, 1.95*inch, 3.2*inch])]))

E.append(KeepTogether([Paragraph("BRONTE: Earth (Chimborazo Project, 10-20 km demonstrator)", S["h2"]),
    styled_table(
    ["Parameter", "Value", "Notes"],
    [
        ["Site",           "Chimborazo, Ecuador",
         "6,263 m ASL; 1.47°S latitude; western Pacific-facing slopes"],
        ["Exit air density","~45% of sea level",
         "Peak drag and stagnation heating roughly halved versus a ground-level exit"],
        ["Equatorial bonus","+465 m/s free",
         "Earth's rotation at the equator: net launcher requirement to LEO is ~7.5 km/s, "
         "not ~8 km/s"],
        ["Demo speeds",    "Mach 2-3 (3 g) / Mach 7-10 (30 g)",
         "Mach 7-10 cargo mode exceeds China's entire 2028 Mach 1.6 target"],
        ["Revenue",        "$50K-$500K per test run",
         "DoD hypersonic test services from day one"],
        ["Full Earth injector","Long-horizon, separate project",
         "Built only after Chimborazo validates the atmosphere subsystems and cost data"],
    ],
    [1.45*inch, 1.85*inch, 3.3*inch])]))

E.append(KeepTogether([Paragraph("ARES: Mars (Phase 3)", S["h2"]),
    styled_table(
    ["Parameter", "Value", "Notes"],
    [
        ["Atmosphere",    "~6 mbar (0.6% of Earth)",
         "Featherweight tube; plasma window's job is 99.4% done by the planet"],
        ["Track (orbit)", "~180 km, 3.3 g",
         "Low Mars orbit speed (~3.4 km/s) in a 105 s run"],
        ["Track (escape)","~390 km, 3.3 g",
         "Mars escape (~5.0 km/s) in a 155 s run"],
        ["Energy per kg", "1.6 kWh orbit / 3.5 kWh escape",
         "Between Moon and Earth in scale; far easier than Earth in engineering"],
        ["Staging",       "Phobos and Deimos",
         "Catch points and fuel depots; SEP tugs handle interplanetary cruise"],
    ],
    [1.45*inch, 1.95*inch, 3.2*inch])]))
E.append(Spacer(1, 6))

# ===== 1. SELENE =====
E.append(KeepTogether(
    sect("1", "SELENE: The Moon Machine") +
    [
        reminder(
            "The Moon has no atmosphere. That sentence deletes every hard engineering "
            "problem on the list below."
        ),
        p("On the Moon, these things do not exist:"),
        b("No vacuum tube. The track is already in vacuum."),
        b("No plasma window. There is no atmosphere trying to get in."),
        b("No aero-shell. Nothing for it to protect against."),
        b("No blast shutters. No tube to breach."),
        b("No transpiration cooling. The exit is into hard vacuum."),
        p(
            "The track lays on regolith. That is the entire system. Every hard engineering "
            "challenge from the Earth machine simply does not exist on the Moon."
        ),
    ]
))
E.append(p(
    "The starter track is <b>1-3 km</b>: roughly the length of an airport runway. "
    "At 100 g, a 1.5 km run reaches lunar orbit speed (<b>1.7 km/s</b>). A 2.9 km "
    "run clears escape velocity (<b>2.38 km/s</b>) in 2.4 seconds. Water, regolith, "
    "and metal don't mind the g-load. The very first segment isn't a demo. "
    "It is a working exporter."
))
E.append(mathbox([
    ("0.79 kWh/kg to escape",
     "Lunar escape costs roughly <b>one-tenth of Earth-to-orbit launch energy</b> "
     "(0.79 kWh/kg vs 8.9 kWh/kg at 8 km/s). From the Moon, you are already "
     "partway to everywhere else. Moon-to-Earth-orbit requires ~2.4 km/s; Earth's "
     "surface to LEO requires 8+ km/s electromagnetically. Every kilogram of water "
     "ice, oxygen, or structural metal that starts on the Moon instead of Earth is "
     "dramatically cheaper to ship anywhere in the inner solar system."),
    ("Ambient ~90K at south pole",
     "YBCO superconductors go superconducting below <b>92K</b>. The lunar south pole "
     "sits at <b>~90K</b>. The Moon refrigerates the coils for free. No liquid nitrogen "
     "supply chain. No active cryogenic infrastructure. The environment does the work."),
]))
E.append(p(
    "<b>The south pole is the right site.</b> Shackleton-rim ridgelines see sun "
    "80-90% of the time. Water ice sits in the permanently shadowed crater next door. "
    "Power, propellant feedstock, and passive coil cooling are all at the same location."
))
E.append(p(
    "<b>The physics has been settled for fifty years.</b> Gerard O'Neill worked this "
    "out at NASA Ames and Princeton in the 1970s. A published San Jose State study "
    "describes a lunar mass driver launching 25 kg pellets at 2.4 km/s using "
    "8.7 MW of continuous polar solar power and approximately one million amps of "
    "coil current per shot. SELENE's starter track is exactly that class of machine. "
    "The physics is not the question. The only thing that killed every previous "
    "program was the same: all government funding, no revenue until a Moon base "
    "already existed. Cislunar freight removes that deadlock."
))
E.append(p(
    "Propellant depots need water ice. Orbital stations need shielding mass. "
    "The Moon has both. After SELENE exists, shipping them costs electricity. "
    "<b>SELENE turns the Moon from a destination into the quarry of cislunar space.</b>"
))
E.append(p(
    "SELENE grows by ladder. The starter track stretches to a <b>10-12 km, 30 g line</b> "
    "for hardened cargo (escape with margin, 8 s ride), then to a <b>~50 km, 3 g track</b> "
    "for passengers. Each step is funded by the previous segment's export revenue and, "
    "once BRONTE operates, by inbound pellet shipments carrying coil segments, "
    "radiators, and solar arrays."
))
E.append(p(
    "<b>The SELENE kit is the template for every airless body worth working.</b> "
    "Phobos. Deimos. Ceres. The asteroid belt. Design once, stamp copies. "
    "The fleet of these machines is the real bet."
))

# ===== 2. PHYSICS =====
E.append(KeepTogether(sect("2", "The Physics and Price") + [reminder(
    "The electricity cost to reach orbit is $0.53 per kilogram at 8 km/s. "
    "Everything above that price is hardware amortization, not physics."
)]))
E.append(p(
    "At 8 km/s, kinetic energy is <b>32 MJ per kilogram</b>. At $0.06/kWh, "
    "that is <b>$0.53 of electricity per kilogram</b>. Falcon 9 burns roughly "
    "$300,000 of propellant per launch for 22.8 tonnes to LEO: about $13 per kg "
    "in fuel alone, on a vehicle that is 90% propellant by mass. "
    "A KERAUNOS pod carries <b>20% propellant</b> for the circularization kick at "
    "apogee only. The other <b>80% is payload</b>. That is an 8x improvement in "
    "payload fraction per launched tonne."
))
E.append(mathbox([
    ("E = &frac12;v&sup2; = 32 MJ/kg",
     "<b>$0.53 of grid electricity per kilogram to orbital velocity</b> at 8 km/s "
     "and $0.06/kWh. Every dollar above that in the ticket price is amortization "
     "of track hardware. The propellant cost of Falcon 9 alone is 25x higher "
     "per kilogram than KERAUNOS's total electricity spend."),
    ("a = v&sup2; / 2L",
     "Acceleration is set by velocity and track length. A 1,000 km Earth tube "
     "reaches 8 km/s at <b>3.3 g</b>, gentle enough for human payloads. StarTram "
     "used 130 km and accepted 30 g: cargo-only. On the Moon, a 3 g passenger "
     "track is ~50 km. <b>Tube length is the unlock.</b>"),
    ("Kick motor: Isp 350 s, 20% propellant",
     "delta-v = 3,434 x ln(1/0.8) = <b>~0.77 km/s</b> for circularization and "
     "trim at apogee. That is the only propellant on board."),
]))
E.append(Spacer(1, 6))
E.append(KeepTogether([
    Paragraph("Comparative launch costs (per kg to LEO)", S["h2"]),
    styled_table(
        ["Launch system", "Cost per kg", "Economic bottleneck"],
        [
            ["Space Shuttle",              "$54,500",
             "Hand-built; massive refurbishment after every flight"],
            ["SpaceX Falcon 9",            "~$2,720 customer / ~$630 internal",
             "Fuel costs plus expended or refurbished hardware"],
            ["SpaceX Starship (projected)", "$100-$1,000",
             "Hard limit of chemical fuel energy density"],
            ["<b>KERAUNOS</b>",            "<b>$20-$250</b>",
             "$0.53/kg electricity; rest is amortization of track capital"],
            ["<b>KERAUNOS + skyhook</b>",  "<b>toward $5</b>",
             "Kick-motor fuel approaches zero once skyhook catches pods at altitude"],
        ],
        [1.9*inch, 1.95*inch, 2.75*inch], highlight_row=4),
    Paragraph(
        "Falcon 9 figures: customer price vs estimated internal cost. "
        "Starship range reflects near-term reuse assumptions.", S["caption"]),
]))

# ===== 3. WHY NOW =====
E.append(KeepTogether(sect("3", "Why Now: Three Signals in 24 Months") + [reminder(
    "The field just validated itself publicly. The window to enter "
    "at peer level is right now."
)]))
E.append(p(
    "<b>SpaceX put a lunar mass driver on its public roadmap in March 2026.</b> "
    "Elon Musk described \"a cannon-like device using magnetic power\" to launch "
    "Moon-manufactured AI satellites at scale, and the company has shifted its "
    "near-term focus from Mars to the Moon. The largest launch company on Earth "
    "is pointing at exactly this machine. That is validation, and it is also a clock."
))
E.append(p(
    "<b>China is building EM launch hardware, targeting 2028.</b> Galactic Energy, "
    "CASIC, and the Ziyang government are constructing an electromagnetic launch "
    "verification platform targeting Mach 1.6 before rocket ignition. "
    "That is a faster runway for a conventional rocket: the rocket still "
    "carries the full propellant penalty. But the supply chain is being built, "
    "and the competitive urgency is real."
))
E.append(p(
    "<b>The US military is already funding this class of technology.</b> "
    "Auriga Space raised $12.2M with AFWERX Phase II contracts for an EM launch-assist "
    "track, using hypersonic test services as Phase 1 revenue. General Atomics EMALS "
    "has operated on USS Gerald R. Ford for years. A <b>2023 AFOSR report explicitly "
    "recommends evolving EMALS for lunar launch.</b> There is a standing US SBIR "
    "solicitation for a magnetically levitated sled driven to 7 km/s by a linear motor. "
    "The demand signal is public and funded."
))
E.append(p(
    "<b>The gap nobody is filling:</b> every competitor is fighting the atmosphere. "
    "China's Mach 1.6 platform, StarTram's 130 km Earth tube, Auriga's launch-assist "
    "rocket. Nobody has built the launcher where the atmosphere simply does not exist. "
    "KERAUNOS starts there. The vacuum-world fleet is the gap in the market, "
    "and the competitors are primed to accept a vacuum-world kit as the logical "
    "evolution of their own research."
))

# ===== 4. CHIMBORAZO =====
E.append(KeepTogether(sect("4", "The Chimborazo Project: BRONTE's Earth Demonstrator") + [reminder(
    "BRONTE is not a 1,000 km commitment. "
    "It is a 10-20 km demonstrator, and the site is already chosen."
)]))
E.append(p(
    "<b>Chimborazo. Ecuador. 6,263 meters above sea level. 1.47 degrees south latitude.</b>"
))
E.append(p(
    "It is not the obvious choice until you look at the numbers. "
    "Then it is the only choice on Earth."
))
E.append(b(
    "<b>Altitude.</b> Air density at the Chimborazo summit is <b>~45% of sea level</b>. "
    "The muzzle exits into air that is already more than half gone. Peak drag and "
    "stagnation heating in the critical milliseconds of the tube-to-atmosphere "
    "transition are roughly halved compared to a ground-level exit. "
    "This matches the StarTram reference design's exit altitude range of 4,000-8,000 m."
))
E.append(b(
    "<b>Equatorial velocity: 465 m/s free.</b> Earth rotates at <b>465 m/s</b> "
    "eastward at the equator. That is Mach 1.4 of velocity that does not have to "
    "come from the launcher. A Chimborazo-based BRONTE needs to add roughly "
    "<b>7.5 km/s</b> to reach LEO, not ~8 km/s. That difference compounds "
    "across tens of thousands of launches per year."
))
E.append(b(
    "<b>Orbital access.</b> Equatorial launches reach any orbital inclination. "
    "Most commercial LEO and GTO missions target equatorial or near-equatorial "
    "orbits. Chimborazo's geometry is optimal for the majority of the commercial "
    "launch market."
))
E.append(b(
    "<b>Safety corridor.</b> Chimborazo's western slopes face the Pacific Ocean. "
    "Spent aero-shells and any misfires cross uninhabited ocean, not populated land. "
    "The same logic that placed Cape Canaveral on the Atlantic and Kourou on the "
    "Atlantic applies here, with the additional advantage of equatorial position."
))
E.append(Paragraph("What the Chimborazo demonstrator proves", S["h2"]))
E.append(p(
    "A 10-20 km evacuated track, exiting near the summit, firing a hypersonic sled "
    "through the mountain's thin air. At 3 g this is human-rated, reaching Mach 2-3. "
    "At 30 g cargo mode it hits <b>Mach 7-10</b>: well past China's 2028 Mach 1.6 "
    "target, and a hypersonic test capability that does not exist anywhere on Earth "
    "at this altitude and latitude combination."
))
E.append(p(
    "<b>Every hard piece of the Earth machine gets tested at 10% of its final scale.</b> "
    "The plasma window holds atmosphere out of the tube. The aero-shell takes the exit "
    "transition at full hypersonic conditions. The superconducting coils operate in "
    "thin, cold mountain air. If these work at Chimborazo, the physics works at "
    "full scale. And if they don't, we find out cheaply."
))
E.append(Paragraph("Revenue from day one", S["h2"]))
E.append(p(
    "DoD hypersonic test contracts: the same market Auriga Space is already selling, "
    "at conditions no other facility can match. Current hypersonic test options are "
    "scarce. Sounding rockets are single-shot. Wind tunnels don't reach real Mach 6+ "
    "at altitude. A track that runs multiple test sleds per day at Mach 7-10 "
    "from 6,263 m on the equator is a facility nobody else has. "
    "At <b>$50K-$500K per test run, one run per week covers operations.</b> "
    "The demonstrator is not a cost center. It is a product."
))
E.append(KeepTogether([
    Paragraph("Chimborazo demonstrator specifications", S["h2"]),
    styled_table(
        ["Parameter", "Value", "Notes"],
        [
            ["Site",            "Chimborazo, Ecuador",
             "6,263 m ASL; 1.47°S; Pacific-facing western slopes; "
             "Andes plateau base at ~4,000 m"],
            ["Track length",    "10-20 km evacuated tube",
             "Superconducting maglev; plasma window; mountain exit near summit"],
            ["Exit air density","~45% of sea level",
             "Peak drag and heating roughly halved vs ground-level exit; "
             "matches StarTram reference exit altitude"],
            ["Equatorial bonus","465 m/s (Mach 1.4)",
             "Free velocity from Earth's rotation; net launcher requirement to "
             "LEO: ~7.5 km/s"],
            ["Demo speeds",     "Mach 2-3 (3 g) / Mach 7-10 (30 g)",
             "Mach 7-10 cargo mode: no other Earth facility reaches this at altitude"],
            ["Revenue model",   "$50K-$500K per test run",
             "DoD hypersonic test services; same market as Auriga, better site"],
            ["What it proves",  "Tube, plasma window, aero-shell, coil survivability",
             "Every atmosphere subsystem validated at 10% of any full Earth-injector "
             "scale before a larger commitment is made"],
        ],
        [1.45*inch, 1.85*inch, 3.3*inch])]))
E.append(Spacer(1, 4))

# ===== 5. ARES =====
E.append(KeepTogether(sect("5", "ARES: The Mars Port") + [reminder(
    "Mars atmosphere is 0.6% of Earth's. The hard parts of the Earth machine "
    "are nearly free there."
)]))
E.append(p(
    "The tube only holds back 0.6% of the pressure the Earth tube fights. "
    "The plasma window's job is 99.4% done by the planet. Exit heating is a "
    "fraction of the Earth case. Dust storms are the main environmental design "
    "driver, not aerodynamics."
))
E.append(mathbox([
    ("Orbit: ~3.4 km/s &rarr; ~180 km",
     "At 3.3 g, low Mars orbit velocity needs roughly <b>180 km of track</b>. "
     "Mars escape (5.0 km/s) needs ~390 km. That is between Moon and Earth in scale, "
     "and far easier than Earth in engineering."),
    ("Phobos &amp; Deimos: free depots",
     "ARES throws cargo to Phobos-orbit catch points. SEP tugs and fuel depots handle "
     "the interplanetary cruise. <b>Mars' moons become the warehouse district.</b>"),
]))
E.append(p(
    "Every Mars settlement plan dies on the same problem: the cost of the return trip. "
    "ISRU propellant (Sabatier methane, LOX), return samples, and eventually "
    "manufactured exports all ride to orbit on electricity. "
    "<b>ARES turns Mars from a destination into a port.</b>"
))
E.append(p(
    "ARES is Phase 4. SELENE proves the vacuum-world kit in the hardest vacuum. "
    "The Chimborazo Project proves the atmosphere technology on Earth. ARES inherits "
    "a mature hardware standard, delivered by the same pellet pipeline BRONTE runs."
))

# ===== 6. BUILD ORDER =====
E.append(KeepTogether(
    sect("6", "The Build Order") +
    [
        reminder(
            "The lightning flashes before the thunder is heard. "
            "SELENE launches silently in vacuum before BRONTE shakes the air on Earth."
        ),
        styled_table(
            ["Phase", "System", "What gets built", "What it proves / earns"],
            [
                ["1", "<b>SELENE PoC</b> (Moon)",
                 "1-3 km surface track, 50-100 g dumb cargo, no tube, south pole",
                 "2.9 km at 100 g clears lunar escape. Exports water ice and regolith "
                 "to cislunar buyers from day one. The atmosphere problems don't exist. "
                 "Grows to 10-12 km (30 g cargo) then ~50 km (3 g passengers)."],
                ["2", "<b>Chimborazo</b> (Earth)",
                 "10-20 km track, Chimborazo, Ecuador; evacuated tube, plasma window, aero-shell",
                 "Mach 7-10 hypersonic capability at 6,263 m on the equator. DoD test "
                 "contracts fund operations. Validates every atmosphere subsystem before "
                 "any larger Earth commitment. Exceeds China's 2028 Mach 1.6 target."],
                ["3", "<b>Vacuum-world fleet</b>",
                 "SELENE-class kits on Phobos, Deimos, Ceres, asteroid belt",
                 "The core bet pays out. Phobos and Deimos become Mars freight terminals "
                 "before ARES exists. A standard launcher on every airless body worth working."],
                ["4", "<b>ARES</b> (Mars)",
                 "~180 km track, featherweight tube",
                 "Mars becomes a port. The freight network closes."],
                ["5", "<b>BRONTE full</b> (Earth, if proven)",
                 "Full Earth injector, if economics and plasma window scaling prove out",
                 "The endgame. Built only after Chimborazo data validates the cost per "
                 "kilometer and the atmosphere subsystems at scale."],
            ],
            [0.55*inch, 1.5*inch, 2.05*inch, 2.5*inch]),
    ]
))
E.append(Paragraph(
    "SELENE is 300x shorter than any full Earth injector, skips every atmosphere "
    "subsystem, and generates revenue immediately. Chimborazo is 50-100x shorter "
    "and proves the hard atmosphere parts before a large commitment. "
    "Both de-risk in parallel.",
    S["caption"]))

# ===== 7. HOW THE NETWORK MOVES MASS =====
E.append(KeepTogether(sect("7", "How the Network Moves Mass") + [reminder(
    "Three launchers, one supply chain. Once all three exist, the cost of moving "
    "mass around the inner solar system is mostly the cost of running the launchers."
)]))
E.append(p(
    "Earth sends what only Earth can build. Machines, precision electronics, "
    "medical supplies, manufactured components - anything that requires industrial "
    "civilization to produce. BRONTE fires at 80 tonnes per day, 29,000 tonnes per "
    "year, at 3.3 g from Chimborazo. Precision cargo at 3 g, bulk at higher "
    "acceleration."
))
E.append(p(
    "The Moon sends raw mass. Water ice from Shackleton Crater is the most "
    "valuable commodity in cislunar space: cracked to hydrogen and oxygen, it "
    "becomes propellant for every depot and transfer vehicle in the system. "
    "Regolith serves as radiation shielding for stations and ships. "
    "Metal goes to orbital construction. SELENE fires all of it at 2.4 km/s toward "
    "any cislunar catch point. The Moon doesn't need to manufacture anything. "
    "It just has to be a source of mass. It already is."
))
E.append(p(
    "Mars closes the return trip. Every Mars settlement plan faces the same problem: "
    "the cost of getting anything back. ARES solves it. ISRU methane and LOX, "
    "return samples, and eventually manufactured exports all ride to Phobos or "
    "Deimos orbit on electricity. SEP tugs handle the interplanetary cruise from "
    "there."
))
E.append(p(
    "SEP tugs connect the nodes. Weeks to months per trip, not hours, but they run "
    "on sunlight and burn almost no propellant. Chemical rockets do final descent "
    "burns and landings only. The electromagnetic launchers handle all the heavy "
    "lifting off any surface."
))
E.append(b(
    "<b>Each node funds the next.</b> Rockets deliver SELENE's first coils to the "
    "Moon: the last rocket buy the program needs for lunar construction. SELENE's "
    "export revenue funds the Chimborazo demonstrator. BRONTE's cargo line delivers "
    "ARES hardware. Every additional airless body added to the network - Phobos, "
    "Deimos, Ceres, anything in the asteroid belt - makes the whole system richer. "
    "The long-term bet is not one system. It is a standard launcher on every "
    "airless body worth working."
))

# ===== 8. THE SKYHOOK =====
E.append(KeepTogether(sect("8", "The Skyhook: How Cost Falls Toward $5 per Kilogram") + [reminder(
    "A rotating tether in orbit catches KERAUNOS pods and flings them higher. "
    "No propellant. The pod delivers more payload per launch. Cost drops."
)]))
E.append(p(
    "The problem with reaching orbit from the ground: the launcher accelerates the "
    "pod to full orbital velocity, and the pod still carries a kick motor for the "
    "circularization burn at apogee. That motor and its propellant account for "
    "roughly 20% of the pod's mass. The skyhook removes that requirement "
    "entirely."
))
E.append(Paragraph("What it is", S["h2"]))
E.append(p(
    "A long tether rotating in low Earth orbit. As it rotates, the bottom tip sweeps "
    "downward and moves slower than orbital velocity at that altitude. A KERAUNOS "
    "pod that reaches the bottom tip at the right moment gets grabbed. Half a "
    "rotation later, the pod is at the top of the tether, now moving much faster "
    "than orbital velocity. It gets released on a trajectory to the Moon, high orbit, "
    "or wherever the mission calls for. No propellant involved."
))
E.append(p(
    "With a tip speed of <b>1.5 km/s</b>, KERAUNOS needs to accelerate a pod to "
    "<b>6.3 km/s</b> instead of 7.8 km/s. Since kinetic energy scales as v&sup2;, "
    "that is roughly <b>35% less energy per launch</b>. Less energy means a shorter "
    "track for the same g-load, or a lower g-load for the same track. "
    "It also means the pod exits the tube at Mach 21 instead of Mach 26, "
    "which reduces stagnation heating and simplifies the aero-shell."
))
E.append(Paragraph("What happens to the pod", S["h2"]))
E.append(p(
    "The pod currently carries ~20% propellant mass for the circularization burn. "
    "That is the only reason the propellant is there. With the skyhook handling "
    "circularization, the pod carries propellant only for small trajectory "
    "corrections: roughly 2-5% by mass instead of 20%. "
    "The other 15-18% becomes additional payload."
))
E.append(p(
    "That shift is where <b>$5/kg</b> comes from. The launcher runs on the same "
    "grid electricity. The tether costs essentially nothing to operate. "
    "Each pod delivers roughly 50% more useful mass per flight than the baseline."
))
E.append(Paragraph("Keeping the tether in orbit", S["h2"]))
E.append(p(
    "Each time the tether catches a pod, it loses a small amount of orbital energy. "
    "Two ways to replenish it:"
))
E.append(b(
    "<b>Electrodynamic tether propulsion.</b> Run electrical current through the "
    "tether cable. Earth's magnetic field acts on that current and pushes the tether "
    "to a higher orbit. No propellant consumed: just electricity from solar panels "
    "on the station at the tether's center. This is demonstrated technology."
))
E.append(b(
    "<b>Return mass flow.</b> Return capsules descending from orbit can be caught at "
    "the tether's bottom tip on the way down, transferring their momentum back into "
    "the system. At 80 tonnes per day going up, even a small fraction of that mass "
    "returning keeps the tether stable with minimal electrodynamic assist."
))
E.append(Paragraph("The lunar extension", S["h2"]))
E.append(p(
    "The same logic applies at the Moon. A tether rotating in cislunar space can "
    "intercept mass fired by SELENE and redirect it: to low lunar orbit, to "
    "Earth-Moon L1, or on a direct Earth trajectory. A catching tether in Earth "
    "orbit handles the arrival. The full chain: SELENE fires, a cislunar tether "
    "redirects, a transfer tug hands off, an Earth-orbit tether captures. "
    "The cargo arrives without a single propellant burn from the cargo itself. "
    "The electricity cost is on both ends. The tether does the rest."
))
E.append(p(
    "Momentum exchange tethers have been studied since the 1970s. Boeing published "
    "a detailed rotovator design study in 1999. The engineering challenge is "
    "building a tether long and strong enough at orbital scale. "
    "Materials and manufacturing, not new physics."
))

# ===== 9. IF THE EARTH SYSTEM GETS BUILT =====
E.append(KeepTogether(sect("9", "If the Full Earth Injector Gets Built") + [reminder(
    "This is not the plan. The vacuum fleet is the plan. "
    "But if the vacuum fleet works, this is what becomes possible."
)]))
E.append(p(
    "A full Earth injector - roughly 1,000 km of evacuated superconducting track, "
    "a plasma window at the muzzle, a high-altitude mountain site, pods surviving "
    "the transition to Mach 26 in open air - is the hardest version of this machine. "
    "It is also the most consequential piece of infrastructure ever built."
))
E.append(p(
    "Here is the key point: <b>if SELENE works on the Moon, and the Chimborazo "
    "demonstrator validates the atmosphere subsystems, the full Earth injector "
    "stops being a physics question. It becomes a construction question.</b> "
    "After a decade of building vacuum-world launchers across the solar system, "
    "the teams involved will know exactly what they are doing."
))
E.append(Paragraph("What $5-20 per kilogram to orbit actually changes", S["h2"]))
E.append(p(
    "Right now, LEO costs roughly $2,700 per kilogram on Falcon 9. "
    "That number puts a floor under everything in space. Satellites are expensive "
    "partly because launch is expensive. Space stations require enormous budgets "
    "partly because resupply is expensive. Orbital manufacturing stays a research "
    "activity because the freight economics never worked. At $5-20/kg, all of "
    "that changes."
))
E.append(b(
    "<b>Satellites.</b> A GPS satellite launch on Falcon 9 costs roughly $60 million. "
    "At $10/kg for a 2,000 kg satellite, that is $20,000. "
    "Constellation operators can afford to replace satellites on a maintenance "
    "schedule rather than engineering them for 15-year lifetimes just to amortize "
    "the launch cost."
))
E.append(b(
    "<b>Space stations.</b> The ISS spends a large fraction of its $4 billion annual "
    "budget on supply launches. At $10/kg, that supply bill drops by a factor of "
    "roughly 300. A station housing a thousand people becomes economically normal. "
    "Stations housing tens of thousands become conceivable."
))
E.append(b(
    "<b>Orbital manufacturing.</b> ZBLAN fiber, pharmaceutical crystals, exotic "
    "alloys: all require microgravity, all require shipping the product back to Earth. "
    "At $5/kg, the viable product list grows to almost anything with real margins. "
    "Flawless Photonics drew 12 km of ZBLAN on the ISS in early 2024. Factory "
    "customers are already queuing. They are waiting on the freight price."
))
E.append(b(
    "<b>Deep space.</b> With cheap Earth-to-orbit and SELENE supplying lunar "
    "propellant mass, the economics of going anywhere in the solar system shift "
    "completely. Mars missions stop being nation-sized budget exercises. "
    "The asteroid belt becomes commercially reachable."
))
E.append(Paragraph("The strategic picture", S["h2"]))
E.append(p(
    "The operator of a full Earth injector controls the access ramp to all of space. "
    "At 80 tonnes per day, the commercial launch market runs through one chokepoint. "
    "Every satellite operator, every space station program, every deep space mission "
    "pays for the privilege. The operator doesn't pay for launch. It charges."
))
E.append(p(
    "A system placing 29,000 tonnes per year into orbit can replenish a damaged "
    "satellite constellation in hours. Orbital logistics become a strategic asset "
    "in a way they have never been, because cost was always the constraint. "
    "At $5-20/kg, it is not the constraint anymore."
))
E.append(p(
    "The vacuum fleet is the plan. It pays for itself. "
    "The Earth injector is what the vacuum fleet eventually makes possible."
))

# ===== 10. ZERO NEW PHYSICS =====
E.append(KeepTogether(sect("10", "Zero New Physics") + [reminder(
    "Every subsystem has flown, fired, or been patented. "
    "The pieces exist. Nobody has assembled them."
)]))
E.append(styled_table(
    ["Building block", "Status (verified June 2026)"],
    [
        ["EMALS (US Navy)",
         "Operational linear EM launcher on USS Gerald R. Ford: 484 MJ flywheel storage, "
         "45 s recharge, in carrier service. A 2023 AFOSR report recommends evolving "
         "it for lunar launch."],
        ["Superconducting maglev",
         "603 km/h crewed rail record (JR Central, 2015). Commercial maglev lines "
         "operating in China today."],
        ["YBCO superconductors",
         "Critical temperature 92K. Liquid nitrogen cools on Earth ($0.30/L vs $30/L "
         "for helium). Lunar south pole ambient (~90K) cools passively. Commercial "
         "tape suppliers exist: SuperPower Inc., American Superconductor."],
        ["MHD plasma window",
         "Invented by A. Hershcovitch at Brookhaven National Lab; patented 1995. Holds "
         "up to ~9 atm. In industrial use for non-vacuum e-beam welding today. "
         "Demonstrated at cm-scale apertures. Scaling to pod diameter is the "
         "R&amp;D centerpiece."],
        ["NASA X-59 shockwave tailoring",
         "First flight Oct 28, 2025 (67 min, Palmdale). Flying supersonic test points "
         "as of Apr-May 2026. XVS camera-vision system flight-proven. "
         "Aero-shell pressure-distribution data is being collected now."],
        ["High-g electronics",
         "Guided artillery electronics survive over 10,000 g in service. "
         "SELENE's 100 g cargo mode is conservative by two orders of magnitude."],
        ["Auriga Space",
         "$12.2M raised; AFWERX Phase II SBIR. Earth-based EM launch-assist track "
         "selling hypersonic test runs: the Phase 1 revenue model is proven in market."],
        ["Orbital manufacturing demand",
         "Flawless Photonics: ~12 km of ZBLAN fiber drawn on ISS, Feb-Mar 2024; "
         "1,141 m in one day vs prior 25 m record. Factory customers queuing; "
         "they are waiting on freight prices."],
        ["Lunar mass driver physics",
         "G. O'Neill, NASA Ames / Princeton, 1970s. SJSU study: 25 kg pellets at "
         "2.4 km/s using 8.7 MW polar solar power and ~1 million amps per shot. "
         "Physics settled for half a century."],
        ["SpaceX lunar mass driver",
         "Public roadmap, March 2026: \"cannon-like device using magnetic power.\" "
         "The largest launch company on Earth is building toward the same machine."],
    ],
    [2.0*inch, 4.6*inch]))
E.append(Spacer(1, 8))
E.append(p(
    "<b>KERAUNOS requires zero new physics.</b> The Chimborazo demonstrator validates "
    "the atmosphere subsystems. SELENE validates the vacuum-world kit. Both generate "
    "revenue while proving the hardware. The opportunity is assembly and "
    "commercialization, not invention."
))

# ===== 11. HARD PARTS =====
E.append(KeepTogether(sect("11", "The Hard Parts") + [reminder(
    "A document about a project this large that doesn't name the real "
    "problems is salesmanship, not engineering."
)]))
E.append(b(
    "<b>Plasma window scaling.</b> Demonstrated at centimeter-scale apertures. "
    "Needed at pod diameter. This gets the first R&amp;D dollar before anything else. "
    "If it doesn't scale, the Chimborazo muzzle needs a different solution, "
    "and we need to know that cheaply, at demonstrator scale."
))
E.append(b(
    "<b>The tube cost per kilometer is unknown.</b> The $20-250/kg figure for a "
    "full Earth system lives or dies on that number. Nobody has published a credible "
    "estimate for vacuum-rated superconducting track at scale. "
    "The Chimborazo demonstrator at 10-20 km produces the first real cost data."
))
E.append(b(
    "<b>SELENE's first bill is a rocket bill.</b> The coils, power plant, and "
    "radiators ride to the Moon on somebody else's launcher at today's prices. "
    "The starter track has to be light enough to afford in one or two heavy-lift flights."
))
E.append(b(
    "<b>Catching is harder than throwing.</b> Cislunar catch points exist on paper. "
    "The first pod has to be caught by a tug with a wide capture cone. "
    "Until the first catch happens, the export revenue is theoretical."
))
E.append(b(
    "<b>The treaty question is unsettled.</b> The Outer Space Treaty says nothing "
    "about commercial mass drivers. A kinetic launcher is inherently dual-use. "
    "That ambiguity generates scrutiny on one side and AFWERX funding on the other. "
    "EMALS and GPS both walked this road."
))

# ===== 12. WHAT THIS UNLOCKS =====
E.append(KeepTogether(sect("12", "What KERAUNOS Unlocks") + [
    Paragraph("Orbital manufacturing", S["h2"])
]))
E.append(b(
    "<b>ZBLAN fiber.</b> Microgravity-drawn fluoride glass with up to 100x lower "
    "theoretical signal loss than silica. Flawless Photonics drew <b>~12 km on the "
    "ISS in Feb-Mar 2024</b>, with 1,141 m in a single day (prior record: 25 m). "
    "Factory customers are queueing. They are waiting on freight prices. "
    "KERAUNOS is the freight price."
))
E.append(b(
    "<b>Orbital bioprinting.</b> Hearts and lungs that collapse under their own weight "
    "in 1 g. KERAUNOS's cadence enables daily return pods: orbital bioprinting "
    "becomes a medical logistics business, not a stunt."
))
E.append(b(
    "<b>Debris salvage.</b> Thousands of tonnes of refined aerospace-grade alloys "
    "orbit as junk. At KERAUNOS freight prices, salvage tugs turn a profit."
))
E.append(Paragraph("Geopolitical position", S["h2"]))
E.append(b(
    "<b>The Space Panama Canal.</b> The host nation stops paying for space access "
    "and starts charging the rest of the world. As space sovereignty becomes a "
    "global priority, every nation without this infrastructure becomes a customer."
))
E.append(b(
    "<b>80 tonnes per day is occupation as a logistics fact.</b> Secure the best "
    "orbital slots and lunar water-ice territories before anyone else can "
    "clear the atmosphere. At that cadence, presence is a supply chain, not a flag."
))
E.append(b(
    "<b>The deterrence dividend.</b> A launcher placing 29,000 tonnes per year "
    "into orbit can replenish a damaged constellation in hours, not months."
))
E.append(Paragraph("The energy loop", S["h2"]))
E.append(b(
    "<b>The track earns between launches.</b> The superconducting storage rings "
    "double as grid-scale battery storage: soak surplus solar and wind by day, "
    "sell grid stability services between launch windows. Nothing is idle."
))
E.append(b(
    "<b>Laser debris sweeping.</b> The same power plant that feeds the track drives "
    "ground lasers that nudge small debris off the launch corridor before each exit."
))

doc.build(E, onFirstPage=cover, onLaterPages=later)
print("OK:", OUT)
