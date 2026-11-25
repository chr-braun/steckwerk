"""
Steck-Tiere – Rentier, Eisbär und Pinguin aus wenigen Teilen Karton, ganz ohne Kleber.

Rentier und Eisbär bestehen aus einem Körper in Seitenansicht und zwei Beinpaaren, die quer von unten
eingesteckt werden. Der Pinguin besteht aus Vorder- und Seitenansicht über Kreuz. Augen, Fell, Hufe und
Schal sind leicht graviert und laden zum Ausmalen ein.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, JointFeature, Part
from pakete import flag, num, sel

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

TIERE = [("rentier", "Rentier"), ("eisbaer", "Eisbär"), ("pinguin", "Pinguin")]

INFO = dict(
    label="Steck-Tiere",
    group="Papier",
    desc="Rentier, Eisbär oder Pinguin aus zwei bis drei Teilen Karton zum Zusammenstecken, mit gravierten "
         "Augen, Fell und Schal zum Ausmalen.",
    params=[
        sel("tier", "Tier", TIERE, "rentier"),
        num("groesse", "Größe", 120, 70, 220),
        flag("schal", "Schal gravieren", True),
        flag("details", "Fell und Ausmal-Linien gravieren", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Steck-Tiere": "Slot-together animals", "Papier": "Paper",
    "Rentier, Eisbär oder Pinguin aus zwei bis drei Teilen Karton zum Zusammenstecken, mit gravierten "
    "Augen, Fell und Schal zum Ausmalen.":
        "Reindeer, polar bear or penguin from two or three card parts slotted together, with engraved eyes, "
        "fur and scarf to colour in.",
    "Tier": "Animal", "Rentier": "Reindeer", "Eisbär": "Polar bear", "Pinguin": "Penguin", "Größe": "Size",
    "Schal gravieren": "Engrave scarf", "Fell und Ausmal-Linien gravieren": "Engrave fur and colouring lines",
}}


def _s(pts, k):
    return [(x * k, y * k) for x, y in pts]


def _schlitz(outline, T, x, y_mid, von_oben):
    """Schlitz bei x (statt nur auf der Achse)."""
    from models._shapes import cut_axis_slot
    out, slot = cut_axis_slot([(px - x, py) for px, py in outline], T, y_mid, von_oben)
    return [(px + x, py) for px, py in out], [(px + x, py) for px, py in slot]


def _raster_teil(cfg, name, fig, box, notes, rund=0.8):
    lw = E.Leinwand(box, W.px_fuer(max(box[2] - box[0], box[3] - box[1])))
    mat = lw.figur(fig).close(lw.px_fuer(rund)).open(lw.px_fuer(rund))
    return E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes)


def _mit_schlitzen(cfg, p: Part, schlitze) -> Part:
    out = p.outline
    feats = []
    ys = [y for _, y in out]
    for fid, x, y_mid, oben in schlitze:
        out, slot = _schlitz(out, cfg.T, x, y_mid, oben)
        span = (y_mid, max(ys)) if oben else (min(ys), y_mid)
        feats.append(JointFeature(fid, "halving", span[1] - span[0], cfg.T, span=span, points=slot))
    q = Part(p.name, out, features=feats)
    for h in p.holes:
        q.add_hole(h)
    return q


# ---------------------------------------------------------------- Vierbeiner

RENTIER = [(36, 42), (10, 38), (-20, 39), (-36, 44), (-45, 54), (-48, 66), (-46, 76), (-51, 81), (-47, 86),
           (-40, 83), (-24, 85), (0, 83), (22, 84), (34, 90), (44, 101), (54, 107), (66, 108), (78, 101),
           (83, 95), (77, 91), (63, 91), (51, 84), (45, 64), (41, 50)]
EISBAER = [(38, 38), (0, 34), (-38, 38), (-50, 46), (-56, 60), (-52, 74), (-34, 82), (0, 80), (28, 78),
           (42, 74), (52, 78), (60, 84), (66, 83), (70, 78), (86, 70), (88, 64), (80, 60), (64, 58),
           (52, 52), (44, 42)]


def _vierbeiner(cfg, asm, tier, k, schal, details, notes):
    rentier = tier == "rentier"
    fig = K.Figur().add(K.spline(_s(RENTIER if rentier else EISBAER, k), closed=True, n=8))
    if rentier:
        w = 3.4 * k
        for ast in ([(56, 104), (52, 120), (45, 133), (40, 146)], [(52, 120), (61, 129)],
                    [(46, 131), (55, 141)], [(64, 104), (70, 120), (78, 131), (87, 139)],
                    [(70, 120), (64, 133)], [(77, 130), (77, 143)]):
            fig.line(K.spline(_s(ast, k), n=6), w)
        fig.add(F_.linse(52 * k, 101 * k, 13 * k, 5 * k, math.radians(155)))       # Ohr
    else:
        fig.add(F_.kreis(58 * k, 83 * k, 4.5 * k, 24))                             # Ohr
    box = (-70 * k, 25 * k, 95 * k, 155 * k)
    p = _raster_teil(cfg, "koerper", fig, box, notes)
    x_v, x_h = (28 * k, -30 * k)
    y_m = (40 if rentier else 36) * k + 9 * k
    q = _mit_schlitzen(cfg, p, [("vorne", x_v, y_m, False), ("hinten", x_h, y_m, False)])
    from models import _deko as dk
    cv = dk.Canvas(q, margin=0.5)
    if rentier:
        cv.draw(F_.kreis(68 * k, 101 * k, 1.6 * k, 16), True)
        cv.draw(F_.kreis(80.5 * k, 95 * k, 2.2 * k, 16), True)                     # rote Nase zum Ausmalen
        if details:
            cv.draw(K.spline(_s([(-40, 60), (-20, 56), (0, 58), (20, 56), (36, 62)], k), n=6))
            for x in (-20, -4, 12):
                cv.draw(K.spline(_s([(x, 70), (x + 4, 66), (x + 8, 70)], k), n=4))
        if schal:
            cv.draw(K.spline(_s([(42, 84), (48, 80), (54, 88)], k), n=6))
            cv.draw(K.spline(_s([(38, 78), (46, 74), (52, 82)], k), n=6))
            cv.draw(K.spline(_s([(44, 76), (40, 64), (44, 56)], k), n=6))
    else:
        cv.draw(F_.kreis(70 * k, 73 * k, 1.6 * k, 16), True)
        cv.draw(F_.kreis(84.5 * k, 66 * k, 2.0 * k, 16), True)
        if details:
            for x, y in ((-36, 64), (-20, 70), (-4, 66), (14, 70), (-28, 52), (-10, 50), (8, 54)):
                cv.draw(K.spline(_s([(x, y), (x + 3, y - 3), (x + 6, y)], k), n=4))
        if schal:
            cv.draw(K.spline(_s([(40, 72), (48, 66), (56, 74)], k), n=6))
            cv.draw(K.spline(_s([(36, 64), (44, 58), (52, 66)], k), n=6))
            cv.draw(K.spline(_s([(42, 62), (36, 50), (40, 44)], k), n=6))
    asm.parts.append(q)
    bw = (8.0 if rentier else 11.0) * k
    top = y_m + 9 * k
    for name, fid in (("beine_vorne", "vorne"), ("beine_hinten", "hinten")):
        f = K.Figur()
        f.add(K.spline([(-19 * k, top - 14 * k), (-14 * k, top - 2 * k), (0, top), (14 * k, top - 2 * k),
                        (19 * k, top - 14 * k), (0, top - 22 * k)], closed=True, n=8))
        for sx in (-1, 1):
            xa, xb = sx * 12 * k, sx * 14 * k
            f.add([(xa - bw * 0.6, top - 16 * k), (xa + bw * 0.6, top - 16 * k), (xb + bw / 2, 0), (xb - bw / 2, 0)])
        b = _raster_teil(cfg, name, f, (-25 * k, -3, 25 * k, top + 3), notes, 1.2)
        bq = _mit_schlitzen(cfg, b, [("kreuz", 0.0, y_m, True)])
        cv = dk.Canvas(bq, margin=0.5)
        for sx in (-1, 1):
            x = sx * 14 * k
            cv.draw([(x - bw / 2, 5 * k), (x + bw / 2, 5 * k)])                      # Hufe / Pfoten
            if rentier:
                cv.draw([(x, 0.8), (x, 5 * k)])
        asm.parts.append(bq)
        asm.connect(f"koerper:{fid}", f"{name}:kreuz")


# ---------------------------------------------------------------- Pinguin

PING_VORNE = [(-22, 7), (22, 7), (30, 30), (31, 60), (25, 85), (14, 102), (0, 108), (-14, 102), (-25, 85),
              (-31, 60), (-30, 30)]
PING_SEITE = [(-20, 7), (18, 7), (25, 30), (26, 60), (21, 86), (19, 95), (29, 95.5), (30.5, 94.5), (21, 91.5),
              (18, 99), (8, 107), (-6, 104), (-16, 90), (-22, 60), (-24, 30), (-24, 12)]


def _pinguin(cfg, asm, k, schal, details, notes):
    from models import _deko as dk
    f = K.Figur().add(K.spline(_s(PING_VORNE, k), closed=True, n=8))
    for sx in (-1, 1):
        f.add(F_.linse(sx * 15 * k, 4 * k, 16 * k, 8 * k, 0.0))                       # Füße
        f.add(F_.linse(sx * 33 * k, 56 * k, 30 * k, 9 * k, sx * math.radians(70)))   # Flügel
    pv = _raster_teil(cfg, "pinguin_vorne", f, (-48 * k, -3, 48 * k, 112 * k), notes)
    y_m = 56 * k
    vq = _mit_schlitzen(cfg, pv, [("kreuz", 0.0, y_m, True)])
    cv = dk.Canvas(vq, margin=0.5)
    cv.draw(K.spline(_s([(-18, 12), (-23, 40), (-20, 70), (-12, 88), (12, 88), (20, 70), (23, 40), (18, 12)],
                        k), closed=True, n=8), True)                                     # weißer Bauch
    for sx in (-1, 1):
        cv.draw(F_.kreis(sx * 8 * k, 94 * k, 2.0 * k, 16), True)
    cv.draw([(-4 * k, 88 * k), (4 * k, 88 * k), (0, 82 * k), (-4 * k, 88 * k)])
    if schal:
        cv.draw(K.spline(_s([(-25, 80), (0, 75), (25, 80)], k), n=8))
        cv.draw(K.spline(_s([(-27, 72), (0, 67), (27, 72)], k), n=8))
        cv.draw(K.spline(_s([(12, 70), (16, 52), (12, 40)], k), n=6))
    if details:
        for sx in (-1, 1):
            for d in (-3, 0, 3):
                cv.draw([(sx * 15 * k + d * k, 1.5 * k), (sx * 15 * k + d * k * 0.6, 5 * k)])
    asm.parts.append(vq)
    f = K.Figur().add(K.spline(_s(PING_SEITE, k), closed=True, n=8))
    f.add(F_.linse(4 * k, 4 * k, 26 * k, 8 * k, 0.0))
    ps = _raster_teil(cfg, "pinguin_seite", f, (-36 * k, -3, 40 * k, 112 * k), notes, 0.6)
    sq = _mit_schlitzen(cfg, ps, [("kreuz", 0.0, y_m, False)])
    cv = dk.Canvas(sq, margin=0.5)
    cv.draw(F_.kreis(12 * k, 96 * k, 2.0 * k, 16), True)
    cv.draw(K.spline(_s([(-14, 66), (-6, 50), (-6, 30), (-12, 20)], k), n=8))         # Flügel
    cv.draw(K.spline(_s([(16, 86), (22, 60), (20, 30), (14, 12)], k), n=8))           # Bauchlinie
    if schal:
        cv.draw(K.spline(_s([(-18, 82), (0, 78), (22, 82)], k), n=8))
        cv.draw(K.spline(_s([(-20, 74), (0, 70), (24, 74)], k), n=8))
    asm.parts.append(sq)
    asm.connect("pinguin_vorne:kreuz", "pinguin_seite:kreuz")


def build(cfg, name: str = "steck_tiere", tier: str = "rentier", groesse: float = 120.0, schal: bool = True,
          details: bool = True):
    if tier not in dict(TIERE):
        raise ValueError(f"Unbekanntes Tier {tier!r}")
    k = cfg.s(groesse) / 120.0
    asm = Assembly(name, params=dict(tier=tier, groesse=120 * k))
    notes: List[str] = []
    if tier == "pinguin":
        _pinguin(cfg, asm, k, schal, details, notes)
        how = "Vorderteil (Schlitz oben) von oben auf das Seitenteil (Schlitz unten) stecken."
    else:
        _vierbeiner(cfg, asm, tier, k, schal, details, notes)
        how = "Die beiden Beinpaare von unten quer in die Schlitze im Körper stecken."
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append(how)
    asm.notes.append("Gravur nur ganz leicht, dann können Kinder Augen, Schal und Nase ausmalen.")
    if cfg.T > 1.0:
        asm.notes.append(f"Tipp: Gedacht für Karton 300 g (ca. 0,5 mm) – eingestellt sind {cfg.T:g} mm.")
    return asm
