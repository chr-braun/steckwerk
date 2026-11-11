"""
_bilder.py – detailreiche Gravurbilder für Puzzles (und alles, was ein großes Bild braucht).

Jedes Bild wird in eine Box (x0, y0, x1, y1) in mm gezeichnet und liefert reine Linien (Strich-Liste).
Gezeichnet wird von vorne nach hinten: Was vorne steht, verdeckt alles, was danach kommt
(einfache Verdeckungsrechnung über die Umrisse). So entstehen saubere, „gedruckt“ wirkende Szenen.

  winterdorf     Dorf bei Nacht: Fachwerkhäuser mit Schneedächern, Kirche, Tannen, Schneemann, Mond, Sterne
  christbaum     geschmückter Weihnachtsbaum mit Kugeln, Stern, Geschenken, Fenster und Girlande
  mandala        Mandala aus vielen Ringen (Blüten, Perlen, Bögen, Gitter) – im Rechteck mit Eckrosetten
  sternenhimmel  Mond, Sternbilder, Sternschnuppe über einem Wald mit Hütte
  waldtiere      Waldlichtung mit Eule, Igel, Fliegenpilzen, Tannen und Laubbäumen
  muster         Hintergrundmuster (Sterne, Schneeflocken, Rauten, Wellen, Punkte) – z. B. hinter eigenen Motiven

Nur Python-Standardbibliothek; jedes Bild rechnet in Bruchteilen einer Sekunde.
"""
from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from steckwerk import Point, PolygonIndex

Poly = List[Point]
Strich = Tuple[List[Point], bool]

BILDER = [("winterdorf", "Winterdorf bei Nacht"), ("christbaum", "Christbaum mit Geschenken"),
          ("mandala", "Mandala"), ("sternenhimmel", "Sternenhimmel über dem Wald"),
          ("waldtiere", "Waldlichtung mit Eule und Igel")]
MUSTER = [("keins", "keins"), ("sterne", "Sterne"), ("flocken", "Schneeflocken"), ("rauten", "Rauten"),
          ("wellen", "Wellen"), ("punkte", "Punkte")]


# ---------------------------------------------------------------------------------------------
# Zeichenfläche mit Verdeckung
# ---------------------------------------------------------------------------------------------

