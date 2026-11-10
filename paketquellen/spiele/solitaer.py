"""
Solitär – rundes Brett für Glasmurmeln (englisch 33 oder französisch 37 Mulden). Außen läuft auf
Wunsch eine Rinne für die geschlagenen Kugeln: dann besteht die Deckplatte aus Innenscheibe und Ring.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, Part
from pakete import flag, sel

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
FORMEN = [("englisch", "englisch (33 Kugeln)"), ("franzoesisch", "französisch (37 Kugeln)")]
KUGELN = [("14", "Murmel 14 mm"), ("16", "Glasmurmel 16 mm"), ("20", "Murmel 20 mm"), ("25", "Murmel 25 mm")]
ECKEN = [("stern", "Sterne"), ("flocke", "Schneeflocken"), ("herz", "Herzen"), ("tanne", "Tannen"),
         ("glatt", "keine")]

INFO = dict(
    label="Solitär",
    group="Spiele",
    desc="Das klassische Denkspiel für eine Person: rundes Brett mit Mulden für Glasmurmeln, englisch oder "
         "französisch, außen eine Rinne für die geschlagenen Kugeln.",
    params=[
        sel("form", "Brett", FORMEN, "englisch"),
        sel("kugel", "Kugel", KUGELN, "16", help="Durchmesser der Murmeln, die du hast"),
        flag("rinne", "Rinne für geschlagene Kugeln", True),
        sel("ecken", "Motive in den Ecken", ECKEN, "stern", section="Gestaltung", when={"form": ["englisch"]}),
        sel("rand", "Zierrand", S.RAENDER, "punkte", section="Gestaltung"),
    ],
)

UEBERSETZUNG = {"en": dict(S.UEBERSETZUNG_GEMEINSAM, **{
    "Solitär": "Peg solitaire",
    "Das klassische Denkspiel für eine Person: rundes Brett mit Mulden für Glasmurmeln, englisch oder "
    "französisch, außen eine Rinne für die geschlagenen Kugeln.":
        "The classic puzzle for one: round board with recesses for glass marbles, English or French, with a "
        "gutter around the outside for the captured marbles.",
    "Brett": "Board", "englisch (33 Kugeln)": "English (33 marbles)", "französisch (37 Kugeln)": "French (37 marbles)",
    "Kugel": "Marble", "Murmel 14 mm": "Marble 14 mm", "Glasmurmel 16 mm": "Glass marble 16 mm",
    "Murmel 20 mm": "Marble 20 mm", "Murmel 25 mm": "Marble 25 mm",
    "Durchmesser der Murmeln, die du hast": "diameter of the marbles you have",
    "Rinne für geschlagene Kugeln": "Gutter for captured marbles", "Motive in den Ecken": "Corner motifs",
    "Schneeflocken": "Snowflakes", "Tannen": "Fir trees", "keine": "none",
    "Innenscheibe und Ring mittig auf die Bodenplatte leimen; die Rinne bleibt dazwischen frei.":
        "Glue the inner disc and the ring centred onto the base plate; the gutter stays free between them.",
    "Deckplatte bündig auf die Bodenplatte leimen.": "Glue the top plate flush onto the base plate.",
    "Spielregel: Alle Mulden außer der Mitte belegen. Eine Kugel springt waagrecht oder senkrecht über eine "
    "Nachbarkugel in ein freies Loch, die übersprungene Kugel kommt in die Rinne. Ziel: eine Kugel bleibt "
    "übrig, am besten in der Mitte.":
        "Rules: fill every recess except the centre. A marble jumps horizontally or vertically over a "
        "neighbour into an empty hole; the jumped marble goes into the gutter. Goal: one marble left, ideally "
        "in the centre.",
})}


def felder(form: str):
    out = []
    for i in range(-3, 4):
        for j in range(-3, 4):
            if abs(i) <= 1 or abs(j) <= 1 or (form == "franzoesisch" and abs(i) == 2 and abs(j) == 2):
                out.append((i, j))
    return out


def build(cfg, name: str = "solitaer", form: str = "englisch", kugel: str = "16", rinne: bool = True,
          ecken: str = "stern", rand: str = "punkte"):
    from models import _deko as dk
    dk.check_choice("Brett", form, FORMEN)
    dk.check_choice("Kugel", kugel, KUGELN)
    dk.check_choice("Motive in den Ecken", ecken, ECKEN)
    dk.check_choice("Zierrand", rand, S.RAENDER)
    k = float(kugel)
    p = 1.22 * k + 1.0                              # Abstand der Mulden
    r = k / 2                                       # Lochdurchmesser: die Kugel liegt auf dem Rand und
    h = min(0.72 * k, 2 * math.sqrt(r * r - (r - 0.8 * cfg.T) ** 2))   # sinkt höchstens 0,8 T ein
    F = felder(form)
    rmax = max(math.hypot(i, j) for i, j in F) * p
    R_in = rmax + h / 2 + 0.5 * p
    cw = k + 1.5
    R_out = R_in + cw + max(8.0, 0.4 * p) if rinne else R_in
    S.platte_passt(cfg, 2 * R_out, 2 * R_out, "Solitär")

    brett = Part(f"{name}_brett", dk.circle(0.0, 0.0, R_in, 0.04))
    for i, j in F:
        brett.add_hole(dk.circle(i * p, j * p, h / 2, 0.04, ccw=False))
    cv = dk.Canvas(brett, margin=1.2, hole_margin=1.2)
    for i, j in F:                                  # Verbindungslinien zu den Nachbarn
        for di, dj in ((1, 0), (0, 1)):
            if (i + di, j + dj) in F:
                cv.draw([(i * p, j * p), ((i + di) * p, (j + dj) * p)])
        cv.draw(dk.circle(i * p, j * p, h / 2 + 1.8, 0.04), True)
    cv.draw(dk.circle(0.0, 0.0, h / 2 + 3.4, 0.04), True)        # Mitte: hier beginnt das Spiel leer
    if form == "englisch" and ecken != "glatt":
        for sx in (-1, 1):
            for sy in (-1, 1):
                for pts, closed in S.motiv_linien(ecken, sx * 2.2 * p, sy * 2.2 * p, 0.45 * p):
                    cv.draw(pts, closed)
    S.zierrand(cv, dk.circle(0.0, 0.0, R_in - 2.0, 0.04), rand, max(3.0, 0.22 * p))

    boden = Part(f"{name}_boden", dk.circle(0.0, 0.0, R_out, 0.04))
    teile = [brett]
    if rinne:
        ring = Part(f"{name}_ring", dk.circle(0.0, 0.0, R_out, 0.04))
        ring.add_hole(dk.circle(0.0, 0.0, R_in + cw, 0.04, ccw=False))
        cvr = dk.Canvas(ring, margin=1.2, hole_margin=1.2)
        S.zierrand(cvr, dk.circle(0.0, 0.0, R_out - 1.5, 0.04), "doppelt" if rand == "keiner" else "linie", 3.0)
        teile.append(ring)
    # Leimmarkierung auf dem Boden, damit die Innenscheibe mittig sitzt
    if rinne:
        boden.add_engrave(dk.circle(0.0, 0.0, R_in, 0.04), closed=True)

    asm = Assembly(name, params=dict(durchmesser=2 * R_out, abstand=p, loch=h, felder=len(F)))
    asm.parts += teile + [boden]
    asm.notes += [
        "Innenscheibe und Ring mittig auf die Bodenplatte leimen; die Rinne bleibt dazwischen frei."
        if rinne else "Deckplatte bündig auf die Bodenplatte leimen.",
        "Spielregel: Alle Mulden außer der Mitte belegen. Eine Kugel springt waagrecht oder senkrecht über eine "
        "Nachbarkugel in ein freies Loch, die übersprungene Kugel kommt in die Rinne. Ziel: eine Kugel bleibt "
        "übrig, am besten in der Mitte.",
    ]
    return asm
