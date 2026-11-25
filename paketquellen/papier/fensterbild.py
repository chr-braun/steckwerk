"""
Fensterbild zum Hinterkleben – Scherenschnitt-Szene in einem Rahmen, die Öffnungen werden mit
Transparentpapier hinterklebt.

Szenen: Winterdorf (Häuser mit leuchtenden Fenstern, Tannen, Mondsichel, hängende Sterne) und
Tannenwald (Tannen, Reh, Mond, Sterne). Rahmen rechteckig oder mit Rundbogen.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, oriented
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

SZENEN = [("winterdorf", "Winterdorf"), ("tannenwald", "Tannenwald mit Reh")]
FORMEN = [("bogen", "Rundbogen"), ("rechteck", "Rechteck")]

INFO = dict(
    label="Fensterbild",
    group="Papier",
    desc="Scherenschnitt-Fensterbild im Rahmen zum Hinterkleben mit Transparentpapier: Winterdorf oder "
         "Tannenwald, mit Mondsichel und hängenden Sternen.",
    params=[
        sel("szene", "Szene", SZENEN, "winterdorf"),
        sel("form", "Rahmen", FORMEN, "bogen"),
        num("breite", "Breite", 200, 120, 280),
        num("hoehe", "Höhe", 260, 150, 290),
        flag("sterne", "Hängende Sterne", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Fensterbild": "Window picture", "Papier": "Paper",
    "Scherenschnitt-Fensterbild im Rahmen zum Hinterkleben mit Transparentpapier: Winterdorf oder "
    "Tannenwald, mit Mondsichel und hängenden Sternen.":
        "Paper-cut window picture in a frame to back with tracing paper: winter village or fir forest, "
        "with crescent moon and hanging stars.",
    "Szene": "Scene", "Winterdorf": "Winter village", "Tannenwald mit Reh": "Fir forest with deer",
    "Rahmen": "Frame", "Rundbogen": "Round arch", "Rechteck": "Rectangle", "Breite": "Width", "Höhe": "Height",
    "Hängende Sterne": "Hanging stars",
}}


def _umriss(form, B, H, r=0.0):
    if form == "rechteck":
        return K.rect(-B / 2, 0, B, H) if r <= 0 else _rundrect(-B / 2, 0, B / 2, H, r)
    R = B / 2
    pts = [(-R, 0), (R, 0)]
    pts += [(R * math.cos(a), H - R + R * math.sin(a)) for a in [math.pi * i / 48 for i in range(49)]]
    return pts


def _rundrect(x0, y0, x1, y1, r):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        pts += [(cx + r * math.cos(math.radians(a0 + 90 * i / 8)), cy + r * math.sin(math.radians(a0 + 90 * i / 8)))
                for i in range(9)]
    return pts


def _tanne(cx, y0, h, b):
    """Tanne aus vier Ast-Etagen (einzelne Dreiecke mit leicht geschwungener Unterkante) und Stamm."""
    out = [K.rect(cx - b * 0.5, y0 - h * 0.18, b, h * 0.2)]                 # Sockel, verschwindet im Hügel
    for i in range(4):
        y = y0 + h * (0.0 + 0.19 * i)
        w = b / 2 * (1 - 0.2 * i)
        th = h - (y - y0) if i == 3 else h * 0.4
        unten = [(cx + w * t, y + (h * 0.05 * (1 - t * t) if i else 0.0)) for t in [-1 + 2 * j / 12 for j in range(13)]]
        out.append(unten + [(cx, y + th)])
    return out


def _haus(cx, y0, b, h, steg):
    """Haus mit Satteldach und Schornstein; liefert (Umriss, Fensterlöcher)."""
    dach = b * 0.55
    um = [(cx - b / 2, y0 - 3), (cx + b / 2, y0 - 3), (cx + b / 2, y0 + h), (cx + b / 2 + b * 0.08, y0 + h),
          (cx, y0 + h + dach), (cx - b / 2 - b * 0.08, y0 + h)]
    schorn = K.rect(cx + b * 0.18, y0 + h + dach * 0.3, b * 0.12, dach * 0.62)
    loecher = []
    fw = b * 0.2
    for fx in (-0.24, 0.24):
        x = cx + fx * b
        y = y0 + h * 0.5
        for dx in (-1, 1):                                                         # vier Scheiben
            for dy in (-1, 1):
                x0 = x + (steg / 2 if dx > 0 else -fw / 2)
                y1 = y + (steg / 2 if dy > 0 else -fw * 0.6)
                loecher.append(K.rect(x0, y1, fw / 2 - steg / 2, fw * 0.6 - steg / 2))
    tuer = [(cx - b * 0.09, y0 + 1), (cx + b * 0.09, y0 + 1), (cx + b * 0.09, y0 + h * 0.32), (cx, y0 + h * 0.4),
            (cx - b * 0.09, y0 + h * 0.32)]
    loecher.append(F_.kreis(cx, y0 + h + dach * 0.42, b * 0.07, 20))                      # Giebelfenster
    return [um, schorn], loecher, tuer


def _reh(x, y, s):
    """Stehendes Reh als Silhouette (nach rechts schauend), Füße bei y."""
    p = [(14.5, 0), (15, 9), (14.6, 18), (16, 24), (19.5, 34), (22, 43), (24, 46.2), (30, 46.4), (30.5, 48),
         (27, 50.5), (24, 52.5), (20.5, 51), (18, 46), (16, 38), (13, 32), (8, 31), (0, 30.4), (-14, 30.6),
         (-18, 29.6), (-21.5, 29.5), (-19.6, 27), (-20, 23), (-18.5, 18), (-18, 9), (-16.5, 0), (-15, 0),
         (-15.8, 9), (-14.5, 17.5), (-13.6, 17), (-13, 9), (-11.5, 0), (-10, 0), (-11, 9), (-11, 18),
         (-8, 18.6), (6, 18.6), (9.2, 17.5), (9.6, 9), (11, 0), (12.4, 0), (11, 9), (11.3, 15), (12.2, 10),
         (12.8, 0)]
    out = [[(x + px * s, y + py * s) for px, py in p]]
    out.append(F_.linse(x + 18.5 * s, y + 52.5 * s, 7 * s, 2.6 * s, math.radians(125)))   # Ohr
    return out


def build(cfg, name: str = "fensterbild", szene: str = "winterdorf", form: str = "bogen", breite: float = 200.0,
          hoehe: float = 260.0, sterne: bool = True):
    if szene not in dict(SZENEN):
        raise ValueError(f"Unbekannte Szene {szene!r}")
    if form not in dict(FORMEN):
        raise ValueError(f"Unbekannte Rahmenform {form!r}")
    B, H = cfg.s(breite), cfg.s(hoehe)
    if form == "bogen":
        H = max(H, B * 0.75)
    steg = max(1.6, cfg.min_web + cfg.kerf + 0.9)
    rahmen = max(7.0, B * 0.04)
    asm = Assembly(name, params=dict(szene=szene, form=form, breite=B, hoehe=H))
    notes: List[str] = []
    fig = K.Figur()
    fig.add(_umriss(form, B, H, 4.0))
    innen_b, innen_h = B - 2 * rahmen, H - 2 * rahmen
    innen = [(x, y + rahmen) for x, y in _umriss(form, innen_b, innen_h, 2.0)]
    fig.cut(innen)
    # Hügel
    y_boden = rahmen + innen_h * 0.14
    hug = [(-B / 2, 0)] + [(x, y_boden + innen_h * 0.05 * math.sin(x / B * 5.0 + 0.6))
                           for x in [-B / 2 + B * i / 40 for i in range(41)]] + [(B / 2, 0)]
    fig.add(hug)

    def boden(x):
        return y_boden + innen_h * 0.05 * math.sin(x / B * 5.0 + 0.6)

    loecher = []
    if szene == "winterdorf":
        for fx, fb, fh in ((-0.25, 0.2, 0.17), (0.02, 0.24, 0.22), (0.28, 0.18, 0.15)):
            cx = fx * B
            um, l, tuer = _haus(cx, boden(cx) - 2, fb * B, fh * innen_h, steg)
            for u in um:
                fig.add(u)
            loecher += l + [tuer]
        for fx, fh in ((-0.39, 0.3), (-0.12, 0.22), (0.16, 0.26), (0.40, 0.33), (-0.05, 0.12)):
            cx = fx * B
            for t in _tanne(cx, boden(cx) - 2, fh * innen_h, fh * innen_h * 0.62):
                fig.add(t)
    else:
        for fx, fh in ((-0.38, 0.5), (-0.24, 0.36), (-0.14, 0.24), (0.27, 0.4), (0.4, 0.55), (0.18, 0.2)):
            cx = fx * B
            for t in _tanne(cx, boden(cx) - 2, fh * innen_h, fh * innen_h * 0.5):
                fig.add(t)
        for t in _reh(0.02 * B, boden(0.02 * B) - 1, innen_b / 170):
            fig.add(t)
    # Mondsichel, mit dem Rahmen verbunden
    mr = innen_b * 0.1
    if form == "bogen":
        R = innen_b / 2
        cy = rahmen + innen_h - R
        a = math.radians(42)
        mx, my = (R - mr * 1.7) * math.cos(a), cy + (R - mr * 1.7) * math.sin(a)
        ende = ((R + rahmen * 0.5) * math.cos(a), cy + (R + rahmen * 0.5) * math.sin(a))
    else:
        mx, my = innen_b / 2 - mr * 1.8, H - rahmen - mr * 1.9
        ende = (B / 2 - rahmen * 0.5, my)
    fig.add(K.stroke([(mx, my), ende], steg * 1.6))
    fig.add(F_.kreis(mx, my, mr, 48))
    fig.cut(F_.kreis(mx - mr * 0.45, my + mr * 0.25, mr * 0.82, 48))
    # hängende Sterne an Fäden
    if sterne:
        oben = H - rahmen if form == "rechteck" else None
        for fx, fl, fs in ((-0.3, 0.16, 0.05), (-0.12, 0.26, 0.04), (0.08, 0.12, 0.045)):
            x = fx * innen_b
            if form == "bogen":
                R = innen_b / 2
                top = rahmen + innen_h - R + math.sqrt(max(0.0, R * R - x * x))
            else:
                top = oben
            ys = top - fl * innen_h
            fig.add(K.stroke([(x, top + 2), (x, ys)], steg))
            fig.add(F_.stern(x, ys - fs * innen_b * 0.8, fs * innen_b, fs * innen_b * 0.45))
    for l in loecher:
        fig.cut(l)
    box = (-B / 2 - 3, -3, B / 2 + 3, H + 3)
    lw = E.Leinwand(box, W.px_fuer(max(B, H)))
    mat = lw.leer()
    for op, poly in fig.ops:                     # jede Fläche einzeln, damit Überlappungen sicher vereinigt werden
        r = lw.flaechen([oriented(list(poly), True)])
        mat = mat.union(r) if op == "+" else E._andnot(mat, r)
    mat = E._and(mat, lw.flaechen([oriented(_umriss(form, B, H, 4.0), True)]))    # nichts ragt über den Rand
    mat = mat.close(lw.px_fuer(0.5)).open(lw.px_fuer(0.7))
    p = E.teil_aus_raster("fensterbild", lw, mat, cfg.min_web, cfg.kerf, notes)
    asm.parts.append(p)
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes += [
        "Von hinten Transparentpapier aufkleben: Himmel blau oder lila, Fenster gelb, Mond und Sterne hell.",
        "Am schönsten aus schwarzem oder dunkelblauem Tonpapier.",
    ]
    if cfg.T > 1.0:
        asm.notes.append(f"Tipp: Gedacht für Tonpapier oder Karton (ca. 0,3–0,5 mm) – eingestellt sind {cfg.T:g} mm.")
    return asm
