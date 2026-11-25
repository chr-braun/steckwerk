"""
Sternen- und Schneeflockengirlande – filigrane Anhänger aus Karton oder Tonpapier zum Auffädeln.

Sterne, Schneeflocken und Herzen mit ausgeschnittenen Fenstern; jedes Teil hat links und rechts ein Loch,
durch das ein Faden oder Band gefädelt wird. So entsteht eine Girlande beliebiger Länge.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, Part, Stroke
from pakete import integer, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_papier_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


F_ = _sub("_form")
E, K, W = F_.E, F_.K, F_.W

FORMEN = [("gemischt", "Sterne, Flocken und Herzen"), ("sterne", "nur Sterne"), ("flocken", "nur Schneeflocken"),
          ("herzen", "nur Herzen")]

INFO = dict(
    label="Sternengirlande",
    group="Papier",
    desc="Girlande zum Auffädeln: filigrane Sterne, Schneeflocken und Herzen mit je zwei Fadenlöchern.",
    params=[
        integer("anzahl", "Anzahl Anhänger", 12, 1, 40),
        num("groesse", "Größe", 60, 35, 120),
        sel("formen", "Formen", FORMEN, "gemischt"),
    ],
)

UEBERSETZUNG = {"en": {
    "Sternengirlande": "Star garland", "Papier": "Paper",
    "Girlande zum Auffädeln: filigrane Sterne, Schneeflocken und Herzen mit je zwei Fadenlöchern.":
        "Garland to thread: filigree stars, snowflakes and hearts with two string holes each.",
    "Anzahl Anhänger": "Number of pieces", "Größe": "Size", "Formen": "Shapes",
    "Sterne, Flocken und Herzen": "Stars, flakes and hearts", "nur Sterne": "stars only",
    "nur Schneeflocken": "snowflakes only", "nur Herzen": "hearts only",
}}


def _herz(cx, cy, s, n=72):
    f = s / 32
    return [(cx + 16 * math.sin(t) ** 3 * f,
             cy + (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * f)
            for t in [2 * math.pi * i / n for i in range(n)]]


def _teil(cfg, form, s, notes) -> Part:
    steg = max(1.2, cfg.min_web + cfg.kerf + 0.5)
    loch = max(1.0, s * 0.022)
    fig = K.Figur()
    R = s / 2
    if form == "stern":
        fig.add(F_.stern(0, 0, R, R * 0.48, 5))
        fig.cut(F_.stern(0, 0, R * 0.62, R * 0.3, 5))
        fig.add(F_.stern(0, 0, R * 0.36, R * 0.17, 5))
        for i in range(5):                                                # Speichen zur Mitte
            a = math.pi / 2 + i * 2 * math.pi / 5
            fig.add(K.stroke([(0, 0), (R * 0.62 * math.cos(a), R * 0.62 * math.sin(a))], steg))
        for i in range(5):                                                # Tropfen in den Zacken
            a = math.pi / 2 + i * 2 * math.pi / 5
            fig.cut(F_.linse(R * 0.76 * math.cos(a), R * 0.76 * math.sin(a), R * 0.16, R * 0.07, a))
        loecher = []                                                      # Faden durch die Tropfen der Seitenzacken
    elif form == "flocke":
        for p in F_.schneeflocke(0, 0, R * 0.94, 0.0, steg):
            fig.add(p)
        fig.add(F_.kreis(0, 0, R * 0.34, 36))
        fig.cut(F_.stern(0, 0, R * 0.26, R * 0.12, 6))
        for sx in (-1, 1):
            fig.add(F_.kreis(sx * R * 0.86, 0, loch + steg * 1.4, 24))
        loecher = [(sx * R * 0.86, 0.0) for sx in (-1, 1)]
    else:
        fig.add(_herz(0, -R * 0.05, s * 1.0))
        fig.cut(_herz(0, -R * 0.05, s * 0.64))
        fig.add(_herz(0, -R * 0.05, s * 0.4))
        fig.cut(_herz(0, -R * 0.08, s * 0.2))
        for a in (math.radians(60), math.radians(120), math.radians(-90)):
            fig.add(K.stroke([(R * 0.25 * math.cos(a), R * 0.25 * math.sin(a) - R * 0.05),
                              (R * 0.75 * math.cos(a), R * 0.75 * math.sin(a) - R * 0.05)], steg))
        loecher = [(sx * R * 0.8, R * 0.3) for sx in (-1, 1)]
    for x, y in loecher:
        fig.cut(F_.kreis(x, y, loch, 20))
    lw = E.Leinwand((-R - 3, -R - 3, R + 3, R + 3), W.px_fuer(s))
    mat = lw.figur(fig).close(lw.px_fuer(0.4)).open(lw.px_fuer(0.5))
    return E.teil_aus_raster(form, lw, mat, cfg.min_web, cfg.kerf, notes)


def build(cfg, name: str = "sternengirlande", anzahl: int = 12, groesse: float = 60.0, formen: str = "gemischt"):
    if formen not in dict(FORMEN):
        raise ValueError(f"Unbekannte Form {formen!r}")
    s = cfg.s(groesse)
    asm = Assembly(name, params=dict(anzahl=anzahl, groesse=s, formen=formen))
    notes: List[str] = []
    folge = {"gemischt": ["stern", "flocke", "herz"], "sterne": ["stern"], "flocken": ["flocke"],
             "herzen": ["herz"]}[formen]
    vorlagen = {f: _teil(cfg, f, s, notes) for f in folge[:max(1, min(int(anzahl), len(folge)))]}
    for i in range(int(anzahl)):
        v = vorlagen[folge[i % len(folge)]]
        asm.parts.append(Part(f"{v.name}_{i + 1}", list(v.outline), [list(h) for h in v.holes],
                              [Stroke(list(st.points), st.closed) for st in v.engrave]))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Einen Faden oder ein schmales Band abwechselnd von hinten und vorne durch die Löcher fädeln.")
    asm.notes.append("Schön in Weiß und Silber oder in Tonpapier in mehreren Farben.")
    if cfg.T > 1.0:
        asm.notes.append(f"Tipp: Gedacht für Karton oder Tonpapier (ca. 0,3–0,5 mm) – eingestellt sind {cfg.T:g} mm.")
    return asm
