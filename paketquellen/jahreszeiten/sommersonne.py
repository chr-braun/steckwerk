"""
Sommersonne – Sonne mit geschwungenen Flammenstrahlen, Lorbeerkranz in Spitze und fein gravierter Mitte.

Lange Flammen und kurze Spitzstrahlen wechseln sich ab; die Flammen tragen ausgeschnittene Tropfen und feine
Schraffur. Darin ein Lorbeerkranz, dessen Blätter als Spitze stehen bleiben (der Grund wird ausgeschnitten), oder
ein Perlenring, und in der Mitte eine Guilloche-Rosette, eine Sonnenblume nach dem goldenen Winkel oder ein Name.
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

MITTE = [("guilloche", "Guilloche-Rosette"), ("sonnenblume", "Sonnenblume"), ("text", "Name oder Gruß")]
RING = [("lorbeer", "Lorbeerkranz als Spitze"), ("perlen", "Perlenring")]
STRAHLEN = [("8", "8 Flammen"), ("12", "12 Flammen"), ("16", "16 Flammen")]

INFO = dict(
    label="Sommersonne",
    group="Jahreszeiten",
    desc="Sonne mit geschwungenen Flammenstrahlen und ausgeschnittenen Tropfen, Lorbeerkranz als Spitze oder "
         "Perlenring, in der Mitte Guilloche-Rosette, Sonnenblume nach dem goldenen Winkel oder Name.",
    params=[
        sel("mitte", "Mitte", MITTE, "guilloche"),
        txt("text", "Text", "Sommer", maxlen=20, help="leer = ohne", when={"mitte": ["text"]}),
        sel("ring", "Ring", RING, "lorbeer"),
        sel("strahlen", "Flammen", STRAHLEN, "8"),
        num("groesse", "Größe", 110, 70, 250, help="Durchmesser ohne Öse"),
        sel("feinheit", "Feinheit", J.FEINHEIT, "mittel"),
        flag("oese", "Öse zum Aufhängen", True),
        integer("anzahl", "Anzahl", 1, 1, 8),
    ],
)

UEBERSETZUNG = {"en": dict(J.FEINHEIT_EN, **{
    "Sommersonne": "Summer sun",
    "Sonne mit geschwungenen Flammenstrahlen und ausgeschnittenen Tropfen, Lorbeerkranz als Spitze oder "
    "Perlenring, in der Mitte Guilloche-Rosette, Sonnenblume nach dem goldenen Winkel oder Name.":
        "Sun with curving flame rays and cut-out drops, a laurel wreath in open lace or a ring of beads, with a "
        "guilloche rosette, a golden-angle sunflower or a name in the centre.",
    "Mitte": "Centre", "Guilloche-Rosette": "Guilloche rosette", "Sonnenblume": "Sunflower",
    "Name oder Gruß": "Name or greeting", "Ring": "Ring", "Lorbeerkranz als Spitze": "Laurel wreath in lace",
    "Perlenring": "Ring of beads", "Flammen": "Flames", "8 Flammen": "8 flames", "12 Flammen": "12 flames",
    "16 Flammen": "16 flames", "Durchmesser ohne Öse": "diameter without loop",
    "Aufhängen: Band oder Kordel durch die Öse ziehen.": "To hang: thread a ribbon or cord through the loop.",
})}


# --------------------------------------------------------------------------------------------------
# Strahlen
# --------------------------------------------------------------------------------------------------

def _strahl(Rk: float, Rt: float, t: float, b: float, krumm: float, welle: float, hmin: float = 0.35):
    """Mittellinie und beide Kanten eines Strahls (Fuß auf Radius Rk, Spitze auf Rt, Breite b am Fuß).
    krumm: seitlicher Schwung (Bogenmaß), welle: Wellung der Kanten."""
    n = 40
    mitte, li, re = [], [], []
    for i in range(n + 1):
        s = i / n
        r = Rk - 1.0 + (Rt - Rk + 1.0) * s
        a = t + krumm * math.sin(math.pi * s) * s
        mitte.append(P(r, a))
    for i in range(n + 1):
        s = i / n
        q = mitte[i]
        j = min(n - 1, i)
        dx, dy = mitte[j + 1][0] - mitte[j][0], mitte[j + 1][1] - mitte[j][1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        hb = max(hmin, b / 2 * (1 - s) ** 0.85 * (1 + welle * math.sin(3 * math.pi * s)))
        li.append((q[0] + nx * hb, q[1] + ny * hb))
        re.append((q[0] - nx * hb, q[1] - ny * hb))
    return mitte, li, re


def _umriss(R: float, Rk: float, n: int, oese: bool = False, hmin: float = 0.35):
    """Sonnenumriss: n geschwungene Flammen (bis R) im Wechsel mit n kurzen Spitzstrahlen."""
    pitch = TAU / (2 * n)
    strahlen = []
    for k in range(2 * n):
        t = k * pitch
        if k % 2 == 0:
            krumm = 0.0 if (oese and k == 0) else 0.32 * pitch
            strahlen.append(("flamme", t) + _strahl(Rk, R, t, 0.82 * pitch * Rk, krumm, 0.1 if krumm else 0.0, hmin))
        else:
            strahlen.append(("spitz", t) + _strahl(Rk, Rk + 0.55 * (R - Rk), t, 0.5 * pitch * Rk, 0.0, 0.0, hmin))
    pts = []
    for art, t, mitte, li, re in strahlen:
        # Kante mit kleinerem Winkel zuerst (vom Fuß zur Spitze), dann die andere zurück
        a_li = math.atan2(li[0][0], li[0][1])
        a_re = math.atan2(re[0][0], re[0][1])
        erst, zweit = (li, re) if (a_li - t + math.pi) % TAU - math.pi < (a_re - t + math.pi) % TAU - math.pi \
            else (re, li)
        spitze = mitte[-1]
        e, z = erst[-1], zweit[-1]
        dx, dy = spitze[0] - mitte[-2][0], spitze[1] - mitte[-2][1]
        dl = math.hypot(dx, dy) or 1.0
        hb = math.hypot(e[0] - spitze[0], e[1] - spitze[1])
        kappe = [(spitze[0] + dx / dl * hb * math.sin(math.pi * j / 6) + (e[0] - spitze[0]) * math.cos(math.pi * j / 6),
                  spitze[1] + dy / dl * hb * math.sin(math.pi * j / 6) + (e[1] - spitze[1]) * math.cos(math.pi * j / 6))
                 for j in range(1, 6)]
        pts += erst + kappe + list(reversed(zweit))
    return J.oriented(J.Z.W.abrunden(pts, 0.9, 5), True), strahlen


def _lorbeer(L: float, b: float):
    um = J.spitzoval(L, b, 18, 1.15)
    lin = [([(0, L * 0.06), (0, L * 0.88)], False)]
    for f in (0.3, 0.5, 0.7):
        for sg in (1, -1):
            lin.append(([(0, L * f), (sg * b * 0.28, L * (f + 0.1))], False))
    return um, lin


def _guilloche(ri: float) -> List:
    lin = []
    m = 9
    for j in range(18):
        ph = TAU * j / 18
        pts = [P(ri * (0.42 + 0.5 * (0.5 + 0.5 * math.cos(m * t + ph))), t) for t in
               [TAU * k / 540 for k in range(541)]]
        lin.append((pts, False))
    for f in (1.0, 0.82):
        pts = [P(ri * 0.36 * f * (0.62 + 0.38 * abs(math.cos(6 * t))), t) for t in [TAU * k / 360 for k in range(361)]]
        lin.append((pts, False))
    lin += J.doppelkreis(ri * 0.94, max(0.5, ri * 0.02))
    lin.append((J.zu(J.kreis(0, 0, ri * 0.12, 0)), False))
    for k in range(12):
        lin.append(([P(ri * 0.12, TAU * k / 12), P(ri * 0.22, TAU * k / 12)], False))
    return lin


def _sonnenblume(ri: float) -> List:
    stapel = []
    rs = ri * 0.48
    for lage, (f, ph, n) in enumerate(((1.0, 0.5, 21), (0.86, 0.0, 21))):
        for k in range(n):
            t = TAU * (k + ph) / n
            L = (ri * 0.96 - rs) * f + rs * 0.12
            um = J.setzen(J.spitzoval(L, L * 0.34, 18, 0.9), *P(rs * 0.92, t), 1.0, t)
            ad = [(J.setzen([(0, L * 0.12), (0, L * 0.84)], *P(rs * 0.92, t), 1.0, t), False)]
            for sg in (1, -1):
                ad.append((J.setzen([(sg * L * 0.06, L * 0.18), (sg * L * 0.08, L * 0.62)], *P(rs * 0.92, t), 1.0, t), False))
            stapel.append((um, [(um, True)] + ad))
    lin = J.blaetter_gravur(stapel + [(J.kreis(0, 0, rs, 0), [(J.kreis(0, 0, rs, 0), True)])])
    gold = math.radians(137.508)
    zahl = int((rs / max(0.55, rs * 0.075)) ** 2 * 0.95)
    c = rs * 0.93 / math.sqrt(zahl)
    for i in range(1, zahl):
        r = c * math.sqrt(i)
        q = P(r, i * gold)
        g = c * 0.36 * (0.6 + 0.4 * r / rs)
        a = i * gold
        lin.append((J.zu([P(g, a, q), P(g * 0.6, a + math.pi / 2, q), P(g, a + math.pi, q),
                          P(g * 0.6, a - math.pi / 2, q)]), False))
    return lin


# --------------------------------------------------------------------------------------------------
# Sonne
# --------------------------------------------------------------------------------------------------

def _sonne(cfg, name: str, S: float, mitte: str, text: str, ring: str, n: int, feinheit: str, oese: bool,
           notes: List[str]):
    R = S / 2
    w = J.steg_breite(cfg, feinheit)
    Rk = 0.66 * R
    n0 = n
    while n > 8 and 0.82 * math.pi / n * Rk < 5.5 * w:
        n -= 4
    if n < n0:
        notes.append(f"{name}: Für diese Größe und Holzstärke sind {n0} Flammen zu fein – es werden {n}.")
    fig = K.Figur()
    rand, strahlen = _umriss(R, Rk, n, oese, w * 0.6)
    umriss, oese_loch = J.umriss_mit_oese(fig, rand, R - 0.6, R, w, oese)
    lin: List = []
    pitch = TAU / (2 * n)
    for art, t, mitte_l, li, re in strahlen:
        if art == "flamme":
            if not (oese and t == 0):
                a, b = mitte_l[6], mitte_l[22]
                breite = min(0.36 * pitch * Rk, 0.3 * math.hypot(b[0] - a[0], b[1] - a[1]))
                tr = J.tropfen(b, a, breite)
                fig.cut(tr)
                lin.append((J.versetzt(tr, max(0.7, 0.014 * R)), True))
            lin.append((mitte_l[24:38], False))
            # Begleitlinien innen an beiden Kanten und Schraffur auf einer Seite
            for kante in (li, re):
                inn = [((x + m[0]) / 2 * 0.0 + x * 0.82 + m[0] * 0.18, y * 0.82 + m[1] * 0.18)
                       for (x, y), m in zip(kante, mitte_l)]
                lin.append((inn[1:-3], False))
            for i in range(2, 37, 2):
                q, e = mitte_l[i], li[i]
                lin.append(([(q[0] * 0.92 + e[0] * 0.08, q[1] * 0.92 + e[1] * 0.08),
                             (q[0] * 0.25 + e[0] * 0.75, q[1] * 0.25 + e[1] * 0.75)], False))
        else:
            lin.append((mitte_l[3:36], False))
            for kante in (li, re):
                lin.append(([(x * 0.7 + m[0] * 0.3, y * 0.7 + m[1] * 0.3) for (x, y), m in zip(kante, mitte_l)][1:-4],
                            False))
    # Kreis am Fuß der Strahlen
    lin += J.doppelkreis(Rk - max(1.0, 0.02 * R), max(0.55, 0.011 * R))
    lin += J.perlenkreis(Rk - max(2.6, 0.05 * R), max(0.28, 0.006 * R), max(1.0, 0.022 * R))
    # Ring
    r1 = Rk - max(4.0, 0.085 * R)
    r0 = r1 - 0.15 * R
    rm, band = (r0 + r1) / 2, r1 - r0
    if ring == "lorbeer":
        fig.cut(J.kreis(0, 0, r1, 0))
        fig.add(J.kreis(0, 0, r0, 0))
        zahl = max(12, int(TAU * rm / (band * 0.95)))
        stapel = []
        rank = [P(rm, TAU * k / 400) for k in range(401)]
        fig.add(K.stroke(rank, w * 1.1, w * 1.1, "rund"))
        for k in range(zahl):
            t = TAU * k / zahl
            for sg in (1, -1):
                L = band * 0.86
                c = P(rm, t)
                um, ad = _lorbeer(L, L * 0.4)
                a = t + math.radians(90 - sg * 42)       # schräg im Uhrzeigersinn, nach außen und innen
                pu = J.setzen(um, c[0], c[1], 1.0, a)
                fig.add(pu)
                stapel.append((pu, [(J.zu(J.versetzt(pu, -0.6)), False)] + [(J.setzen(p, c[0], c[1], 1.0, a), cl) for p, cl in ad]))
            b = P(rm, t + TAU / zahl * 0.5)
            fig.add(J.kreis(b[0], b[1], max(w * 0.7, band * 0.09), 14))
        lin += J.blaetter_gravur([(s[0], s[1]) for s in stapel])
        lin += J.doppelkreis(r0 - max(1.0, 0.02 * R), max(0.5, 0.01 * R))
    else:
        m = max(16, int(TAU * rm / (band * 0.55)))
        for k in range(m):
            t = TAU * (k + 0.5) / m
            rr = min(0.32 * TAU * rm / m, 0.36 * band)
            c = P(rm, t)
            fig.cut(J.kreis(c[0], c[1], rr, 24))
            lin.append((J.kreis(c[0], c[1], rr + max(0.7, 0.014 * R), 24), True))
            c2 = P(rm, t + math.pi / m)
            lin.append((J.kreis(c2[0], c2[1], max(0.35, rr * 0.22), 10), True))
        lin += J.doppelkreis(r1 + max(0.8, 0.016 * R), max(0.5, 0.01 * R))
        lin += J.doppelkreis(r0 - max(0.8, 0.016 * R), max(0.5, 0.01 * R))
    # Mitte
    ri = r0 - max(2.5, 0.05 * R)
    if mitte == "guilloche":
        lin += _guilloche(ri)
    elif mitte == "sonnenblume":
        lin += _sonnenblume(ri)
    else:
        lin += J.doppelkreis(ri, max(0.5, 0.01 * R))
        if text:
            lin += J.text(text, 0, 0, 1.7 * ri, 0.9 * ri, 0.32 * ri, 1.9)
        for k in range(24):
            t = TAU * (k + 0.5) / 24
            lin.append(([P(ri * 0.82, t), P(ri * (0.9 if k % 2 else 0.95), t)], False))
    part, _ = J.bauen(cfg, name, fig, lin, notes, oese_loch, umriss=umriss)
    return part


def build(cfg, name: str = "sommersonne", mitte: str = "guilloche", text: str = "Sommer", ring: str = "lorbeer",
          strahlen: str = "8", groesse: float = 110.0, feinheit: str = "mittel", oese: bool = True, anzahl: int = 1):
    J.auswahl(mitte, MITTE, "Mitte")
    J.auswahl(ring, RING, "Ring")
    strahlen = J.auswahl(str(strahlen), STRAHLEN, "Flammen")
    J.auswahl(feinheit, J.FEINHEIT, "Feinheit")
    text = J.text_pruefen(text) if mitte == "text" else ""
    S = cfg.s(groesse)
    if S < 65:
        raise ValueError("Die Sonne ist zu klein für so feine Arbeit – mindestens 70 mm")
    asm = Assembly(name, params=dict(mitte=mitte, ring=ring, strahlen=strahlen, groesse=S, feinheit=feinheit))
    notes: List[str] = []
    for i in range(max(1, int(anzahl))):
        tag = name if anzahl <= 1 else f"{name}_{i + 1}"
        asm.parts.append(_sonne(cfg, tag, S, mitte, text, ring, int(strahlen), feinheit, oese, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    if oese:
        asm.notes.append("Aufhängen: Band oder Kordel durch die Öse ziehen.")
    asm.notes.append("Tipp: Die Guilloche besteht aus vielen sich kreuzenden Linien – mit wenig Leistung und hoher "
                     "Geschwindigkeit gravieren, dann schimmert sie wie geprägtes Metall.")
    return asm
