"""
_spuk.py – fein gezeichnete Halloween-Figuren für das Raster-Verfahren (siehe _kit.py und _ebenen.py).

Jede Figur ist eine _kit.Figur in mm: Flächen werden hinzugefügt (+) oder weggeschnitten (−). Aus der
Figur macht teil() ein laserfestes Teil: zu schmale Stege und Schlitze werden ausgeglichen, lose Inseln
entfallen, runde Löcher (Gelenke, Auffädellöcher) werden danach exakt eingesetzt.

  fledermaus   vier Flügelhaltungen, Flügelknochen als feine Schlitze, Ohren, Augen, Füße, Schwanzflughaut
  kuerbis      Rippen-Buckel, Stiel, Blatt mit Adern, Ranke, geschnitztes Gesicht
  gespenst     mit erhobenen Armen, zerfranstem Saum, Augen und heulendem Mund
  spinne       Kreuzspinne mit gegliederten Beinen, Tastern und Rückenzeichnung
  netz         Spinnennetz: Speichen, durchhängende Fangfäden, Nabe, Tautropfen, gerissene Stellen
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Optional, Sequence, Tuple

from steckwerk import Part, min_distance, oriented, point_in_polygon
from pakete import bibliothek

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_halloween_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


K = bibliothek("verzierungen").K
E = bibliothek("verzierungen").E
E.MIN_LOCH = 1.6        # Augen und Zähnchen der Figuren sollen bleiben (kompensiert noch > 1 mm²)
Figur = K.Figur
Point = Tuple[float, float]
Poly = List[Point]
TAU = 2 * math.pi


# --------------------------------------------------------------------------------------------------
# Laser-Grundmaße und Teil aus Figur
# --------------------------------------------------------------------------------------------------

def wmin(cfg) -> float:
    """Schmalster Steg, der das Ausgleichen der Leinwand auch schräg liegend sicher übersteht
    (das Raster rundet achteckig, schräge Stege brauchen etwas mehr als web + kerf + 0.45)."""
    return cfg.min_web + cfg.kerf + 0.75


def smin(cfg) -> float:
    """Schmalster Schlitz, der als Durchbruch erhalten bleibt."""
    return max(cfg.kerf + 0.75, 0.95)


def rot(p: Point, a: float, c: Point = (0.0, 0.0)) -> Point:
    x, y = p[0] - c[0], p[1] - c[1]
    ca, sa = math.cos(a), math.sin(a)
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def lerp(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def innen(path: Sequence[Point], poly: Sequence[Point], d: float) -> Poly:
    """Längstes Stück der Linie, das überall mindestens d vom Rand von poly entfernt (und innen) liegt."""
    from steckwerk import point_seg_dist
    n = len(poly)
    best, cur = [], []
    for p in path:
        ok = point_in_polygon(p, poly) and min(point_seg_dist(p, poly[i], poly[(i + 1) % n]) for i in range(n)) >= d
        if ok:
            cur.append(p)
            if len(cur) > len(best):
                best = list(cur)
        else:
            cur = []
    return best


def teil(name: str, fig: Figur, cfg, notes: List[str], loecher: Sequence[Tuple[float, float, float]] = (),
         ring: Optional[float] = None, px: Optional[float] = None, unten_flach: bool = False) -> Part:
    """Figur → laserfestes Teil. loecher = [(x, y, durchmesser)] werden exakt rund geschnitten; um jedes
    Loch bleibt ein Ring aus Material (Breite ring, Standard 1,6 × wmin)."""
    web, kerf = cfg.min_web, cfg.kerf
    ring = ring if ring is not None else max(1.6 * wmin(cfg), 2.2)
    f = Figur(list(fig.ops))
    for x, y, d in loecher:
        f.add(K.circle(x, y, d / 2 + ring, 40))
    x0, y0, x1, y1 = f.bbox()
    if px is None:
        px = max(0.06, min(0.12, max(x1 - x0, y1 - y0) / 1800.0))
    lw = E.Leinwand((x0 - 3, y0 - 3, x1 + 3, y1 + 3), px)
    mat = lw.figur(f)
    if loecher:          # Bereich der runden Löcher frei von Rasterlöchern halten
        mat = mat.union(lw.flaechen([K.circle(x, y, d / 2 + ring * 0.9, 40) for x, y, d in loecher]))
    part = E.teil_aus_raster(name, lw, mat, web, kerf, notes, unten_flach)
    for x, y, d in loecher:
        c = oriented(K.circle(x, y, d / 2, max(24, int(d * 8))), False)
        if not point_in_polygon((x, y), part.outline) or min_distance(c, part.outline, limit=web + 0.3) < web + 0.2:
            raise ValueError(f"{name}: Loch Ø {d:g} mm passt nicht – Teil größer oder Loch kleiner wählen")
        part.holes = [h for h in part.holes
                      if min_distance(h, c, limit=web + 0.3) >= web + 0.2 and not point_in_polygon(h[0], c)
                      and not point_in_polygon((x, y), h)]
        part.add_hole(c)
    return part


def gravur(part: Part, linien: Sequence[Tuple[Sequence[Point], bool]], seed: int = 1, rand: float = 0.9) -> None:
    """Gravurlinien kollisionsfrei setzen (werden an Rand und Durchbrüchen abgeschnitten)."""
    from models import _deko as dk
    cv = dk.Canvas(part, margin=rand, hole_margin=rand, seed=seed)
    for pts, closed in linien:
        if len(pts) >= 2:
            cv.draw(list(pts), closed)


def eingepasst(fig: Figur, groesse: float, cx: float = 0.0, cy: float = 0.0) -> Figur:
    """Figur so skalieren und verschieben, dass ihre größte Abmessung = groesse ist (Mitte cx, cy)."""
    x0, y0, x1, y1 = fig.bbox()
    k = groesse / max(x1 - x0, y1 - y0)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    T = lambda p: (cx + (p[0] - mx) * k, cy + (p[1] - my) * k)
    out = fig.map(T)
    out.gravur = [([T(q) for q in pts], c) for pts, c in getattr(fig, "gravur", [])]
    if getattr(fig, "gloeckchen", None):
        gx, gy, gr = fig.gloeckchen
        out.gloeckchen = T((gx, gy)) + (gr * k,)
    return out


# --------------------------------------------------------------------------------------------------
# Fledermaus
# --------------------------------------------------------------------------------------------------

POSEN = [("segeln", "Segeln (Flügel ausgebreitet)"), ("hoch", "Flügel hoch"), ("tief", "Flügel tief"),
         ("kurve", "In der Kurve (ein Flügel hoch)")]

# rechter Flügel ausgebreitet, Einheit = halbe Spannweite
_SH, _EL, _WR = (0.085, 0.045), (0.34, 0.20), (0.58, 0.27)
_TIPS = [(1.00, 0.17), (0.95, -0.08), (0.76, -0.27), (0.48, -0.33)]
_ANK = (0.075, -0.22)


def _fluegel(pose: str) -> Tuple[Point, Point, List[Point], Point, Point]:
    """Ellbogen, Handgelenk, Fingerspitzen, Daumen eines rechten Flügels für eine Haltung."""
    a, fold = {"segeln": (0.0, 0.0), "hoch": (math.radians(40), math.radians(16)),
               "tief": (math.radians(-30), math.radians(-12)), "mitte": (math.radians(14), 0.0)}[pose]
    el, wr = rot(_EL, a, _SH), rot(_WR, a, _SH)
    tips = [rot(rot(t, a, _SH), fold * (0.4 + 0.25 * i), wr) for i, t in enumerate(_TIPS)]
    if pose == "hoch":                       # Hinterkante zieht zur Flanke, letzte Spitze tiefer
        tips[3] = lerp(tips[3], (0.30, -0.10), 0.35)
    thumb = rot((0.615, 0.325), a, _SH)
    return el, wr, tips, thumb, _ANK


def _bogen(a: Point, b: Point, zug: Point, tiefe: float, n: int = 10) -> Poly:
    """Flughaut-Bogen von a nach b, zur Stelle zug hin eingezogen."""
    m = lerp(a, b, 0.5)
    c = lerp(m, zug, tiefe)
    return K.bez(a, c, b, n)


def fledermaus(S: float, pose: str, cfg, augen: bool = True) -> Tuple[Figur, List[Point]]:
    """Fledermaus mit Spannweite ~S (mm), Mitte 0/0. Liefert (Figur, zwei Auffädelpunkte)."""
    s = S / 2
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    sides = {"kurve": ("hoch", "mitte")}.get(pose, (pose, pose))
    slits: List[Poly] = []
    lines_k = []
    for side, ps in zip((1, -1), sides):
        el, wr, tips, thumb, ank = _fluegel(ps)
        X = lambda p: (side * p[0] * s, p[1] * s)
        # Vorderkante: Oberarm, Unterarm, langer Finger – leicht gewölbt
        lead = K.spline([_SH, lerp(_SH, el, 0.5), el, lerp(el, wr, 0.5), wr,
                         lerp(wr, tips[0], 0.5), tips[0]], n=6)
        edge = list(lead)
        zug = lerp(wr, _SH, 0.25)
        for i in range(3):
            edge += _bogen(tips[i], tips[i + 1], zug, 0.30 + 0.04 * i, 12)[1:]
        edge += _bogen(tips[3], ank, lerp(_SH, (0.2, 0.0), 0.5), 0.30, 12)[1:]
        edge += [(0.04, -0.12), (0.03, 0.02)]
        f.add([X(p) for p in edge])
        # kräftiger Armknochen an der Vorderkante, Ellbogen- und Handgelenkknöchel
        f.line([X(p) for p in K.spline([_SH, el, wr], n=8)], max(0.045 * s, w))
        f.add(K.circle(*X(el), max(0.03 * s, w * 0.6), 20), K.circle(*X(wr), max(0.032 * s, w * 0.6), 20))
        # Daumenkralle
        f.line([X(wr), X(thumb), X(lerp(thumb, (thumb[0] + 0.03, thumb[1] - 0.01), 1.0))], max(0.022 * s, w), w * 0.7,
               cap="spitz")
        # Fingerknochen als Schlitze (beginnen dort, wo sie weit genug auseinander liegen)
        for i, t in enumerate(tips):
            L = math.hypot(t[0] - wr[0], t[1] - wr[1]) * s
            a0 = max(0.16, (w + sw) * 1.5 / max(L * 0.42, 1e-6))
            if i == 0 or 0.86 - a0 < 0.15:
                continue
            mid = lerp(wr, t, 0.5)
            off = (-(t[1] - wr[1]) * 0.05, (t[0] - wr[0]) * 0.05)
            path = K.bez(lerp(wr, t, a0), (mid[0] + off[0], mid[1] + off[1]), lerp(wr, t, 0.86), 24)
            path = innen([X(p) for p in path], [X(p) for p in edge], w + sw / 2 + 0.6)
            if len(path) >= 2 and K.path_len(path) >= 2.5:
                slits.append(K.stroke(path, sw, sw * 0.9, "rund"))
        # Falten der Flughaut (Gravur)
        for i in range(3):
            m = lerp(tips[i + 1], tips[i], 0.5)
            lines_k.append(([X(lerp(wr, m, 0.35)), X(lerp(lerp(wr, m, 0.6), zug, 0.12)), X(lerp(wr, m, 0.78))], False))
    # Körper mit Fellzipfeln, Kopf, Ohren – Kopf mindestens so groß, dass Augen Platz haben
    rx, ry = max(0.02 * s, 1.05), max(0.013 * s, 0.72)
    ex = rx + w / 2 + 0.25
    hr = max(0.085 * s, (ex + rx + w + 0.1) if augen else 2 * w + 1.2)
    hy = 0.075 * s + hr * 0.35
    body = []
    for i in range(48):
        t = TAU * i / 48
        r = 1.0 + (0.10 if i % 4 == 0 and math.sin(t) < 0.4 else 0.0)
        body.append((max(0.088 * s, hr * 0.72) * math.cos(t) * r, -0.05 * s + 0.165 * s * math.sin(t) * r))
    f.add(body)
    f.add(K.circle(0.0, hy, hr, 40))
    ew = max(0.075 * s, 2.2 * w)                                  # Ohrbreite am Ansatz
    eh = max(0.17 * s, 2.4 * w)                                   # Ohrhöhe über dem Kopf
    for side in (1, -1):
        X = lambda u, v: (side * u, hy + v)
        f.add(K.chain(K.bez(X(0.10 * hr, 0.6 * hr), X(0.18 * hr + 0.2 * ew, hr + 0.3 * eh),
                            X(0.45 * hr + 0.75 * ew, hr + eh), 8),
                      K.bez(X(0.45 * hr + 0.75 * ew, hr + eh), X(0.55 * hr + 0.9 * ew, hr + 0.3 * eh),
                            X(1.0 * hr, 0.45 * hr), 8), [X(0.9 * hr, 0.0)]))
        # Füße mit Krallen
        foot = (side * 0.035 * s, -0.23 * s)
        f.line([(side * 0.03 * s, -0.17 * s), foot], max(0.035 * s, w * 1.1))
        if 0.012 * s >= w * 0.8:
            for k in (-1, 0, 1):
                f.line([foot, (foot[0] + side * (0.014 + 0.014 * k) * s, foot[1] - 0.045 * s)], max(0.012 * s, w),
                       cap="spitz")
    # Schwanzflughaut zwischen den Füßen
    f.add(K.chain([(-0.075 * s, -0.20 * s), (0.075 * s, -0.20 * s)],
                  K.bez((0.075 * s, -0.20 * s), (0.0, -0.27 * s), (-0.075 * s, -0.20 * s), 10)))
    for sl in slits:
        f.cut(sl)
    if augen:
        ey = hy + 0.15 * hr
        if ex + rx + w <= hr:
            for side in (1, -1):
                f.cut(K.ellipse(side * ex, ey, rx, ry, side * math.radians(-22), 24))
            # Mund mit zwei Zähnchen, wenn unter den Augen genug Platz bleibt
            mt = ey - ry - w - 0.3
            mw, mh = max(0.03 * s, 2.2 * sw), max(0.022 * s, 1.6)
            if mt - mh >= hy - hr * 0.9 and mw + w <= hr:
                f.cut([(-mw, mt), (mw, mt), (mw * 0.5, mt - mh), (mw * 0.28, mt - mh * 0.45),
                       (-mw * 0.28, mt - mh * 0.45), (-mw * 0.5, mt - mh)])
        # Innenohr nur, wenn das Ohr breit genug ist
        if ew * 0.6 >= sw + 2 * w:
            for side in (1, -1):
                x0 = side * (hr * 0.15 + ew * 0.55)
                f.cut(K.stroke([(x0, hy + hr * 0.9), (x0 + side * ew * 0.15, hy + hr + 0.07 * s)], sw, sw, "rund"))
    f.gravur = lines_k
    hy_ = {"tief": -0.07}.get(pose, 0.035)
    holes = [(-0.24 * s, hy_ * s), (0.24 * s, hy_ * s)]
    return f, holes


# --------------------------------------------------------------------------------------------------
# Kürbis
# --------------------------------------------------------------------------------------------------

def kuerbis(S: float, cfg, gesicht: str = "klassisch", seed: int = 1) -> Tuple[Figur, List[Point]]:
    """Kürbis, Breite ~S, Mitte 0/0, mit Stiel, Blatt, Ranke und Gesicht."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    lobes = [(0.0, 0.0, 0.25, 0.38), (0.19, -0.01, 0.24, 0.36), (-0.19, -0.01, 0.24, 0.36),
             (0.33, -0.03, 0.16, 0.30), (-0.33, -0.03, 0.16, 0.30)]
    for x, y, rx, ry in lobes:
        f.add(K.ellipse(x * s, y * s, rx * s, ry * s, 0.0, 64))
    # Stiel (gebogen, oben schräg abgeschnitten), Blatt, Ranke
    f.line([(0.0, 0.32 * s), (0.01 * s, 0.42 * s), (0.05 * s, 0.50 * s)], 0.085 * s, 0.065 * s, cap="flach")
    f.add([(0.02 * s, 0.53 * s), (0.085 * s, 0.505 * s), (0.07 * s, 0.47 * s), (0.015 * s, 0.48 * s)])
    mid = K.bez((0.05 * s, 0.40 * s), (0.16 * s, 0.50 * s), (0.31 * s, 0.47 * s), 16)
    lw_ = [max(0.12 * s * math.sin(math.pi * (0.08 + 0.92 * i / 16)) ** 0.8, w) *
           (1 + 0.18 * math.sin(i * 1.9)) for i in range(17)]
    f.add(K.stroke(mid, 0, widths=lw_, cap="spitz"))
    f.line(K.spline([(-0.02 * s, 0.37 * s), (-0.10 * s, 0.43 * s), (-0.17 * s, 0.42 * s), (-0.19 * s, 0.37 * s),
                     (-0.15 * s, 0.345 * s), (-0.125 * s, 0.37 * s)], n=8), max(0.018 * s, w))
    # Blattadern als Schlitze, wenn das Blatt breit genug ist
    if 0.12 * s >= sw + 2 * w + 0.8:
        f.cut(K.stroke(mid[3:13], sw, sw * 0.8))
        if 0.12 * s >= 2 * sw + 3 * w + 2:
            for i in (6, 9):
                q = mid[i]
                f.cut(K.stroke([(q[0] + 0.012 * s, q[1] + 0.006 * s), (q[0] + 0.03 * s, q[1] + 0.035 * s)], sw, sw))
    for side in (1, -1):
        for x0, bend in ((0.27, 0.05),):
            path = K.bez((side * x0 * s, 0.22 * s), (side * (x0 + bend) * s, -0.03 * s), (side * x0 * s, -0.27 * s), 14)
            f.cut(K.stroke(path, sw, sw, "rund"))
    # Gesicht
    if gesicht == "klassisch":
        for side in (1, -1):
            f.cut([(side * 0.05 * s, 0.06 * s), (side * 0.19 * s, 0.07 * s), (side * 0.125 * s, 0.19 * s)])
        f.cut([(-0.035 * s, -0.015 * s), (0.035 * s, -0.015 * s), (0.0, 0.05 * s)])
        top = [(-0.21 * s, -0.07 * s), (-0.13 * s, -0.10 * s), (-0.10 * s, -0.06 * s), (-0.065 * s, -0.11 * s),
               (0.065 * s, -0.11 * s), (0.10 * s, -0.06 * s), (0.13 * s, -0.10 * s), (0.21 * s, -0.07 * s)]
        bot = [(0.16 * s, -0.17 * s), (0.08 * s, -0.215 * s), (0.055 * s, -0.17 * s), (0.02 * s, -0.225 * s),
               (-0.06 * s, -0.22 * s), (-0.085 * s, -0.175 * s), (-0.11 * s, -0.205 * s), (-0.16 * s, -0.17 * s)]
        f.cut(top + bot)
    elif gesicht == "gruselig":             # schräge Augen, Fangzähne
        for side in (1, -1):
            f.cut([(side * 0.04 * s, 0.06 * s), (side * 0.20 * s, 0.15 * s), (side * 0.17 * s, 0.04 * s)])
        f.cut([(0.0, 0.03 * s), (0.03 * s, -0.03 * s), (-0.03 * s, -0.03 * s)])
        f.cut([(-0.22 * s, -0.06 * s), (-0.12 * s, -0.11 * s), (-0.10 * s, -0.19 * s), (-0.07 * s, -0.115 * s),
               (0.07 * s, -0.115 * s), (0.10 * s, -0.19 * s), (0.12 * s, -0.11 * s), (0.22 * s, -0.06 * s),
               (0.15 * s, -0.20 * s), (0.0, -0.25 * s), (-0.15 * s, -0.20 * s)])
    gr = [(K.bez((side * 0.12 * s, 0.30 * s), (side * 0.17 * s, 0.05 * s), (side * 0.13 * s, -0.30 * s), 14),
           False) for side in (1, -1)]
    gr += [(K.bez((side * 0.36 * s, 0.18 * s), (side * 0.43 * s, -0.02 * s), (side * 0.37 * s, -0.22 * s), 14), False)
           for side in (1, -1)]
    gr.append((K.arc(-0.06 * s, 0.0, 0.40 * s, math.radians(128), math.radians(150), 10), False))   # Glanzlicht
    gr.append((K.arc(-0.06 * s, 0.0, 0.37 * s, math.radians(131), math.radians(146), 8), False))
    gr.append(([(0.005 * s, 0.34 * s), (0.02 * s, 0.47 * s)], False))                                # Stielfasern
    gr.append(([(0.03 * s, 0.33 * s), (0.045 * s, 0.45 * s)], False))
    f.gravur = gr
    holes = [(-0.30 * s, 0.17 * s), (0.30 * s, 0.17 * s)]
    return f, holes


