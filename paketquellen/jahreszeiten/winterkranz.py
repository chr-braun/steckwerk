"""
Winterkranz-Medaille – runde Medaille im Spitzenschnitt mit fein graviertem Winterkranz.

Außen ein Bogenrand mit ausgeschnittenen Tropfen und Perlen, darin ein Kranz aus einzeln gravierten
Tannennadeln mit Beeren und Stechpalme (oder ein Stechpalmenkranz), ein Fries aus ausgeschnittenen
Bogenfenstern und in der Mitte ein Eiskristall, ein Zierstern oder ein Name.
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
K, P, TAU = J.K, J.P, J.TAU

MITTE = [("kristall", "Eiskristall"), ("stern", "Zierstern"), ("text", "Name oder Gruß")]
KRANZ = [("tanne", "Tannengrün mit Beeren"), ("stechpalme", "Stechpalme mit Beeren"),
         ("zapfen", "Tannengrün mit Zapfen")]
BOEGEN = [("16", "16 Bögen"), ("24", "24 Bögen"), ("32", "32 Bögen")]

INFO = dict(
    label="Winterkranz-Medaille",
    group="Jahreszeiten",
    desc="Runde Medaille im Spitzenschnitt: Bogenrand mit Tropfen, fein gravierter Winterkranz aus Tannengrün, "
         "Beeren und Stechpalme, Fries aus Bogenfenstern und in der Mitte Eiskristall, Zierstern oder Name.",
    params=[
        sel("mitte", "Mitte", MITTE, "kristall"),
        txt("text", "Text", "Frohe Weihnacht", maxlen=24, help="leer = ohne", when={"mitte": ["text"]}),
        sel("kranz", "Kranz", KRANZ, "tanne"),
        sel("boegen", "Bogenrand", BOEGEN, "24"),
        num("groesse", "Größe", 100, 60, 250, help="Durchmesser ohne Öse"),
        sel("feinheit", "Feinheit", J.FEINHEIT, "mittel"),
        flag("oese", "Öse zum Aufhängen", True),
        integer("anzahl", "Anzahl", 1, 1, 8),
    ],
)

UEBERSETZUNG = {"en": dict(J.FEINHEIT_EN, **{
    "Winterkranz-Medaille": "Winter wreath medal",
    "Runde Medaille im Spitzenschnitt: Bogenrand mit Tropfen, fein gravierter Winterkranz aus Tannengrün, "
    "Beeren und Stechpalme, Fries aus Bogenfenstern und in der Mitte Eiskristall, Zierstern oder Name.":
        "Round lace-cut medal: scalloped rim with drops, finely engraved winter wreath of fir, berries and holly, "
        "a frieze of arched windows and an ice crystal, ornamental star or name in the centre.",
    "Mitte": "Centre", "Eiskristall": "Ice crystal", "Zierstern": "Ornamental star", "Name oder Gruß": "Name or greeting",
    "Kranz": "Wreath", "Tannengrün mit Beeren": "Fir with berries", "Stechpalme mit Beeren": "Holly with berries",
    "Tannengrün mit Zapfen": "Fir with cones", "Bogenrand": "Scalloped rim", "16 Bögen": "16 scallops",
    "24 Bögen": "24 scallops", "32 Bögen": "32 scallops", "Durchmesser ohne Öse": "diameter without loop",
    "Aufhängen: Band oder Kordel durch die Öse ziehen.": "To hang: thread a ribbon or cord through the loop.",
})}


# --------------------------------------------------------------------------------------------------
# Kranz
# --------------------------------------------------------------------------------------------------

def _zapfen(L: float):
    """Kleiner Tannenzapfen von (0, 0) nach unten (0, −L): Umriss und Schuppen."""
    b = 0.46 * L
    um = J.spitzoval(L, b, 20, 0.8)
    um = [(x, -y) for x, y in um]
    lin = [(um, True)]
    reihen = 5
    for i in range(reihen):
        y = -L * (0.16 + 0.74 * i / reihen)
        s = (i + 0.5) / reihen
        w = b / 2 * math.sin(math.pi * min(0.95, 0.12 + s)) * 0.92
        n = 3 if i % 2 == 0 else 2
        for k in range(n):
            x0 = -w + 2 * w * (k + (0.5 if i % 2 else 0.0)) / max(1, n - (0 if i % 2 else 1))
            x0 = max(-w, min(w, x0))
            sw = w / max(1.5, n - 0.5)
            lin.append((K.bez((x0 - sw, y), (x0, y - L * 0.16), (x0 + sw, y), 8), False))
    lin.append(([(0, 0), (0, L * 0.12)], False))
    return J.oriented(um, True), lin


def _zweig(r0: float, r1: float, t0: float, t1: float, nadel: float, abstand: float, winkel: float, seed: int = 0):
    """Ein Tannenzweig im Uhrzeigersinn von (r0, t0) nach (r1, t1): (Hüllfläche, Gravurlinien)."""
    tm = (t0 + t1) / 2
    pfad = K.bez3(P(r0, t0), P(r0 + (r1 - r0) * 0.25, t0 + (t1 - t0) * 0.33),
                  P(r0 + (r1 - r0) * 0.8, t0 + (t1 - t0) * 0.66), P(r1, t1), 16)
    lin = J.nadelzweig(pfad, nadel, abstand, winkel, seed)
    breit = 2 * nadel * math.sin(math.radians(winkel)) * 0.92
    huelle = K.stroke(pfad, breit, breit * 0.45, "rund")
    return J.oriented(huelle, True), lin


def _kranz(R0: float, R1: float, art: str, n_deko: int):
    """Gravur des Kranzes zwischen R0 (innen) und R1 (außen): drei Lagen Tannenzweige, die sich
    gegenseitig verdecken, darauf Stechpalme, Beeren oder Zapfen."""
    rm = (R0 + R1) / 2
    band = R1 - R0
    n = max(14, int(round(TAU * rm / (0.5 * band + 4))))
    nadel = band * (0.19 if art != "stechpalme" else 0.15)
    abstand = max(0.5, band * 0.04)
    stapel = []
    lagen = ((-0.30, 0.10, 0.0, 0.92), (0.30, -0.10, 0.33, 0.92), (-0.04, 0.06, 0.66, 1.0))
    for k in range(n):
        for dr0, dr1, ph, f in lagen:
            t0 = TAU * (k + ph) / n
            t1 = t0 + TAU / n * 1.8
            r0 = rm + dr0 * band
            r1 = rm + dr1 * band
            stapel.append(_zweig(r0, r1, t0, t1, nadel * f, abstand, 34 + 8 * f, k * 3 + int(ph * 3)))
    # Schmuck obenauf
    deko = []
    for k in range(n_deko):
        t = TAU * (k + 0.5) / n_deko
        if art in ("tanne", "stechpalme"):
            L = band * (0.6 if art == "tanne" else 0.66)
            for dt, sg in ((-0.13, -1), (0.13, 1)):
                c = P(rm, t + dt * band / rm)
                deko.append(J.platziert(J.stechpalme(L, L * 0.5), c[0], c[1], t + sg * math.radians(72)))
            if art == "stechpalme":
                for dt in (-0.36, 0.36):
                    a = t + dt * TAU / n_deko
                    c = P(rm, a)
                    deko.append(J.platziert(J.stechpalme(L * 0.85, L * 0.42), c[0], c[1],
                                            a + math.radians(100 if dt > 0 else -100)))
        else:
            L = band * 0.62
            for dt, sg in ((-0.1, -1), (0.1, 1)):
                c = P(rm + band * 0.24, t + dt * band / rm)
                deko.append(J.platziert(_zapfen(L), c[0], c[1], t + sg * math.radians(160)))
        rb = band * 0.085
        for dx, dy in ((0, 0), (1.9, 0.6), (0.7, 1.8), (-1.2, 1.3), (1.2, -1.4)):
            if art == "zapfen" and dy < 0:
                continue
            c = P(rm + dy * rb, t + dx * rb / rm)
            deko.append((J.kreis(c[0], c[1], rb, 18), J.beere(c[0], c[1], rb)))
    return J.blaetter_gravur(stapel + deko)


# --------------------------------------------------------------------------------------------------
# Medaille
# --------------------------------------------------------------------------------------------------

def _medaille(cfg, name: str, S: float, mitte: str, text: str, kranz: str, m: int, feinheit: str, oese: bool,
              notes: List[str]):
    R = S / 2
    w = J.steg_breite(cfg, feinheit)
    tiefe = max(0.05 * R, 1.6)
    fig = K.Figur()
    umriss, oese_loch = J.umriss_mit_oese(fig, J.bogenrand(R, m, tiefe), R - 0.4, R, w, oese)
    linien: List = []
    # Tropfen in den Bögen, Perlen in den Kerben
    r_sp = R - max(1.25 * w, 0.045 * R)
    L = max(3.0, 0.085 * R)
    r_fu = r_sp - L
    b = min(0.48 * TAU * r_fu / m, 0.6 * L)
    for k in range(m):
        t = TAU * k / m
        if oese and k == 0:
            continue
        fig.cut(J.tropfen(P(r_fu, t), P(r_sp, t), b))
        rp = min(0.32 * L, 0.18 * TAU * r_fu / m)
        rk = R - tiefe - max(1.2 * w, 0.03 * R) - rp
        if rp > 0.75:
            fig.cut(J.kreis(*P(rk, t + math.pi / m), rp, 16))
        # feine Begleitlinie um jeden Tropfen
        linien.append((J.versetzt(J.tropfen(P(r_fu, t), P(r_sp, t), b), max(0.7, 0.014 * R)), True))
    # Ringe aus Gravur
    r1 = r_fu - max(1.0, 0.025 * R)
    linien += J.doppelkreis(r1, max(0.6, 0.012 * R))
    rp = r1 - max(1.4, 0.035 * R)
    linien += J.perlenkreis(rp, max(0.28, 0.006 * R), max(1.0, 0.024 * R))
    # Bogenfries (ausgeschnitten)
    f_innen = (0.43 if mitte == "text" else 0.38) * R
    f_aussen = f_innen + 0.12 * R
    n_f = 24 if R < 70 else 32
    breite = min(TAU * f_innen / n_f - max(1.5 * w, 0.03 * R), 0.62 * TAU * f_innen / n_f)
    for k in range(n_f):
        t = TAU * (k + 0.5) / n_f
        fen = J.polar_fenster(f_innen, f_aussen, t, breite, "spitz")
        fig.cut(fen)
        linien.append((J.versetzt(fen, max(0.75, 0.016 * R)), True))
        linien.append((J.kreis(*P(f_aussen + max(1.4, 0.03 * R), t - math.pi / n_f), max(0.35, 0.008 * R), 10), True))
    # Kranz zwischen Fries und Perlenkreis
    k_innen = f_aussen + max(1.6, 0.035 * R) + max(0.75, 0.016 * R)
    k_aussen = rp - max(0.9, 0.02 * R)
    linien += _kranz(k_innen, k_aussen, kranz, 6 if R < 80 else 8)
    # Mitte
    rc = f_innen - max(1.5, 0.03 * R)
    linien += J.doppelkreis(rc, max(0.55, 0.011 * R))
    ri = rc - max(1.2, 0.03 * R)
    if mitte == "kristall":
        linien += J.eiskristall(ri * 0.98)
        for k in range(6):
            c = P(ri * 0.82, TAU * (k + 0.5) / 6)
            linien.append((J.kreis(c[0], c[1], max(0.3, 0.007 * R), 10), True))
    elif mitte == "stern":
        linien += J.zierstern(ri * 0.92, 8, max(0.42, 0.009 * R))
        linien += J.perlenkreis(ri * 0.97, max(0.25, 0.005 * R), max(0.9, 0.02 * R))
        for k in range(16):
            t = TAU * (k + 0.5) / 16
            linien.append(([P(ri * 0.55, t), P(ri * (0.78 if k % 2 else 0.88), t)], False))
    else:
        if text:
            linien += J.text(text, 0, 0, 1.7 * ri, 0.95 * ri, 0.28 * ri, 1.9)
        for sg in (1, -1):
            kr = J.eiskristall(ri * 0.16, 2)
            linien += [([(x, y + sg * ri * 0.72) for x, y in p], c) for p, c in kr]
            for dx in (-0.42, 0.42):
                c = (dx * ri, sg * ri * 0.62)
                linien.append((K.star(c[0], c[1], ri * 0.07, ri * 0.028, 5), True))
    part, _ = J.bauen(cfg, name, fig, linien, notes, oese_loch, umriss=umriss)
    return part


def build(cfg, name: str = "winterkranz", mitte: str = "kristall", text: str = "Frohe Weihnacht",
          kranz: str = "tanne", boegen: str = "24", groesse: float = 100.0, feinheit: str = "mittel",
          oese: bool = True, anzahl: int = 1):
    J.auswahl(mitte, MITTE, "Mitte")
    J.auswahl(kranz, KRANZ, "Kranz")
    boegen = J.auswahl(str(boegen), BOEGEN, "Bogenrand")
    J.auswahl(feinheit, J.FEINHEIT, "Feinheit")
    text = J.text_pruefen(text) if mitte == "text" else ""
    S = cfg.s(groesse)
    if S < 55:
        raise ValueError("Die Medaille ist zu klein für so feine Arbeit – mindestens 60 mm")
    asm = Assembly(name, params=dict(mitte=mitte, kranz=kranz, boegen=boegen, groesse=S, feinheit=feinheit))
    notes: List[str] = []
    for i in range(max(1, int(anzahl))):
        tag = name if anzahl <= 1 else f"{name}_{i + 1}"
        asm.parts.append(_medaille(cfg, tag, S, mitte, text, kranz, int(boegen), feinheit, oese, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    if oese:
        asm.notes.append("Aufhängen: Band oder Kordel durch die Öse ziehen.")
    asm.notes.append("Tipp: Erst gravieren, dann schneiden. Die Nadeln mit wenig Leistung und hoher Geschwindigkeit "
                     "gravieren, dann bleiben sie fein – am schönsten in 3 mm Ahorn oder Birke.")
    return asm
