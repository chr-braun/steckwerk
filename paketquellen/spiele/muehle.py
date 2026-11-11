"""
Mühle – Spielbrett aus zwei Lagen mit 24 Mulden, Ablage für je 9 Steine und 18 Spielsteinen.
Die Deckplatte hat Löcher, darunter liegt die geschlossene Bodenplatte: so entstehen Mulden, in
denen die Steine sicher liegen.
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
ABLAGEN = [("seiten", "links und rechts (je 3 × 3)"), ("schmal", "links und rechts, schmal (je 2 Reihen)"),
           ("keine", "keine")]

INFO = dict(
    label="Mühle",
    group="Spiele",
    desc="Mühlebrett aus zwei Lagen: 24 Mulden, in denen die Steine fest liegen, Ablage für je 9 Steine, "
         "18 Spielsteine mit Motiv und auf Wunsch die Namen der beiden Spieler.",
    params=[
        num("groesse", "Spielfeld", 200, 150, 260, help="Seitenlänge des quadratischen Spielfelds; mit Ablage passen bis etwa 210 mm auf die Platte"),
        sel("ablage", "Ablage für die Steine", ABLAGEN, "seiten"),
        sel("motiv_a", "Steine Spieler 1", S.MOTIVE, "ring", section="Gestaltung"),
        sel("motiv_b", "Steine Spieler 2", S.MOTIVE, "stern", section="Gestaltung"),
        sel("rand", "Zierrand", S.RAENDER, "doppelt", section="Gestaltung"),
        txt("name_a", "Name links", "", section="Beschriftung", help="erscheint über der linken Ablage"),
        txt("name_b", "Name rechts", "", section="Beschriftung", help="erscheint über der rechten Ablage"),
    ],
)

UEBERSETZUNG = {"en": dict(S.UEBERSETZUNG_GEMEINSAM, **{
    "Mühle": "Nine men's morris",
    "Mühlebrett aus zwei Lagen: 24 Mulden, in denen die Steine fest liegen, Ablage für je 9 Steine, "
    "18 Spielsteine mit Motiv und auf Wunsch die Namen der beiden Spieler.":
        "Two-layer morris board: 24 recesses that hold the pieces, storage for 9 pieces per player, "
        "18 pieces with a motif and optionally both players' names.",
    "Spielfeld": "Playing field", "Seitenlänge des quadratischen Spielfelds; mit Ablage passen bis etwa 210 mm auf die Platte":
        "side length of the square field; with storage up to about 210 mm fits on the sheet",
    "Ablage für die Steine": "Storage for the pieces", "links und rechts (je 3 × 3)": "left and right (3 × 3 each)",
    "links und rechts, schmal (je 2 Reihen)": "left and right, narrow (2 rows each)",
    "keine": "none", "Steine Spieler 1": "Pieces player 1", "Steine Spieler 2": "Pieces player 2",
    "Name links": "Name left", "Name rechts": "Name right",
    "erscheint über der linken Ablage": "shown above the left storage",
    "erscheint über der rechten Ablage": "shown above the right storage",
    "Die Bodenplatte unter die Deckplatte leimen (Kanten bündig, mit Zwingen oder Büchern beschweren).":
        "Glue the base plate under the top plate (edges flush, clamp or weigh down with books).",
    "Eine Steinfarbe dunkel beizen oder bemalen, dann sind die Spieler auf einen Blick zu unterscheiden.":
        "Stain or paint one set of pieces dark so the players are easy to tell apart.",
})}


def punkte(a: float) -> List[tuple]:
    """Die 24 Mühlepunkte im Raster a, Mitte (0, 0)."""
    out = []
    for k in (3, 2, 1):
        o = k * a
        for x, y in ((-o, -o), (0, -o), (o, -o), (o, 0), (o, o), (0, o), (-o, o), (-o, 0)):
            out.append((x, y))
    return out


def build(cfg, name: str = "muehle", groesse: float = 200.0, ablage: str = "seiten", motiv_a: str = "ring",
          motiv_b: str = "stern", rand: str = "doppelt", name_a: str = "", name_b: str = ""):
    from models import _deko as dk
    dk.check_choice("Ablage", ablage, ABLAGEN)
    dk.check_choice("Steine Spieler 1", motiv_a, S.MOTIVE)
    dk.check_choice("Steine Spieler 2", motiv_b, S.MOTIVE)
    dk.check_choice("Zierrand", rand, S.RAENDER)
    G = cfg.s(groesse)
    if not 150 <= G <= 260:
        raise ValueError("Mühle: Spielfeld muss zwischen 150 und 260 mm liegen")
    rand_m = 0.105 * G
    a = (G - 2 * rand_m) / 6                       # Rasterabstand der Punkte
    m = 0.70 * a                                   # Mulde Ø
    d = m - 1.2                                    # Stein Ø (Spiel in der Mulde)
    q = m + max(3.0, 0.2 * m)                      # Rasterabstand der Ablage
    spalten = {"seiten": 3, "schmal": 2}.get(ablage, 0)
    seite = (spalten - 1) * q * (1.0 if spalten == 3 else 0.9) + m + 0.11 * G if spalten else 0.0
    Wt, H = G + 2 * seite, G
    try:
        S.platte_passt(cfg, Wt, H, "Mühle")
    except ValueError as e:
        if spalten:
            raise ValueError(str(e) + " oder die schmale Ablage nehmen" if spalten == 3 else str(e)) from None
        raise

    mulden = [(x, y, m) for x, y in punkte(a)]
    ablagen = []
    if seite:
        for sx in (-1, 1):
            xc = sx * (G / 2 + (seite - 0.03 * G) / 2)
            if spalten == 3:
                zellen = [(i - 1, j - 1) for j in range(3) for i in range(3)]
            else:                                  # 5 + 4, versetzt wie Bienenwaben
                zellen = [(-0.5, j - 2) for j in range(5)] + [(0.5, j - 1.5) for j in range(4)]
            for i, j in zellen:
                ablagen.append((xc + i * q * (0.9 if spalten == 2 else 1.0), j * q - 0.06 * G, m))
    outline = dk.rounded_rect(-Wt / 2, -H / 2, Wt / 2, H / 2, 0.05 * G)
    oben, unten = S.brett_teile(name, outline, mulden + ablagen)

    cv = dk.Canvas(oben, margin=1.5, hole_margin=1.0)
    # Zierrand
    ins = 0.03 * G
    S.zierrand(cv, dk.rounded_rect(-Wt / 2 + ins, -H / 2 + ins, Wt / 2 - ins, H / 2 - ins, 0.03 * G), rand,
               max(3.0, 0.022 * G))
    # Mühlelinien
    for k in (1, 2, 3):
        o = k * a
        cv.draw([(-o, -o), (o, -o), (o, o), (-o, o)], True)
    for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cv.draw([(ux * a, uy * a), (ux * 3 * a, uy * 3 * a)])
    # Zierringe um die Mulden
    for x, y, dd in mulden:
        cv.draw(dk.circle(x, y, dd / 2 + 1.6, 0.04), True)
    if seite:
        for sx in (-1, 1):                         # Trennlinie Spielfeld | Ablage
            x = sx * G / 2
            cv.draw([(x, -H / 2 + 0.1 * G), (x, H / 2 - 0.1 * G)])
        top_ablage = max(y for _, y, _ in ablagen) + m / 2
        frei_h = H / 2 - ins - 3 - top_ablage - 3
        for sx, nm in ((-1, name_a), (1, name_b)):
            xc = sx * (G / 2 + (seite - ins) / 2)
            S.text(cv, nm, xc, top_ablage + 3 + frei_h / 2, seite - ins - 8, frei_h, min(9.0, 0.045 * G))
    elif (name_a or name_b).strip():
        raise ValueError("Mühle: Für die Namen braucht es die Ablage links und rechts")

    asm = Assembly(name, params=dict(groesse=G, raster=a, mulde=m, stein=d, breite=Wt))
    asm.parts += [oben, unten]
    for i in range(9):
        asm.parts.append(S.stein(f"{name}_stein_a{i + 1}", d, motiv_a))
    for i in range(9):
        asm.parts.append(S.stein(f"{name}_stein_b{i + 1}", d, motiv_b))
    asm.notes += [
        "Die Bodenplatte unter die Deckplatte leimen (Kanten bündig, mit Zwingen oder Büchern beschweren).",
        "Eine Steinfarbe dunkel beizen oder bemalen, dann sind die Spieler auf einen Blick zu unterscheiden.",
    ]
    return asm
