"""
_muster.py – Flächenmuster zum Gravieren (für jedes Bauteil, siehe gravur.py).

Jedes Muster füllt die freie Fläche einer Leinwand (models._deko.Canvas): Linien werden an Kontur,
Durchbrüchen und vorhandenen Gravuren abgeschnitten, kleine Ornamente (Sterne, Flocken, Herzen) nur
ganz gesetzt. Damit das auch auf alten Rechnern flott geht, prüft `Schnell` mit einem Gitter vorab,
welche Zellen sicher frei sind – nur Linien in Randzellen gehen durch die genaue (langsame) Prüfung.

  muster(cv, art, box, abstand, drehung, seed)

abstand  Größe eines Rapports in mm (Linienabstand, Wabengröße …); kleiner = feiner und detailreicher.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

from steckwerk import Point, dist
from models import _deko as dk
from models._shapes import star

Box = Tuple[float, float, float, float]

MUSTER = [("rauten", "Rautengitter"), ("karo", "Karo (doppelt)"), ("waben", "Waben"),
          ("schuppen", "Schuppen"), ("fischgraet", "Fischgrät"), ("wellen", "Wellen"),
          ("holz", "Holzmaserung"), ("streifen", "Streifen schräg"), ("punkte", "Punkte"),
          ("blume", "Blume des Lebens"), ("mandala", "Mandala"), ("strahlen", "Strahlen"),
          ("spitze", "Spitze"), ("ranken", "Ranken"), ("sterne", "Sternenhimmel"),
          ("schneeflocken", "Schneeflocken"), ("herzen", "Herzen"), ("tannen", "Tannenwald")]
MUSTER_KEYS = [k for k, _ in MUSTER]


# ---------------------------------------------------------------------------
# Schnelles Abschneiden über ein Zellgitter
# ---------------------------------------------------------------------------

class Schnell:
    """Beschleunigt Canvas.draw/put für viele kurze Linien. Zellen, durch die keine Kante läuft und
    deren Mitte frei ist, gelten als sicher frei."""

    def __init__(self, cv: dk.Canvas, box: Box, zelle: float = 2.0):
        self.cv = cv
        x0, y0, x1, y1 = box
        self.x0, self.y0, self.g = x0 - zelle, y0 - zelle, zelle
        self.nx = int((x1 - x0) / zelle) + 3
        self.ny = int((y1 - y0) / zelle) + 3
        rand = bytearray(self.nx * self.ny)
        for P in list(cv.inside) + list(cv.blocks):
            for a, b, *_ in P.edges:
                L = dist(a, b)
                n = max(1, int(L / (zelle / 3)) + 1)
                for k in range(n + 1):
                    t = k / n
                    i, j = self._cell((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                    for di in (-1, 0, 1):
                        for dj in (-1, 0, 1):
                            ii, jj = i + di, j + dj
                            if 0 <= ii < self.nx and 0 <= jj < self.ny:
                                rand[jj * self.nx + ii] = 1
        self.frei = bytearray(self.nx * self.ny)
        for j in range(self.ny):
            for i in range(self.nx):
                k = j * self.nx + i
                if not rand[k] and cv.free((self.x0 + (i + 0.5) * zelle, self.y0 + (j + 0.5) * zelle)):
                    self.frei[k] = 1

    def _cell(self, p: Point) -> Tuple[int, int]:
        return int((p[0] - self.x0) / self.g), int((p[1] - self.y0) / self.g)

    def sicher(self, p: Point) -> bool:
        i, j = self._cell(p)
        return 0 <= i < self.nx and 0 <= j < self.ny and self.frei[j * self.nx + i] == 1

    def draw(self, pts: Sequence[Point], closed: bool = False, min_len: float = 0.8) -> None:
        pts = list(pts)
        if closed and len(pts) >= 3:
            if all(self.sicher(p) for p in pts) and _max_seg(pts, True) <= self.g:
                self.cv.part.add_engrave(pts, closed=True)
                return
            pts = pts + [pts[0]]
        runs: List[List[Point]] = []
        cur: List[Point] = []
        for a, b in zip(pts, pts[1:]):
            if dist(a, b) < 1e-9:
                continue
            if dist(a, b) <= self.g and self.sicher(a) and self.sicher(b):
                segs = [(a, b)]
            else:
                segs = self.cv._seg(a, b)
            for s, e in segs:
                if cur and dist(cur[-1], s) < 1e-7:
                    cur.append(e)
                else:
                    if len(cur) >= 2:
                        runs.append(cur)
                    cur = [s, e]
        if len(cur) >= 2:
            runs.append(cur)
        for r in runs:
            if sum(dist(a, b) for a, b in zip(r, r[1:])) >= min_len:
                self.cv.part.add_engrave(r)

    def put(self, pts: Sequence[Point], closed: bool = True) -> bool:
        if len(pts) < 2:
            return False
        if all(self.sicher(p) for p in pts) and _max_seg(pts, closed) <= self.g:
            self.cv.part.add_engrave(pts, closed=closed)
            return True
        return self.cv.put(pts, closed)

    def put_all(self, items: Sequence[Tuple[Sequence[Point], bool]]) -> bool:
        if not items:
            return False
        if all(all(self.sicher(p) for p in pts) and _max_seg(pts, c) <= self.g for pts, c in items):
            for pts, c in items:
                self.cv.part.add_engrave(pts, closed=c)
            return True
        return self.cv.put_all(items)


def _max_seg(pts: Sequence[Point], closed: bool) -> float:
    seq = list(pts) + ([pts[0]] if closed else [])
    return max((dist(a, b) for a, b in zip(seq, seq[1:])), default=0.0)


def _teile(pts: Sequence[Point], step: float) -> List[Point]:
    """Lange Strecken in kurze Stücke teilen (damit das Gitter greift)."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.ceil(dist(a, b) / step)))
        for k in range(1, n + 1):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def _kreis(cx: float, cy: float, r: float, n: int = 0) -> List[Point]:
    n = n or max(12, min(96, int(2 * math.pi * r / 0.6)))
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def _bogen(cx: float, cy: float, r: float, a0: float, a1: float, n: int = 0) -> List[Point]:
    n = n or max(4, int(abs(a1 - a0) * r / 0.6))
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