# --------------------------------------------------------------------------------------------------
# Gespenst
# --------------------------------------------------------------------------------------------------

def gespenst(S: float, cfg, seed: int = 1) -> Tuple[Figur, List[Point]]:
    """Gespenst mit erhobenen Armen, Höhe ~S, Mitte 0/0."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    right = [(0.0, 0.50), (0.13, 0.47), (0.205, 0.37), (0.225, 0.25), (0.29, 0.25), (0.36, 0.30), (0.40, 0.37),
             (0.44, 0.40), (0.445, 0.355), (0.47, 0.33), (0.43, 0.29), (0.40, 0.22), (0.33, 0.15), (0.26, 0.10),
             (0.25, -0.05), (0.28, -0.20), (0.34, -0.32), (0.42, -0.40), (0.47, -0.47), (0.36, -0.445),
             (0.28, -0.40), (0.22, -0.47), (0.15, -0.40), (0.08, -0.48), (0.02, -0.41)]
    left = [(-0.05, -0.47), (-0.11, -0.40), (-0.18, -0.46), (-0.24, -0.38), (-0.30, -0.42), (-0.26, -0.25),
            (-0.24, -0.08), (-0.25, 0.08), (-0.32, 0.13), (-0.40, 0.21), (-0.45, 0.30), (-0.47, 0.36),
            (-0.43, 0.345), (-0.42, 0.40), (-0.38, 0.36), (-0.31, 0.29), (-0.225, 0.25), (-0.205, 0.37),
            (-0.13, 0.47)]
    body = K.spline([(x * s, y * s) for x, y in right + left], closed=True, n=6, tension=0.45)
    f.add(body)
    for side in (1, -1):
        f.cut(K.ellipse(side * 0.075 * s, 0.30 * s, 0.045 * s, 0.07 * s, side * math.radians(10), 32))
    f.cut(K.ellipse(0.0, 0.15 * s, 0.045 * s, 0.07 * s, 0.0, 32))
    # Faltenschlitze im Laken
    for path in (K.bez((0.13 * s, 0.02 * s), (0.16 * s, -0.15 * s), (0.22 * s, -0.31 * s), 12),
                 K.bez((-0.12 * s, 0.0), (-0.14 * s, -0.14 * s), (-0.13 * s, -0.30 * s), 12),
                 K.bez((0.02 * s, -0.08 * s), (0.04 * s, -0.20 * s), (0.08 * s, -0.33 * s), 12)):
        f.cut(K.stroke(path, sw, sw * 0.9))
    f.gravur = [(K.bez((-0.30 * s, 0.20 * s), (-0.36 * s, 0.26 * s), (-0.40 * s, 0.31 * s), 8), False),
                (K.bez((0.30 * s, 0.21 * s), (0.36 * s, 0.27 * s), (0.39 * s, 0.33 * s), 8), False)]
    holes = [(-0.17 * s, 0.15 * s), (0.17 * s, 0.15 * s)]
    return f, holes


# --------------------------------------------------------------------------------------------------
# Spinne
# --------------------------------------------------------------------------------------------------

def spinne(S: float, cfg, cx: float = 0.0, cy: float = 0.0, ang: float = 0.0, zeichnung: bool = True) -> Figur:
    """Kreuzspinne von oben, Beinspanne ~S, Kopf zeigt nach oben (ang dreht), Mitte = Kopfbruststück.
    Gegliederte, geknickte Beine mit Gelenkverdickungen, Taster, Kieferklauen, schlanke Taille,
    großer Hinterleib mit Kreuz und Seitenbändern."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    lw0 = max(0.042 * s, w)
    # Beine: Ansatz, Knie (nach außen hochgezogen), Fersengelenk, Fußspitze (rechts; links gespiegelt)
    legs = [((0.035, 0.055), (0.15, 0.22), (0.20, 0.34), (0.23, 0.47)),
            ((0.05, 0.025), (0.22, 0.14), (0.35, 0.15), (0.47, 0.10)),
            ((0.05, -0.01), (0.21, -0.03), (0.33, -0.13), (0.43, -0.21)),
            ((0.035, -0.04), (0.14, -0.13), (0.19, -0.29), (0.21, -0.45))]
    for side in (1, -1):
        for base, knee, heel, foot in legs:
            P = [(side * x * s, y * s) for x, y in (base, knee, heel, foot)]
            path = K.spline(P, n=10, tension=0.35)
            m = len(path)
            ws = [max(w * 1.2, lw0 * (1.0 - 0.5 * i / (m - 1))) for i in range(m)]
            f.add(K.stroke(path, 0, widths=ws, cap="spitz"))
            for q, r in ((P[1], lw0 * 0.62), (P[2], lw0 * 0.5)):
                f.add(K.circle(q[0], q[1], max(r, w * 0.55), 16))
        # Taster und Kieferklauen
        f.add(K.stroke(K.spline([(side * 0.02 * s, 0.09 * s), (side * 0.055 * s, 0.14 * s), (side * 0.04 * s, 0.18 * s)],
                                n=6), max(0.03 * s, w), max(0.02 * s, w * 0.8)))
    f.add(K.ellipse(0.0, 0.02 * s, 0.07 * s, 0.09 * s, 0.0, 48))                       # Kopfbruststück
    f.add(K.ellipse(0.0, -0.08 * s, max(0.055 * s, 0.6 * w), max(0.035 * s, w * 0.6), 0.0, 24))   # Taille
    ab = K.spline([(0.0, -0.085 * s), (0.10 * s, -0.11 * s), (0.145 * s, -0.20 * s), (0.125 * s, -0.31 * s),
                   (0.06 * s, -0.375 * s), (0.0, -0.385 * s), (-0.06 * s, -0.375 * s), (-0.125 * s, -0.31 * s),
                   (-0.145 * s, -0.20 * s), (-0.10 * s, -0.11 * s)], closed=True, n=8)
    f.add(ab)
    if zeichnung:
        r = max(0.013 * s, sw * 0.55)
        if 0.05 * s >= 2 * r + w:                    # Kreuz aus fünf Punkten
            for x, y in ((0, -0.155), (0, -0.215), (0, -0.275), (0.055, -0.215), (-0.055, -0.215)):
                f.cut(K.circle(x * s, y * s, r, 16))
        elif 0.11 * s >= sw + 2 * w:                 # klein: Längsschlitz
            f.cut(K.stroke([(0.0, -0.15 * s), (0.0, -0.30 * s)], sw, sw, "rund"))
        if 0.04 * s >= sw + 2 * w:
            for side in (1, -1):
                f.cut(K.stroke(K.spline([(side * 0.095 * s, -0.13 * s), (side * 0.115 * s, -0.21 * s),
                                         (side * 0.085 * s, -0.31 * s)], n=6),
                               max(0.012 * s, sw), max(0.009 * s, sw * 0.8), "rund"))
        if 0.07 * s >= 2 * sw + 3 * w:
            for side in (1, -1):
                f.cut(K.circle(side * 0.024 * s, 0.07 * s, max(0.009 * s, sw * 0.55), 12))      # Augen
    return f.place(cx, cy, 1.0, ang)


