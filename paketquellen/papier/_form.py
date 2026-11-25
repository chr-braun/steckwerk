"""Gemeinsame Werkzeuge des Pakets „Papier“ (wie im Steckstern): Bibliothek, Formen, Raster.
Linsen, Sterne, Schneeflocken und das Zusammensetzen von Material aus Figur-Rastern."""
from __future__ import annotations

import math
import random
from typing import Callable, List, Sequence, Tuple

from pakete import bibliothek
from steckwerk import point_in_polygon

V = bibliothek("verzierungen")
E, K, W = V.E, V.K, V.W
Point = Tuple[float, float]
Poly = List[Point]


def drehen(poly: Sequence[Point], ang: float, cx: float = 0.0, cy: float = 0.0) -> Poly:
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in poly]


def schieben(poly: Sequence[Point], dx: float, dy: float) -> Poly:
    return [(x + dx, y + dy) for x, y in poly]


def linse(cx: float, cy: float, L: float, B: float, ang: float = 0.0, n: int = 40, spitz: float = 0.3) -> Poly:
    """Blattform der Länge L und Breite B, zur einen Seite leicht spitzer."""
    pts = [(L / 2 * math.cos(t), B / 2 * math.sin(t) * (1 - spitz * math.cos(t)))
           for t in (2 * math.pi * k / n for k in range(n))]
    return schieben(drehen(pts, ang), cx, cy)


def stern(cx: float, cy: float, ro: float, ri: float, k: int = 5, rot: float = 0.0) -> Poly:
    return [(cx + (ro if i % 2 == 0 else ri) * math.cos(rot + math.pi / 2 + i * math.pi / k),
             cy + (ro if i % 2 == 0 else ri) * math.sin(rot + math.pi / 2 + i * math.pi / k)) for i in range(2 * k)]


def kreis(cx: float, cy: float, r: float, n: int = 0) -> Poly:
    return K.circle(cx, cy, r, n)


def mond(cx: float, cy: float, r: float, n: int = 48) -> Poly:
    """Mondsichel als eine Kontur (äußerer Bogen + innerer Bogen)."""
    a = []
    for k in range(n + 1):
        t = -math.pi / 2 - 0.9 + (math.pi + 1.8) * k / n
        a.append((cx - r * math.cos(t) * 0.0 + r * math.cos(t + math.pi), cy + r * math.sin(t + math.pi)))
    b = []
    for k in range(n + 1):
        t = -math.pi / 2 - 0.9 + (math.pi + 1.8) * (n - k) / n
        b.append((cx + 0.38 * r + 0.86 * r * math.cos(t + math.pi), cy + 0.12 * r + 0.86 * r * math.sin(t + math.pi)))
    return a + b


def schneeflocke(cx: float, cy: float, R: float, rot: float, steg: float) -> List[Poly]:
    """Schneeflocke als Liste sich überlappender Flächen (wird im Raster vereinigt)."""
    teile: List[Poly] = [kreis(cx, cy, R * 0.2, 16)]
    for k in range(6):
        a = rot + k * math.pi / 3
        u = (math.cos(a), math.sin(a))
        n = (-u[1], u[0])
        teile.append(K.stroke([(cx, cy), (cx + u[0] * R, cy + u[1] * R)], R * 0.2 + 0.4))
        for f in (0.5, 0.76):
            b = (cx + u[0] * R * f, cy + u[1] * R * f)
            for sg in (1, -1):
                w = (u[0] * math.cos(0.96) + sg * n[0] * math.sin(0.96), u[1] * math.cos(0.96) + sg * n[1] * math.sin(0.96))
                L = R * 0.34 * (1.2 - f)
                teile.append(K.stroke([b, (b[0] + w[0] * L, b[1] + w[1] * L)], R * 0.13 + 0.35))
    return teile


def innen(poly: Sequence[Point], pruef: Callable[[Point], bool]) -> bool:
    return all(pruef(p) for p in poly)


def abstand_frei(c: Point, r: float, belegt: List[Tuple[float, float, float]], luft: float) -> bool:
    return all(math.hypot(c[0] - x, c[1] - y) >= r + rr + luft for x, y, rr in belegt)


def zufall(seed: int, *salz) -> random.Random:
    return random.Random(hash((seed,) + salz) & 0xFFFFFFFF)


def pip(p: Point, poly: Sequence[Point]) -> bool:
    return point_in_polygon(p, poly)


def gerade_dist(p: Point, a: Point, b: Point) -> float:
    """Abstand von p zur (unendlichen) Geraden durch a und b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    return abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / math.hypot(dx, dy)


def material(lw, umriss: Sequence[Poly], feld: Sequence[Poly], stege_fig=None, loecher: Sequence[Poly] = (),
             minus_feld: Sequence[Poly] = (), solid: Sequence[Poly] = ()):
    """Material = Umriss − (Feld − minus_feld) + (Stege ∧ Feld) − Löcher + solid."""
    shape = lw.flaechen(umriss)
    f = lw.flaechen(feld)
    if minus_feld:
        f = E._andnot(f, lw.flaechen(minus_feld))
    mat = E._andnot(shape, f)
    if stege_fig is not None:
        mat = mat.union(E._and(lw.figur(stege_fig), E._and(f, shape)))
    if loecher:
        mat = E._andnot(mat, lw.flaechen(loecher))
    if solid:
        mat = mat.union(E._and(lw.flaechen(solid), shape))
    return mat


def spitzblatt(cx: float, cy: float, L: float, B: float, ang: float = 0.0, n: int = 14) -> Poly:
    """Spitzes Blatt (Vesica) aus zwei Kreisbögen: Länge L, Breite B."""
    h = B / 2
    R = (L * L / 4 + h * h) / (2 * h)
    a = math.asin(min(1.0, (L / 2) / R))
    pts = []
    for k in range(n + 1):                      # obere Hälfte, von rechts nach links
        t = -a + 2 * a * k / n
        pts.append((R * math.sin(-t), R * math.cos(t) - (R - h)))
    for k in range(1, n):
        t = -a + 2 * a * k / n
        pts.append((R * math.sin(t), -(R * math.cos(t) - (R - h))))
    return schieben(drehen(pts, ang), cx, cy)