# ---------------------------------------------------------------------------
# Muster
# ---------------------------------------------------------------------------

def muster(cv: dk.Canvas, art: str, box: Box, abstand: float = 6.0, drehung: float = 0.0, seed: int = 1,
           zentrum: Optional[Point] = None) -> int:
    """Muster `art` in die Leinwand zeichnen. Liefert die Zahl der neuen Gravurlinien."""
    if art not in MUSTER_KEYS:
        raise ValueError(f"Muster {art!r} unbekannt – erlaubt: {', '.join(MUSTER_KEYS)}")
    if not cv.ok:
        return 0
    a = max(1.5, float(abstand))
    vorher = len(cv.part.engrave)
    x0, y0, x1, y1 = box
    cx, cy = zentrum or ((x0 + x1) / 2, (y0 + y1) / 2)
    R = math.hypot(x1 - x0, y1 - y0) / 2 + a          # Radius, der das gedrehte Feld sicher abdeckt
    sn = Schnell(cv, box, zelle=max(1.0, min(3.0, a / 3)))
    rng = random.Random(seed)
    ang = math.radians(drehung)
    ca, sa = math.cos(ang), math.sin(ang)

    def T(pts):
        return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]

    def line(pts, closed=False):
        sn.draw(_teile(T(pts), sn.g) if not closed else T(pts), closed)

    step = sn.g
    if art in ("rauten", "streifen", "karo"):
        winkel = {"rauten": (60.0, 120.0), "streifen": (45.0,), "karo": (0.0, 90.0)}[art]
        for w in winkel:
            u = math.radians(w)
            dx, dy = math.cos(u), math.sin(u)
            nx, ny = -dy, dx
            k = -R
            while k <= R:
                offs = (0.0, a * 0.18) if art == "karo" else (0.0,)
                for o in offs:
                    px, py = nx * (k + o), ny * (k + o)
                    line([(px - dx * R, py - dy * R), (px + dx * R, py + dy * R)])
                k += a
    elif art == "waben":
        r = a / 2
        h = math.sqrt(3) * r
        j = -int(R / h) - 1
        while j * h <= R + h:
            i = -int(R / (1.5 * r)) - 1
            while i * 1.5 * r <= R + r:
                hx, hy = i * 1.5 * r, j * h + (h / 2 if i % 2 else 0.0)
                if math.hypot(hx, hy) <= R + r:
                    hexa = [(hx + r * math.cos(math.pi / 3 * k), hy + r * math.sin(math.pi / 3 * k)) for k in range(6)]
                    line(_teile(hexa + [hexa[0]], step))
                i += 1
            j += 1
    elif art == "schuppen":
        r = a / 2
        row = 0
        y = -R
        while y <= R:
            off = r if row % 2 else 0.0
            x = -R - off
            while x <= R:
                line(_bogen(x + r, y, r, math.pi, 2 * math.pi))
                x += 2 * r
            y += r
            row += 1
    elif art == "fischgraet":
        w = a                                           # Spaltenbreite; Stäbe abwechselnd ±45°
        d = a * 0.32
        col = 0
        x = -R
        while x <= R:
            s_ = 1 if col % 2 == 0 else -1
            y = -R
            while y <= R:
                line([(x, y), (x + w, y + s_ * w)])
                y += d
            col += 1
            x += w
    elif art in ("wellen", "holz"):
        y = -R
        while y <= R:
            pts = []
            ph = rng.uniform(0, 2 * math.pi)
            amp = a * (0.25 if art == "wellen" else rng.uniform(0.08, 0.22))
            lam = a * (2.0 if art == "wellen" else rng.uniform(3.0, 6.0))
            x = -R
            while x <= R:
                yy = y + amp * math.sin(2 * math.pi * x / lam + (ph if art == "holz" else 0.0))
                if art == "holz":
                    yy += amp * 0.5 * math.sin(2 * math.pi * x / (lam * 0.37) + ph * 1.7)
                pts.append((x, yy))
                x += min(step, lam / 12)
            line(pts)
            y += a * (0.5 if art == "wellen" else rng.uniform(0.35, 0.6))
        if art == "holz":                               # Astlöcher
            for _ in range(max(1, int((R * R) / (a * a * 40)))):
                kx, ky = rng.uniform(-R * 0.7, R * 0.7), rng.uniform(-R * 0.7, R * 0.7)
                for s in (1.0, 0.6, 0.3):
                    pts = [(kx + a * 0.9 * s * math.cos(t), ky + a * 0.35 * s * math.sin(t))
                           for t in (2 * math.pi * k / 24 for k in range(24))]
                    sn.put(T(pts))
    elif art == "punkte":
        r = a * 0.14
        row = 0
        y = -R
        while y <= R:
            x = -R + (a / 2 if row % 2 else 0.0)
            while x <= R:
                sn.put(T(_kreis(x, y, r, 12)))
                x += a
            y += a * math.sqrt(3) / 2
            row += 1
    elif art == "blume":
        r = a
        hgt = r * math.sqrt(3) / 2
        j = -int(R / hgt) - 1
        while j * hgt <= R + r:
            i = -int(R / r) - 2
            while i * r <= R + r:
                px, py = i * r + (r / 2 if j % 2 else 0.0), j * hgt
                if math.hypot(px, py) <= R + r:
                    line(_kreis(px, py, r) + [_kreis(px, py, r)[0]])
                i += 1
            j += 1
    elif art == "mandala":
        _mandala(sn, T, R, a)
    elif art == "strahlen":
        n = max(12, int(2 * math.pi * R / a))
        for k in range(n):
            t = 2 * math.pi * k / n
            r0 = a * (0.8 if k % 2 == 0 else 2.2)
            line([(r0 * math.cos(t), r0 * math.sin(t)), (R * math.cos(t), R * math.sin(t))])
        line(_kreis(0, 0, a * 0.6) + [_kreis(0, 0, a * 0.6)[0]])
    elif art == "spitze":
        r = a / 2
        y = -R
        row = 0
        while y <= R:
            off = r if row % 2 else 0.0
            x = -R - off
            while x <= R:
                line(_bogen(x + r, y, r, math.pi, 2 * math.pi))
                line(_bogen(x + r, y, r * 0.62, math.pi * 1.1, math.pi * 1.9))
                sn.put(T(_kreis(x + r, y - r * 0.32, r * 0.14, 10)))
                x += 2 * r
            y += r * 1.25
            row += 1
    elif art == "ranken":
        _ranken(sn, T, R, a, rng)
    elif art in ("sterne", "schneeflocken", "herzen", "tannen"):
        _streuen(sn, T, R, a, art, rng)
    return len(cv.part.engrave) - vorher