def _bb(pts: Sequence[Point]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


class _Deckel:
    __slots__ = ("pts", "ix", "bb", "kanten")

    def __init__(self, pts: Poly):
        self.pts = pts
        self.ix = PolygonIndex(pts)
        self.bb = _bb(pts)
        n = len(pts)
        self.kanten = [(pts[i][0], pts[i][1], pts[(i + 1) % n][0], pts[(i + 1) % n][1]) for i in range(n)]


class Bild:
    """Sammelt Gravurlinien; `decke` macht eine Fläche undurchsichtig für alles, was danach kommt."""

    def __init__(self, box: Tuple[float, float, float, float], seed: int = 1):
        self.box = box
        self.striche: List[Strich] = []
        self.deckel: List[_Deckel] = []
        self.rng = random.Random(seed)

    # -- Verdeckung ---------------------------------------------------------------------------
    def decke(self, poly: Sequence[Point]) -> None:
        if len(poly) >= 3:
            self.deckel.append(_Deckel(list(poly)))

    def _sichtbar(self, a: Point, b: Point, ds: Sequence[_Deckel]) -> List[Tuple[float, float]]:
        dx, dy = b[0] - a[0], b[1] - a[1]
        x0, y0, x1, y1 = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
        ts = [0.0, 1.0]
        aktiv = []
        for d in ds:
            bb = d.bb
            if x1 < bb[0] or x0 > bb[2] or y1 < bb[1] or y0 > bb[3]:
                continue
            aktiv.append(d)
            for ex0, ey0, ex1, ey1 in d.kanten:
                if (ex0 if ex0 > ex1 else ex1) < x0 or (ex0 if ex0 < ex1 else ex1) > x1 or \
                        (ey0 if ey0 > ey1 else ey1) < y0 or (ey0 if ey0 < ey1 else ey1) > y1:
                    continue
                ex, ey = ex1 - ex0, ey1 - ey0
                den = dx * ey - dy * ex
                if abs(den) < 1e-12:
                    continue
                t = ((ex0 - a[0]) * ey - (ey0 - a[1]) * ex) / den
                u = ((ex0 - a[0]) * dy - (ey0 - a[1]) * dx) / den
                if 0.0 < t < 1.0 and 0.0 <= u <= 1.0:
                    ts.append(t)
        if not aktiv:
            return [(0.0, 1.0)]
        ts.sort()
        keep: List[Tuple[float, float]] = []
        for t0, t1 in zip(ts, ts[1:]):
            if t1 - t0 < 1e-9:
                continue
            tm = (t0 + t1) / 2
            m = (a[0] + dx * tm, a[1] + dy * tm)
            if any(d.bb[0] <= m[0] <= d.bb[2] and d.bb[1] <= m[1] <= d.bb[3] and d.ix.contains(m) for d in aktiv):
                continue
            if keep and abs(keep[-1][1] - t0) < 1e-9:
                keep[-1] = (keep[-1][0], t1)
            else:
                keep.append((t0, t1))
        return keep

    def linie(self, pts: Sequence[Point], closed: bool = False) -> None:
        pts = list(pts)
        if len(pts) < 2:
            return
        sb = _bb(pts)
        ds = [d for d in self.deckel if not (sb[2] < d.bb[0] or sb[0] > d.bb[2] or sb[3] < d.bb[1] or sb[1] > d.bb[3])]
        if not ds:
            self.striche.append((pts, closed))
            return
        seq = pts + ([pts[0]] if closed else [])
        runs: List[Poly] = []
        cur: Poly = []
        for a, b in zip(seq, seq[1:]):
            if a == b:
                continue
            for t0, t1 in self._sichtbar(a, b, ds):
                s = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
                e = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
                if cur and abs(cur[-1][0] - s[0]) < 1e-7 and abs(cur[-1][1] - s[1]) < 1e-7:
                    cur.append(e)
                else:
                    if len(cur) >= 2:
                        runs.append(cur)
                    cur = [s, e]
        if len(cur) >= 2:
            runs.append(cur)
        if closed and len(runs) == 1 and len(runs[0]) == len(seq) and runs[0][0] == seq[0]:
            self.striche.append((pts, True))
            return
        for r in runs:
            self.striche.append((r, False))

    def form(self, poly: Sequence[Point], deckt: bool = True) -> None:
        """Umriss zeichnen und (standardmäßig) die Fläche als Verdeckung eintragen."""
        self.linie(poly, True)
        if deckt:
            self.decke(poly)

    def schraffur(self, poly: Sequence[Point], abstand: float, winkel: float = 0.0,
                  loecher: Sequence[Sequence[Point]] = ()) -> None:
        for seg in schraffur([list(poly)] + [list(h) for h in loecher], abstand, winkel):
            self.linie(seg)


def schraffur(polys: Sequence[Sequence[Point]], step: float, angle: float = 0.0) -> List[Poly]:
    """Schraffur nach Gerade-/Ungerade-Regel im Abstand step, Winkel in Grad, Zeilen im Zickzack."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    rot = [[(x * ca + y * sa, -x * sa + y * ca) for x, y in p] for p in polys if len(p) >= 3]
    ys = [y for p in rot for _, y in p]
    if not ys:
        return []
    y = min(ys) + step / 2
    out: List[Poly] = []
    flip = False
    while y < max(ys):
        xs = []
        for p in rot:
            n = len(p)
            for i in range(n):
                (x0, y0), (x1, y1) = p[i], p[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        segs = [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]
        if flip:
            segs = [(q, p) for p, q in reversed(segs)]
        for x0, x1 in segs:
            if abs(x1 - x0) > 0.25:
                out.append([(x0 * ca - y * sa, x0 * sa + y * ca), (x1 * ca - y * sa, x1 * sa + y * ca)])
        flip = not flip
        y += step
    return out


# ---------------------------------------------------------------------------------------------
# Formen
# ---------------------------------------------------------------------------------------------

def kreis(cx: float, cy: float, r: float, n: int = 0) -> Poly:
    n = n or max(12, min(160, int(2 * math.pi * r / 0.6)))
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def ellipse(cx: float, cy: float, rx: float, ry: float, rot: float = 0.0, n: int = 0) -> Poly:
    n = n or max(16, min(160, int(math.pi * (rx + ry) / 0.6)))
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for k in range(n):
        t = 2 * math.pi * k / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def stern(cx: float, cy: float, r: float, ri: float, n: int = 5, rot: float = 0.0) -> Poly:
    out = []
    for k in range(2 * n):
        a = math.pi / 2 + rot + k * math.pi / n
        rr = r if k % 2 == 0 else ri
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return out


def blatt(cx: float, cy: float, laenge: float, breite: float, winkel: float, n: int = 14) -> Poly:
    """Spitzes Blütenblatt (Mandorla) von (cx, cy) aus in Richtung winkel."""
    c, s = math.cos(winkel), math.sin(winkel)
    pts = []
    for k in range(n + 1):
        t = k / n
        pts.append((t * laenge, breite / 2 * math.sin(math.pi * t)))
    for k in range(n - 1, 0, -1):
        t = k / n
        pts.append((t * laenge, -breite / 2 * math.sin(math.pi * t)))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def herz(cx: float, cy: float, w: float, h: float, n: int = 48) -> Poly:
    out = []
    for k in range(n):
        t = 2 * math.pi * k / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        out.append((cx + x / 32 * w, cy + (y + 2.5) / 30 * h))
    return out


def flocke(b: Bild, cx: float, cy: float, r: float, rot: float = 0.0, fein: bool = True) -> None:
    for k in range(6):
        a = rot + math.pi / 2 + k * math.pi / 3
        ux, uy = math.cos(a), math.sin(a)
        b.linie([(cx, cy), (cx + ux * r, cy + uy * r)])
        for t, L in ((0.45, 0.34), (0.72, 0.24)) if fein else ((0.55, 0.3),):
            bx, by = cx + ux * r * t, cy + uy * r * t
            for sgn in (-1, 1):
                q = a + sgn * math.pi / 3.3
                b.linie([(bx, by), (bx + math.cos(q) * r * L, by + math.sin(q) * r * L)])


def funkeln(b: Bild, cx: float, cy: float, r: float) -> None:
    """Vierzackiger Funkelstern mit geschwungenen Flanken."""
    pts = []
    for k in range(4):
        a = math.pi / 2 + k * math.pi / 2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        m = a + math.pi / 4
        pts.append((cx + 0.22 * r * math.cos(m), cy + 0.22 * r * math.sin(m)))
    b.form(pts)


def welle(x0: float, x1: float, y: float, amp: float, lam: float, phase: float = 0.0) -> Poly:
    n = max(8, int(abs(x1 - x0) / 0.8))
    return [(x0 + (x1 - x0) * k / n, y + amp * math.sin(phase + 2 * math.pi * (x0 + (x1 - x0) * k / n) / lam))
            for k in range(n + 1)]


def bogenreihe(x0: float, x1: float, y: float, r: float, unten: bool = True) -> Poly:
    """Reihe kleiner Halbkreise (Schneekante, Schuppen)."""
    n = max(1, int(round((x1 - x0) / (2 * r))))
    rr = (x1 - x0) / (2 * n)
    pts = []
    for i in range(n):
        cx = x0 + rr * (2 * i + 1)
        for k in range(9):
            a = math.pi - math.pi * k / 8
            pts.append((cx + rr * math.cos(a), y + (-1 if unten else 1) * rr * math.sin(a)))
    return pts


def tannen_etagen(cx: float, y0: float, w: float, h: float, etagen: int = 4):
    """Tanne mit überstehenden Etagen; Mitte unten bei (cx, y0), ohne Stamm.
    Liefert (Umriss, Etagen) mit Etagen = [(y_unten, halbe_breite, y_absatz_oben, x_absatz)]."""
    top = y0 + h
    dy = h * 0.74 / etagen
    et = []
    for e in range(etagen):
        yb = y0 + e * dy
        ww = w / 2 * (1 - 0.5 * e / etagen)
        et.append((yb, ww))
    rechts: Poly = []
    info = []
    for e, (yb, ww) in enumerate(et):
        if e > 0:
            rechts.append((cx + (ww + rechts[-1][0] - cx) / 2, yb - 0.025 * h))   # leicht hängender Absatz
        rechts.append((cx + ww, yb))
        if e + 1 < etagen:
            yn = et[e + 1][0]
            spitze = yb + 0.42 * h * (1 - 0.2 * e / etagen)
            xs = ww * (1 - (yn - yb) / (spitze - yb))
            rechts.append((cx + xs, yn + 0.01 * h))
            info.append((yb, ww, yn, xs))
        else:
            info.append((yb, ww, top, 0.0))
    rechts.append((cx, top))
    # Unterkante der untersten Etage: flache Bögen
    unten: Poly = []
    n = max(2, int(w / max(4.0, 0.22 * w)))
    for i in range(n):
        xa = cx + w / 2 - w * i / n
        for k in range(1, 7):
            t = k / 6
            unten.append((xa - w / n * t, y0 - 0.035 * h * math.sin(math.pi * t)))
    links = [(2 * cx - x, y) for x, y in reversed(rechts[:-1])]
    return rechts + links + unten[::-1][1:], info


def tanne(b: Bild, cx: float, y0: float, w: float, h: float, schnee: bool = True, detail: int = 2) -> None:
    stamm_h = 0.1 * h
    etagen = 5 if h > 45 else 4 if h > 18 else 3
    um, info = tannen_etagen(cx, y0 + stamm_h, w, h - stamm_h, etagen)
    b.linie(um, True)
    if detail >= 1:                       # Nadeln: feine Striche unter jedem Absatz
        for yb, ww, yn, xs in info:
            n = max(2, int(2 * ww / 1.4))
            for i in range(1, n):
                x = -ww * 0.85 + 1.7 * ww * i / n
                L = min(0.18 * (yn - yb), 2.5)
                b.linie([(cx + x, yb + 0.6), (cx + x * 0.92, yb + 0.6 + L)])
    if schnee:                            # Schneehauben auf den Absätzen
        for yb, ww, yn, xs in info[:-1]:
            hw = xs + (ww - xs) * 0.2
            pts = [(cx - hw + 2 * hw * k / 10, yn + 0.012 * h + 0.025 * h * math.sin(math.pi * k / 10)
                    + 0.01 * h * math.sin(k * 2.1)) for k in range(11)]
            b.linie(pts)
    b.decke(um)
    sw = max(0.8, 0.07 * w)
    st = [(cx - sw, y0), (cx + sw, y0), (cx + sw, y0 + stamm_h + 0.5), (cx - sw, y0 + stamm_h + 0.5)]
    b.form(st)


def laubbaum(b: Bild, cx: float, y0: float, w: float, h: float, rng: random.Random) -> None:
    """Laubbaum: wolkige Krone aus Bögen, Blätter-Striche, Stamm mit Rinde und Ästen."""
    kh = 0.68 * h
    ky = y0 + h - kh / 2
    n = 14
    krone = []
    for k in range(n):
        a = 2 * math.pi * k / n
        r0 = 1.0 + 0.12 * math.sin(3 * a + 1)
        p0 = (cx + w / 2 * r0 * math.cos(a), ky + kh / 2 * r0 * math.sin(a))
        a1 = 2 * math.pi * (k + 1) / n
        r1 = 1.0 + 0.12 * math.sin(3 * a1 + 1)
        p1 = (cx + w / 2 * r1 * math.cos(a1), ky + kh / 2 * r1 * math.sin(a1))
        m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        out = (m[0] - cx, (m[1] - ky) * w / kh)
        L = math.hypot(*out) or 1
        bul = 0.12 * w
        c = (m[0] + out[0] / L * bul, m[1] + out[1] / L * bul * kh / w)
        for i in range(6):
            t = i / 6
            krone.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
                          (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]))
    b.linie(krone, True)
    for _ in range(int(w * kh / 14)):     # Blätter-Häkchen
        x = cx + rng.uniform(-0.38, 0.38) * w
        y = ky + rng.uniform(-0.36, 0.36) * kh
        if ((x - cx) / (w * 0.45)) ** 2 + ((y - ky) / (kh * 0.45)) ** 2 < 1:
            s = rng.uniform(0.7, 1.2)
            b.linie([(x - s, y), (x, y - 0.5 * s), (x + s, y)])
    b.decke(krone)
    sw = max(1.0, 0.09 * w)
    stamm = [(cx - sw * 1.4, y0), (cx - sw, y0 + 0.5), (cx - sw * 0.8, ky - kh * 0.3), (cx + sw * 0.8, ky - kh * 0.3),
             (cx + sw, y0 + 0.5), (cx + sw * 1.4, y0)]
    b.linie(stamm)
    b.linie([(cx - sw * 0.2, y0 + 1), (cx - sw * 0.35, ky - kh * 0.35)])
    b.linie([(cx + sw * 0.3, y0 + 2), (cx + sw * 0.2, ky - kh * 0.4)])
    b.decke(stamm + [(cx, ky)])


# ---------------------------------------------------------------------------------------------
# Szenen
# ---------------------------------------------------------------------------------------------

def _haus(b: Bild, x: float, y: float, w: float, h: float, rng: random.Random, kirche: bool = False) -> None:
    """Fachwerkhaus mit Schneedach, Fenstern, Tür und Schornstein; (x, y) = links unten."""
    dach_h = w * rng.uniform(0.45, 0.6)
    ue = 0.08 * w
    # Schornstein (hinter dem Dach, darum zuerst Dach zeichnen und decken)
    giebel = [(x - ue, y + h), (x + w + ue, y + h), (x + w / 2, y + h + dach_h)]
    # Schneekante am Dach
    sk = 0.13 * dach_h
    schnee = [(x - ue - 0.4, y + h - 0.2)] + \
        [(x - ue + (w + 2 * ue) * k / 10, y + h - sk * (0.6 + 0.4 * math.sin(k * 1.7 + x))) for k in range(11)] + \
        [(x + w + ue + 0.4, y + h - 0.2), (x + w / 2, y + h + dach_h + 0.6)]
    b.linie(schnee, True)
    # Dachziegel: Bogenreihen zwischen Schneekante und First
    zr = max(0.9, 0.045 * w)
    reihe = y + h + 2.2 * zr
    while reihe < y + h + dach_h * 0.72:
        f = (reihe - y - h) / dach_h
        hw = (w / 2 + ue) * (1 - f) - zr * 0.8
        if hw > 2 * zr:
            b.linie(bogenreihe(x + w / 2 - hw, x + w / 2 + hw, reihe, zr))
        reihe += 1.7 * zr
    b.decke(schnee)
    b.decke(giebel)
    if not kirche:
        sx = x + w * rng.uniform(0.62, 0.74)
        sw = 0.11 * w
        sy0 = y + h + dach_h * (1 - (sx + sw - x - w / 2) / (w / 2 + ue)) * 0.95
        sy1 = y + h + dach_h * 0.95
        sch = [(sx, sy0 - 1), (sx + sw, sy0 - 1), (sx + sw, sy1), (sx - 0.3, sy1), (sx - 0.3, sy1 - 1.2), (sx, sy1 - 1.2)]
        b.linie(sch, True)
        b.linie(bogenreihe(sx - 0.3, sx + sw + 0.3, sy1, (sw + 0.6) / 4, unten=False))
        # Rauch: drei Kringel
        rx, ry = sx + sw / 2, sy1 + 1.5
        rauch = []
        for k in range(60):
            t = k / 59
            rauch.append((rx + 2.2 * math.sin(t * 9) * (0.5 + t) + t * 6, ry + t * 0.9 * dach_h))
        b.linie(rauch)
        b.decke(sch)
    # Wand
    wand = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    b.linie(wand, True)
    # Fachwerk: Rahmen und Kreuzstreben im oberen Teil
    if not kirche and h > 10:
        b.linie([(x, y + h * 0.55), (x + w, y + h * 0.55)])
        nfeld = max(2, int(w / (0.32 * h)))
        for i in range(1, nfeld):
            b.linie([(x + w * i / nfeld, y + h * 0.55), (x + w * i / nfeld, y + h)])
    # Tür mit Bogen
    tw = 0.22 * w
    tx = x + w * (0.18 if not kirche else 0.5 - 0.11)
    th = 0.42 * h
    tur = [(tx, y), (tx + tw, y), (tx + tw, y + th)] + \
        [(tx + tw / 2 + tw / 2 * math.cos(math.pi * k / 8), y + th + tw / 2 * math.sin(math.pi * k / 8))
         for k in range(1, 8)] + [(tx, y + th)]
    b.linie(tur, True)
    b.linie([(tx + tw / 2, y), (tx + tw / 2, y + th + tw / 2)])
    b.linie(kreis(tx + tw * 0.38, y + th * 0.55, 0.35, 8), True)
    b.decke(tur)
    # Fenster: Rahmen, Sprossen, Fensterbank mit Schnee, leuchtend schraffiert
    fw = 0.2 * w
    fh = 0.22 * h if h > 10 else 0.3 * h
    fen = []
    if kirche:
        fen = [(x + w / 2 - fw / 2, y + h * 0.62)]
    else:
        fen = [(x + w * 0.56, y + h * 0.18), (x + w * 0.18, y + h * 0.66), (x + w * 0.6, y + h * 0.66)]
    for fx, fy in fen:
        if kirche:
            r = fw / 2
            f = [(fx, fy), (fx + fw, fy), (fx + fw, fy + fh)] + \
                [(fx + r + r * math.cos(math.pi * k / 10), fy + fh + r * math.sin(math.pi * k / 10)) for k in range(1, 10)] + \
                [(fx, fy + fh)]
            b.linie(f, True)
            b.schraffur(f, 0.55, 45)
            b.linie([(fx + fw / 2, fy), (fx + fw / 2, fy + fh + r)])
            b.decke(f)
            continue
        f = [(fx, fy), (fx + fw, fy), (fx + fw, fy + fh), (fx, fy + fh)]
        b.linie(f, True)
        b.linie([(fx + fw / 2, fy), (fx + fw / 2, fy + fh)])
        b.linie([(fx, fy + fh / 2), (fx + fw, fy + fh / 2)])
        b.linie([(fx - 0.6, fy - 0.2), (fx + fw + 0.6, fy - 0.2)])
        b.linie(bogenreihe(fx - 0.6, fx + fw + 0.6, fy - 0.2, 0.55, unten=False))
        # Fensterläden
        b.linie([(fx - 0.35 * fw, fy), (fx - 0.05, fy), (fx - 0.05, fy + fh), (fx - 0.35 * fw, fy + fh)], True)
        b.linie([(fx + fw + 0.05, fy), (fx + 1.35 * fw, fy), (fx + 1.35 * fw, fy + fh), (fx + fw + 0.05, fy + fh)], True)
        b.decke([(fx - 0.35 * fw - 0.1, fy - 0.8), (fx + 1.35 * fw + 0.1, fy - 0.8), (fx + 1.35 * fw + 0.1, fy + fh + 0.1),
                 (fx - 0.35 * fw - 0.1, fy + fh + 0.1)])
    # Holzbretter-Struktur im unteren Wandteil
    yy = y + 1.4
    while yy < y + h * (0.5 if not kirche else 0.95):
        b.linie([(x, yy), (x + w, yy)])
        yy += 1.5 if not kirche else 2.0
    b.decke(wand)


def _kirche(b: Bild, x: float, y: float, w: float, h: float, rng: random.Random) -> None:
    """Kirche mit Turm, Uhr und Zwiebelhelm; (x, y) = links unten des Schiffs."""
    tw = 0.42 * w
    tx = x + w - tw * 0.3
    th = h * 1.9
    # Turm vorne
    turm = [(tx, y), (tx + tw, y), (tx + tw, y + th), (tx, y + th)]
    b.linie(turm, True)
    uc = (tx + tw / 2, y + th * 0.78)
    ur = tw * 0.3
    b.linie(kreis(uc[0], uc[1], ur), True)
    b.linie(kreis(uc[0], uc[1], ur * 0.82), True)
    for k in range(12):
        a = math.pi / 2 - k * math.pi / 6
        b.linie([(uc[0] + ur * 0.62 * math.cos(a), uc[1] + ur * 0.62 * math.sin(a)),
                 (uc[0] + ur * 0.78 * math.cos(a), uc[1] + ur * 0.78 * math.sin(a))])
    b.linie([uc, (uc[0], uc[1] + ur * 0.55)])
    b.linie([uc, (uc[0] + ur * 0.4, uc[1] - ur * 0.15)])
    sf = [(tx + tw * 0.32, y + th * 0.4), (tx + tw * 0.68, y + th * 0.4), (tx + tw * 0.68, y + th * 0.6)] + \
        [(tx + tw / 2 + tw * 0.18 * math.cos(math.pi * k / 8), y + th * 0.6 + tw * 0.18 * math.sin(math.pi * k / 8))
         for k in range(1, 8)] + [(tx + tw * 0.32, y + th * 0.6)]
    b.linie(sf, True)
    b.schraffur(sf, 0.55, 45)
    b.decke(sf)
    # Zwiebelhelm + Kreuz
    hx, hy = tx + tw / 2, y + th
    prof = [(0.42, 0.0), (0.6, 0.1), (0.7, 0.26), (0.66, 0.42), (0.5, 0.58), (0.3, 0.72), (0.14, 0.84),
            (0.07, 0.93), (0.0, 1.0)]
    zw = [(hx + px * tw, hy + py * tw * 1.5) for px, py in prof]
    zw = zw + [(2 * hx - px, py) for px, py in reversed(zw[:-1])]
    b.linie([(hx - 0.6 * tw, hy + 0.15 * tw), (hx + 0.6 * tw, hy + 0.15 * tw)])
    b.linie(zw, True)
    b.linie([(hx, hy + tw * 1.5), (hx, hy + tw * 2.0)])
    b.linie([(hx - tw * 0.14, hy + tw * 1.82), (hx + tw * 0.14, hy + tw * 1.82)])
    b.decke(zw)
    yy = y + 2.0
    while yy < y + th * 0.36:
        b.linie([(tx, yy), (tx + tw, yy)])
        for i in range(3):
            xo = tx + tw * (i + (0.5 if int((yy - y) / 2) % 2 else 0)) / 3
            b.linie([(xo, yy), (xo, yy + 2.0)])
        yy += 2.0
    b.decke(turm)
    _haus(b, x, y, w * 0.85, h, rng, kirche=True)


def _schneemann(b: Bild, cx: float, y0: float, h: float) -> None:
    r1, r2, r3 = 0.22 * h, 0.16 * h, 0.115 * h
    c3 = (cx, y0 + 2 * r1 + 2 * r2 + r3 - 0.1 * h)
    c2 = (cx, y0 + 2 * r1 + r2 - 0.05 * h)
    c1 = (cx, y0 + r1)
    # Hut
    hw = r3 * 0.85
    hut = [(cx - hw * 1.35, c3[1] + r3 * 0.7), (cx + hw * 1.35, c3[1] + r3 * 0.7), (cx + hw * 1.35, c3[1] + r3 * 0.85),
           (cx + hw, c3[1] + r3 * 0.85), (cx + hw, c3[1] + r3 * 1.9), (cx - hw, c3[1] + r3 * 1.9),
           (cx - hw, c3[1] + r3 * 0.85), (cx - hw * 1.35, c3[1] + r3 * 0.85)]
    b.form(hut)
    b.linie([(cx - hw, c3[1] + r3 * 1.05), (cx + hw, c3[1] + r3 * 1.05)])
    # Kopf: Augen, Karottennase, Kohlemund
    b.linie(kreis(cx - r3 * 0.35, c3[1] + r3 * 0.25, max(0.35, r3 * 0.09), 10), True)
    b.linie(kreis(cx + r3 * 0.35, c3[1] + r3 * 0.25, max(0.35, r3 * 0.09), 10), True)
    b.linie([(cx, c3[1] + 0.06 * r3), (cx + r3 * 0.9, c3[1] - 0.05 * r3), (cx, c3[1] - 0.12 * r3)], True)
    for k in range(5):
        a = math.pi * (1.25 + 0.125 * k)
        b.linie(kreis(cx + r3 * 0.55 * math.cos(a), c3[1] + r3 * 0.55 * math.sin(a), max(0.25, r3 * 0.06), 8), True)
    b.form(kreis(c3[0], c3[1], r3))
    # Schal
    sch = [(cx - r3 * 1.05, c3[1] - r3 * 0.75), (cx + r3 * 1.05, c3[1] - r3 * 0.75), (cx + r3 * 1.0, c3[1] - r3 * 1.15),
           (cx + r3 * 0.8, c3[1] - r3 * 1.2), (cx + r3 * 0.95, c3[1] - r3 * 2.4), (cx + r3 * 0.45, c3[1] - r3 * 2.3),
           (cx + r3 * 0.4, c3[1] - r3 * 1.2), (cx - r3 * 1.0, c3[1] - r3 * 1.15)]
    b.linie(sch, True)
    for k in range(1, 4):
        b.linie([(cx - r3 * (1.0 - 0.5 * k), c3[1] - r3 * 0.75), (cx - r3 * (1.0 - 0.5 * k), c3[1] - r3 * 1.15)])
    b.decke(sch)
    # Bauch: Knöpfe, Arme
    for k in range(3):
        b.linie(kreis(cx, c2[1] + r2 * (0.45 - 0.42 * k), max(0.35, r2 * 0.08), 10), True)
    b.form(kreis(c2[0], c2[1], r2))
    for sg in (-1, 1):
        ax = cx + sg * r2 * 0.95
        b.linie([(ax, c2[1] + r2 * 0.2), (ax + sg * r2 * 1.3, c2[1] + r2 * 0.95)])
        b.linie([(ax + sg * r2 * 1.0, c2[1] + r2 * 0.75), (ax + sg * r2 * 1.05, c2[1] + r2 * 1.15)])
        b.linie([(ax + sg * r2 * 1.0, c2[1] + r2 * 0.75), (ax + sg * r2 * 1.4, c2[1] + r2 * 0.7)])
    b.form(kreis(c1[0], c1[1], r1))


def _himmel(b: Bild, x0: float, y0: float, x1: float, y1: float, rng: random.Random, dichte: float = 1.0,
            flocken: bool = True) -> None:
    """Sterne, Funkeln und Schneeflocken verteilt (mit Mindestabstand)."""
    W, H = x1 - x0, y1 - y0
    plaetze: List[Tuple[float, float, float]] = []
    n = int(W * H / 140 * dichte)
    for _ in range(n * 4):
        if len(plaetze) >= n:
            break
        x, y = rng.uniform(x0 + 2, x1 - 2), rng.uniform(y0 + 2, y1 - 2)
        r = rng.choice((0.6, 0.8, 1.0, 1.3, 1.8, 2.4)) * (1 + min(W, H) / 400)
        if any(math.hypot(x - a, y - c) < r + rr + 1.6 for a, c, rr in plaetze):
            continue
        plaetze.append((x, y, r))
    for x, y, r in plaetze:
        k = rng.random()
        if r < 0.9:
            b.form(kreis(x, y, r * 0.45, 8))
        elif k < 0.45:
            b.form(stern(x, y, r, r * 0.42, 5, rng.uniform(-0.3, 0.3)))
        elif k < 0.7 or not flocken:
            funkeln(b, x, y, r * 1.2)
        else:
            flocke(b, x, y, r * 1.15, rng.uniform(0, 1), fein=r > 1.5)
            b.decke(kreis(x, y, r * 1.15, 12))


def _mond(b: Bild, cx: float, cy: float, r: float) -> None:
    """Sichelmond mit Kratern, feiner Schraffur und Lichtkranz."""
    aussen = kreis(cx, cy, r, 96)
    sichel = []
    for k in range(49):
        a = math.pi / 2 + math.pi * k / 48
        sichel.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    for k in range(1, 48):
        a = 3 * math.pi / 2 - math.pi * k / 48
        sichel.append((cx + 0.35 * r * math.cos(a) - 0.0, cy + r * math.sin(a)))
    b.linie(sichel, True)
    for dx, dy, rr in ((-0.55, 0.25, 0.12), (-0.45, -0.35, 0.09), (-0.7, -0.05, 0.07), (-0.3, 0.6, 0.06)):
        b.linie(kreis(cx + dx * r, cy + dy * r, rr * r, 16), True)
    b.schraffur(sichel, max(0.6, r / 14), 60)
    b.decke(sichel)
    for k in range(16):                    # Lichtstrahlen um den Mond (kurz, unterbrochen)
        a = 2 * math.pi * k / 16
        b.linie([(cx + 1.25 * r * math.cos(a), cy + 1.25 * r * math.sin(a)),
                 (cx + (1.4 + 0.12 * (k % 2)) * r * math.cos(a), cy + (1.4 + 0.12 * (k % 2)) * r * math.sin(a))])
    b.decke(kreis(cx, cy, r * 1.55, 48))
    del aussen


def winterdorf(box, seed: int = 1) -> List[Strich]:
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    rng = random.Random(seed)
    b = Bild(box, seed)
    boden = y0 + 0.2 * H
    s = min(W, H)
    # Vordergrund: Schneemann rechts, große Tannen an den Rändern, Zaun
    _schneemann(b, x0 + W * 0.8, y0 + 0.05 * H, 0.32 * H)
    tanne(b, x0 + W * 0.07, y0 + 0.02 * H, 0.2 * W, 0.62 * H)
    tanne(b, x0 + W * 0.93, y0 + 0.02 * H, 0.16 * W, 0.5 * H)
    zy = y0 + 0.1 * H
    zh = 0.07 * H
    x = x0 + 0.16 * W
    while x < x0 + 0.66 * W:
        lat = [(x, zy), (x + 1.6, zy), (x + 1.6, zy + zh), (x + 0.8, zy + zh + 1.2), (x, zy + zh)]
        b.form(lat)
        x += 3.6
    b.linie([(x0 + 0.16 * W, zy + zh * 0.35), (x0 + 0.66 * W, zy + zh * 0.35)])
    b.linie([(x0 + 0.16 * W, zy + zh * 0.75), (x0 + 0.66 * W, zy + zh * 0.75)])
    b.decke([(x0 + 0.16 * W, zy + zh * 0.25), (x0 + 0.66 * W, zy + zh * 0.25), (x0 + 0.66 * W, zy + zh * 0.85),
             (x0 + 0.16 * W, zy + zh * 0.85)])
    # Schneeverwehung vorne
    b.linie(welle(x0, x1, y0 + 0.07 * H, 0.012 * H, 0.33 * W, 0.6))
    # Häuser in einer Reihe, Kirche in der Mitte
    nh = max(3, min(7, int(W / (0.16 * W + 6))))
    breiten = [rng.uniform(0.11, 0.15) * W for _ in range(nh)]
    ges = sum(breiten) + 0.03 * W * (nh - 1)
    if ges > 0.84 * W:
        f = 0.84 * W / ges
        breiten = [bw * f for bw in breiten]
        ges = 0.84 * W
    x = x0 + (W - ges) / 2
    mitte = nh // 2
    for i, bw in enumerate(breiten):
        hh = bw * rng.uniform(0.7, 0.95)
        yy = boden + rng.uniform(-0.01, 0.02) * H
        if i == mitte:
            _kirche(b, x, yy, bw * 1.1, hh * 0.95, rng)
        else:
            _haus(b, x, yy, bw, hh, rng)
        x += bw + 0.03 * W
    # Hügel mit kleinen Tannen
    hy = boden + 0.18 * H
    b.linie(welle(x0, x1, hy, 0.03 * H, 0.7 * W, 1.0))
    b.linie(welle(x0, x1, hy + 0.06 * H, 0.025 * H, 0.45 * W, 2.4))
    for k in range(int(W / 9)):
        tx = x0 + rng.uniform(0.02, 0.98) * W
        ty = hy + 0.03 * H * math.sin(1.0 + 2 * math.pi * tx / (0.7 * W)) - 0.3
        hgt = rng.uniform(0.05, 0.09) * H
        tanne(b, tx, ty, hgt * 0.55, hgt, schnee=False, detail=0)
    b.decke([(x0, y0)] + welle(x0, x1, hy + 0.06 * H, 0.025 * H, 0.45 * W, 2.4)[::-1][::-1] + [(x1, y0)])
    # Himmel: Mond und Sterne
    _mond(b, x0 + W * 0.2, y1 - 0.2 * H, 0.09 * s)
    _himmel(b, x0, hy, x1, y1, rng, 1.0)
    return b.striche


def _kugel(b: Bild, cx: float, cy: float, r: float, art: int) -> None:
    """Christbaumkugel mit Kappe und Muster."""
    kap = [(cx - r * 0.3, cy + r * 0.9), (cx + r * 0.3, cy + r * 0.9), (cx + r * 0.3, cy + r * 1.2),
           (cx - r * 0.3, cy + r * 1.2)]
    b.form(kap)
    b.linie(kreis(cx, cy + r * 1.38, r * 0.18, 10), True)
    um = kreis(cx, cy, r)
    b.linie(um, True)
    if art == 0:                                    # Bänder mit Zickzack
        for dy in (-0.3, 0.3):
            hw = r * math.sqrt(1 - dy * dy)
            b.linie([(cx - hw, cy + dy * r), (cx + hw, cy + dy * r)])
        n = 6
        pts = [(cx - r * 0.95 + 1.9 * r * k / n, cy + (0.2 if k % 2 else -0.2) * r) for k in range(n + 1)]
        b.linie(pts)
    elif art == 1:                                  # Stern
        b.linie(stern(cx, cy, r * 0.62, r * 0.27, 5), True)
    elif art == 2:                                  # Punkte im Ring
        for k in range(8):
            a = 2 * math.pi * k / 8
            b.linie(kreis(cx + r * 0.6 * math.cos(a), cy + r * 0.6 * math.sin(a), r * 0.1, 8), True)
        b.linie(kreis(cx, cy, r * 0.25, 12), True)
    else:                                           # Glanz + schräge Streifen
        for k in range(-2, 3):
            pts = []
            for i in range(9):
                t = -1 + 2 * i / 8
                x = cx + t * r
                y = cy + k * 0.35 * r + t * 0.35 * r
                if (x - cx) ** 2 + (y - cy) ** 2 < (0.92 * r) ** 2:
                    pts.append((x, y))
            if len(pts) >= 2:
                b.linie(pts)
    b.linie([(cx - r * 0.55 + r * 0.45 * math.cos(a), cy + r * 0.45 * math.sin(a))
             for a in [math.pi * (0.55 + 0.05 * k) for k in range(7)]])
    b.decke(um + [])


def _geschenk(b: Bild, x: float, y: float, w: float, h: float, art: int) -> None:
    deckel_h = 0.2 * h
    # Schleife
    cx = x + w / 2
    top = y + h
    for sg in (-1, 1):
        sl = [(cx, top + 0.3)] + [(cx + sg * (0.18 * w + 0.16 * w * math.cos(t)), top + 0.12 * w + 0.1 * w * math.sin(t))
                                  for t in [math.pi * (1 + k / 10) * (1 if sg > 0 else 1) for k in range(-5, 16)]]
        b.linie(sl, True)
        b.decke(sl)
    b.form(kreis(cx, top + 0.6, max(0.6, 0.05 * w), 10))
    dk = [(x - 0.04 * w, top - deckel_h), (x + w * 1.04, top - deckel_h), (x + w * 1.04, top), (x - 0.04 * w, top)]
    b.linie(dk, True)
    b.linie([(cx - 0.06 * w, top - deckel_h), (cx - 0.06 * w, top)])
    b.linie([(cx + 0.06 * w, top - deckel_h), (cx + 0.06 * w, top)])
    b.decke(dk)
    box = [(x, y), (x + w, y), (x + w, top - deckel_h), (x, top - deckel_h)]
    b.linie(box, True)
    b.linie([(cx - 0.06 * w, y), (cx - 0.06 * w, top - deckel_h)])
    b.linie([(cx + 0.06 * w, y), (cx + 0.06 * w, top - deckel_h)])
    b.decke([(cx - 0.06 * w, y), (cx + 0.06 * w, y), (cx + 0.06 * w, top), (cx - 0.06 * w, top)])
    hb = h - deckel_h
    if art == 0:                                    # Punkte
        for i in range(4):
            for j in range(3):
                b.linie(kreis(x + w * (i + 0.5 + 0.5 * (j % 2)) / 4.5, y + hb * (j + 0.5) / 3, max(0.35, 0.04 * w), 10), True)
    elif art == 1:                                  # Streifen schräg
        b.schraffur(box, max(1.4, 0.12 * w), 45)
    elif art == 2:                                  # kleine Sterne
        for i in range(3):
            for j in range(2):
                b.linie(stern(x + w * (i + 0.5) / 3, y + hb * (j + 0.5) / 2, 0.09 * w, 0.04 * w), True)
    else:                                           # Karo
        b.schraffur(box, max(1.8, 0.16 * w), 0)
        b.schraffur(box, max(1.8, 0.16 * w), 90)
    b.decke(box)


def _kerze(b: Bild, x: float, y: float, s: float) -> None:
    """Kerze mit tropfenförmiger Flamme und Lichtschein; (x, y) = Mitte unten."""
    kw, kh = 0.28 * s, 1.2 * s
    fl = []
    for k in range(20):
        t = 2 * math.pi * k / 20
        fx = 0.22 * s * math.sin(t)
        fy = 0.32 * s * (1 - math.cos(t)) * (1 + 0.6 * max(0.0, -math.cos(t)))
        fl.append((x + fx * (1 - 0.35 * fy / s), y + kh + 0.15 * s + fy))
    b.form(fl)
    for k in range(6):
        a = math.pi / 2 + (k - 2.5) * 0.45
        cx, cy = x, y + kh + 0.45 * s
        b.linie([(cx + 0.55 * s * math.cos(a), cy + 0.55 * s * math.sin(a)),
                 (cx + 0.8 * s * math.cos(a), cy + 0.8 * s * math.sin(a))])
    b.form([(x - kw / 2, y), (x + kw / 2, y), (x + kw / 2, y + kh), (x - kw / 2, y + kh)])
    b.form([(x - kw * 1.1, y - 0.12 * s), (x + kw * 1.1, y - 0.12 * s), (x + kw * 1.1, y + 0.05 * s),
            (x - kw * 1.1, y + 0.05 * s)])


def christbaum(box, seed: int = 1) -> List[Strich]:
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    rng = random.Random(seed)
    b = Bild(box, seed)
    cx = x0 + W / 2
    s = min(W, H)
    boden = y0 + 0.13 * H
    th = 0.72 * H
    tw = min(0.6 * W, 0.8 * th)
    # Geschenke vor dem Baum
    gs = [(-0.3, 0.14, 0.12, 0), (-0.16, 0.1, 0.085, 1), (0.15, 0.12, 0.11, 2), (0.29, 0.09, 0.075, 3),
          (0.0, 0.1, 0.07, 2)]
    for dx, gw, gh, art in sorted(gs, key=lambda g: g[2]):
        _geschenk(b, cx + dx * W - gw * s / 2, y0 + 0.03 * H, gw * s, gh * H, (art + seed) % 4)
    # Stern auf der Spitze mit Strahlen
    spitze = (cx, boden + th + 0.03 * H)
    sr = 0.055 * s
    b.linie(stern(spitze[0], spitze[1], sr * 0.55, sr * 0.24, 5), True)
    b.form(stern(spitze[0], spitze[1], sr, sr * 0.42, 5))
    for k in range(10):
        a = math.pi / 2 + (k + 0.5) * math.pi / 5
        L = 1.55 if k % 2 else 1.85
        b.linie([(spitze[0] + sr * 1.15 * math.cos(a), spitze[1] + sr * 1.15 * math.sin(a)),
                 (spitze[0] + sr * L * math.cos(a), spitze[1] + sr * L * math.sin(a))])
    b.decke(kreis(spitze[0], spitze[1], sr * 1.25, 24))
    um, info = tannen_etagen(cx, boden, tw, th, 5)
    # Kugeln: an den Etagenspitzen hängend und verteilt auf den Etagen
    kr = 0.03 * s
    kugeln = []
    for e, (yb, ww, yn, xs) in enumerate(info):
        for sg in (-1, 1):
            kugeln.append((cx + sg * (ww - 1.4 * kr), yb - 0.4 * kr))
        n = max(1, int((ww * 1.2) / (3.4 * kr)))
        for i in range(n):
            t = (i + 0.5) / n
            x = cx - ww * 0.55 + 1.1 * ww * t
            y = yb + (yn - yb) * (0.35 + 0.18 * ((i + e) % 2))
            if abs(x - cx) < ww * (1 - (y - yb) / max(1e-6, (yn - yb) * 1.6)) - kr:
                kugeln.append((x, y))
    for i, (kx, ky) in enumerate(kugeln):
        _kugel(b, kx, ky, kr * (0.85 + 0.3 * ((i * 7) % 3) / 2), (i + seed) % 4)
    # Kerzen auf den Absätzen
    for e, (yb, ww, yn, xs) in enumerate(info[:-1]):
        for sg in (-1, 1):
            _kerze(b, cx + sg * (xs + 0.45 * (info[e + 1][1] - xs)), yn + 0.01 * th, 0.035 * s)
    # Lametta-Girlanden: Perlenketten quer über jede Etage
    for e, (yb, ww, yn, xs) in enumerate(info):
        y_a, y_b = yb + 0.25 * (yn - yb), yb + 0.6 * (yn - yb)
        pts = []
        for k in range(25):
            t = k / 24
            y = y_a + (y_b - y_a) * t - 0.05 * (yn - yb) * math.sin(math.pi * t)
            hw = ww * (1 - (y - yb) / max(1e-6, (yn - yb) * 1.7))
            pts.append((cx - hw * 0.92 + 1.84 * hw * 0.92 * t, y))
        for p in pts[1:-1]:
            b.linie(kreis(p[0], p[1], max(0.35, 0.0065 * s), 8), True)
    # Baum: Umriss, Nadeln unter den Absätzen, Zweig-Struktur
    for yb, ww, yn, xs in info:
        n = max(3, int(2 * ww / 1.6))
        for i in range(1, n):
            x = -ww * 0.9 + 1.8 * ww * i / n
            b.linie([(cx + x, yb + 0.5), (cx + x * 0.93, yb + 0.5 + min(3.0, 0.16 * (yn - yb)))])
        for k in range(int(ww * (yn - yb) / 30)):
            x = cx + rng.uniform(-0.8, 0.8) * ww
            y = yb + rng.uniform(0.3, 0.95) * (yn - yb)
            d = 1 if x > cx else -1
            b.linie([(x, y), (x + d * 1.1, y - 0.8), (x + d * 2.0, y - 1.1)])
    b.linie(um, True)
    b.decke(um)
    # Stamm und Topf
    sw = 0.045 * tw
    b.form([(cx - sw, boden - 0.03 * H), (cx + sw, boden - 0.03 * H), (cx + sw, boden + 1), (cx - sw, boden + 1)])
    topf = [(cx - 2.4 * sw, y0 + 0.025 * H), (cx + 2.4 * sw, y0 + 0.025 * H), (cx + 3.1 * sw, boden - 0.03 * H),
            (cx - 3.1 * sw, boden - 0.03 * H)]
    b.linie([(cx - 2.8 * sw, y0 + 0.06 * H), (cx + 2.8 * sw, y0 + 0.06 * H)])
    b.linie([(cx - 2.6 * sw, y0 + 0.045 * H), (cx + 2.6 * sw, y0 + 0.045 * H)])
    b.form(topf)
    # Fußboden-Dielen
    for k in range(3):
        b.linie([(x0, y0 + 0.02 * H * (k + 1)), (x1, y0 + 0.02 * H * (k + 1))])
    # Fenster links mit Schneeflocken und Vorhang
    fx0, fy0, fx1, fy1 = x0 + 0.05 * W, y0 + 0.36 * H, x0 + 0.21 * W, y0 + 0.76 * H
    rahmen = [(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)]
    for sg, xa in ((1, fx0 - 1.5), (-1, fx1 + 1.5)):
        vh = [(xa, fy1 + 2)] + [(xa + sg * (0.05 * W + 0.02 * W * math.sin(math.pi * k / 10)), fy1 + 2 - (fy1 - fy0) * 0.75 * k / 10)
                                for k in range(11)] + [(xa, fy1 + 2 - (fy1 - fy0) * 0.75)]
        b.linie(vh, True)
        for k in range(1, 4):
            b.linie([(xa + sg * 0.012 * W * k, fy1 + 1.5), (xa + sg * 0.014 * W * k, fy1 + 2 - (fy1 - fy0) * 0.7)])
        b.decke(vh)
    b.linie([(fx0 - 3, fy1 + 2), (fx1 + 3, fy1 + 2)])
    b.linie(rahmen, True)
    b.linie([(fx0 + 1.2, fy0 + 1.2), (fx1 - 1.2, fy0 + 1.2), (fx1 - 1.2, fy1 - 1.2), (fx0 + 1.2, fy1 - 1.2)], True)
    b.linie([((fx0 + fx1) / 2, fy0 + 1.2), ((fx0 + fx1) / 2, fy1 - 1.2)])
    b.linie([(fx0 + 1.2, (fy0 + fy1) / 2), (fx1 - 1.2, (fy0 + fy1) / 2)])
    for k in range(6):
        flocke(b, fx0 + (fx1 - fx0) * (0.22 + 0.56 * ((k * 37) % 10) / 10), fy0 + (fy1 - fy0) * (0.12 + 0.15 * k),
               0.016 * s, k * 0.3, fein=False)
    b.linie([(fx0 - 1.5, fy0 - 0.8), (fx1 + 1.5, fy0 - 0.8)])
    b.decke(rahmen)
    # Adventskranz-Herz an der Wand rechts
    kx, ky, kr2 = x0 + 0.84 * W, y0 + 0.6 * H, 0.075 * s
    b.linie(herz(kx, ky - 0.05 * kr2, kr2 * 0.8, kr2 * 0.75), True)
    for k in range(20):
        a = 2 * math.pi * k / 20
        b.linie(blatt(kx + kr2 * math.cos(a), ky + kr2 * math.sin(a), 0.48 * kr2, 0.2 * kr2, a + 1.9, 8), True)
    for k in range(4):
        a = -math.pi / 2 + (k - 1.5) * 0.5
        b.linie(kreis(kx + kr2 * 1.02 * math.cos(a), ky + kr2 * 1.02 * math.sin(a), 0.1 * kr2, 10), True)
    b.linie([(kx - kr2 * 0.3, ky + kr2 * 1.1), (kx, ky + kr2 * 1.7), (kx + kr2 * 0.3, ky + kr2 * 1.1)])
    b.decke(kreis(kx, ky, kr2 * 1.35, 32))
    # Wimpelgirlande oben
    pts = [(x0 + W * k / 40, y1 - 0.05 * H - 0.05 * H * math.sin(math.pi * ((k % 20) / 20))) for k in range(41)]
    for k in range(2, 40, 3):
        px, py = pts[k]
        wim = [(px - 0.012 * W, py), (px + 0.012 * W, py), (px, py - 0.045 * H)]
        b.linie([(px - 0.006 * W, py - 0.01 * H), (px + 0.006 * W, py - 0.01 * H)])
        b.form(wim)
    b.linie(pts)
    # Wandmuster: kleine Sterne verstreut
    _himmel(b, x0, y0 + 0.2 * H, x1, y1 - 0.12 * H, rng, 0.3, flocken=False)
    return b.striche


def mandala(box, seed: int = 1) -> List[Strich]:
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = min(W, H) / 2 * 0.96
    rng = random.Random(seed)
    b = Bild(box, seed)
    n = rng.choice((8, 10, 12, 16))
    radien = []
    # Mitte: Rosette
    r = 0.09 * R
    b.linie(kreis(cx, cy, r * 0.35), True)
    b.linie(stern(cx, cy, r * 0.32, r * 0.14, n // 2), True)
    for k in range(n):
        a = 2 * math.pi * k / n
        b.linie(blatt(cx, cy, r, r * 0.42, a), True)
    b.linie(kreis(cx, cy, r * 1.08), True)
    radien.append(r * 1.08)
    ringe = ["perlen", "blaetter", "boegen", "gitter", "doppelblatt", "zacken", "perlen", "tropfen", "blaetter",
             "boegen", "spitzen"]
    rng.shuffle(ringe)
    ringe = ["perlen", "blaetter"] + ringe
    ri = r * 1.08
    k_ring = 0
    while ri < R * 0.97:
        art = ringe[k_ring % len(ringe)]
        k_ring += 1
        bw = max(2.2, 0.075 * R * (1 + 0.12 * (k_ring % 3)))
        ro = min(R, ri + bw)
        m = n * (1 + (k_ring // 3)) if art not in ("perlen",) else max(n, int(2 * math.pi * (ri + ro) / 2 / (ro - ri) / 1.1))
        if art == "perlen":
            rm = (ri + ro) / 2
            pr = (ro - ri) * 0.36
            mm = max(n, int(2 * math.pi * rm / (2.4 * pr)))
            for i in range(mm):
                a = 2 * math.pi * i / mm
                b.linie(kreis(cx + rm * math.cos(a), cy + rm * math.sin(a), pr, 12), True)
        elif art == "blaetter":
            for i in range(m):
                a = 2 * math.pi * (i + 0.5 * (k_ring % 2)) / m
                pe = blatt(cx + ri * math.cos(a), cy + ri * math.sin(a), ro - ri, (ro - ri) * 0.55, a)
                b.linie(pe, True)
                b.linie([(cx + ri * math.cos(a), cy + ri * math.sin(a)),
                         (cx + (ri + 0.75 * (ro - ri)) * math.cos(a), cy + (ri + 0.75 * (ro - ri)) * math.sin(a))])
        elif art == "doppelblatt":
            for i in range(m):
                a = 2 * math.pi * i / m
                b.linie(blatt(cx + ri * math.cos(a), cy + ri * math.sin(a), ro - ri, (ro - ri) * 0.7, a), True)
                b.linie(blatt(cx + ri * math.cos(a), cy + ri * math.sin(a), (ro - ri) * 0.62, (ro - ri) * 0.36, a), True)
        elif art == "tropfen":
            for i in range(m):
                a = 2 * math.pi * (i + 0.5) / m
                rm = (ri + ro) / 2
                tr = (ro - ri) * 0.32
                pts = []
                for j in range(16):
                    t = 2 * math.pi * j / 16
                    x = tr * math.cos(t)
                    y = tr * math.sin(t) * (1 + 0.9 * max(0, math.cos(t)))
                    pts.append((x, y))
                c, s_ = math.cos(a), math.sin(a)
                b.linie([(cx + rm * c + (px * c - py * s_ * 0.6), cy + rm * s_ + (px * s_ + py * c * 0.6)) for px, py in pts],
                        True)
        elif art == "boegen":
            pts = []
            for i in range(m * 12 + 1):
                a = 2 * math.pi * i / (m * 12)
                t = (i % 12) / 12
                rr = ri + (ro - ri) * math.sin(math.pi * t)
                pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
            b.linie(pts[:-1], True)
            for i in range(m):
                a = 2 * math.pi * (i + 0.5) / m
                rr = ri + (ro - ri) * 0.45
                b.linie(kreis(cx + rr * math.cos(a), cy + rr * math.sin(a), (ro - ri) * 0.14, 10), True)
        elif art == "gitter":
            for i in range(m):
                a0 = 2 * math.pi * i / m
                a1 = 2 * math.pi * (i + 1) / m
                b.linie([(cx + ri * math.cos(a0), cy + ri * math.sin(a0)), (cx + ro * math.cos(a1), cy + ro * math.sin(a1))])
                b.linie([(cx + ro * math.cos(a0), cy + ro * math.sin(a0)), (cx + ri * math.cos(a1), cy + ri * math.sin(a1))])
        elif art == "zacken":
            pts = []
            for i in range(2 * m):
                a = math.pi * i / m
                rr = ro if i % 2 == 0 else ri
                pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
            b.linie(pts, True)
            for i in range(m):
                a = 2 * math.pi * i / m
                rr = ri + 0.62 * (ro - ri)
                b.linie(kreis(cx + rr * math.cos(a), cy + rr * math.sin(a), (ro - ri) * 0.09, 8), True)
        elif art == "spitzen":
            for i in range(m):
                a = 2 * math.pi * i / m
                c, s_ = math.cos(a), math.sin(a)
                pts = [(cx + ri * math.cos(a - math.pi / m), cy + ri * math.sin(a - math.pi / m)),
                       (cx + (ri + 0.6 * (ro - ri)) * math.cos(a - 0.3 * math.pi / m),
                        cy + (ri + 0.6 * (ro - ri)) * math.sin(a - 0.3 * math.pi / m)),
                       (cx + ro * c, cy + ro * s_),
                       (cx + (ri + 0.6 * (ro - ri)) * math.cos(a + 0.3 * math.pi / m),
                        cy + (ri + 0.6 * (ro - ri)) * math.sin(a + 0.3 * math.pi / m)),
                       (cx + ri * math.cos(a + math.pi / m), cy + ri * math.sin(a + math.pi / m))]
                b.linie(pts)
        b.linie(kreis(cx, cy, ro), True)
        ri = ro + max(0.6, 0.012 * R)
        if ri < R * 0.97:
            b.linie(kreis(cx, cy, ri), True)
    # Ecken im Rechteck: Viertelrosetten und Zierbögen
    ecken = [(x0, y0, 0.0), (x1, y0, math.pi / 2), (x1, y1, math.pi), (x0, y1, 3 * math.pi / 2)]
    rest = math.hypot(W / 2, H / 2) - R
    if rest > 0.12 * R:
        ER = min(rest * 0.95, 0.42 * R)
        for ex, ey, a0 in ecken:
            for k in range(7):
                a = a0 + math.pi / 2 * (k + 0.5) / 7
                b.linie(blatt(ex, ey, ER, ER * 0.28, a), True)
                b.linie(blatt(ex, ey, ER * 0.6, ER * 0.16, a), True)
            pts = [(ex + ER * 1.12 * math.cos(a0 + math.pi / 2 * k / 24), ey + ER * 1.12 * math.sin(a0 + math.pi / 2 * k / 24))
                   for k in range(25)]
            b.linie(pts)
            for k in range(1, 8):
                a = a0 + math.pi / 2 * k / 8
                b.linie(kreis(ex + ER * 1.25 * math.cos(a), ey + ER * 1.25 * math.sin(a), max(0.5, ER * 0.05), 10), True)
    # Ausfüllen links/rechts (breites Rechteck) mit Ranken
    if W > H * 1.25:
        for sg in (-1, 1):
            mx = cx + sg * (R + (W / 2 - R) / 2)
            hw = (W / 2 - R) * 0.42
            for k in range(5):
                yy = cy - H * 0.3 + H * 0.6 * k / 4
                b.linie(stern(mx, yy, min(hw, H * 0.07), min(hw, H * 0.07) * 0.4, 8), True)
                b.linie(kreis(mx, yy, min(hw, H * 0.07) * 0.25), True)
    return b.striche


def _sternbild(b: Bild, pts: Sequence[Point], kanten: Sequence[Tuple[int, int]], r: float) -> None:
    for i, j in kanten:
        a, c = pts[i], pts[j]
        L = math.hypot(c[0] - a[0], c[1] - a[1])
        if L < 3 * r:
            continue
        ux, uy = (c[0] - a[0]) / L, (c[1] - a[1]) / L
        b.linie([(a[0] + ux * r * 1.6, a[1] + uy * r * 1.6), (c[0] - ux * r * 1.6, c[1] - uy * r * 1.6)])
    for p in pts:
        b.form(stern(p[0], p[1], r, r * 0.4, 5))


def sternenhimmel(box, seed: int = 1) -> List[Strich]:
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    rng = random.Random(seed)
    b = Bild(box, seed)
    s = min(W, H)
    # Vordergrund: Hügel mit Hütte und Tannen
    hy = y0 + 0.22 * H
    hx = x0 + 0.62 * W
    hw, hh = 0.14 * W, 0.08 * H
    # Hütte
    dach = [(hx - hw * 0.1, hy + hh), (hx + hw * 1.1, hy + hh), (hx + hw / 2, hy + hh + hw * 0.5)]
    b.linie(bogenreihe(hx - hw * 0.1, hx + hw * 1.1, hy + hh, hw * 0.05), False)
    b.form(dach)
    wand = [(hx, hy), (hx + hw, hy), (hx + hw, hy + hh), (hx, hy + hh)]
    fx, fy, fw = hx + hw * 0.6, hy + hh * 0.35, hw * 0.22
    fen = [(fx, fy), (fx + fw, fy), (fx + fw, fy + fw), (fx, fy + fw)]
    b.linie(fen, True)
    b.schraffur(fen, 0.5, 45)
    b.decke(fen)
    b.form([(hx + hw * 0.15, hy), (hx + hw * 0.35, hy), (hx + hw * 0.35, hy + hh * 0.7), (hx + hw * 0.15, hy + hh * 0.7)])
    yy = hy + 1.2
    while yy < hy + hh:
        b.linie([(hx, yy), (hx + hw, yy)])
        yy += 1.3
    b.form(wand)
    for k in range(9):
        tx = x0 + W * (0.04 + 0.11 * k + rng.uniform(-0.03, 0.03))
        if abs(tx - (hx + hw / 2)) < hw * 0.8:
            continue
        th = H * rng.uniform(0.18, 0.3)
        tanne(b, tx, y0 + rng.uniform(0.0, 0.08) * H, th * 0.5, th, schnee=True)
    hug = [(x0, y0)] + welle(x0, x1, hy, 0.025 * H, 0.9 * W, 0.4) + [(x1, y0)]
    b.linie(welle(x0, x1, hy, 0.025 * H, 0.9 * W, 0.4))
    b.decke(hug)
    b.linie(welle(x0, x1, hy + 0.07 * H, 0.03 * H, 0.5 * W, 2.0))
    for k in range(int(W / 6)):
        tx = x0 + rng.uniform(0, 1) * W
        ty = hy + 0.07 * H + 0.03 * H * math.sin(2.0 + 2 * math.pi * tx / (0.5 * W))
        tanne(b, tx, ty - 0.2, 0.03 * H, 0.06 * H, schnee=False, detail=0)
    b.decke([(x0, y0)] + welle(x0, x1, hy + 0.07 * H, 0.03 * H, 0.5 * W, 2.0) + [(x1, y0)])
    # Mond
    _mond(b, x1 - 0.18 * W, y1 - 0.22 * H, 0.1 * s)
    # Sternbilder: Großer Wagen und Kassiopeia
    sk = 0.12 * s
    wx, wy = x0 + 0.18 * W, y1 - 0.22 * H
    wagen = [(0, 0), (0.9, -0.15), (1.7, -0.1), (2.4, 0.05), (2.75, -0.6), (3.8, -0.8), (3.95, 0.05)]
    wagen = [(wx + px * sk, wy + py * sk) for px, py in wagen]
    _sternbild(b, wagen, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3)], max(0.9, 0.012 * s))
    kx, ky = x0 + 0.5 * W, y1 - 0.12 * H
    kas = [(0, 0), (0.6, -0.5), (1.2, -0.1), (1.8, -0.6), (2.4, -0.15)]
    kas = [(kx + px * sk * 0.8, ky + py * sk * 0.8) for px, py in kas]
    _sternbild(b, kas, [(0, 1), (1, 2), (2, 3), (3, 4)], max(0.8, 0.01 * s))
    # Sternschnuppe
    sx, sy = x0 + 0.62 * W, y0 + 0.62 * H
    b.form(stern(sx, sy, 0.025 * s, 0.011 * s, 5, 0.3))
    for k, off in enumerate((-0.006, 0.0, 0.006)):
        L = (0.22 - 0.05 * abs(k - 1)) * W
        b.linie([(sx - 0.03 * s, sy + 0.012 * s + off * s), (sx - 0.03 * s - L, sy + 0.012 * s + off * s + 0.35 * L)])
    b.decke([(sx + 0.03 * s, sy), (sx - 0.04 * s - 0.22 * W, sy + 0.08 * W + 0.03 * s),
             (sx - 0.04 * s - 0.22 * W, sy + 0.08 * W - 0.0), (sx, sy - 0.03 * s)])
    _himmel(b, x0, hy + 0.06 * H, x1, y1, rng, 1.4, flocken=False)
    # Milchstraße: feine Punktwolke diagonal
    for _ in range(int(W * H / 140)):
        t = rng.random()
        x = x0 + t * W
        y = y0 + 0.5 * H + (t - 0.5) * 0.5 * H + rng.gauss(0, 0.06 * H)
        if y > hy + 0.1 * H and y < y1 - 1:
            b.linie(kreis(x, y, 0.18, 5), True)
    return b.striche


def _eule(b: Bild, cx: float, cy: float, h: float) -> None:
    w = 0.62 * h
    # Ohren und Körper
    kopf_y = cy + 0.22 * h
    # Augen
    for sg in (-1, 1):
        ex = cx + sg * 0.19 * w * 1.15
        for rr in (0.15, 0.11, 0.06):
            b.linie(kreis(ex, kopf_y, rr * h, 18), True)
        b.form(kreis(ex + 0.02 * h, kopf_y + 0.02 * h, 0.03 * h, 8))
        b.decke(kreis(ex, kopf_y, 0.155 * h, 18))
    b.form([(cx - 0.05 * w, kopf_y - 0.08 * h), (cx + 0.05 * w, kopf_y - 0.08 * h), (cx, kopf_y - 0.2 * h)])
    # Bauchfedern: Schuppenreihen
    by = cy - 0.08 * h
    for j in range(5):
        y = by - j * 0.075 * h
        hw = 0.28 * w * math.sqrt(max(0.05, 1 - ((y - (cy - 0.2 * h)) / (0.32 * h)) ** 2))
        if hw > 1:
            b.linie(bogenreihe(cx - hw, cx + hw, y, max(0.6, 0.035 * h)))
    # Flügel
    for sg in (-1, 1):
        fl = [(cx + sg * 0.32 * w, cy + 0.05 * h), (cx + sg * 0.52 * w, cy - 0.15 * h), (cx + sg * 0.42 * w, cy - 0.4 * h),
              (cx + sg * 0.3 * w, cy - 0.3 * h)]
        b.linie(fl, True)
        b.linie([(cx + sg * 0.36 * w, cy - 0.05 * h), (cx + sg * 0.42 * w, cy - 0.28 * h)])
        b.decke(fl)
    koerper = []
    for k in range(40):
        t = 2 * math.pi * k / 40
        x = 0.5 * w * math.cos(t)
        y = 0.5 * h * math.sin(t)
        if y > 0.32 * h:                           # Ohrbüschel
            y += 0.08 * h * max(0, abs(math.cos(t)) - 0.15)
        koerper.append((cx + x * (1 - 0.08 * math.sin(t)), cy + y))
    b.form(koerper)
    # Krallen
    for sg in (-1, 1):
        for d in (-0.05, 0.0, 0.05):
            x = cx + sg * 0.15 * w + d * w
            b.linie([(x, cy - 0.5 * h + 0.6), (x, cy - 0.5 * h - 0.06 * h)])


def _igel(b: Bild, cx: float, y0: float, w: float) -> None:
    h = 0.55 * w
    # Gesicht
    nase = (cx + 0.58 * w, y0 + 0.18 * h)
    b.form(kreis(nase[0], nase[1], 0.035 * w, 10))
    b.form(kreis(cx + 0.38 * w, y0 + 0.4 * h, 0.03 * w, 10))
    kopf = [(cx + 0.2 * w, y0 + 0.05 * h), (nase[0], nase[1] - 0.05 * h), (nase[0], nase[1] + 0.05 * h),
            (cx + 0.25 * w, y0 + 0.72 * h)]
    b.form(kopf)
    # Stacheln: Zickzack-Reihen
    for j in range(5):
        r = 0.5 * w - j * 0.08 * w
        pts = []
        n = 18 - 2 * j
        for k in range(n + 1):
            a = math.pi * (0.06 + 0.82 * k / n)
            rr = r * (1.0 if k % 2 == 0 else 0.86)
            pts.append((cx - 0.05 * w + rr * math.cos(a) * 1.0, y0 + rr * math.sin(a) * h / (0.5 * w)))
        b.linie(pts)
    rumpf = [(cx - 0.05 * w + 0.5 * w * math.cos(math.pi * k / 30), y0 + h * math.sin(math.pi * k / 30)) for k in range(31)]
    b.form(rumpf)
    for d in (-0.3, -0.1, 0.12):
        b.linie([(cx + d * w, y0), (cx + d * w, y0 - 0.06 * w)])


def _pilz(b: Bild, cx: float, y0: float, h: float) -> None:
    w = 0.9 * h
    hut_y = y0 + 0.5 * h
    hut = [(cx + w / 2 * math.cos(math.pi * k / 24), hut_y + 0.5 * h * math.sin(math.pi * k / 24)) for k in range(25)]
    for k, (dx, dy, rr) in enumerate(((-0.2, 0.25, 0.07), (0.12, 0.33, 0.06), (0.28, 0.12, 0.05), (-0.05, 0.1, 0.045),
                                       (-0.33, 0.08, 0.04), (0.02, 0.42, 0.04))):
        b.linie(kreis(cx + dx * w, hut_y + dy * h, rr * h, 10), True)
    b.form(hut)
    b.linie(bogenreihe(cx - 0.18 * w, cx + 0.18 * w, y0 + 0.3 * h, 0.05 * h, unten=True))
    b.form([(cx - 0.12 * w, y0), (cx + 0.12 * w, y0), (cx + 0.09 * w, hut_y), (cx - 0.09 * w, hut_y)])


def waldtiere(box, seed: int = 1) -> List[Strich]:
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    rng = random.Random(seed)
    b = Bild(box, seed)
    s = min(W, H)
    # Vorne: Pilze, Igel, Grasbüschel
    for dx, hh in ((0.12, 0.13), (0.18, 0.09), (0.86, 0.11)):
        _pilz(b, x0 + dx * W, y0 + 0.03 * H, hh * H)
    _igel(b, x0 + 0.35 * W, y0 + 0.04 * H, 0.2 * s)
    for k in range(int(W / 5)):
        gx = x0 + rng.uniform(0, 1) * W
        gy = y0 + rng.uniform(0.0, 0.1) * H
        for d in (-1, 0, 1):
            b.linie([(gx, gy), (gx + d * 1.2 + rng.uniform(-0.3, 0.3), gy + rng.uniform(1.8, 3.2))])
    # Eule auf einem Ast am Baum rechts
    ex, ey = x0 + 0.68 * W, y0 + 0.62 * H
    eh = 0.26 * s
    _eule(b, ex, ey, eh)
    ast = [(ex - 0.4 * eh, ey - 0.52 * eh), (x0 + 0.86 * W, ey - 0.56 * eh), (x0 + 0.86 * W, ey - 0.62 * eh),
           (ex - 0.4 * eh, ey - 0.6 * eh)]
    b.form(ast)
    b.linie([(ex - 0.2 * eh, ey - 0.52 * eh), (ex - 0.35 * eh, ey - 0.35 * eh)])
    b.form(blatt(ex - 0.35 * eh, ey - 0.35 * eh, 0.15 * eh, 0.07 * eh, 2.0))
    stamm_x = x0 + 0.87 * W
    st = [(stamm_x - 0.06 * W, y0), (stamm_x + 0.06 * W, y0), (stamm_x + 0.05 * W, y1), (stamm_x - 0.05 * W, y1)]
    yy = y0 + 2
    while yy < y1:
        a = stamm_x - 0.05 * W + rng.uniform(0, 0.02) * W
        b.linie([(a, yy), (a + rng.uniform(0.02, 0.06) * W, yy + rng.uniform(-0.6, 0.6))])
        yy += rng.uniform(2.0, 3.6)
    b.linie(kreis(stamm_x, y0 + 0.4 * H, 0.025 * W, 16), True)
    b.form(st)
    # Mittelgrund: Tannen und Laubbäume
    for k in range(7):
        tx = x0 + W * (0.05 + 0.13 * k + rng.uniform(-0.03, 0.03))
        th = H * rng.uniform(0.38, 0.55)
        if k % 3 == 1:
            laubbaum(b, tx, y0 + 0.12 * H, th * 0.6, th, rng)
        else:
            tanne(b, tx, y0 + 0.12 * H, th * 0.42, th, schnee=False, detail=1)
    b.linie(welle(x0, x1, y0 + 0.12 * H, 0.01 * H, 0.4 * W))
    b.decke([(x0, y0), (x1, y0), (x1, y0 + 0.12 * H), (x0, y0 + 0.12 * H)])
    # Hinten: Berge, Sonne mit Strahlen, Vögel
    b.linie([(x0, y0 + 0.5 * H), (x0 + 0.2 * W, y0 + 0.68 * H), (x0 + 0.32 * W, y0 + 0.58 * H), (x0 + 0.5 * W, y0 + 0.78 * H),
             (x0 + 0.66 * W, y0 + 0.6 * H), (x0 + 0.8 * W, y0 + 0.7 * H), (x1, y0 + 0.52 * H)])
    sx, sy, sr = x0 + 0.3 * W, y1 - 0.18 * H, 0.07 * s
    b.form(kreis(sx, sy, sr))
    for k in range(18):
        a = 2 * math.pi * k / 18
        L = 1.35 if k % 2 else 1.6
        b.linie([(sx + sr * 1.15 * math.cos(a), sy + sr * 1.15 * math.sin(a)), (sx + sr * L * math.cos(a), sy + sr * L * math.sin(a))])
    for k in range(5):
        vx, vy, vs = x0 + W * (0.5 + 0.07 * k), y1 - H * (0.1 + 0.04 * (k % 2)), 0.02 * s
        b.linie([(vx - vs, vy + vs * 0.3), (vx - vs * 0.5, vy + vs * 0.5), (vx, vy), (vx + vs * 0.5, vy + vs * 0.5),
                 (vx + vs, vy + vs * 0.3)])
    return b.striche


# ---------------------------------------------------------------------------------------------
# Hintergrundmuster
# ---------------------------------------------------------------------------------------------

def muster(art: str, box, b: Optional[Bild] = None, groesse: float = 6.0, seed: int = 1) -> List[Strich]:
    """Hintergrundmuster in der Box. Mit einem vorhandenen Bild wird hinter dessen Verdeckungen gezeichnet."""
    x0, y0, x1, y1 = box
    b = b or Bild(box, seed)
    g = max(3.0, groesse)
    if art == "keins":
        return b.striche
    if art in ("sterne", "flocken", "punkte"):
        j = 0
        y = y0 + g / 2
        while y < y1:
            x = x0 + g / 2 + (g / 2 if j % 2 else 0)
            while x < x1:
                if art == "sterne":
                    b.linie(stern(x, y, g * 0.22, g * 0.09, 5), True)
                elif art == "flocken":
                    flocke(b, x, y, g * 0.25, 0.0, fein=g > 7)
                else:
                    b.linie(kreis(x, y, g * 0.08, 10), True)
                x += g
            y += g * 0.87
            j += 1
    elif art == "rauten":
        d = g
        k = -int((y1 - y0) / d) - 1
        while x0 + k * d < x1:
            b.linie([(x0 + k * d, y0), (x0 + k * d + (y1 - y0), y1)])
            b.linie([(x0 + k * d, y1), (x0 + k * d + (y1 - y0), y0)])
            k += 1
    elif art == "wellen":
        y = y0 + g / 3
        j = 0
        while y < y1:
            b.linie(welle(x0, x1, y, g * 0.18, g * 1.2, j * 1.3))
            y += g / 2.2
            j += 1
    else:
        raise ValueError(f"Muster {art!r} unbekannt")
    return b.striche


def boden(art: str, box) -> List[Strich]:
    """Bodenstreifen unter einer nach oben gerückten Szene (Platz für ein Schriftband)."""
    x0, y0, x1, y1 = box
    H = y1 - y0
    b = Bild(box)
    if art == "christbaum":
        for k in range(1, 6):
            b.linie([(x0, y0 + H * k / 6), (x1, y0 + H * k / 6)])
        for k in range(12):
            x = x0 + (x1 - x0) * (k + 0.5 * (k % 2)) / 12
            j = k % 5
            b.linie([(x, y0 + H * j / 6), (x, y0 + H * (j + 1) / 6)])
    elif art == "waldtiere":
        b.linie(welle(x0, x1, y1 - 0.15 * H, 0.08 * H, (x1 - x0) / 3))
        rng = random.Random(3)
        for _ in range(int((x1 - x0) / 4)):
            gx, gy = rng.uniform(x0, x1), rng.uniform(y0 + 0.1 * H, y1 - 0.35 * H)
            for d in (-1, 0, 1):
                b.linie([(gx, gy), (gx + d * 1.1, gy + rng.uniform(1.6, 2.8))])
    else:
        for k, ph in ((0.75, 0.3), (0.45, 1.7), (0.18, 3.1)):
            b.linie(welle(x0, x1, y0 + k * H, 0.06 * H, (x1 - x0) / 2.3, ph))
    return b.striche


SZENEN: Dict[str, Callable] = dict(winterdorf=winterdorf, christbaum=christbaum, mandala=mandala,
                                   sternenhimmel=sternenhimmel, waldtiere=waldtiere)


def szene(art: str, box, seed: int = 1) -> List[Strich]:
    if art not in SZENEN:
        raise ValueError(f"Bild {art!r} unbekannt")
    return SZENEN[art](box, seed)
