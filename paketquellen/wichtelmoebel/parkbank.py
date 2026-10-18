"""
Parkbank – Paket „Wichtelmöbel“.

Eine Lattenbank wie im Stadtpark: zwei Seitenteile im Gusseisen-Look (Beine mit Löwenfüßen, geschwungene
Armlehne mit Schnecke, Ranken unter dem Sitz), dazwischen einzelne Sitz- und Lehnenlatten, die mit ihren
Zapfen durch Schlitze in den Seitenteilen gesteckt werden. Die oberste Lehnenlatte kann einen Text tragen.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import integer, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtelmoebel__lade_parkbank",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.moebel()
Z, K = M.Z, M.K

STILE = [("ranken", "Gusseisen mit Ranken"), ("herz", "mit Herz"), ("schlicht", "schlicht")]

UEBERSETZUNG = {"en": {
    "Parkbank": "Park bench", "Wichtelmöbel": "Elf furniture",
    "Lattenbank wie im Stadtpark: Seitenteile im Gusseisen-Look mit Armlehne und Löwenfüßen, Sitz- und Lehnenlatten zum Durchstecken.":
        "Slatted bench like in a city park: cast-iron style side frames with armrest and lion feet, seat and backrest slats that plug through.",
    "Länge": "Length", "Sitzhöhe": "Seat height", "Sitzlatten": "Seat slats", "Lehnenlatten": "Backrest slats",
    "Seitenteile": "Side frames", "Text auf der Lehne": "Text on the backrest", "Gusseisen mit Ranken": "cast iron with scrolls",
    "mit Herz": "with heart", "schlicht": "plain",
    "Die Latten mit ihren Zapfen durch die Schlitze beider Seitenteile stecken – erst die Sitzlatten, dann die Lehne.":
        "Push the slats with their tabs through the slots of both side frames – first the seat slats, then the backrest.",
    "Sitzhöhe angehoben – bei dieser Materialstärke brauchen die Holme Platz für die Schlitze.":
        "Seat height raised – with this material thickness the frames need room for the slots.",
    "Tipp: Seitenteile schwarz oder dunkelgrün anmalen, die Latten holzfarben lassen.":
        "Tip: paint the side frames black or dark green and leave the slats wood-coloured.",
}}

INFO = dict(
    label="Parkbank", group="Wichtelmöbel",
    desc="Lattenbank wie im Stadtpark: Seitenteile im Gusseisen-Look mit Armlehne und Löwenfüßen, Sitz- und "
         "Lehnenlatten zum Durchstecken.",
    params=[
        num("laenge", "Länge", 80, 45, 220),
        num("sitzhoehe", "Sitzhöhe", 28, 18, 80),
        integer("sitzlatten", "Sitzlatten", 4, 2, 6),
        integer("lehnenlatten", "Lehnenlatten", 3, 1, 5),
        sel("stil", "Seitenteile", STILE, "ranken"),
        txt("text", "Text auf der Lehne", "", "z. B. „Wichtelpause“ – kommt auf die oberste Latte", maxlen=24,
            symbols=True),
    ],
)


def _vec(a, b):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return (b[0] - a[0]) / L, (b[1] - a[1]) / L, L


def build(cfg, name="parkbank", laenge=80.0, sitzhoehe=28.0, sitzlatten=4, lehnenlatten=3, stil="ranken", text=""):
    T = cfg.T
    w = Z.wmin(cfg)
    Lb, hs = cfg.s(laenge), cfg.s(sitzhoehe)
    ns, nl = int(sitzlatten), int(lehnenlatten)
    tw = max(cfg.min_tab_width + 0.6, min(cfg.tab_factor * T, T + 2.0))
    b = max(tw + 2.6, T * 2.0)                                # Lattenbreite
    gap = max(1.2, b * 0.3)
    rand = max(2.0, T * 0.8)
    rw = T + 2 * rand + 0.6                                   # Stärke der Holme (Schlitz + Rand)
    notes = []
    if hs < 2.5 * rw + 6:
        hs = 2.5 * rw + 6
        notes.append("Sitzhöhe angehoben – bei dieser Materialstärke brauchen die Holme Platz für die Schlitze.")
    asm = Assembly(name, params=dict(laenge=Lb, sitzhoehe=hs, stil=stil))
    tb = 0.0
    if text.strip():
        tb = max(b, min(14.0, hs * 0.4))                      # breitere oberste Latte für den Text
    # Sitzfläche: von hinten (sh) nach vorne (sv), leicht nach hinten geneigt
    tiefe = ns * b + (ns - 1) * gap + 2 * rand + 2
    sv = (tiefe + rw * 0.6, hs)
    sh = (rw * 0.6 + 1.0, hs - tiefe * 0.06)
    ux, uy, Ls = _vec(sh, sv)
    # Lehne: vom hinteren Sitzende schräg nach hinten oben
    lehne_h = nl * b + (nl - 1) * gap + tb + (gap if tb else 0) + 2 * rand + 2
    ang = math.radians(100)
    lu = (sh[0] - 0.5, sh[1] + rw * 0.4)
    lo = (lu[0] + math.cos(ang) * lehne_h, lu[1] + math.sin(ang) * lehne_h)
    vx, vy, Ll = _vec(lu, lo)
    sw = rw                                                   # Strichstärke der Holme
    # --- Seitenteil (x = Tiefe, y = Höhe) ---
    fig = Z.Figur()
    fx_v, fx_h = sv[0] - rw * 0.4, sh[0] + rw * 0.2          # Fußpunkte vorne/hinten
    fig.line([(fx_v + rw * 0.3, 0), (fx_v + rw * 0.1, hs * 0.5), (sv[0] - rw * 0.3, hs)], sw * 0.95, sw)
    fig.line([(fx_h - rw * 0.4, 0), (fx_h, hs * 0.5), (sh[0], sh[1])], sw * 0.95, sw)
    fig.line([(sh[0] - ux * rw * 0.3, sh[1] - uy * rw * 0.3), (sv[0] + ux * rw * 0.3, sv[1] + uy * rw * 0.3)], sw, sw, "rund")
    fig.line([(lu[0] - vx * rw * 0.3, lu[1] - vy * rw * 0.3), (lo[0] + vx * rw * 0.2, lo[1] + vy * rw * 0.2)], sw, sw * 0.9,
             "rund")
    for x in (fx_v + rw * 0.3, fx_h - rw * 0.4):              # Löwenfüße
        fig.add(K.ellipse(x + rw * 0.25, rw * 0.32, rw * 0.85, rw * 0.36, 0, 24))
        for k in (-1, 0, 1):
            fig.add(K.circle(x + rw * 0.25 + k * rw * 0.42 + rw * 0.35, rw * 0.22, rw * 0.24, 14))
    # Armlehne: von der Lehne nach vorne, vorne mit Schnecke nach unten
    ya = hs + max(rw * 1.6, lehne_h * 0.45)
    pa = (lu[0] + vx * (ya - lu[1]) / vy, ya)
    ende = (sv[0] + rw * 0.2, ya - rw * 0.2)
    fig.line(K.bez3(pa, (pa[0] + (ende[0] - pa[0]) * 0.4, ya + rw * 0.4), (ende[0] - rw, ya + rw * 0.3), ende, 16),
             sw * 0.8, sw * 0.75)
    rs = max(rw * 0.9, (ya - hs) * 0.32)
    spi = Z.spirale(ende[0] - rs * 0.1, ende[1] - rs, rs * 0.25, rs, 0.85, math.pi / 2, -1)
    fig.line(spi, max(1.6 * w, sw * 0.42), max(1.4 * w, sw * 0.32))
    fig.line([(ende[0] - rs * 0.1, ende[1] - rs * 2), (sv[0] - rw * 0.1, hs + rw * 0.3)], max(1.6 * w, sw * 0.42))
    # Verzierung unter dem Sitz
    mx, my = (fx_v + fx_h) / 2 + rw * 0.1, hs * 0.48
    if stil == "ranken":
        r = min((fx_v - fx_h) * 0.22, hs * 0.18)
        if r > 3 * w:
            for sg in (1, -1):
                sp = Z.spirale(mx + sg * r * 1.05, my, r * 0.2, r, 1.0, math.pi if sg > 0 else 0.0, sg)
                fig.line(sp, max(1.5 * w, rw * 0.3), max(1.3 * w, rw * 0.22))
            fig.line([(mx - r * 2.1, my - r), (mx + r * 2.1, my - r)], max(1.5 * w, rw * 0.3))
            fig.line([(mx, my - r), (mx, sh[1] + (sv[1] - sh[1]) * 0.5 - rw * 0.3)], max(1.5 * w, rw * 0.3))
            fig.line([(fx_h + rw * 0.2, my - r), (mx - r * 2.1, my - r)], max(1.5 * w, rw * 0.3))
            fig.line([(mx + r * 2.1, my - r), (fx_v, my - r)], max(1.5 * w, rw * 0.3))
    elif stil == "herz":
        g = min((fx_v - fx_h) * 0.6, hs * 0.5)
        fig.add(Z.herz(mx, my, g))
        fig.cut(Z.herz(mx, my, g - 2 * max(1.6 * w, rw * 0.35)))
        fig.line([(fx_h + rw * 0.2, my - g * 0.1), (fx_v, my - g * 0.1)], max(1.5 * w, rw * 0.3))
    else:
        fig.line([(fx_h, hs * 0.3), (fx_v + rw * 0.1, hs * 0.3)], max(1.5 * w, rw * 0.35))
    # Schlitze: Sitzlatten entlang der Sitzlinie, Lehnenlatten entlang der Lehne
    slots = []
    s = rand + 1 + b / 2
    for i in range(ns):
        cx, cy = sh[0] + ux * s, sh[1] + uy * s
        slots.append((f"sitz{i}", cx, cy, tw, math.atan2(uy, ux), 10 + i))
        s += b + gap
    s = rand + 1 + rw * 0.4
    for i in range(nl):
        bi = tb if (tb and i == nl - 1) else b
        cx, cy = lu[0] + vx * (s + bi / 2), lu[1] + vy * (s + bi / 2)
        slots.append((f"lehne{i}", cx, cy, tw, math.atan2(vy, vx), 30 + i))
        s += bi + gap
    solid = [Z.schlitz_polster(cx, cy, L, T, rand, a) for _, cx, cy, L, a, _ in slots]
    seiten = []
    for k, seite in enumerate(("links", "rechts")):
        part = Z.figur_teil(cfg, f"seite_{seite}", fig, notes, solid=solid, unten_flach=True)
        for fid, cx, cy, L, a, pos in slots:
            Z.schlitz(part, fid, cx, cy, L, T, pos + 100 * k, a)
        asm.parts.append(part)
        seiten.append(part)
    # --- Latten (zwischen den Seitenteilen: Länge Lb, Zapfen durch beide) ---
    Li = Lb - 2 * T
    for i in range(ns):
        lt = Z.brett(f"sitzlatte{i + 1}", Li, b, T, links=[(b / 2, tw, "links", 10 + i)], rechts=[(b / 2, tw, "rechts", 110 + i)])
        Z.gravur(lt, _maserung(Li, b, 60 + i), rand=0.6)
        asm.parts.append(lt)
        asm.connect(f"sitzlatte{i + 1}:links", f"seite_links:sitz{i}")
        asm.connect(f"sitzlatte{i + 1}:rechts", f"seite_rechts:sitz{i}")
    for i in range(nl):
        bi = tb if (tb and i == nl - 1) else b
        lt = Z.brett(f"lehnenlatte{i + 1}", Li, bi, T, links=[(bi / 2, tw, "links", 30 + i)],
                     rechts=[(bi / 2, tw, "rechts", 130 + i)])
        if bi == tb and text.strip():
            M.text_gravur(lt, text, Li / 2, bi / 2, Li * 0.8, bi * 0.62, 9.0)
        else:
            Z.gravur(lt, _maserung(Li, bi, 80 + i), rand=0.6)
        asm.parts.append(lt)
        asm.connect(f"lehnenlatte{i + 1}:links", f"seite_links:lehne{i}")
        asm.connect(f"lehnenlatte{i + 1}:rechts", f"seite_rechts:lehne{i}")
    asm.notes.append("Die Latten mit ihren Zapfen durch die Schlitze beider Seitenteile stecken – erst die "
                     "Sitzlatten, dann die Lehne.")
    asm.notes.append("Tipp: Seitenteile schwarz oder dunkelgrün anmalen, die Latten holzfarben lassen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm


def _maserung(L, b, seed):
    r = K.rng(seed, "latte")
    lin = []
    for j in range(2 if b > 5 else 1):
        y = b * (0.35 + 0.3 * j) + K.jitter(r, b * 0.06)
        x0, x1 = L * r.random() * 0.2 + 1.5, L * (0.8 + r.random() * 0.2) - 1.5
        pts = [(x0 + (x1 - x0) * k / 8, y + math.sin(k * 0.9 + seed) * b * 0.05) for k in range(9)]
        lin.append((pts, False))
    return lin