def _mandala(sn: Schnell, T, R: float, a: float) -> None:
    """Rosette: Ringe aus Blütenblättern (Linsen), Bögen und Perlen – nach außen immer feiner."""
    def line(pts, closed=False):
        sn.draw(_teile(T(pts), sn.g) if not closed else T(pts), closed)
    r = a * 0.6
    line(_kreis(0, 0, r) + [_kreis(0, 0, r)[0]])
    ring = 0
    while r < R:
        ring += 1
        dr = a * (1.0 + 0.15 * ring)
        n = 6 * (ring + 1)
        r2 = r + dr
        for k in range(n):
            t = 2 * math.pi * (k + (0.5 if ring % 2 else 0.0)) / n
            w = math.pi / n * 0.9
            if ring % 3 == 1:                               # Linsenblatt
                pts = []
                for s in range(9):
                    u = s / 8
                    rr = r + dr * u
                    off = w * math.sin(math.pi * u)
                    pts.append((rr * math.cos(t - off), rr * math.sin(t - off)))
                for s in range(8, -1, -1):
                    u = s / 8
                    rr = r + dr * u
                    off = w * math.sin(math.pi * u)
                    pts.append((rr * math.cos(t + off), rr * math.sin(t + off)))
                line(pts)
            elif ring % 3 == 2:                             # Bogenkranz mit Perle
                ta, tb = t - math.pi / n, t + math.pi / n
                mx, my = (r + dr * 0.25) * math.cos(t), (r + dr * 0.25) * math.sin(t)
                rr = dist((r * math.cos(ta), r * math.sin(ta)), (mx, my))
                line([(r * math.cos(ta + (tb - ta) * s / 10) + (mx - r * math.cos(t)) * math.sin(math.pi * s / 10),
                       r * math.sin(ta + (tb - ta) * s / 10) + (my - r * math.sin(t)) * math.sin(math.pi * s / 10))
                      for s in range(11)])
                pr = min(dr * 0.16, rr * 0.4)
                pc = (r + dr * 0.62) * math.cos(t), (r + dr * 0.62) * math.sin(t)
                sn.put(T(_kreis(pc[0], pc[1], pr, 12)))
            else:                                           # Spitzblatt (Tropfen)
                pts = []
                for s in range(13):
                    u = s / 12
                    ang = t - w * 0.8 + 2 * w * 0.8 * u
                    rr = r + dr * (0.85 * math.sin(math.pi * u) ** 0.6)
                    pts.append((rr * math.cos(ang), rr * math.sin(ang)))
                line(pts)
        line(_kreis(0, 0, r2) + [_kreis(0, 0, r2)[0]])
        r = r2


