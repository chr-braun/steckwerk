"""
Tic-Tac-Toe – rundes Brett aus zwei Lagen: 3 × 3 Mulden in der Mitte, ringsum je fünf Ablagemulden
für die Figuren. Die Figuren sind ausgeschnitten (X/O, Tanne/Stern, Herz/Stern, Glocke/Stern …).
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly
from pakete import num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_spiele_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod



S = _sub("_spiel")
PAARE = [("tanne_stern", "Tanne gegen Stern"), ("x_o", "X gegen O"), ("herz_stern", "Herz gegen Stern"),
         ("glocke_tanne", "Glocke gegen Tanne"), ("herz_o", "Herz gegen O")]

INFO = dict(
    label="Tic-Tac-Toe",
    group="Spiele",
    desc="Rundes Tic-Tac-Toe aus zwei Lagen: neun Mulden in der Mitte, ringsum Ablagen für je fünf Figuren. "
         "Die Figuren sind ausgesägt, zum Beispiel Tannen gegen Sterne. Unten ist Platz für einen Namen.",
    params=[
        num("durchmesser", "Durchmesser", 170, 130, 260),
        sel("figuren", "Figuren", PAARE, "tanne_stern"),
        sel("rand", "Zierrand", S.RAENDER, "sterne", section="Gestaltung"),
        txt("beschriftung", "Beschriftung", "", section="Beschriftung", help="unten auf dem Brett, z. B. ein Name"),
    ],
)

UEBERSETZUNG = {"en": dict(S.UEBERSETZUNG_GEMEINSAM, **{
    "Tic-Tac-Toe": "Tic-tac-toe",
    "Rundes Tic-Tac-Toe aus zwei Lagen: neun Mulden in der Mitte, ringsum Ablagen für je fünf Figuren. "
    "Die Figuren sind ausgesägt, zum Beispiel Tannen gegen Sterne. Unten ist Platz für einen Namen.":
        "Round two-layer tic-tac-toe: nine recesses in the middle, storage for five pieces each around them. "
        "The pieces are cut out, for example fir trees against stars. There is room for a name at the bottom.",
    "Durchmesser": "Diameter", "Figuren": "Pieces", "Tanne gegen Stern": "Fir tree vs. star",
    "X gegen O": "X vs. O", "Herz gegen Stern": "Heart vs. star", "Glocke gegen Tanne": "Bell vs. fir tree",
    "Herz gegen O": "Heart vs. O", "unten auf dem Brett, z. B. ein Name": "at the bottom of the board, e.g. a name",
    "Die Bodenplatte unter die Deckplatte leimen (Kanten bündig, mit Zwingen oder Büchern beschweren).":
        "Glue the base plate under the top plate (edges flush, clamp or weigh down with books).",
    "Die Figuren einer Sorte bemalen oder beizen, dann wirkt das Spiel noch schöner.":
        "Paint or stain one kind of piece to make the game look even nicer.",
})}


def lage(R: float):
    """Raster, Mulden-Ø und Ablageradius für ein Brett vom Radius R."""
    e = max(6.0, 0.045 * 2 * R)
    c = (R - 2.0 * e) / 2.62
    m = 0.72 * c
    rr = math.sqrt(2) * c + m + 0.12 * c
    return c, m, rr, e


def build(cfg, name: str = "tictactoe", durchmesser: float = 170.0, figuren: str = "tanne_stern",
          rand: str = "sterne", beschriftung: str = ""):
    from models import _deko as dk
    dk.check_choice("Figuren", figuren, PAARE)
    dk.check_choice("Zierrand", rand, S.RAENDER)
    D = cfg.s(durchmesser)
    if not 130 <= D <= 260:
        raise ValueError("Tic-Tac-Toe: Durchmesser muss zwischen 130 und 260 mm liegen")
    S.platte_passt(cfg, D, D, "Tic-Tac-Toe")
    R = D / 2
    c, m, rr, e = lage(R)
    fd = m - 1.4                                   # Figur passt mit Luft in die Mulde
    feld = [((i - 1) * c, (j - 1) * c, m) for j in range(3) for i in range(3)]
    dw = 2 * math.asin(min(1.0, (m + max(2.5, 0.12 * m)) / (2 * rr)))
    ablage = []
    for mitte in (math.pi, 0.0):
        for k in range(5):
            a = mitte + (k - 2) * dw
            ablage.append((rr * math.cos(a), rr * math.sin(a), m))
    outline = dk.circle(0.0, 0.0, R, 0.04)
    oben, unten = S.brett_teile(name, outline, feld + ablage)

    cv = dk.Canvas(oben, margin=1.2, hole_margin=1.0)
    for pts in ([(-c / 2, -1.5 * c), (-c / 2, 1.5 * c)], [(c / 2, -1.5 * c), (c / 2, 1.5 * c)],
                [(-1.5 * c, -c / 2), (1.5 * c, -c / 2)], [(-1.5 * c, c / 2), (1.5 * c, c / 2)]):
        cv.draw(pts)
    for x, y, dd in feld + ablage:
        cv.draw(dk.circle(x, y, dd / 2 + 1.4, 0.04), True)
    # Text unten zwischen den Ablagebögen
    if beschriftung.strip():
        r_in = R - 1.4 * e - 1.0
        y_top = -c - m / 2 - 2.6
        h = min(11.0, 0.5 * (r_in + y_top))
        y_bot = y_top - h
        w = 2 * math.sqrt(max(0.0, r_in ** 2 - y_bot ** 2))
        for x, y, dd in ablage:                    # nicht in die Ablagemulden schreiben
            if y - dd / 2 - 1.4 < y_top and y + dd / 2 + 1.4 > y_bot:
                w = min(w, 2 * (abs(x) - dd / 2 - 3.0))
        if h < 4 or w < 20:
            raise ValueError("Tic-Tac-Toe: Für die Beschriftung ist das Brett zu klein")
        S.text(cv, beschriftung, 0.0, (y_top + y_bot) / 2, w, h, h)
    S.zierrand(cv, dk.circle(0.0, 0.0, R - e * 0.6, 0.04), rand, max(3.0, 0.75 * e))

    a1, a2 = figuren.split("_")
    asm = Assembly(name, params=dict(durchmesser=D, raster=c, mulde=m, figur=fd))
    asm.parts += [oben, unten]
    for i in range(5):
        asm.parts.append(S.figur(f"{name}_{a1}{i + 1}", a1, fd))
    for i in range(5):
        asm.parts.append(S.figur(f"{name}_{a2}{i + 1}", a2, fd))
    asm.notes += [
        "Die Bodenplatte unter die Deckplatte leimen (Kanten bündig, mit Zwingen oder Büchern beschweren).",
        "Die Figuren einer Sorte bemalen oder beizen, dann wirkt das Spiel noch schöner.",
    ]
    return asm
