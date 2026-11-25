"""
Herbstkranz – Kranz aus Ahorn- und Eichenlaub mit Eicheln und Beeren, fein graviert.

Die Blätter liegen überlappend wie in einem gebundenen Kranz; jedes trägt seine Adern als Gravur, und wo ein
Blatt ein anderes verdeckt, endet dessen Gravur sauber an der Kante. Als offener Kranz mit Schleife (der Umriss
folgt den Blättern) oder als Medaille: Blätter als Spitze im ausgeschnittenen Ring, in der Mitte ein Name.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly
from pakete import flag, integer, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_jahreszeiten_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


J = _sub("_jz")
K, E, P, TAU = J.K, J.E, J.P, J.TAU

FORMEN = [("kranz", "offener Kranz mit Schleife"), ("medaille", "Medaille mit Namen")]
LAUB = [("gemischt", "Ahorn, Eiche, Eicheln und Beeren"), ("ahorn", "Ahornlaub"), ("eiche", "Eichenlaub mit Eicheln")]

INFO = dict(
    label="Herbstkranz",
    group="Jahreszeiten",
    desc="Kranz aus überlappendem Ahorn- und Eichenlaub mit Eicheln und Beeren, jedes Blatt mit gravierten Adern – "
         "als offener Kranz mit Schleife oder als Medaille mit Namen in der Mitte.",
    params=[
        sel("form", "Form", FORMEN, "kranz"),
        sel("laub", "Laub", LAUB, "gemischt"),
        txt("text", "Text", "Erntedank", maxlen=20, help="leer = ohne", when={"form": ["medaille"]}),
        integer("startwert", "Startwert", 1, 1, 9999, help="ändert die Anordnung der Blätter"),
        num("groesse", "Größe", 110, 70, 250, help="Durchmesser ohne Öse"),
        sel("feinheit", "Feinheit", J.FEINHEIT, "mittel"),
        flag("oese", "Öse zum Aufhängen", True),
        integer("anzahl", "Anzahl", 1, 1, 8),
    ],
)

UEBERSETZUNG = {"en": dict(J.FEINHEIT_EN, **{
    "Herbstkranz": "Autumn wreath",
    "Kranz aus überlappendem Ahorn- und Eichenlaub mit Eicheln und Beeren, jedes Blatt mit gravierten Adern – "
    "als offener Kranz mit Schleife oder als Medaille mit Namen in der Mitte.":
        "Wreath of overlapping maple and oak leaves with acorns and berries, every leaf with engraved veins – as an "
        "open wreath with a bow or as a medal with a name in the centre.",
    "Form": "Shape", "offener Kranz mit Schleife": "open wreath with bow", "Medaille mit Namen": "medal with name",
    "Laub": "Leaves", "Ahorn, Eiche, Eicheln und Beeren": "maple, oak, acorns and berries", "Ahornlaub": "maple leaves",
    "Eichenlaub mit Eicheln": "oak leaves with acorns", "Startwert": "Seed",
    "ändert die Anordnung der Blätter": "changes the arrangement of the leaves",
    "Durchmesser ohne Öse": "diameter without loop",
    "Aufhängen: Band oder Kordel durch die Öse ziehen.": "To hang: thread a ribbon or cord through the loop.",
})}


# --------------------------------------------------------------------------------------------------
# Blätter und Früchte: Einheitsformen, Stiel bei (0, 0), Spitze nach oben
# --------------------------------------------------------------------------------------------------

def _ahorn(L: float):
    """Ahornblatt der Länge L: fünf gezähnte Lappen, Adern zu jeder Lappenspitze."""
    lappen = [(0.0, 1.0), (50.0, 0.86), (100.0, 0.56)]
    mitte = (0.0, 0.3 * L)
    pts = []
    rechts = []
    for i, (wi, ln) in enumerate(lappen):
        a = math.radians(wi)
        tip = (mitte[0] + math.sin(a) * ln * L * 0.72, mitte[1] + math.cos(a) * ln * L * 0.72)
        rechts.append(tip)
    # rechte Hälfte von der Spitze nach unten: Spitze, Zähne, Bucht, nächster Lappen …
    def zahnkante(p, q, n, tiefe):
        out = []
        for k in range(1, n + 1):
            f = k / (n + 1)
            x, y = p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f
            nx, ny = (q[1] - p[1]), -(q[0] - p[0])
            nl = math.hypot(nx, ny) or 1
            out.append((x + nx / nl * tiefe * (1 if k % 2 else -0.3), y + ny / nl * tiefe * (1 if k % 2 else -0.3)))
        return out
    pts.append(rechts[0])
    for i in range(len(rechts)):
        tip = rechts[i]
        a_tip = math.radians(lappen[i][0])
        if i + 1 < len(rechts):
            a_b = math.radians((lappen[i][0] + lappen[i + 1][0]) / 2)
            bucht = (mitte[0] + math.sin(a_b) * L * 0.3, mitte[1] + math.cos(a_b) * L * 0.3)
        else:
            bucht = (L * 0.1, 0.06 * L)
        schulter = (tip[0] * 0.62 + bucht[0] * 0.38 + math.cos(a_tip) * L * 0.07,
                    tip[1] * 0.62 + bucht[1] * 0.38 - math.sin(a_tip) * L * 0.07)
        pts += zahnkante(tip, schulter, 3, L * 0.025)
        pts.append(schulter)
        pts += [bucht]
        if i + 1 < len(rechts):
            nt = rechts[i + 1]
            a_n = math.radians(lappen[i + 1][0])
            sch2 = (nt[0] * 0.62 + bucht[0] * 0.38 - math.cos(a_n) * L * 0.07,
                    nt[1] * 0.62 + bucht[1] * 0.38 + math.sin(a_n) * L * 0.07)
            pts.append(sch2)
            pts += zahnkante(sch2, nt, 3, L * 0.025)
            pts.append(nt)
    rechts_h = pts + [(0.0, 0.04 * L)]
    voll = rechts_h + [(-x, y) for x, y in reversed(rechts_h[1:-1])]
    um = J.oriented(voll, True)
    lin = [(um, True), ([(0, -0.12 * L), (0, 0.04 * L)], False)]
    for wi, ln in lappen:
        for sg in ((1,) if wi == 0 else (1, -1)):
            a = math.radians(wi) * sg
            tip = (mitte[0] + math.sin(a) * ln * L * 0.66, mitte[1] + math.cos(a) * ln * L * 0.66)
            start = (0.0, 0.04 * L) if wi else (0.0, 0.04 * L)
            lin.append((K.bez(start, ((start[0] + tip[0]) / 2 * 0.9, (start[1] + tip[1]) / 2 + 0.02 * L), tip, 10), False))
            for f in (0.4, 0.6, 0.78):                     # Seitenadern
                q = (start[0] + (tip[0] - start[0]) * f, start[1] + (tip[1] - start[1]) * f)
                d = math.atan2(tip[0] - start[0], tip[1] - start[1])
                for s2 in (1, -1):
                    e = P(ln * L * 0.12 * (1.1 - f), d + s2 * 0.75, q)
                    lin.append(([q, e], False))
    return um, lin


def _eiche(L: float):
    """Eichenblatt der Länge L: gelappter Rand (je Seite fünf Lappen), Fiederadern."""
    n = 5
    rechts = []
    m = 120
    for k in range(m + 1):
        s = k / m
        grund = 0.22 * L * math.sin(math.pi * min(1.0, s * 1.05)) ** 0.8 * (1 - 0.25 * s)
        lap = 0.4 + 0.6 * abs(math.sin(math.pi * n * (s - 0.04)))
        rechts.append((grund * lap + 0.012 * L, L * s))
    rechts[-1] = (0.0, L)
    um = J.oriented([(0.0, 0.0)] + rechts + [(-x, y) for x, y in reversed(rechts[:-1])], True)
    lin = [(um, True), ([(0, -0.1 * L), (0, 0.94 * L)], False)]
    for j in range(n):
        s = (j + 0.55) / n * 0.96 + 0.04
        if s > 0.95:
            continue
        y0 = L * (s - 0.08)
        idx = min(m, int(s * m))
        x1 = rechts[idx][0] * 0.82
        for sg in (1, -1):
            lin.append((K.bez((0, y0), (sg * x1 * 0.5, y0 + 0.02 * L), (sg * x1, L * s), 8), False))
    return um, lin


def _eichel(L: float):
    """Eichel der Länge L: Hütchen mit Gitterschraffur, Nuss mit Glanzlinie und Spitze, Stielchen."""
    hb = 0.36 * L
    kappe_h = 0.36 * L
    nuss = K.spline([(0, 0.0), (0.26 * L, 0.18 * L), (0.3 * L, 0.5 * L), (0.24 * L, 0.7 * L), (-0.24 * L, 0.7 * L),
                     (-0.3 * L, 0.5 * L), (-0.26 * L, 0.18 * L)], closed=True, n=8)
    kappe = K.spline([(0.0, 0.62 * L), (hb, 0.62 * L), (hb * 1.02, 0.62 * L + kappe_h * 0.6),
                      (0.0, 0.62 * L + kappe_h), (-hb * 1.02, 0.62 * L + kappe_h * 0.6), (-hb, 0.62 * L)],
                     closed=True, n=8)
    um = J.huelle(nuss + kappe + [(0, 1.0 * L), (0.03 * L, 1.12 * L)])
    lin = [(nuss, True), (kappe, True)]
    lin += J.nur_in(J.schraffur(kappe, max(0.5, 0.07 * L), 0.6) + J.schraffur(kappe, max(0.5, 0.07 * L), -0.6),
                    J.versetzt(kappe, -0.25))
    lin.append((K.bez((0.14 * L, 0.18 * L), (0.2 * L, 0.35 * L), (0.18 * L, 0.52 * L), 8), False))
    lin.append(([(0, -0.02 * L), (0, 0.04 * L)], False))
    lin.append((K.bez((0, 0.62 * L + kappe_h), (0.02 * L, 1.06 * L), (0.07 * L, 1.14 * L), 6), False))
    return J.oriented(um, True), lin


def _beeren(r: float):
    """Kleine Traube aus fünf Beeren (Radius r) mit Kelchsternchen."""
    stellen = [(0, 0), (1.8, 0.7), (-1.7, 0.8), (0.1, 1.9), (0.9, -1.6)]
    polys, lin = [], []
    for dx, dy in stellen:
        c = (dx * r, dy * r)
        kr = J.kreis(c[0], c[1], r, 18)
        polys += kr
        lin += J.beere(c[0], c[1], r)
        for k in range(5):
            lin.append(([c, P(r * 0.3, TAU * k / 5 + 0.3, c)], False))
    return J.oriented(J.huelle(polys), True), lin


def _schleife(b: float):
    """Schleife (Breite b, Mitte 0/0): massive Fläche und gravierte Falten."""
    teile = []
    lin = []
    for s in (-1, 1):
        loop = K.chain(K.bez3((0, 0), (s * b * 0.25, b * 0.34), (s * b * 0.54, b * 0.32), (s * b * 0.5, b * 0.02), 18),
                       K.bez3((s * b * 0.5, b * 0.02), (s * b * 0.48, -b * 0.2), (s * b * 0.2, -b * 0.1), (0, 0), 18)[1:-1])
        teile.append(J.oriented(loop, True))
        lin.append((loop, True))
        lin.append((K.bez3((s * b * 0.08, b * 0.04), (s * b * 0.25, b * 0.22), (s * b * 0.4, b * 0.2), (s * b * 0.42, b * 0.04), 12), False))
        lin.append((K.bez((s * b * 0.1, -b * 0.01), (s * b * 0.3, b * 0.05), (s * b * 0.44, -b * 0.04), 10), False))
        tail = [(s * b * 0.04, -b * 0.02), (s * b * 0.32, -b * 0.46), (s * b * 0.24, -b * 0.4), (s * b * 0.18, -b * 0.5),
                (-s * b * 0.05, -b * 0.06)]
        teile.append(J.oriented(tail, True))
        lin.append((tail, True))
        lin.append(([(s * b * 0.03, -b * 0.06), (s * b * 0.2, -b * 0.4)], False))
    knoten = K.ellipse(0, 0, b * 0.1, b * 0.12)
    teile.append(knoten)
    lin.append((knoten, True))
    lin.append(([(-b * 0.05, -b * 0.08), (-b * 0.02, b * 0.09)], False))
    lin.append(([(b * 0.05, -b * 0.08), (b * 0.02, b * 0.09)], False))
    return teile, lin


# --------------------------------------------------------------------------------------------------
# Kranz
# --------------------------------------------------------------------------------------------------

def _laub(rm: float, band: float, laub: str, seed: int, luecke_unten: float = 0.0):
    """Blätter und Früchte rund um den Kreis rm (Breite band), unten → oben gestapelt: [(Umriss, Linien)]."""
    r = K.rng(seed, "herbst", laub)
    folge = dict(gemischt=["ahorn", "eiche", "eichel", "ahorn", "beeren", "eiche", "eichel"],
                 ahorn=["ahorn", "ahorn", "beeren", "ahorn"],
                 eiche=["eiche", "eichel", "eiche", "eiche", "eichel"])[laub]
    stapel = []
    n = max(14, int(TAU * rm / (band * 0.3)))
    for k in range(n):
        t = TAU * (k + r.uniform(-0.15, 0.15)) / n + TAU * 0.25 / n
        if luecke_unten and abs(((t - math.pi + math.pi) % TAU) - math.pi) < luecke_unten:
            continue
        art = folge[(k + seed) % len(folge)]
        aus = 1 if k % 2 == 0 else -1
        c = P(rm + aus * band * r.uniform(0.0, 0.06), t)
        neig = t + math.radians(90 - aus * r.uniform(28, 50))       # im Uhrzeigersinn, abwechselnd nach außen/innen
        if art == "ahorn":
            stapel.append(J.platziert(_ahorn(band * r.uniform(0.7, 0.8)), c[0], c[1], neig))
        elif art == "eiche":
            stapel.append(J.platziert(_eiche(band * r.uniform(0.78, 0.9)), c[0], c[1], neig))
        elif art == "eichel":
            for d in (-0.25, 0.25):
                stapel.append(J.platziert(_eichel(band * 0.34), c[0], c[1], neig + d + math.pi * 0.8))
        else:
            stapel.append(J.platziert(_beeren(band * 0.065), c[0], c[1], neig))
    return stapel


def _kranzteil(cfg, name: str, S: float, form: str, laub: str, text: str, seed: int, feinheit: str, oese: bool,
               notes: List[str]):
    R = S / 2
    w = J.steg_breite(cfg, feinheit)
    fig = K.Figur()
    lin: List = []
    if form == "kranz":
        band = 0.42 * R
        rm = R - band * 0.55
        stapel = _laub(rm, band, laub, seed, luecke_unten=0.0)
        ring = [P(rm, TAU * k / 360) for k in range(361)]
        fig.add(K.stroke(ring, max(2.2 * w, 0.06 * R), max(2.2 * w, 0.06 * R), "rund"))  # verborgener Tragring
        for um, _ in stapel:
            fig.add(um)
        b = 0.5 * R
        teile, slin = _schleife(b)
        unten = (0.0, -rm - band * 0.08)
        for p in teile:
            fig.add([(x + unten[0], y + unten[1]) for x, y in p])
        stapel.append((J.huelle([(x + unten[0], y + unten[1]) for p in teile for x, y in p]),
                       [([(x + unten[0], y + unten[1]) for x, y in p], c) for p, c in slin]))
        lin += J.blaetter_gravur(stapel)
        oese_loch = None
        if oese:
            c, ro, ri = J.oese_mass(rm + band * 0.36, R, w)
            fig.add(J.kreis(c[0], c[1], ro, 48))
            fig.add(K.stroke([(0, rm), c], 2.2 * w, 2.2 * w))
            oese_loch = J.kreis(c[0], c[1], ri, 40)
        x0, y0, x1, y1 = fig.bbox()
        px = max(0.055, min(0.08, max(x1 - x0, y1 - y0) / 1800.0))
        lw = E.Leinwand((x0 - 2, y0 - 2, x1 + 2, y1 + 2), px)
        mat = lw.figur(fig)
        if oese_loch:
            mat = E._andnot(mat, lw.flaechen([oese_loch]))
        part = J.teil(cfg, name, lw, mat, notes)
        part = J.scharf(cfg, part, [oese_loch] if oese_loch else [])
        J.gravieren(part, lw, lin)
        return part
    # Medaille: Rand, ausgeschnittener Ring mit Laub als Spitze, Mitte mit Namen
    rand = J.bogenrand(R, 36, max(1.2, 0.025 * R))
    umriss, oese_loch = J.umriss_mit_oese(fig, rand, R - 0.3, R, w, oese)
    r1 = R - max(3.2 * w, 0.1 * R)
    r0 = 0.45 * R
    rm, band = (r0 + r1) / 2, r1 - r0
    fig.cut(J.kreis(0, 0, r1, 0))
    fig.add(J.kreis(0, 0, r0, 0))
    ring = [P(rm, TAU * k / 360) for k in range(361)]
    fig.add(K.stroke(ring, w * 1.2, w * 1.2, "rund"))
    stapel = _laub(rm, band * 1.05, laub, seed)
    for um, _ in stapel:
        fig.add(um)
    lin += J.verdecken(J.nur_in(J.blaetter_gravur(stapel), J.kreis(0, 0, r1 - 0.2, 0)), [J.kreis(0, 0, r0 + 0.2, 0)])
    lin.append((J.zu(J.versetzt(rand, -max(0.8, 0.016 * R))), False))
    lin += J.perlenkreis((R + r1) / 2 - 0.2, max(0.3, 0.006 * R), max(1.1, 0.024 * R))
    lin += J.doppelkreis(r0 - max(1.0, 0.02 * R), max(0.5, 0.01 * R))
    ri = r0 - max(2.4, 0.045 * R)
    if text:
        lin += J.text(text, 0, 0.05 * ri, 1.7 * ri, 0.7 * ri, 0.3 * ri, 1.9)
    for sg in (1, -1):
        e = J.platziert(_eichel(ri * 0.36), sg * ri * 0.12, -ri * 0.52, sg * 0.45 + math.pi)
        lin += [(p, c) for p, c in e[1]]
    e = J.platziert(_ahorn(ri * 0.34), 0, ri * 0.52, 0.0)
    lin += e[1]
    part, _ = J.bauen(cfg, name, fig, lin, notes, oese_loch, umriss=umriss)
    return part


def build(cfg, name: str = "herbstkranz", form: str = "kranz", laub: str = "gemischt", text: str = "Erntedank",
          startwert: int = 1, groesse: float = 110.0, feinheit: str = "mittel", oese: bool = True, anzahl: int = 1):
    J.auswahl(form, FORMEN, "Form")
    J.auswahl(laub, LAUB, "Laub")
    J.auswahl(feinheit, J.FEINHEIT, "Feinheit")
    text = J.text_pruefen(text) if form == "medaille" else ""
    S = cfg.s(groesse)
    if S < 65:
        raise ValueError("Der Kranz ist zu klein für so feine Arbeit – mindestens 70 mm")
    asm = Assembly(name, params=dict(form=form, laub=laub, startwert=startwert, groesse=S, feinheit=feinheit))
    notes: List[str] = []
    for i in range(max(1, int(anzahl))):
        tag = name if anzahl <= 1 else f"{name}_{i + 1}"
        asm.parts.append(_kranzteil(cfg, tag, S, form, laub, text, int(startwert) + i, feinheit, oese, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    if oese:
        asm.notes.append("Aufhängen: Band oder Kordel durch die Öse ziehen.")
    asm.notes.append("Tipp: In Kirsche oder Nussbaum wirkt der Herbstkranz besonders warm; die Adern mit wenig Leistung "
                     "gravieren, danach dünn ölen.")
    return asm