def _ranken(sn: Schnell, T, R: float, a: float, rng: random.Random) -> None:
    def line(pts):
        sn.draw(_teile(T(pts), sn.g))
    y = -R
    while y <= R:
        lam = a * 4
        pts = []
        x = -R
        while x <= R:
            pts.append((x, y + a * 0.5 * math.sin(2 * math.pi * x / lam)))
            x += sn.g * 0.8
        line(pts)
        x = -R
        k = 0
        while x <= R:
            side = 1 if k % 2 == 0 else -1
            bx = x + lam * 0.25
            by = y + a * 0.5 * math.sin(2 * math.pi * bx / lam)
            # Einrollung (Spirale)
            sp = []
            for s in range(28):
                t = s / 27
                rr = a * 0.55 * (1 - t * 0.85)
                ang = side * (math.pi / 2 + t * 2.6 * math.pi)
                sp.append((bx + a * 0.15 * side + rr * math.cos(ang) * 0.9,
                           by + side * a * 0.55 + rr * math.sin(ang) * side))
            line(sp)
            # Blatt
            lx, ly = bx + lam * 0.25, y + a * 0.5 * math.sin(2 * math.pi * (bx + lam * 0.25) / lam)
            leaf = [(lx + a * 0.5 * u, ly - side * a * 0.32 * math.sin(math.pi * u) - side * a * 0.1 * u) for u in
                    (s / 8 for s in range(9))]
            leaf += [(lx + a * 0.5 * u, ly + side * a * 0.12 * math.sin(math.pi * u) - side * a * 0.1 * u) for u in
                     (s / 8 for s in range(8, -1, -1))]
            line(leaf)
            x += lam / 2
            k += 1
        y += a * 2.2


