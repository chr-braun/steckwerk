"""
Fensterstern – flacher Scherenschnitt-Stern aus Papier für Fenster, Tür und Christbaum.

Drei sehr feine Entwürfe, gedacht für Karton 200–300 g oder Transparentpapier-Karton:
Eisblume (acht Zacken mit Federästen), Rosette (zwölf Zacken mit Blütenmitte, Perlenring und
Linsenketten) und Spitzenstern (sechs Zacken mit Wabenspitze und Perlenborte). Oben ein Loch zum Aufhängen.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, offset_polygon, oriented
from pakete import num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_steckstern_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


S_ = _sub("_stern")
E, K, W = S_.E, S_.K, S_.W

ENTWUERFE = [("eisblume", "Eisblume (8 Zacken)"), ("rosette", "Rosette (12 Zacken)"),
             ("spitze", "Spitzenstern (6 Zacken)")]

INFO = dict(
    label="Fensterstern",
    group="Steckstern",
    desc="Flacher Scherenschnitt-Stern aus Papier mit sehr feinem Filigran: Eisblume, Rosette oder "
         "Spitzenstern – für Fenster, Tür und Christbaum.",
    params=[
        sel("entwurf", "Entwurf", ENTWUERFE, "eisblume"),
        num("groesse", "Durchmesser", 200, 100, 320),
    ],
)

UEBERSETZUNG = {"en": {
    "Fensterstern": "Window star", "Steckstern": "Slotted star",
    "Flacher Scherenschnitt-Stern aus Papier mit sehr feinem Filigran: Eisblume, Rosette oder "
    "Spitzenstern – für Fenster, Tür und Christbaum.":
        "Flat paper-cut star with very fine filigree: frost flower, rosette or lace star – for windows, "
        "doors and the tree.",
    "Entwurf": "Design", "Eisblume (8 Zacken)": "Frost flower (8 points)", "Rosette (12 Zacken)":
        "Rosette (12 points)", "Spitzenstern (6 Zacken)": "Lace star (6 points)", "Durchmesser": "Diameter",
}}

ZACKEN = {"eisblume": (8, 0.46), "rosette": (12, 0.62), "spitze": (6, 0.52)}


def _innen_poly(umriss, d):
    g = offset_polygon(oriented(umriss, True), -d, miter_limit=4.0)
    return g if len(g) >= 3 else umriss


def _eisblume(R, k, steg, lw, mat, innen, ok):
    """Feld innen frei, dann Federäste als Stege."""
    mat = E._andnot(mat, lw.flaechen([innen]))
    fig = K.Figur()
    fig.add(S_.kreis(0, 0, R * 0.2, 64))
    for i in range(k):
        a = math.pi / 2 + i * 2 * math.pi / k
        u = (math.cos(a), math.sin(a))
        n = (-u[1], u[0])
        fig.line([(u[0] * R * 0.15, u[1] * R * 0.15), (u[0] * R, u[1] * R)], steg * 1.25)       # Mittelrippe
        b = a + math.pi / k                                                                     # Sektorgrenze
        fig.line([(0, 0), (math.cos(b) * R, math.sin(b) * R)], steg)
        d = R * 0.075
        t = R * 0.26
        while t < R * 0.92:
            for s in (1, -1):
                w = (u[0] * math.cos(0.75) + s * n[0] * math.sin(0.75), u[1] * math.cos(0.75) + s * n[1] * math.sin(0.75))
                L = R * 0.5
                p0 = (u[0] * t, u[1] * t)
                fig.line([p0, (p0[0] + w[0] * L, p0[1] + w[1] * L)], steg)
                # kleiner Zweig am Ast
                q = (p0[0] + w[0] * R * 0.09, p0[1] + w[1] * R * 0.09)
                fig.line([q, (q[0] + u[0] * R * 0.05, q[1] + u[1] * R * 0.05)], steg * 0.95)
            t += d
    ring = lw.figur(fig)
    mat = mat.union(E._and(ring, lw.flaechen([_innen_poly(innen, -steg)])))
    # Blüte in der Mitte
    loecher = [S_.spitzblatt(math.cos(a) * R * 0.11, math.sin(a) * R * 0.11, R * 0.11, R * 0.045, a)
               for a in [math.pi / 2 + j * 2 * math.pi / k for j in range(k)]]
    loecher.append(S_.kreis(0, 0, R * 0.03, 24))
    return E._andnot(mat, lw.flaechen(loecher))


def _rosette(R, k, steg, lw, mat, innen, ok):
    loecher = []
    for j in range(k):                                                    # Blütenmitte, zwei Kränze
        a = math.pi / 2 + j * 2 * math.pi / k
        loecher.append(S_.spitzblatt(math.cos(a) * R * 0.1, math.sin(a) * R * 0.1, R * 0.085, R * 0.032, a))
    for j in range(2 * k):
        a2 = math.pi / 2 + (j + 0.5) * math.pi / k
        loecher.append(S_.spitzblatt(math.cos(a2) * R * 0.205, math.sin(a2) * R * 0.205, R * 0.08, R * 0.026, a2))
    loecher.append(S_.kreis(0, 0, R * 0.022, 24))
    rp = R * 0.29                                                         # Perlenring
    m = int(2 * math.pi * rp / (R * 0.034 + steg * 1.2 + R * 0.02))
    for j in range(m):
        a = j * 2 * math.pi / m
        loecher.append(S_.kreis(math.cos(a) * rp, math.sin(a) * rp, R * 0.017, 20))
    for i in range(k):                                                    # Linsenketten in den Zacken
        a = math.pi / 2 + i * 2 * math.pi / k
        u = (math.cos(a), math.sin(a))
        t, L = R * 0.4, R * 0.1
        while t + L / 2 < R * 0.9:
            loecher.append(S_.linse(u[0] * t, u[1] * t, L, L * 0.38, a))
            t += L / 2 + steg * 1.3
            L *= 0.8
            t += L / 2
        b = a + math.pi / k                                               # Tropfen zwischen den Zacken
        for f, s in ((0.38, 0.045), (0.47, 0.03)):
            loecher.append(S_.kreis(math.cos(b) * R * f, math.sin(b) * R * f, R * s * 0.5, 20))
    loecher = [q for q in loecher if S_.innen(q, ok)]
    return E._andnot(mat, lw.flaechen(loecher))


def _spitze(R, k, steg, lw, mat, innen, ok):
    loecher = []
    p = R * 0.062
    r = p * 0.5 - steg * 0.8
    rr = max(1.05, steg * 0.8)
    tief = _innen_poly(innen, 2 * rr + steg * 1.6)
    for iy in range(-20, 21):                                             # Wabenspitze
        for ix in range(-20, 21):
            x = (ix + 0.5 * (iy % 2)) * p
            y = iy * p * math.sqrt(3) / 2
            d = math.hypot(x, y)
            if d < R * 0.27 or d > R:
                continue
            c = S_.kreis(x, y, r, 20)
            if S_.innen(c, ok) and all(S_.pip(q, tief) for q in c[::4]):
                loecher.append(c)
    loecher.append(S_.stern(0, 0, R * 0.16, R * 0.07, k))                # Mitte
    for j in range(k):
        a = math.pi / 2 + (j + 0.5) * 2 * math.pi / k
        loecher.append(S_.spitzblatt(math.cos(a) * R * 0.18, math.sin(a) * R * 0.18, R * 0.07, R * 0.03, a))
    # Perlenborte entlang des Randes
    bord = _innen_poly(innen, rr + steg * 0.3)
    acc = 0.0
    schritt = 2 * rr + steg * 1.4
    for a_, b_ in zip(bord, bord[1:] + bord[:1]):
        L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        while acc < L:
            t = acc / L
            loecher.append(S_.kreis(a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t, rr, 14))
            acc += schritt
        acc -= L
    return E._andnot(mat, lw.flaechen(loecher))


def build(cfg, name: str = "fensterstern", entwurf: str = "eisblume", groesse: float = 200.0):
    if entwurf not in ZACKEN:
        raise ValueError(f"Unbekannter Entwurf {entwurf!r}")
    D = cfg.s(groesse)
    R = D / 2
    k, ri = ZACKEN[entwurf]
    steg = max(1.0, cfg.min_web + cfg.kerf + 0.4)
    rand = max(2.2, steg * 2.0)
    if R * 0.05 < steg:
        raise ValueError("Für dieses Material ist der Stern zu klein – Durchmesser vergrößern")
    asm = Assembly(name, params=dict(entwurf=entwurf, groesse=D))
    notes: List[str] = []
    umriss = S_.stern(0, 0, R, R * ri, k)
    innen = _innen_poly(umriss, rand)
    aufh = (0.0, R - rand * 2.6)
    frei = (aufh[0], aufh[1], rand * 1.6)

    def ok(q):
        if math.hypot(q[0] - frei[0], q[1] - frei[1]) < frei[2] + steg:
            return False
        return S_.pip(q, innen)

    lw = E.Leinwand((-R - 3, -R - 3, R + 3, R + 3), W.px_fuer(D) * 0.75)
    mat = lw.flaechen([oriented(umriss, True)])
    mat = {"eisblume": _eisblume, "rosette": _rosette, "spitze": _spitze}[entwurf](R, k, steg, lw, mat, innen, ok)
    mat = mat.union(lw.flaechen([S_.kreis(aufh[0], aufh[1], rand * 1.6, 32)]))
    mat = E._andnot(mat, lw.flaechen([S_.kreis(aufh[0], aufh[1], max(1.0, rand * 0.55), 24)]))
    mat = mat.close(lw.px_fuer(0.25)).open(lw.px_fuer(0.25))
    p = E.teil_aus_raster("stern", lw, mat, cfg.min_web, cfg.kerf, notes)
    asm.parts.append(p)
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Mit wenig Leistung und Luftunterstützung schneiden; feine Stege nach dem Schnitt vorsichtig lösen.")
    asm.notes.append("Am schönsten in Weiß oder Creme vor dem Fenster, hinterlegt mit Transparentpapier leuchtet er farbig.")
    if cfg.T > 1.0:
        asm.notes.append(f"Tipp: Gedacht für Karton 200–300 g (ca. 0,3–0,5 mm) – eingestellt sind {cfg.T:g} mm.")
    return asm
