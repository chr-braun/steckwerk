"""
Adventskalender aus 24 Faltschachteln – Würfelschachteln mit Steckdeckel, Zahl und Motiv zum Ausmalen.

Jede Schachtel ist ein Netz aus vier Wänden mit Klebelasche, Boden mit Einstecklasche, Deckel mit
Einstecklasche und Staublaschen. Vorne sitzt eine Griffmulde, darunter die gravierte Zahl und ein kleines
Motiv (Stern, Tanne, Herz, Schneeflocke, Glocke, Mond), das von Tag zu Tag wechselt.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, Part, Stroke
from pakete import flag, integer, num

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

INFO = dict(
    label="Adventskalender",
    group="Papier",
    desc="24 Würfelschachteln aus Karton zum Falten, mit Steckdeckel, Griffmulde, gravierter Zahl und "
         "wechselndem Motiv zum Ausmalen.",
    params=[
        num("groesse", "Kantenlänge", 45, 30, 80),
        integer("von", "Erste Zahl", 1, 1, 24),
        integer("bis", "Letzte Zahl", 24, 1, 24),
        flag("motive", "Motive gravieren", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Adventskalender": "Advent calendar", "Papier": "Paper",
    "24 Würfelschachteln aus Karton zum Falten, mit Steckdeckel, Griffmulde, gravierter Zahl und "
    "wechselndem Motiv zum Ausmalen.":
        "24 folding card cube boxes with tuck lid, thumb notch, engraved number and a changing motif to "
        "colour in.",
    "Kantenlänge": "Edge length", "Erste Zahl": "First number", "Letzte Zahl": "Last number",
    "Motive gravieren": "Engrave motifs",
}}


def _glocke(cx, cy, s):
    pts = []
    for i in range(21):
        t = i / 20
        y = cy + s * (0.5 - t)
        w = s * (0.18 + 0.32 * t ** 1.8)
        pts.append((cx - w, y))
    rechts = [(2 * cx - x, y) for x, y in reversed(pts)]
    return pts + rechts


def _tanne(cx, cy, s):
    return [(cx, cy + s * 0.55), (cx + s * 0.22, cy + s * 0.2), (cx + s * 0.12, cy + s * 0.2),
            (cx + s * 0.34, cy - s * 0.15), (cx + s * 0.2, cy - s * 0.15), (cx + s * 0.42, cy - s * 0.45),
            (cx + s * 0.08, cy - s * 0.45), (cx + s * 0.08, cy - s * 0.6), (cx - s * 0.08, cy - s * 0.6),
            (cx - s * 0.08, cy - s * 0.45), (cx - s * 0.42, cy - s * 0.45), (cx - s * 0.2, cy - s * 0.15),
            (cx - s * 0.34, cy - s * 0.15), (cx - s * 0.12, cy + s * 0.2), (cx - s * 0.22, cy + s * 0.2)]


def _motiv(i, cx, cy, s):
    """Liste geschlossener Linienzüge für Motiv Nummer i."""
    art = i % 6
    if art == 0:
        return [F_.stern(cx, cy, s * 0.5, s * 0.22, 5)]
    if art == 1:
        return [_tanne(cx, cy, s)]
    if art == 2:
        f = s / 34
        return [[(cx + 16 * math.sin(t) ** 3 * f, cy + (13 * math.cos(t) - 5 * math.cos(2 * t)
                  - 2 * math.cos(3 * t) - math.cos(4 * t)) * f) for t in [2 * math.pi * j / 56 for j in range(56)]]]
    if art == 3:
        out = []
        for j in range(6):
            a = math.pi / 2 + j * math.pi / 3
            ex, ey = cx + s * 0.48 * math.cos(a), cy + s * 0.48 * math.sin(a)
            out.append([(cx, cy), (ex, ey)])
            for d in (0.6,):
                mx, my = cx + s * 0.48 * d * math.cos(a), cy + s * 0.48 * d * math.sin(a)
                for b in (a + 0.6, a - 0.6):
                    out.append([(mx, my), (mx + s * 0.15 * math.cos(b), my + s * 0.15 * math.sin(b))])
        return out
    if art == 4:
        return [_glocke(cx, cy, s), F_.kreis(cx, cy - s * 0.58, s * 0.07, 16)]
    return [F_.mond(cx, cy, s * 0.42)]


def _netz(cfg, a, notes) -> Part:
    zunge = 0.3 * a
    staub = 0.42 * a
    lasche = max(6.0, 0.16 * a)
    luft = 1.0
    fig = K.Figur()
    fig.add(K.rect(0, 0, 4 * a, a))                                                     # vier Wände
    fig.add([(4 * a - 0.5, 0), (4 * a + lasche, lasche * 0.6), (4 * a + lasche, a - lasche * 0.6), (4 * a - 0.5, a)])
    fig.add(K.rect(2 * a, a - 0.5, a, a + 0.5))                                          # Deckel
    fig.add(K.rect(0, -a, a, a + 0.5))                                                   # Boden
    for x0, y0, s in ((2 * a, 2 * a, 1), (0, -a, -1)):                                   # Einstecklaschen
        fig.add([(x0 + 1.5, y0 - s * 0.5), (x0 + a - 1.5, y0 - s * 0.5), (x0 + a - 1.5 - zunge * 0.5, y0 + s * zunge),
                 (x0 + 1.5 + zunge * 0.5, y0 + s * zunge)])
    for x0 in (a, 3 * a):                                                                # Staublaschen
        fig.add([(x0 + luft, a - 0.5), (x0 + a - luft, a - 0.5), (x0 + a - luft, a + staub * 0.35),
                 (x0 + a * 0.55, a + staub), (x0 + luft + 2, a + staub)])
        fig.add([(x0 + luft, 0.5), (x0 + a - luft, 0.5), (x0 + a - luft, -staub * 0.35),
                 (x0 + a * 0.55, -staub), (x0 + luft + 2, -staub)])
    fig.cut(F_.kreis(a / 2, a, 0.13 * a, 32))                                            # Griffmulde
    lw = E.Leinwand((-3, -a - zunge - 3, 4 * a + lasche + 3, 2 * a + zunge + 3), W.px_fuer(4.2 * a))
    mat = lw.figur(fig).close(lw.px_fuer(0.6)).open(lw.px_fuer(0.8))
    p = E.teil_aus_raster("schachtel", lw, mat, cfg.min_web, cfg.kerf, notes)
    from models import _deko as dk
    cv = dk.Canvas(p, margin=0.2)
    for x in (a, 2 * a, 3 * a, 4 * a):
        cv.draw([(x, 0), (x, a)])
    for x0, x1, y in ((a + luft, 2 * a, a), (2 * a, 3 * a, a), (3 * a, 4 * a - luft, a), (0, a, 0),
                      (a + luft, 2 * a - luft, 0), (3 * a + luft, 4 * a - luft, 0),
                      (2 * a + 1.5, 3 * a - 1.5, 2 * a), (1.5, a - 1.5, -a)):
        cv.draw([(x0, y), (x1, y)])
    return p


def build(cfg, name: str = "adventskalender", groesse: float = 45.0, von: int = 1, bis: int = 24,
          motive: bool = True):
    if not 1 <= int(von) <= int(bis) <= 24:
        raise ValueError("Die Zahlen müssen von 1 bis 24 aufsteigend sein")
    from models import _font
    from models import _deko as dk
    a = cfg.s(groesse)
    asm = Assembly(name, params=dict(groesse=a, von=von, bis=bis))
    notes: List[str] = []
    vorlage = _netz(cfg, a, notes)
    for n in range(int(von), int(bis) + 1):
        p = Part(f"tag_{n}", list(vorlage.outline), [list(h) for h in vorlage.holes],
                 [Stroke(list(s.points), s.closed) for s in vorlage.engrave])
        cv = dk.Canvas(p, margin=0.8)
        oben = a - 0.13 * a - 2
        rand = max(2.5, a * 0.07)
        cv.draw(dk.scalloped_rect(rand, rand, a - rand, a - rand, max(2.5, a * 0.09)), True)
        if motive:
            zh = a * 0.34
            striche, _ = _font.fit_text(str(n), a / 2, a * 0.32, a * 0.66, zh, min_h=3.0, max_cap=zh, style="fett")
            for s in _motiv(n, a / 2, a * 0.66, min(a * 0.3, (oben - a * 0.66) * 1.6)):
                cv.draw(s, len(s) > 2)
        else:
            zh = a * 0.5
            striche, _ = _font.fit_text(str(n), a / 2, a * 0.45, a * 0.7, zh, min_h=3.0, max_cap=zh, style="fett")
        for s in striche:
            cv.draw(s)
        asm.parts.append(p)
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes += [
        "Falzlinien nur ritzen, dann alle Falze nach innen knicken und die seitliche Lasche ankleben.",
        "Boden und Deckel werden nur eingesteckt – so lässt sich jede Schachtel wieder öffnen und füllen.",
    ]
    if cfg.T > 1.0:
        asm.notes.append(f"Tipp: Gedacht für Karton 200–300 g (ca. 0,3–0,5 mm) – eingestellt sind {cfg.T:g} mm.")
    return asm