def _flocke(cx: float, cy: float, r: float) -> List[Tuple[List[Point], bool]]:
    items = []
    for k in range(6):
        t = math.pi / 3 * k
        ux, uy = math.cos(t), math.sin(t)
        items.append(([(cx, cy), (cx + ux * r, cy + uy * r)], False))
        for f in (0.45, 0.72):
            bx, by = cx + ux * r * f, cy + uy * r * f
            L = r * (0.32 if f < 0.6 else 0.22)
            for s in (1, -1):
                tt = t + s * math.pi / 4
                items.append(([(bx, by), (bx + math.cos(tt) * L, by + math.sin(tt) * L)], False))
    return items


def _streuen(sn: Schnell, T, R: float, a: float, art: str, rng: random.Random) -> None:
    """Ornamente locker über die Fläche streuen (gerütteltes Gitter, nur ganz gesetzt)."""
    g = a * 1.6
    j = -R
    while j <= R:
        i = -R
        while i <= R:
            x, y = i + rng.uniform(0.15, 0.85) * g, j + rng.uniform(0.15, 0.85) * g
            s = a * rng.uniform(0.35, 0.6)
            if art == "sterne":
                pts = star(x, y, s, s * 0.45, 5, rng.uniform(0, math.pi))
                sn.put(T(pts))
                if rng.random() < 0.5:                       # Funkelpunkt daneben
                    sn.put(T(_kreis(x + s * 1.1, y - s * 0.9, s * 0.12, 8)))
            elif art == "schneeflocken":
                sn.put_all([(T(p), c) for p, c in _flocke(x, y, s)])
            elif art == "herzen":
                pts = dk.heart(x, y, s * 1.4, s * 1.3, 32)
                sn.put(T(pts))
            else:                                            # Tannen
                h = s * 2.0
                rs = [(0.0, 0.5), (0.24, 0.16), (0.11, 0.16), (0.34, -0.16), (0.15, -0.16), (0.44, -0.46),
                      (0.07, -0.46), (0.07, -0.62)]
                right = [(x + h * u, y + h * v) for u, v in rs]
                left = [(x - h * u, y + h * v) for u, v in reversed(rs[1:])]
                pts = right + left
                sn.put(T(pts))
            i += g
        j += g