def spinne_frei(S: float, cfg, cx: float = 0.0, cy: float = 0.0, ang: float = 0.0) -> Figur:
    """Schnittflächen, die das Netz unter dem Spinnenkörper freistellen (vor spinne() anwenden)."""
    g = smin(cfg) + 0.6
    f = Figur()
    f.cut(K.ellipse(0.0, 0.02 * S, 0.07 * S + g, 0.09 * S + g, 0.0, 40))
    f.cut(K.ellipse(0.0, -0.235 * S, 0.145 * S + g, 0.155 * S + g, 0.0, 40))
    return f.place(cx, cy, 1.0, ang)


# --------------------------------------------------------------------------------------------------
# Spinnennetz
# --------------------------------------------------------------------------------------------------

def netz(cx: float, cy: float, R: float, a0: float, a1: float, ringe: int, speichen: int, w: float,
         seed: int = 1, riss: bool = False, tropfen: bool = True, voll: bool = True):
    """Netz als Figur aus Fäden (Material) zwischen den Winkeln a0..a1. voll = geschlossener Kreis.
    Liefert (Figur, Speichen-Endpunkte, Punkte auf dem äußersten Fangfaden zum Anhängen)."""
    r = K.rng(seed, "netz", ringe, speichen)
    n_sp = speichen if voll else speichen + 1
    span = (a1 - a0)
    angs = []
    for i in range(n_sp):
        t = i / (speichen if voll else speichen)
        j = 0.0 if (i == 0 or (not voll and i == n_sp - 1)) else K.jitter(r, 0.18) * span / speichen
        angs.append(a0 + span * t + j)
    hub = max(0.07 * R, 2.2 * w, (w + 3.2) / (span / speichen))
    radii = []
    for k in range(ringe):
        t = (k + 1) / ringe
        radii.append(hub + (R - hub) * t ** 0.92)
    # Radius je Speiche leicht unregelmäßig
    rr = [radii[k] * (1 + K.jitter(r, 0.03)) if (k < ringe - 1 and (voll or 0 < i < n_sp - 1)) else radii[k]
          for k in range(ringe) for i in range(n_sp)]
    RR = lambda k, i: rr[k * n_sp + i]
    P = lambda rad, a: (cx + rad * math.cos(a), cy + rad * math.sin(a))
    f = Figur()
    ends = []
    sag = 0.20
    pairs = list(range(n_sp)) if voll else list(range(n_sp - 1))
    torn = set()
    if riss:
        for _ in range(max(1, ringe * len(pairs) // 26)):
            k = r.randrange(1, ringe - 1) if ringe > 2 else 0
            torn.add((k, r.choice(pairs)))
    outer_pts = []
    for k in range(ringe):
        thick = w * (1.25 if k == ringe - 1 else 1.0)
        for i in pairs:
            j = (i + 1) % n_sp
            pa, pb = P(RR(k, i), angs[i]), P(RR(k, j), angs[j] + (TAU if j < i else 0.0))
            m = lerp(pa, pb, 0.5)
            depth = sag * (1 - 0.35 * (k == ringe - 1))
            c = lerp(m, (cx, cy), depth * math.hypot(pb[0] - pa[0], pb[1] - pa[1]) / max(RR(k, i), 1e-6))
            curve = K.bez(pa, c, pb, 14)
            if (k, i) in torn:
                # gerissener Faden: zwei hängende Enden
                L = len(curve)
                e1 = curve[:L // 3]
                e2 = curve[-L // 4:]
                d1 = [e1[-1], (e1[-1][0], e1[-1][1] - 0.04 * R)]
                f.line(e1 + [d1[1]], w)
                f.line([(e2[0][0], e2[0][1] - 0.025 * R)] + e2, w)
                continue
            f.line(curve, thick)
            if k == ringe - 1:
                outer_pts.append(lerp(pa, pb, 0.5))
            if tropfen and k % 2 == 1 and r.random() < 0.28:
                q = curve[r.randrange(3, 11)]
                f.add(K.circle(q[0], q[1], w * 0.95, 16))
    for i in range(n_sp):
        e = P(RR(ringe - 1, i), angs[i])
        ends.append(e)
        f.line([P(hub * 0.5, angs[i]), e], w)
    # Nabe: volle Scheibe (bzw. Viertel), darauf eine gravierte Spirale
    rh = hub * 0.92
    if voll:
        f.add(K.circle(cx, cy, rh, 48))
    else:
        f.add([(cx, cy)] + K.arc(cx, cy, rh, a0, a1, 24))
    spiral = []
    turns = 3.0 if voll else 0.75
    for j in range(int(60 * turns) + 1):
        t = j / (60 * turns)
        a = a0 + 0.08 + (TAU * turns if voll else (span - 0.16)) * t
        rad = rh * (0.15 + 0.7 * t) if voll else rh * (0.25 + 0.55 * (j % 60 / 60.0 if False else t))
        spiral.append(P(rad, a))
    f.gravur = [(spiral, False)]
    if not voll:
        f.gravur = [(K.arc(cx, cy, rh * q, a0 + 0.1, a1 - 0.1, 20), False) for q in (0.35, 0.55, 0.75)]
    return f, ends, outer_pts, angs, radii


# --------------------------------------------------------------------------------------------------
# Aufhängeöse (für Anhänger aus Figuren)
# --------------------------------------------------------------------------------------------------

def oese(f: Figur, x: float, y_top: float, d: float, cfg, einsatz: float = 0.45) -> Tuple[float, float, float]:
    """Öse über der Figur: Steg vom Rand nach oben, Loch Ø d. Liefert das Loch (x, y, d) für teil()."""
    ring = max(1.6 * wmin(cfg), 2.2)
    r = d / 2 + ring
    cy = y_top + r * (1.0 - einsatz) + ring * 0.2
    y_fuss = min(y_top - r * 0.6, oberkante(f, x, max(0.6, r * 0.2)) - 1.0)   # bis ins Material darunter
    f.add(K.circle(x, cy, r, 40))
    f.line([(x, y_fuss), (x, cy)], r * 1.1, r * 0.9)
    return (x, cy, d)


def oberkante(fig: Figur, x: float, breite: float) -> float:
    """Höchster Punkt der Figur im Streifen x ± breite."""
    ys = [q[1] for s, p in fig.ops if s == "+" for q in p if abs(q[0] - x) <= breite]
    return max(ys) if ys else fig.bbox()[3]


# --------------------------------------------------------------------------------------------------
# Totenkopf
# --------------------------------------------------------------------------------------------------

def totenkopf(S: float, cfg, risse: bool = True) -> Figur:
    """Schädel von vorn, Höhe ~S, Mitte 0/0: Schädeldach, Jochbeine, Unterkiefer, tiefe Augenhöhlen mit
    Brauenbogen, herzförmige Nasenhöhle, zwei Zahnreihen, Risse und Nähte."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    R = lambda pts: [(x * s, y * s) for x, y in pts]
    half = [(0.0, 0.50), (0.17, 0.485), (0.31, 0.42), (0.40, 0.31), (0.44, 0.17), (0.435, 0.04), (0.40, -0.05),
            (0.415, -0.10), (0.37, -0.15), (0.29, -0.16), (0.255, -0.21), (0.20, -0.235)]
    ring_ = list(reversed(half)) + [(-x, y) for x, y in half[1:]]
    f.add(K.spline(R(ring_), closed=False, n=8))
    # Ober- und Unterkiefer; die Zahnreihen hängen seitlich am Jochbein
    f.add(R([(-0.205, -0.19), (0.205, -0.19), (0.20, -0.30), (-0.20, -0.30)]))
    jaw = [(0.19, -0.28), (0.235, -0.20), (0.275, -0.25), (0.28, -0.32), (0.25, -0.41), (0.17, -0.47), (0.0, -0.50)]
    f.add(K.spline(R(jaw + [(-x, y) for x, y in reversed(jaw[:-1])]), closed=True, n=8))
    gap = max(sw, 0.012 * s)
    f.cut(K.stroke(R([(-0.165, -0.292), (0.165, -0.292)]), gap, gap, "rund"))
    span = 0.33 * s
    n = max(3, min(8, int(span / (w + sw + 0.4))))
    for i in range(1, n):
        x = -span / 2 + span * i / n
        for y0, y1 in ((-0.215, -0.282), (-0.302, -0.37 + 0.03 * (2 * i / n - 1) ** 2)):
            f.cut(K.stroke([(x, y0 * s), (x * 1.02, y1 * s)], sw, sw * 0.8, "rund"))
    # Augenhöhlen
    for side in (1, -1):
        eye = [(0.05, 0.02), (0.08, 0.10), (0.15, 0.135), (0.25, 0.12), (0.31, 0.06), (0.30, -0.03), (0.24, -0.08),
               (0.15, -0.085), (0.08, -0.05)]
        f.cut(K.spline([(side * x * s, y * s) for x, y in eye], closed=True, n=6))
    # Nasenhöhle: umgedrehtes Herz
    nose_r = [(0.0, -0.075), (0.025, -0.045), (0.05, -0.11), (0.035, -0.165), (0.0, -0.17)]
    f.cut(K.spline(R(nose_r + [(-x, y) for x, y in reversed(nose_r[1:-1])]), closed=True, n=6))
    # Riss im Schädeldach als Schlitz
    if risse and 0.02 * s >= sw + w:
        f.cut(K.stroke(R([(0.10, 0.43), (0.13, 0.36), (0.11, 0.31), (0.16, 0.25), (0.15, 0.20)]),
                       sw, sw * 0.6, "spitz"))
    # Gravur: Schädelnähte, Schläfen, Jochbeinbogen, Brauenbogen, Wangen
    gr = []
    gr.append((K.spline(R([(-0.36, 0.30), (-0.20, 0.36), (-0.06, 0.38), (0.0, 0.395)]), n=6), False))
    gr.append((K.spline(R([(0.0, 0.395), (0.02, 0.44), (-0.01, 0.47), (0.0, 0.49)]), n=4), False))
    for side in (1, -1):
        X = lambda pts: [(side * x * s, y * s) for x, y in pts]
        gr.append((K.spline(X([(0.37, 0.18), (0.34, 0.09), (0.35, -0.02)]), n=6), False))          # Schläfe
        gr.append((K.spline(X([(0.06, 0.155), (0.16, 0.18), (0.27, 0.165), (0.33, 0.10)]), n=6), False))  # Braue
        gr.append((K.spline(X([(0.10, -0.12), (0.20, -0.115), (0.30, -0.10), (0.37, -0.12)]), n=6), False))  # Jochbein
        gr.append((K.spline(X([(0.21, -0.37), (0.17, -0.42), (0.09, -0.45)]), n=6), False))       # Kinn
    gr.append((K.spline(R([(-0.22, 0.42), (-0.27, 0.36), (-0.25, 0.31), (-0.30, 0.25)]), n=4), False))  # Haarriss
    f.gravur = gr
    return f


# --------------------------------------------------------------------------------------------------
# Katze
# --------------------------------------------------------------------------------------------------

def katze(S: float, cfg) -> Figur:
    """Sitzende schwarze Katze von vorn, Höhe ~S, Mitte 0/0: spitze Ohren mit Innenohr, Mandelaugen,
    Nase und Mund, Schnurrhaare, Brustfell, Vorderpfoten mit Zehen, geschwungener Schwanz."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    R = lambda pts: [(x * s, y * s) for x, y in pts]
    # Körper (sitzend, breite Hüften)
    body = [(0.0, 0.10), (0.11, 0.09), (0.17, 0.02), (0.20, -0.10), (0.25, -0.25), (0.27, -0.38), (0.24, -0.47),
            (0.12, -0.50), (0.0, -0.50)]
    f.add(K.spline(R(body + [(-x, y) for x, y in reversed(body[1:-1])]), closed=True, n=8))
    # Kopf mit Wangen
    head = [(0.0, 0.40), (0.10, 0.385), (0.17, 0.34), (0.205, 0.26), (0.22, 0.19), (0.17, 0.13), (0.09, 0.095),
            (0.0, 0.09)]
    f.add(K.spline(R(head + [(-x, y) for x, y in reversed(head[1:-1])]), closed=True, n=8))
    for side in (1, -1):
        X = lambda pts: [(side * x * s, y * s) for x, y in pts]
        f.add(K.spline(X([(0.05, 0.37), (0.10, 0.44), (0.16, 0.50), (0.185, 0.40), (0.20, 0.30), (0.12, 0.33)]),
                       closed=True, n=6))                                                  # Ohr
        # Vorderpfote
        f.add(K.ellipse(side * 0.075 * s, -0.465 * s, 0.065 * s, 0.04 * s, 0.0, 32))
        f.line(X([(0.07, -0.20), (0.075, -0.33), (0.075, -0.44)]), 0.075 * s, 0.10 * s)
    # Schwanz: von rechts unten geschwungen nach oben, Spitze eingerollt
    tail = K.spline(R([(0.18, -0.46), (0.33, -0.44), (0.43, -0.33), (0.44, -0.17), (0.38, -0.05), (0.35, 0.06),
                       (0.40, 0.14), (0.46, 0.13)]), n=10)
    tw = [max(0.07 * s * (1 - 0.55 * i / (len(tail) - 1)), w * 1.2) for i in range(len(tail))]
    f.add(K.stroke(tail, 0, widths=tw, cap="rund"))
    # Durchbrüche: Augen, Innenohr, Nase/Mund, Beinlinie, Zehen, Schnurrhaare
    for side in (1, -1):
        X = lambda pts: [(side * x * s, y * s) for x, y in pts]
        f.cut(K.spline(X([(0.035, 0.255), (0.08, 0.29), (0.135, 0.275), (0.15, 0.245), (0.10, 0.225), (0.05, 0.235)]),
                       closed=True, n=6))
        if 0.04 * s >= sw + 2 * w:
            f.cut(K.stroke(X([(0.115, 0.36), (0.15, 0.43), (0.16, 0.36)]), sw, sw * 0.7, "spitz"))
        if 0.016 * s >= sw and s >= 110:
            for dy, ang in ((0.0, -0.06), (0.025, 0.08)):
                f.cut(K.stroke(X([(0.115, 0.175 + dy), (0.17, 0.18 + dy + ang * 0.3), (0.21, 0.17 + dy + ang)]),
                               sw, sw * 0.5, "spitz"))
        f.cut(K.stroke(X([(0.012, -0.22), (0.02, -0.32), (0.012, -0.42)]), sw, sw, "rund"))   # zwischen den Beinen
        for dx in (0.055, 0.095):
            f.cut(K.stroke(X([(dx, -0.47), (dx, -0.49)]), sw, sw, "rund"))
        f.cut(K.stroke(X([(0.13, -0.30), (0.18, -0.36), (0.19, -0.44)]), sw, sw * 0.8, "rund"))  # Hüfte
    f.cut(K.spline(R([(-0.025, 0.205), (0.025, 0.205), (0.0, 0.18)]), closed=True, n=3))       # Nase
    f.cut(K.stroke(R([(-0.05, 0.16), (-0.025, 0.145), (0.0, 0.165), (0.025, 0.145), (0.05, 0.16)]), sw, sw, "rund"))
    gr = []
    for side in (1, -1):
        X = lambda pts: [(side * x * s, y * s) for x, y in pts]
        gr.append((K.spline(X([(0.07, 0.32), (0.10, 0.315), (0.13, 0.30)]), n=4), False))      # Braue
        gr.append((K.spline(X([(0.04, 0.06), (0.06, 0.0), (0.05, -0.06)]), n=4), False))       # Brustfell
        gr.append((K.spline(X([(0.20, 0.05), (0.22, -0.05), (0.24, -0.15)]), n=4), False))     # Flanke
        if s < 110:                                                                         # Schnurrhaare graviert
            for dy, ang in ((0.0, -0.05), (0.022, 0.06)):
                gr.append(([(side * 0.12 * s, (0.175 + dy) * s), (side * 0.23 * s, (0.175 + dy + ang) * s)], False))
    gr.append((K.spline(R([(-0.03, 0.03), (0.0, -0.03), (0.03, 0.03)]), n=4), False))
    gr.append((K.spline(R([(-0.025, -0.07), (0.0, -0.12), (0.025, -0.07)]), n=4), False))
    gr.append((K.spline(R([(-0.11, 0.10), (0.0, 0.065), (0.11, 0.10)]), n=6), False))          # Halsband
    gr.append((K.spline(R([(-0.11, 0.075), (0.0, 0.04), (0.11, 0.075)]), n=6), False))
    f.gravur = gr
    f.gloeckchen = (0.0, 0.025 * s, 0.022 * s)
    return f


# --------------------------------------------------------------------------------------------------
# Hexenhut
# --------------------------------------------------------------------------------------------------

def hexenhut(S: float, cfg) -> Figur:
    """Hexenhut, Breite ~S: geknickte Spitze, breite gewellte Krempe, Hutband mit Schnalle, Flicken mit
    Stichen, ausgeschnittene Sterne und Mondsichel, Knitterfalten."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    R = lambda pts: [(x * s, y * s) for x, y in pts]
    # Krempe
    brim = K.spline(R([(-0.50, -0.20), (-0.36, -0.15), (-0.20, -0.12), (0.0, -0.115), (0.20, -0.12), (0.36, -0.15),
                       (0.50, -0.20), (0.44, -0.25), (0.25, -0.30), (0.0, -0.31), (-0.25, -0.30), (-0.44, -0.25)]),
                    closed=True, n=8)
    f.add(brim)
    # Kegel mit Knick
    cone = K.spline(R([(-0.22, -0.16), (-0.17, -0.02), (-0.10, 0.14), (-0.06, 0.25), (0.0, 0.33), (0.08, 0.40),
                       (0.17, 0.43), (0.25, 0.40), (0.21, 0.375), (0.14, 0.36), (0.09, 0.31), (0.08, 0.20),
                       (0.11, 0.06), (0.17, -0.06), (0.22, -0.16)]), closed=True, n=8)
    f.add(cone)
    f.add(K.circle(0.26 * s, 0.395 * s, 0.03 * s, 24))                                     # Bommel an der Spitze
    # Hutband (Schlitze oben und unten), Schnalle (vier Schlitze)
    for xa, xb in ((-0.155, -0.06), (0.075, 0.16)):
        f.cut(K.stroke(R([(xa, -0.07 + 0.01 * (xa > 0)), ((xa + xb) / 2, -0.063), (xb, -0.07 + 0.01 * (xb < 0))]),
                       sw, sw, "rund"))
    bx, by, bw, bh = -0.04, -0.085, 0.10, 0.055
    if bw * s >= 2 * sw + 3 * w:
        for a, b in (((bx, by), (bx + bw * 0.8, by)), ((bx, by + bh), (bx + bw * 0.8, by + bh)),
                     ((bx, by), (bx, by + bh)), ((bx + bw * 0.45, by + bh * 0.5), (bx + bw, by + bh * 0.5))):
            f.cut(K.stroke(R([a, b]), sw, sw, "flach"))
    # Sterne und Mond
    for x, y, r in ((-0.07, 0.10, 0.035), (0.10, 0.00, 0.026), (-0.12, -0.01, 0.02), (0.02, 0.22, 0.022)):
        if r * s >= 2.2 * sw:
            f.cut(K.star(x * s, y * s, r * s, r * s * 0.45, 5))
    mr = 0.045 * s
    if mr >= 3 * sw:
        moon = K.chain(K.arc(0.045 * s, 0.13 * s, mr, math.radians(60), math.radians(300), 24),
                       list(reversed(K.arc(0.065 * s, 0.13 * s, mr * 0.8, math.radians(70), math.radians(290), 24))))
        f.cut(moon)
    if 0.03 * s >= sw + 2 * w:                                              # Knick in der Spitze
        f.cut(K.stroke(R([(0.035, 0.30), (0.08, 0.34), (0.13, 0.37)]), sw, sw * 0.5, "spitz"))
        f.cut(K.stroke(R([(-0.14, -0.04), (-0.10, 0.05)]), sw, sw * 0.5, "spitz"))
    # Knitterfalten (Schlitze) an der Krempe
    for x in (-0.36, 0.33):
        f.cut(K.stroke(R([(x, -0.19), (x + 0.03, -0.23)]), sw, sw * 0.6, "spitz"))
    gr = []
    # Flicken mit Stichen
    patch = R([(0.03, -0.035), (0.13, -0.025), (0.12, 0.045), (0.035, 0.035)])
    gr.append((patch, True))
    for i in range(5):
        t = (i + 0.5) / 5
        a = lerp(patch[0], patch[1], t)
        gr.append(([(a[0], a[1] - 0.012 * s), (a[0] + 0.004 * s, a[1] + 0.012 * s)], False))
    gr.append((K.spline(R([(-0.15, 0.0), (-0.10, 0.03), (-0.13, 0.07)]), n=4), False))
    gr.append((K.spline(R([(0.09, 0.25), (0.11, 0.21), (0.10, 0.17)]), n=4), False))
    gr.append((K.spline(R([(-0.42, -0.215), (-0.20, -0.255), (0.0, -0.26), (0.20, -0.255), (0.42, -0.215)]),
                         n=8), False))
    f.gravur = gr
    return f


# --------------------------------------------------------------------------------------------------
# Großer Kürbis (Kürbis-Leuchte) mit geschnitzten Gesichtern
# --------------------------------------------------------------------------------------------------

GESICHTER = ("klassisch", "gruselig", "froehlich", "katze", "fledermaus", "hexe", "spinnennetz")


def _sym(pts: Sequence[Point], s: float) -> Poly:
    """Rechte Hälfte (von oben nach unten) gespiegelt zu einer geschlossenen Form."""
    right = [(x * s, y * s) for x, y in pts]
    return right + [(-x, y) for x, y in reversed(right[1:-1])]


def kuerbis_gesicht(f: Figur, kind: str, s: float, cfg, cy: float = 0.0, seed: int = 1) -> None:
    """Geschnitztes Gesicht (bzw. Silhouette) in den Kürbis schneiden. Gesichtsfeld ±0.25·s um (0, cy)."""
    w, sw = wmin(cfg), smin(cfg)
    P = lambda pts: [(x * s, y * s + cy) for x, y in pts]
    mir = lambda pts: [(-x, y) for x, y in pts]
    if kind == "klassisch":
        eye = [(0.045, 0.06), (0.125, 0.205), (0.20, 0.065), (0.125, 0.085)]
        for e in (eye, mir(eye)):
            f.cut(K.spline(P(e), closed=True, n=4, tension=0.15))
        f.cut(K.spline(P([(0.0, 0.07), (0.035, 0.005), (-0.035, 0.005)]), closed=True, n=3, tension=0.1))
        mouth = [(-0.24, -0.02), (-0.15, -0.075), (-0.115, -0.04), (-0.09, -0.09), (0.04, -0.095), (0.07, -0.05),
                 (0.10, -0.095), (0.24, -0.02), (0.19, -0.13), (0.10, -0.19), (0.075, -0.15), (0.045, -0.20),
                 (-0.06, -0.20), (-0.09, -0.155), (-0.12, -0.185), (-0.19, -0.13)]
        f.cut(K.spline(P(mouth), closed=True, n=5, tension=0.2))
    elif kind == "gruselig":
        eye = [(0.035, 0.055), (0.13, 0.08), (0.22, 0.17), (0.19, 0.055), (0.13, 0.02), (0.06, 0.025)]
        for e in (eye, mir(eye)):
            f.cut(K.spline(P(e), closed=True, n=5, tension=0.25))
        for side in (1, -1):                                                    # zornige Brauen
            f.cut(K.stroke([(side * 0.04 * s, 0.13 * s + cy), (side * 0.13 * s, 0.155 * s + cy),
                            (side * 0.21 * s, 0.235 * s + cy)], max(sw, 0.014 * s), sw, "spitz"))
        f.cut(K.spline(P([(0.0, 0.0), (0.03, -0.045), (0.0, -0.035), (-0.03, -0.045)]), closed=True, n=3,
                       tension=0.2))
        mouth = [(-0.25, -0.03), (-0.17, -0.08), (-0.14, -0.15), (-0.11, -0.085), (-0.04, -0.095), (-0.02, -0.13),
                 (0.0, -0.095), (0.06, -0.09), (0.10, -0.165), (0.13, -0.085), (0.18, -0.075), (0.25, -0.03),
                 (0.20, -0.14), (0.16, -0.17), (0.13, -0.135), (0.10, -0.205), (0.0, -0.235), (-0.07, -0.225),
                 (-0.09, -0.17), (-0.12, -0.215), (-0.20, -0.15)]
        f.cut(K.spline(P(mouth), closed=True, n=4, tension=0.1))
    elif kind == "froehlich":
        for side in (1, -1):                                                    # lachende Halbmond-Augen
            c = (side * 0.12, 0.08)
            top = [(c[0] + 0.08 * math.cos(a), c[1] + 0.09 * math.sin(a)) for a in
                   (math.radians(d) for d in range(0, 181, 15))]
            bot = [(c[0] + 0.065 * math.cos(a), c[1] + 0.012 + 0.04 * math.sin(a)) for a in
                   (math.radians(d) for d in range(180, -1, -15))]
            f.cut(P(top + bot))
            f.cut(K.circle(side * 0.19 * s, -0.035 * s + cy, max(0.025 * s, sw), 24))     # Bäckchen
        f.cut(K.circle(0.0, 0.0 + cy, max(0.024 * s, sw), 20))
        smile = [(-0.22, -0.05), (-0.11, -0.085), (0.0, -0.09), (0.11, -0.085), (0.22, -0.05), (0.17, -0.15),
                 (0.08, -0.205), (0.0, -0.215), (-0.08, -0.205), (-0.17, -0.15)]
        f.cut(K.spline(P(smile), closed=True, n=6))
        for x in (-0.06, 0.06):                                                 # Zähne stehen als Stege
            f.add(K.stroke(P([(x, -0.075), (x, -0.15)]), max(w, 0.026 * s), max(w, 0.02 * s), "flach"))
    elif kind == "katze":
        eye = [(0.04, 0.07), (0.10, 0.13), (0.19, 0.15), (0.20, 0.08), (0.13, 0.035), (0.07, 0.04)]
        for side, e in ((1, eye), (-1, mir(eye))):
            f.cut(K.spline(P(e), closed=True, n=5))
            f.add(K.stroke(P([(side * 0.125, 0.165), (side * 0.13, 0.09), (side * 0.125, 0.02)]),
                           max(w, 0.022 * s), max(w, 0.016 * s), "spitz"))    # Schlitzpupille
            for dy, k in ((0.0, -0.03), (0.035, 0.0), (-0.035, -0.06)):
                f.cut(K.stroke(P([(side * 0.09, -0.04 + dy), (side * 0.17, -0.04 + dy + k * 0.5),
                                  (side * 0.25, -0.04 + dy + k)]), sw, sw * 0.6, "spitz"))
        f.cut(K.spline(P([(-0.035, 0.0), (0.035, 0.0), (0.0, -0.035)]), closed=True, n=3, tension=0.2))
        f.cut(K.stroke(P([(-0.075, -0.075), (-0.035, -0.10), (0.0, -0.065), (0.035, -0.10), (0.075, -0.075)]),
                       max(sw, 0.016 * s), None, "rund"))
    elif kind == "fledermaus":
        bat, _ = fledermaus(0.50 * s, "segeln", cfg, augen=False)
        for sgn, poly in bat.place(0.02 * s, -0.07 * s + cy, 1.0, math.radians(-8)).ops:
            if sgn == "+":
                f.cut(poly)
        small, _ = fledermaus(0.17 * s, "hoch", cfg, augen=False)
        for sgn, poly in small.place(0.17 * s, 0.17 * s + cy, 1.0, math.radians(12)).ops:
            if sgn == "+":
                f.cut(poly)
        mr = 0.07 * s
        f.cut(K.chain(K.arc(-0.15 * s, 0.15 * s + cy, mr, math.radians(60), math.radians(300), 24),
                      list(reversed(K.arc(-0.125 * s, 0.165 * s + cy, mr * 0.8, math.radians(75), math.radians(285),
                                          24)))))
    elif kind == "hexe":
        from pakete import bibliothek
        G = bibliothek("verzierungen").G
        f.cut(G.place(G.witch_unit(), 0.0, -0.04 * s + cy, 0.56 * s))
        f.cut(K.circle(0.13 * s, 0.17 * s + cy, 0.06 * s, 40))                # Vollmond hinter der Hexe
        for x, y, r in ((-0.17, 0.15, 0.022), (-0.09, 0.21, 0.016), (0.21, 0.05, 0.016)):
            if r * s >= 2.4 * sw:
                f.cut(K.star(x * s, y * s + cy, r * s, r * s * 0.45, 5))
    elif kind == "spinnennetz":
        R = 0.22 * s
        wx, wy = -0.03 * s, cy + 0.03 * s
        f.cut(K.circle(wx, wy, R, 72))
        netz_, _, _, _, radii = netz(wx, wy, R + w * 0.5, math.pi / 2, math.pi / 2 + TAU, 4, 10, w, seed, False, True,
                                     voll=True)
        f.merge(netz_)
        # Spinne hängt am Faden rechts unten (als Silhouette ausgeschnitten)
        a = math.radians(-38)
        top = (wx + R * math.cos(a), wy + R * math.sin(a))
        sx, sy = 0.20 * s, cy - 0.17 * s
        f.cut(K.stroke(K.bez(top, (sx + 0.02 * s, (top[1] + sy) / 2), (sx, sy + 0.03 * s), 10), sw, sw, "rund"))
        for sgn, poly in spinne(0.15 * s, cfg, sx, sy, 0.0, zeichnung=False).ops:
            if sgn == "+":
                f.cut(poly)
        f.gravur = getattr(f, "gravur", []) + netz_.gravur
    else:
        raise ValueError(kind)


def kuerbis_gross(S: float, cfg, gesicht: str = "gruselig", blatt: bool = True, rippen: bool = True,
                  seed: int = 1) -> Figur:
    """Bauchiger Kürbis aus sieben Rippen-Buckeln, Breite ~S, Mitte 0/0 (unten bei y ≈ −0.37·S): gebogener
    Stiel mit Kerben, Blatt mit Adern, eingerollte Ranke, Rippen als Schlitze, geschnitztes Gesicht."""
    s = S
    w, sw = wmin(cfg), smin(cfg)
    f = Figur()
    f.gravur = []
    lobes = [(0.0, 0.0, 0.17, 0.37), (0.12, -0.005, 0.17, 0.365), (-0.12, -0.005, 0.17, 0.365),
             (0.25, -0.02, 0.15, 0.335), (-0.25, -0.02, 0.15, 0.335), (0.355, -0.06, 0.115, 0.26),
             (-0.355, -0.06, 0.115, 0.26)]
    for x, y, rx, ry in lobes:
        f.add(K.ellipse(x * s, y * s, rx * s, ry * s, 0.0, 72))
    # Stiel: gebogen, oben schräg abgebrochen, mit Kerben
    stem = [(0.0, 0.31), (0.005, 0.40), (0.03, 0.47), (0.07, 0.51)]
    f.line(K.spline([(x * s, y * s) for x, y in stem], n=8), 0.075 * s, 0.05 * s, cap="flach")
    f.add([(0.05 * s, 0.535 * s), (0.105 * s, 0.505 * s), (0.085 * s, 0.48 * s), (0.045 * s, 0.50 * s)])
    if 0.075 * s >= 2 * sw + 3 * w:
        f.cut(K.stroke([(0.012 * s, 0.37 * s), (0.02 * s, 0.43 * s), (0.04 * s, 0.47 * s)], sw, sw * 0.6, "spitz"))
    if blatt:
        mid = K.bez((0.04 * s, 0.39 * s), (0.17 * s, 0.50 * s), (0.34 * s, 0.45 * s), 20)
        lw_ = [max(0.13 * s * math.sin(math.pi * (0.06 + 0.94 * i / 20)) ** 0.75, w) *
               (1 + 0.16 * math.sin(i * 2.3)) for i in range(21)]
        f.add(K.stroke(mid, 0, widths=lw_, cap="spitz"))
        if 0.13 * s >= sw + 2 * w + 1:
            f.cut(K.stroke(mid[3:17], sw, sw * 0.6, "spitz"))
            for i in (6, 9, 12):
                q = mid[i]
                for d in (1, -1):
                    L = 0.035 * s * (1.2 - i / 20)
                    if L > 2 * sw:
                        f.cut(K.stroke([(q[0] + 0.008 * s, q[1] + d * 0.006 * s),
                                        (q[0] + 0.008 * s + L * 0.6, q[1] + d * L)], sw, sw * 0.5, "spitz"))
        # Ranke: aus dem Stiel nach links, eingerollt
        cx_, cy_ = -0.15 * s, 0.40 * s
        tr = [(0.0, 0.36 * s), (-0.06 * s, 0.41 * s), (-0.12 * s, 0.43 * s)]
        tr += [(cx_ + 0.035 * s * (1 - t / 14) * math.cos(1.2 + t * 0.55),
                cy_ + 0.035 * s * (1 - t / 14) * math.sin(1.2 + t * 0.55)) for t in range(0, 12)]
        f.line(K.spline(tr, n=6), max(0.016 * s, w), max(0.011 * s, w))
    # Rippen zwischen den Buckeln (Schlitze außerhalb des Gesichts), weitere Rippen graviert
    if rippen:
        for side in (1, -1):
            for x0, bend, y0, y1 in ((0.305, 0.045, 0.24, -0.27), (0.19, 0.03, 0.30, -0.30)):
                path = K.bez((side * x0 * s, y0 * s), (side * (x0 + bend) * s, 0.0), (side * x0 * s, y1 * s), 20)
                if x0 < 0.25:                                   # innere Rippe: nur oberhalb und unterhalb des Gesichts
                    for seg in (path[:5], path[-5:]):
                        f.cut(K.stroke(seg, sw, sw * 0.6, "spitz"))
                else:
                    f.cut(K.stroke(path, sw, sw * 0.7, "rund"))
            f.gravur.append((K.bez((side * 0.06 * s, 0.33 * s), (side * 0.085 * s, 0.0), (side * 0.06 * s, -0.33 * s),
                                   20), False))
            f.gravur.append((K.bez((side * 0.40 * s, 0.17 * s), (side * 0.45 * s, -0.04 * s),
                                   (side * 0.40 * s, -0.25 * s), 16), False))
    for k in range(3):                                                      # Glanzlicht links oben
        f.gravur.append((K.arc(-0.05 * s, 0.0, (0.33 - 0.025 * k) * s, math.radians(122 + 4 * k),
                               math.radians(150 - 4 * k), 12), False))
    for dx in (-0.015, 0.012):                                               # Stielfasern
        f.gravur.append((K.spline([(dx * s, 0.33 * s), (dx * 1.2 * s + 0.01 * s, 0.42 * s),
                                   (dx * s + 0.04 * s, 0.48 * s)], n=6), False))
    kuerbis_gesicht(f, gesicht, s, cfg, cy=-0.01 * s, seed=seed)
    return f


# --------------------------------------------------------------------------------------------------
# Efeu
# --------------------------------------------------------------------------------------------------

def efeublatt(cx: float, cy: float, g: float, ang: float) -> Tuple[Poly, List[Poly]]:
    """Dreilappiges Efeublatt, Stielansatz bei (cx, cy), Länge g, zeigt in Richtung ang.
    Liefert (Umriss, Adern)."""
    half = [(0.0, 0.0), (0.08, -0.20), (0.30, -0.44), (0.42, -0.24), (0.62, -0.32), (0.74, -0.14), (1.0, 0.0)]
    pts = half + [(x, -y) for x, y in reversed(half[1:-1])]
    ca, sa = math.cos(ang), math.sin(ang)
    T = lambda p: (cx + (p[0] * ca - p[1] * sa) * g, cy + (p[0] * sa + p[1] * ca) * g)
    outline = K.spline([T(p) for p in pts], closed=True, n=6, tension=0.4)
    veins = [[T((0.08, 0.0)), T((0.88, 0.0))]]
    for d in (1, -1):
        veins.append([T((0.12, 0.0)), T((0.30, d * 0.34))])
        veins.append([T((0.30, 0.0)), T((0.60, d * 0.24))])
    return outline, veins


def efeuranke(f: Figur, pfad: Sequence[Point], g: float, cfg, seed: int = 1, blatt_alle: float = 1.0,
              seite: int = 1) -> List[Tuple[Poly, bool]]:
    """Ranke als Material entlang pfad mit Efeublättern abwechselnd links/rechts. Liefert Gravur (Blattumrisse
    und Adern), damit Blätter auch auf gleichfarbigem Grund sichtbar sind."""
    w = wmin(cfg)
    r = K.rng(seed, "efeu", len(pfad))
    p = K.resample(pfad, max(1.0, g * 0.18))
    f.line(p, max(w, 0.10 * g), max(w * 0.9, 0.06 * g))
    gr: List[Tuple[Poly, bool]] = [(p, False)]
    L = K.path_len(p)
    n = max(2, int(L / (g * 0.75 * blatt_alle)))
    for k in range(1, n + 1):
        i = min(len(p) - 2, int(k / (n + 1) * (len(p) - 1)))
        a = math.atan2(p[i + 1][1] - p[i][1], p[i + 1][0] - p[i][0])
        side = 1 if k % 2 else -1
        aa = a + side * seite * math.radians(55 + 20 * r.random())
        size = g * (0.75 + 0.35 * r.random()) * (0.6 + 0.4 * k / n)
        stem = (p[i][0] + math.cos(aa) * size * 0.25, p[i][1] + math.sin(aa) * size * 0.25)
        f.line([p[i], stem], max(w, 0.05 * g))
        out, veins = efeublatt(stem[0], stem[1], size, aa)
        f.add(out)
        gr.append((out, True))
        gr += [(v, False) for v in veins]
    return gr


# --------------------------------------------------------------------------------------------------
# Hexe auf dem Besen (Silhouette) und Silhouetten als Polygon
# --------------------------------------------------------------------------------------------------

def hexe(S: float, cfg, katze_: bool = True) -> Figur:
    """Hexe auf dem Besen nach rechts fliegend, Breite ~S, Mitte 0/0: geknickter Hut mit Krempe, Hakennase
    und spitzes Kinn, wehende Haare, gezackter Umhang, Schnabelschuh, Besen mit gebundenem Reisig und
    eine Katze mit hochgestelltem Schwanz hinten auf dem Besen."""
    s = S
    w = wmin(cfg)
    f = Figur()
    R = lambda pts: [(x * s, y * s) for x, y in pts]
    lw = lambda v: max(w, v * s)
    # Besen: Stiel, Bindung, Reisig
    f.line(R([(-0.34, -0.055), (0.0, -0.03), (0.47, 0.0)]), lw(0.022), lw(0.016))
    f.add(K.ellipse(-0.335 * s, -0.056 * s, 0.022 * s, 0.03 * s, 0.1, 24))
    for k in range(7):
        t = k / 6
        tip = (-0.52 + 0.02 * math.sin(k * 1.7), -0.15 + 0.16 * t)
        f.line(K.bez(R([(-0.33, -0.056)])[0], R([(-0.42, -0.07 + 0.06 * (t - 0.5))])[0], R([tip])[0], 8),
               lw(0.024), max(w * 0.8, 0.004 * s), "spitz")
    # Rock und Bein mit Schnabelschuh
    f.add(K.spline(R([(-0.10, 0.02), (0.06, 0.03), (0.10, -0.03), (0.06, -0.08), (-0.04, -0.07), (-0.12, -0.03)]),
                   closed=True, n=6))
    f.line(R([(0.06, -0.06), (0.12, -0.11), (0.15, -0.115)]), lw(0.028), lw(0.02))
    f.add(K.spline(R([(0.13, -0.10), (0.19, -0.105), (0.215, -0.085), (0.19, -0.125), (0.13, -0.13)]),
                   closed=True, n=4))
    # Oberkörper vorgebeugt, Arm zum Stiel
    f.add(K.spline(R([(-0.04, 0.02), (0.03, 0.16), (0.08, 0.21), (0.12, 0.18), (0.07, 0.03)]), closed=True, n=6))
    f.line(R([(0.09, 0.17), (0.17, 0.09), (0.25, 0.015)]), lw(0.026), lw(0.02))
    f.add(K.circle(0.255 * s, 0.012 * s, 0.018 * s, 16))
    # Umhang mit gezacktem Saum
    cape = R([(0.06, 0.21), (-0.03, 0.205), (-0.11, 0.19), (-0.19, 0.20), (-0.16, 0.16), (-0.21, 0.145),
              (-0.15, 0.115), (-0.18, 0.085), (-0.11, 0.08), (-0.10, 0.04), (-0.05, 0.05), (0.02, 0.12)])
    f.add(K.spline(cape, closed=True, n=4, tension=0.3))
    # Kopf, Hakennase, Kinn
    f.add(K.circle(0.12 * s, 0.255 * s, 0.042 * s, 32))
    f.add(K.spline(R([(0.14, 0.27), (0.19, 0.255), (0.215, 0.235), (0.185, 0.245), (0.15, 0.245)]), closed=True,
                   n=4, tension=0.3))
    f.add(K.spline(R([(0.12, 0.22), (0.16, 0.205), (0.17, 0.19), (0.14, 0.205), (0.11, 0.215)]), closed=True,
                   n=4, tension=0.3))
    # Haare wehen nach hinten
    for k, (ex, ey) in enumerate(((0.0, 0.255), (-0.03, 0.235), (0.01, 0.215), (-0.04, 0.27))):
        f.line(K.bez(R([(0.10, 0.25)])[0], R([((0.10 + ex) / 2, 0.245 + 0.015 * (k % 2))])[0], R([(ex, ey)])[0], 8),
               lw(0.011), max(w * 0.8, 0.004 * s), "spitz")
    # Hut: Krempe und geknickte Spitze
    f.add(K.ellipse(0.105 * s, 0.295 * s, 0.10 * s, 0.017 * s, math.radians(8), 36))
    f.add(K.spline(R([(0.06, 0.30), (0.08, 0.37), (0.06, 0.43), (-0.02, 0.47), (0.03, 0.42), (0.10, 0.37),
                      (0.15, 0.30)]), closed=True, n=6, tension=0.4))
    # Katze auf dem Besen
    if katze_:
        cx, cy = -0.25, -0.05
        f.add(K.ellipse((cx) * s, (cy + 0.045) * s, 0.04 * s, 0.05 * s, 0.0, 28))
        f.add(K.circle((cx + 0.012) * s, (cy + 0.11) * s, 0.03 * s, 24))
        for d in (-1, 1):
            f.add(R([(cx + 0.012 + d * 0.012, cy + 0.125), (cx + 0.012 + d * 0.032, cy + 0.16),
                     (cx + 0.012 + d * 0.03, cy + 0.115)]))
        f.line(K.spline(R([(cx - 0.03, cy + 0.02), (cx - 0.08, cy + 0.04), (cx - 0.09, cy + 0.10),
                           (cx - 0.07, cy + 0.14)]), n=6), lw(0.014), max(w * 0.9, 0.008 * s))
    return f


def silhouette(fig: Figur, cfg, name: str = "silhouette") -> List[Point]:
    """Nur die Außenkontur einer Figur (Durchbrüche entfallen) als laserfestes Polygon."""
    notes: List[str] = []
    plus = Figur([o for o in fig.ops if o[0] == "+"])
    return teil(name, plus, cfg, notes).outline


def silhouette_loch(fig: Figur, cfg, name: str = "loch") -> List[Point]:
    """Außenkontur einer Figur als Durchbruch: so geglättet, dass sie als Innenschnitt kerf-fest ist."""
    notes: List[str] = []
    x0, y0, x1, y1 = fig.bbox()
    m = 3 * wmin(cfg) + 3
    rahmen = Figur().add(K.rect(x0 - m, y0 - m, x1 - x0 + 2 * m, y1 - y0 + 2 * m))
    rahmen.ops += [("-", p) for s, p in fig.ops if s == "+"]
    holes = teil(name, rahmen, cfg, notes).holes
    if not holes:
        raise ValueError("Silhouette zu klein")
    from steckwerk import signed_area
    return max(holes, key=lambda h: abs(signed_area(h)))
