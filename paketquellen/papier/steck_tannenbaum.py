"""
Steck-Tannenbaum – Bastelset für Kinder aus Karton, ohne Schere und ohne Kleber.

Zwei Baumhälften werden über Kreuz gesteckt und stehen dann von allein. Anhänger (Kugel, Stern, Herz)
werden mit ihrem Schlitz auf die Astspitzen geschoben, der Stern kommt auf die Spitze. Leicht gravierte
Girlanden, Kugeln und Stammmaserung laden zum Ausmalen ein. Alle Spitzen sind gerundet.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, JointFeature, Part
from pakete import flag, integer, num, sel

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

FORMEN = [("gemischt", "Kugel, Stern und Herz"), ("kugel", "nur Kugeln"), ("stern", "nur Sterne"),
          ("herz", "nur Herzen")]

INFO = dict(
    label="Steck-Tannenbaum",
    group="Papier",
    desc="Bastelset für Kinder: zwei Baumhälften aus Karton über Kreuz gesteckt, mit Anhängern zum Einhängen, "
         "Stern für die Spitze und Linien zum Ausmalen – ohne Schere und ohne Kleber.",
    params=[
        num("groesse", "Höhe", 220, 120, 320),
        integer("anhaenger", "Anhänger", 18, 0, 36),
        sel("formen", "Anhänger-Formen", FORMEN, "gemischt"),
        flag("fenster", "Sterne und Kreise ausschneiden", True),
        flag("ausmalen", "Ausmal-Linien gravieren", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Steck-Tannenbaum": "Slot-together Christmas tree", "Papier": "Paper",
    "Bastelset für Kinder: zwei Baumhälften aus Karton über Kreuz gesteckt, mit Anhängern zum Einhängen, "
    "Stern für die Spitze und Linien zum Ausmalen – ohne Schere und ohne Kleber.":
        "Craft kit for children: two card tree halves slotted crosswise, with ornaments to hang, a star for the top "
        "and lines to colour in – no scissors, no glue.",
    "Höhe": "Height", "Anhänger": "Ornaments", "Anhänger-Formen": "Ornament shapes",
    "Kugel, Stern und Herz": "Bauble, star and heart", "nur Kugeln": "baubles only", "nur Sterne": "stars only",
    "nur Herzen": "hearts only", "Sterne und Kreise ausschneiden": "Cut out stars and circles",
    "Ausmal-Linien gravieren": "Engrave colouring lines",
}}


def _tiers(k: float):
    H, B = 220.0 * k, 160.0 * k
    sh = 22.0 * k
    return H, B, sh, [(sh, B / 2, 70 * k), (sh + 48 * k, B * 0.40, 62 * k), (sh + 92 * k, B * 0.30, 56 * k),
                      (sh + 132 * k, B * 0.20, H - (sh + 132 * k))]


def _stufe(y0, hw, ht, k):
    pts = [(-hw + t * 2 * hw, y0 + 3.5 * k * math.sin(t * math.pi)) for t in [i / 19 for i in range(20)]]
    side = [(hw * (1 - t), y0 + ht * t - 2.5 * k * math.sin(t * math.pi)) for t in [i / 15 for i in range(16)]]
    return pts + side[1:] + [(-x, y) for x, y in reversed(side[:-1])]


def _kante(tiers, y):
    """Halbe Baumbreite auf Höhe y (schmalste Stelle der Stufen, die dort liegen)."""
    w = 0.0
    for y0, hw, ht in tiers:
        if y0 + 4 <= y <= y0 + ht:
            w = max(w, hw * (1 - (y - y0) / ht) - 3.0)
    return w


def _baum(cfg, name: str, k: float, oben: bool, fenster: bool, ausmalen: bool, notes) -> Part:
    from models._shapes import cut_axis_slot
    T = cfg.T
    H, B, sh, tiers = _tiers(k)
    sw = 26 * k
    fig = K.Figur()
    fig.add(K.rect(-sw / 2, 0, sw, sh + 4 * k))
    for y0, hw, ht in tiers:
        fig.add(_stufe(y0, hw, ht, k))
    band = T / 2 + max(3.0, 2 * cfg.min_web)
    fenster_ = []
    if fenster:
        rand = max(4.0 * k, 3 * (cfg.min_web + cfg.kerf))
        for i, (y0, hw, ht) in enumerate(tiers):
            for j, (f, fx) in enumerate([(0.30, 0.52), (0.62, 0.42)][:2 if i < 3 else 1]):
                y = y0 + ht * f
                kante = _kante(tiers, y)
                s = max(min(8.0 * k, (kante - band) * 0.26), 2.2 * (cfg.min_web + cfg.kerf))
                x = band + s + (kante - band - 2 * s) * fx
                if x + s > kante - rand or x - s < band + rand:
                    continue
                for sx in (-1, 1):
                    stern = (i + j + (sx > 0)) % 2 == 0
                    fenster_.append(F_.stern(sx * x, y, s, s * 0.48) if stern else F_.kreis(sx * x, y, s * 0.7, 32))
    lw = E.Leinwand((-B / 2 - 4, -4, B / 2 + 4, H + 4), W.px_fuer(H))
    mat = lw.figur(fig)
    mat = mat.close(lw.px_fuer(2.0 * k)).open(lw.px_fuer(1.6 * k))      # weiche Innenecken, runde Spitzen
    if fenster_:
        mat = E._andnot(mat, lw.flaechen(fenster_))
    p = E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes, unten_flach=True)
    y_mid = sh + (H - sh) / 2
    out, slot = cut_axis_slot(p.outline, T, y_mid, oben)
    ys = [q[1] for q in p.outline]
    span = (y_mid, max(ys)) if oben else (min(ys), y_mid)
    q = Part(name, out, features=[JointFeature("kreuz", "halving", span[1] - span[0], T, span=span, points=slot)])
    for h in p.holes:
        q.add_hole(h)
    if ausmalen:
        from models import _deko as dk
        cv = dk.Canvas(q, margin=0.8)
        cv.block(K.rect(-band, 0, 2 * band, H + 2))
        for y0, hw, ht in tiers[:3]:
            yy = y0 + ht * 0.38
            w = hw * 0.62 * 0.9
            cv.draw([(-w + 2 * w * i / 59, yy + 3 * k * math.cos((-w + 2 * w * i / 59) / w * math.pi) - 4 * k)
                     for i in range(60)])
        for x, y in [(-48, 34), (46, 38), (-30, 74), (32, 80), (-10, 118), (20, 118), (-24, 30), (22, 104), (8, 160)]:
            c = F_.kreis(x * k, y * k, 4.2 * k, 28)
            if cv.fits(c, True):
                cv.draw(c, True)
        cv.draw(K.rect(-sw / 2 + 4 * k, 4 * k, sw - 8 * k, sh - 6 * k), True)
        for j in range(3):
            x = -sw / 2 + 7 * k + j * 6 * k
            cv.draw([(x, 6 * k), (x + 1.5 * k, sh - 4 * k)])
    return q


def _anhaenger(cfg, name: str, form: str, s: float, notes) -> Part:
    T = cfg.T
    fig = K.Figur()
    if form == "kugel":
        fig.add(F_.kreis(0, 0, s / 2, 48))
        fig.add(K.rect(-3.5 * s / 24, s / 2 - 1.5, 7 * s / 24, 5 * s / 24 + 1.5))
        top = s / 2 + 5 * s / 24
    elif form == "stern":
        fig.add(F_.stern(0, 0, s * 0.58, s * 0.29))
        top = s * 0.58
    else:
        pts = [(16 * math.sin(t) ** 3, 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
               for t in [2 * math.pi * i / 80 for i in range(80)]]
        f = s * 1.05 / 32
        pts = [(x * f, y * f - 1) for x, y in pts]
        fig.add(pts)
        top = max(y for _, y in pts) - 2.5 * f
    sl = max(T, 0.6)
    fig.cut(K.rect(-sl / 2, top - 0.3 * s, sl, 0.3 * s + 5))
    lw = E.Leinwand((-s, -s, s, s), W.px_fuer(2 * s))
    mat = lw.figur(fig).open(lw.px_fuer(0.8))
    p = E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes)
    from models import _deko as dk
    cv = dk.Canvas(p, margin=0.6)
    if form == "kugel":
        for dy in (3, -3):
            cv.draw([(x, dy * s / 24 + 1.6 * s / 24 * math.sin(x / 2)) for x in
                     [-s / 2 + 1.5 + (s - 3) * i / 29 for i in range(30)]])
    elif form == "stern":
        cv.draw(F_.stern(0, 0, s * 0.3, s * 0.14), True)
    else:
        f = s * 0.6 / 32
        inner = [(16 * math.sin(t) ** 3 * f, (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t)
                  - math.cos(4 * t)) * f - 1) for t in [2 * math.pi * i / 60 for i in range(60)]]
        cv.draw(inner, True)
    return p


def _spitze(cfg, name: str, s: float, notes) -> Part:
    T = cfg.T
    fig = K.Figur().add(F_.stern(0, 0, s, s * 0.46))
    sl = max(T, 0.6)
    fig.cut(K.rect(-sl / 2, -s - 2, sl, s * 1.25))
    lw = E.Leinwand((-s - 3, -s - 3, s + 3, s + 3), W.px_fuer(2 * s))
    mat = lw.figur(fig).open(lw.px_fuer(0.9))
    p = E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes)
    from models import _deko as dk
    dk.Canvas(p, margin=0.6).draw(F_.stern(0, 0, s * 0.5, s * 0.23), True)
    return p


def build(cfg, name: str = "steck_tannenbaum", groesse: float = 220.0, anhaenger: int = 18,
          formen: str = "gemischt", fenster: bool = True, ausmalen: bool = True):
    if formen not in dict(FORMEN):
        raise ValueError(f"Unbekannte Anhänger-Form {formen!r}")
    k = cfg.s(groesse) / 220.0
    asm = Assembly(name, params=dict(groesse=220 * k, anhaenger=anhaenger, formen=formen))
    notes: List[str] = []
    asm.parts.append(_baum(cfg, "baum_a", k, True, fenster, ausmalen, notes))
    asm.parts.append(_baum(cfg, "baum_b", k, False, fenster, ausmalen, notes))
    asm.connect("baum_a:kreuz", "baum_b:kreuz")
    s = max(16.0, 24 * k)
    folge = ["kugel", "stern", "herz"] if formen == "gemischt" else [formen]
    vorlagen = {f: _anhaenger(cfg, f, f, s, notes) for f in dict.fromkeys(folge[:max(1, min(anhaenger, 3))])}
    for i in range(int(anhaenger)):
        f = folge[i % len(folge)]
        v = vorlagen[f]
        asm.parts.append(Part(f"{f}_{i + 1}", list(v.outline), [list(h) for h in v.holes],
                              [type(st)(list(st.points), st.closed) for st in v.engrave]))
    asm.parts.append(_spitze(cfg, "stern_spitze", max(16.0, 24 * k), notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Baum A (Schlitz oben) von oben auf Baum B (Schlitz unten) stecken – fertig steht der Baum.")
    asm.notes.append("Anhänger mit dem Schlitz auf die Astspitzen schieben, den Stern oben auf die Spitze stecken.")
    asm.notes.append("Ausmal-Linien nur ganz leicht gravieren, sonst wird der Karton braun.")
    if cfg.T > 1.0:
        asm.notes.append(f"Tipp: Gedacht für Karton 300 g (ca. 0,5 mm) – eingestellt sind {cfg.T:g} mm.")
    return asm
