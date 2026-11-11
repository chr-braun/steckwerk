"""
_puzzle.py – Puzzle-Geometrie und schnelles Verteilen einer Gravur auf die Teile.

  raster_teile   rechteckiges Puzzle: Spalten × Zeilen, Kanten mit Nasen (klassisch, verspielt, gerade)
  rund_teile     rundes Puzzle: Mittelstück und Ringe aus Segmenten, ebenfalls mit Nasen
  Clipper        Linien schnell an einer Kontur abschneiden (Rasterindex über die Kanten)
  verteilen      ein Gravurbild (Liste von Linien) auf alle Teile aufteilen

Jede Kante wird genau einmal erzeugt und von beiden Nachbarteilen benutzt – so passen die Teile exakt
ineinander. Das Spiel zwischen den Teilen entsteht durch ein kleines Einrücken jeder Kontur.
Alles ist reine Vektorgeometrie mit Python-Bordmitteln und läuft auch auf alten Rechnern flott.
"""
from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from steckwerk import Point, PolygonIndex, clean, offset_polygon, oriented, signed_area

Poly = List[Point]
Strich = Tuple[List[Point], bool]

SCHNITTE = [("klassisch", "klassisch mit Nasen"), ("verspielt", "verspielt (unregelmäßige Nasen)"),
            ("gerade", "gerade Kanten (für Kleinkinder)")]


# ---------------------------------------------------------------------------------------------
# Kanten
# ---------------------------------------------------------------------------------------------

class Nase:
    """Puzzle-Nase auf einer Kante: Mitte c (mm entlang der Kante), Kopfradius r, Seite s (+1 links)."""
    __slots__ = ("c", "r", "s", "hoch", "hals", "schief", "fuss")

    def __init__(self, c: float, r: float, s: int, hoch: float = 1.25, hals: float = 0.55, schief: float = 0.0):
        self.c, self.r, self.s, self.hoch, self.hals, self.schief = c, r, s, hoch, hals, schief
        # Fußrundung nie höher als der Halsansatz am Kopf (sonst knickt die Kontur zurück)
        dy = math.sqrt(max(1e-9, 1.0 - hals * hals))
        self.fuss = max(0.15, min(0.45, hoch - dy - 0.1))

    def profil(self) -> List[Tuple[float, float]]:
        """Punkte (u, v) der Nase: u entlang der Kante, v senkrecht (positiv = links)."""
        c, r, s = self.c, self.r, self.s
        a = self.hals * r                       # halbe Halsbreite
        f = self.fuss * r                       # Ausrundung am Fuß
        hc = self.hoch * r                      # Höhe der Kopfmitte
        kx = c + self.schief * r                # Kopf leicht seitlich versetzt (verspielt)
        dy = math.sqrt(max(1e-9, r * r - a * a))
        pts: List[Tuple[float, float]] = []
        n_f = 5
        for k in range(n_f + 1):                # linke Fußrundung (−90° → 0°)
            t = -math.pi / 2 + (math.pi / 2) * k / n_f
            pts.append((c - a - f + f * math.cos(t), f + f * math.sin(t)))
        # Hals gerade nach oben bis zum Kopf (mit Versatz: weich zum Kopf hin)
        a0 = math.atan2(-dy, -a)                # Startwinkel am Kopf (links unten)
        a1 = math.atan2(-dy, a)                 # Endwinkel (rechts unten)
        span = (a0 - a1) % (2 * math.pi)        # im Uhrzeigersinn über die Kuppe
        n_k = max(18, int(span * r / 0.35))
        for k in range(n_k + 1):
            t = a0 - span * k / n_k
            pts.append((kx + r * math.cos(t), hc + r * math.sin(t)))
        for k in range(n_f + 1):                # rechte Fußrundung (180° → 270°)
            t = math.pi + (math.pi / 2) * k / n_f
            pts.append((c + a + f + f * math.cos(t), f + f * math.sin(t)))
        return [(u, s * v) for u, v in pts]

    @property
    def breite(self) -> float:
        return (self.hals + self.fuss) * self.r

    @property
    def hoehe(self) -> float:
        return (self.hoch + 1.0) * self.r


class Kante:
    """Kante zwischen zwei Teilen auf einer Grundlinie (Strecke oder Kreisbogen)."""

    def __init__(self, laenge: float, ort: Callable[[float], Tuple[Point, Point]], nase: Optional[Nase] = None,
                 welle: float = 0.0, schritt: float = 0.0):
        self.L = laenge
        self.ort = ort                          # u (mm) → (Punkt, Normale links)
        self.nase = nase
        self.welle = welle                      # Amplitude einer sanften S-Welle (verspielt)
        self.schritt = schritt                  # Abtastung der Grundlinie (0 = nur Endpunkte)
        self._pts: Optional[Poly] = None

    def _v_welle(self, u: float) -> float:
        if not self.welle:
            return 0.0
        t = u / self.L
        return self.welle * math.sin(2 * math.pi * t) * math.sin(math.pi * t)

    def punkte(self) -> Poly:
        if self._pts is not None:
            return self._pts
        L = self.L
        us: List[Tuple[float, float]] = []
        n = 1
        if self.schritt > 0:
            n = max(1, int(math.ceil(L / self.schritt)))
        elif self.welle:
            n = max(6, int(L / 1.2))
        base = [(L * k / n, 0.0) for k in range(n + 1)]
        if self.nase is not None:
            nz = self.nase
            u0, u1 = nz.c - nz.breite, nz.c + nz.breite
            us = [p for p in base if p[0] < u0 - 0.05] + nz.profil() + [p for p in base if p[0] > u1 + 0.05]
        else:
            us = base
        out: Poly = []
        for u, v in us:
            (x, y), (nx, ny) = self.ort(u)
            v += self._v_welle(u)
            out.append((x + nx * v, y + ny * v))
        self._pts = out
        return out


def strecke(p: Point, q: Point) -> Tuple[float, Callable[[float], Tuple[Point, Point]]]:
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L

    def ort(u: float):
        return (p[0] + ux * u, p[1] + uy * u), (-uy, ux)
    return L, ort


def bogen(cx: float, cy: float, R: float, a0: float, a1: float) -> Tuple[float, Callable[[float], Tuple[Point, Point]]]:
    """Kreisbogen gegen den Uhrzeigersinn von a0 nach a1 (Normale links = zur Mitte hin)."""
    L = R * (a1 - a0)

    def ort(u: float):
        a = a0 + u / R
        ca, sa = math.cos(a), math.sin(a)
        return (cx + R * ca, cy + R * sa), (-ca, -sa)
    return L, ort


def _kette(teile: Sequence[Tuple[Kante, bool]]) -> Poly:
    """Kanten (vorwärts/rückwärts) zu einer geschlossenen Kontur verbinden."""
    out: Poly = []
    for k, vor in teile:
        pts = k.punkte() if vor else k.punkte()[::-1]
        if out and math.hypot(out[-1][0] - pts[0][0], out[-1][1] - pts[0][1]) < 1e-6:
            pts = pts[1:]
        out.extend(pts)
    if len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


def _nase(rng: random.Random, L: float, p: float, schnitt: str) -> Optional[Nase]:
    """Zufällige Nase für eine Kante der Länge L in einem Puzzle mit Teilegröße p."""
    if schnitt == "gerade":
        return None
    basis = min(L, p)
    if schnitt == "verspielt":
        r = 0.122 * basis * rng.uniform(0.9, 1.08)
        c = L * rng.uniform(0.44, 0.56)
        return Nase(c, r, rng.choice((-1, 1)), hoch=rng.uniform(1.2, 1.32), hals=rng.uniform(0.5, 0.58),
                    schief=rng.uniform(-0.12, 0.12))
    r = 0.12 * basis * rng.uniform(0.95, 1.05)
    c = L * rng.uniform(0.46, 0.54)
    return Nase(c, r, rng.choice((-1, 1)))


# ---------------------------------------------------------------------------------------------
# Puzzle-Formen
# ---------------------------------------------------------------------------------------------

def raster_mass(W: float, H: float, teile: int) -> Tuple[int, int]:
    """Spalten und Zeilen, deren Produkt nahe an `teile` liegt und deren Teile möglichst quadratisch sind."""
    best = None
    for z in range(1, 41):
        for s in range(1, 41):
            n = s * z
            form = max(W / s / (H / z), H / z / (W / s))
            score = abs(n - teile) / max(1, teile) * 3.0 + (form - 1.0)
            if best is None or score < best[0]:
                best = (score, s, z)
    return best[1], best[2]


def raster_teile(W: float, H: float, spalten: int, zeilen: int, schnitt: str, seed: int) -> List[Tuple[str, Poly]]:
    """Rechteckiges Puzzle, Mitte bei (0, 0). Liefert [(Name, Kontur)], Zeile für Zeile von oben."""
    rng = random.Random(seed * 7919 + 17)
    xs = [-W / 2 + W * i / spalten for i in range(spalten + 1)]
    ys = [-H / 2 + H * j / zeilen for j in range(zeilen + 1)]
    p = min(W / spalten, H / zeilen)
    welle = 0.035 * p if schnitt == "verspielt" else 0.0
    senk: Dict[Tuple[int, int], Kante] = {}         # senkrechte Kante bei x_i zwischen y_j und y_j+1
    waag: Dict[Tuple[int, int], Kante] = {}         # waagrechte Kante bei y_j zwischen x_i und x_i+1
    for i in range(spalten + 1):
        for j in range(zeilen):
            L, ort = strecke((xs[i], ys[j]), (xs[i], ys[j + 1]))
            innen = 0 < i < spalten
            senk[i, j] = Kante(L, ort, _nase(rng, L, p, schnitt) if innen else None, welle if innen else 0.0)
    for j in range(zeilen + 1):
        for i in range(spalten):
            L, ort = strecke((xs[i], ys[j]), (xs[i + 1], ys[j]))
            innen = 0 < j < zeilen
            waag[i, j] = Kante(L, ort, _nase(rng, L, p, schnitt) if innen else None, welle if innen else 0.0)
    out = []
    for j in reversed(range(zeilen)):
        for i in range(spalten):
            kontur = _kette([(waag[i, j], True), (senk[i + 1, j], True), (waag[i, j + 1], False),
                             (senk[i, j], False)])
            out.append((f"{zeilen - j}-{i + 1}", kontur))
    return out


def _ringe_plan(R: float, teile: int) -> Tuple[float, List[int]]:
    """Ringbreite und Segmentzahlen je Ring für ein rundes Puzzle mit ungefähr `teile` Teilen."""
    best = None
    for n in range(1, 9):
        w = R / (n + 0.65)
        R0 = R - n * w
        m = [max(3, round(2 * math.pi * (R0 + (k + 0.5) * w) / w)) for k in range(n)]
        tot = 1 + sum(m)
        f = (teile - 1) / max(1, sum(m))
        if 0.6 <= f <= 1.5:                         # Segmentzahl anpassen, Teile bleiben brauchbar
            m2 = [max(3, round(x * f)) for x in m]
            tot2 = 1 + sum(m2)
            score = abs(tot2 - teile) + abs(1 - f) * 3
            cand = (score, w, m2)
        else:
            cand = (abs(tot - teile) + 10, w, m)
        if best is None or cand[0] < best[0]:
            best = cand
    return best[1], best[2]


def rund_teile(R: float, teile: int, schnitt: str, seed: int) -> List[Tuple[str, Poly]]:
    """Rundes Puzzle um (0, 0): Mittelstück und Ringe aus Segmenten."""
    rng = random.Random(seed * 104729 + 3)
    w, m = _ringe_plan(R, teile)
    n = len(m)
    R0 = R - n * w
    radien = [R0 + k * w for k in range(n + 1)]      # radien[k] = Innenradius von Ring k+1
    welle = 0.03 * w if schnitt == "verspielt" else 0.0
    # Winkel der Trennlinien je Ring, gegen die Nachbarringe verdreht (keine fast gleichen Winkel)
    winkel: List[List[float]] = []
    for k in range(n):
        step = 2 * math.pi / m[k]
        if not winkel:
            off = rng.uniform(0, step)
        else:
            prev = winkel[-1]
            best = None
            for t in range(24):
                o = step * t / 24
                d = min(abs(((o + i * step - a + math.pi) % (2 * math.pi)) - math.pi)
                        for i in range(m[k]) for a in prev)
                if best is None or d > best[0]:
                    best = (d, o)
            off = best[1]
        winkel.append([off + i * step for i in range(m[k])])

    def bogen_kanten(k: int) -> Dict[Tuple[float, float], Kante]:
        """Bögen auf Radius radien[k], geteilt an den Trennlinien von Ring k (innen) und k+1 (außen)."""
        rad = radien[k]
        ws = set()
        if k >= 1:
            ws.update(a % (2 * math.pi) for a in winkel[k - 1])
        if k < n:
            ws.update(a % (2 * math.pi) for a in winkel[k])
        ws = sorted(ws)
        out = {}
        for i, a0 in enumerate(ws):
            a1 = ws[(i + 1) % len(ws)]
            if a1 <= a0:
                a1 += 2 * math.pi
            L, ort = bogen(0.0, 0.0, rad, a0, a1)
            innen = k < n and k >= 0
            nase = _nase(rng, L, w, schnitt) if innen and L > 0.55 * w else None
            schritt = max(0.6, math.sqrt(8 * rad * 0.012))     # Bogen auf ±0,012 mm genau
            out[(a0, a1)] = Kante(L, ort, nase, welle if (innen and nase) else 0.0, schritt=schritt)
        return out

    boegen = [bogen_kanten(k) for k in range(n + 1)]
    radial: Dict[Tuple[int, float], Kante] = {}
    for k in range(n):
        for a in winkel[k]:
            p = (radien[k] * math.cos(a), radien[k] * math.sin(a))
            q = (radien[k + 1] * math.cos(a), radien[k + 1] * math.sin(a))
            L, ort = strecke(p, q)
            radial[k, a] = Kante(L, ort, _nase(rng, L, min(w, 2 * math.pi * radien[k] / m[k]), schnitt), welle)

    def bogen_teil(k: int, a0: float, a1: float) -> List[Kante]:
        """Alle Bogenstücke auf Radius k zwischen den Winkeln a0 < a1 (in Reihenfolge)."""
        lst = []
        for (b0, b1), kante in boegen[k].items():
            # Bogenstück liegt in [a0, a1] (modulo 2π)
            d = (b0 - a0) % (2 * math.pi)
            if d < (a1 - a0) - 1e-9:
                lst.append((d, kante))
        lst.sort(key=lambda t: t[0])
        return [kk for _, kk in lst]

    out: List[Tuple[str, Poly]] = []
    mitte = _kette([(kk, True) for kk in bogen_teil(0, 0.0, 2 * math.pi)])
    out.append(("Mitte", mitte))
    for k in range(n):
        ws = winkel[k]
        for i, a0 in enumerate(ws):
            a1 = ws[(i + 1) % len(ws)]
            if a1 <= a0:
                a1 += 2 * math.pi
            aussen = bogen_teil(k + 1, a0 % (2 * math.pi), a0 % (2 * math.pi) + (a1 - a0))
            innen = bogen_teil(k, a0 % (2 * math.pi), a0 % (2 * math.pi) + (a1 - a0))
            folge = [(radial[k, a0], True)] + [(kk, True) for kk in aussen] + \
                    [(radial[k, ws[(i + 1) % len(ws)]], False)] + [(kk, False) for kk in reversed(innen)]
            out.append((f"R{k + 1}-{i + 1}", _kette(folge)))
    return out


def einruecken(kontur: Poly, d: float) -> Poly:
    """Kontur um d nach innen versetzen (Spiel zwischen den Teilen) und aufräumen.
    Die Rundungen der Nasen sind viel größer als d, darum entstehen keine Schleifen – die teure
    Schleifensuche entfällt (wichtig für viele Teile auf alten Rechnern)."""
    k = oriented(clean(kontur), True)
    if d > 0:
        k = offset_polygon(k, -d, miter_limit=2.0)
    g = _ausduennen(k, 0.06)
    if len(g) < 3 or signed_area(g) <= 0:
        raise ValueError("Puzzle: Ein Teil ist zu klein für das eingestellte Spiel – weniger Teile wählen")
    return g


def _ausduennen(pts: Poly, eps: float) -> Poly:
    out: Poly = []
    for p in pts:
        if out and math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) < eps:
            continue
        out.append(p)
    while len(out) > 3 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


# ---------------------------------------------------------------------------------------------
# Gravur verteilen
# ---------------------------------------------------------------------------------------------

def _bb(pts: Sequence[Point]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


class Clipper:
    """Linien an einem Bereich abschneiden: innerhalb von `innen`, außerhalb aller `sperren`.
    Die Kanten liegen in einem Raster; jede Strecke prüft nur die Kanten in ihren Zellen."""

    def __init__(self, innen: Poly, sperren: Sequence[Poly] = (), zelle: float = 3.0):
        self.innen = innen
        self.ix = PolygonIndex(innen)
        self.bb = _bb(innen)
        self.sperren = []
        for s in sperren:
            sb = _bb(s)
            if not (sb[2] < self.bb[0] or sb[0] > self.bb[2] or sb[3] < self.bb[1] or sb[1] > self.bb[3]):
                self.sperren.append((PolygonIndex(s), sb))
        self.z = zelle
        self.kanten: List[Tuple[float, float, float, float]] = []
        self.zellen: Dict[Tuple[int, int], List[int]] = {}
        for poly in [innen] + [s for s in sperren]:
            n = len(poly)
            for i in range(n):
                a, b = poly[i], poly[(i + 1) % n]
                k = len(self.kanten)
                self.kanten.append((a[0], a[1], b[0], b[1]))
                for c in self._zellen(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])):
                    self.zellen.setdefault(c, []).append(k)

    def _zellen(self, x0, y0, x1, y1):
        z = self.z
        i0, i1 = int(math.floor(x0 / z)), int(math.floor(x1 / z))
        j0, j1 = int(math.floor(y0 / z)), int(math.floor(y1 / z))
        return [(i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)]

    def frei(self, p: Point) -> bool:
        if not self.ix.contains(p):
            return False
        for ix, sb in self.sperren:
            if sb[0] <= p[0] <= sb[2] and sb[1] <= p[1] <= sb[3] and ix.contains(p):
                return False
        return True

    def strecke(self, a: Point, b: Point) -> List[Tuple[float, float]]:
        x0, y0, x1, y1 = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
        bb = self.bb
        if x1 < bb[0] or x0 > bb[2] or y1 < bb[1] or y0 > bb[3]:
            return []
        z = self.z
        ni = int(math.floor(x1 / z)) - int(math.floor(x0 / z)) + 1
        nj = int(math.floor(y1 / z)) - int(math.floor(y0 / z)) + 1
        if ni * nj > 400:
            kand = range(len(self.kanten))
        else:
            s = set()
            for c in self._zellen(x0, y0, x1, y1):
                lst = self.zellen.get(c)
                if lst:
                    s.update(lst)
            kand = s
        dx, dy = b[0] - a[0], b[1] - a[1]
        ts = [0.0, 1.0]
        K = self.kanten
        for k in kand:
            ex0, ey0, ex1, ey1 = K[k]
            if max(ex0, ex1) < x0 or min(ex0, ex1) > x1 or max(ey0, ey1) < y0 or min(ey0, ey1) > y1:
                continue
            ex, ey = ex1 - ex0, ey1 - ey0
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = ((ex0 - a[0]) * ey - (ey0 - a[1]) * ex) / den
            u = ((ex0 - a[0]) * dy - (ey0 - a[1]) * dx) / den
            if 0.0 < t < 1.0 and -1e-12 <= u <= 1.0 + 1e-12:
                ts.append(t)
        if len(ts) == 2:
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            return [(0.0, 1.0)] if self.frei(m) else []
        ts.sort()
        keep: List[Tuple[float, float]] = []
        for t0, t1 in zip(ts, ts[1:]):
            if t1 - t0 < 1e-9:
                continue
            tm = (t0 + t1) / 2
            if self.frei((a[0] + dx * tm, a[1] + dy * tm)):
                if keep and abs(keep[-1][1] - t0) < 1e-9:
                    keep[-1] = (keep[-1][0], t1)
                else:
                    keep.append((t0, t1))
        return keep

    def linie(self, pts: Sequence[Point], closed: bool = False) -> List[Poly]:
        """Linie abschneiden; liefert die sichtbaren Stücke."""
        seq = list(pts) + ([pts[0]] if closed else [])
        runs: List[Poly] = []
        cur: Poly = []
        for a, b in zip(seq, seq[1:]):
            if a == b:
                continue
            for t0, t1 in self.strecke(a, b):
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
        if closed and len(runs) >= 2 and runs[0][0] == runs[-1][-1]:
            runs[0] = runs.pop() + runs[0][1:]
        return runs


def _plen(pts: Sequence[Point]) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def verteilen(teile, bild: Sequence[Strich], sperren: Sequence[Poly] = (), oben: Sequence[Strich] = (),
              abstand: float = 0.45, min_len: float = 0.3) -> int:
    """Gravurbild auf die Teile (Part-Objekte) aufteilen. `bild` wird an `sperren` ausgespart
    (z. B. ein Namensband), `oben` (Text, Band, Zierrand) nicht. Liefert die Zahl der Gravurlinien."""
    gruppen = []
    for liste, sp in ((bild, sperren), (oben, ())):
        gruppen.append(([(pts, cl, _bb(pts)) for pts, cl in liste if len(pts) >= 2], sp))
    zahl = 0
    for teil in teile:
        innen = oriented(offset_polygon(teil.outline, -abstand, miter_limit=2.0), True)
        if len(innen) < 3:
            continue
        tb = _bb(innen)
        for striche, sp in gruppen:
            cl = Clipper(innen, sp)
            for pts, closed, sb in striche:
                if sb[2] < tb[0] or sb[0] > tb[2] or sb[3] < tb[1] or sb[1] > tb[3]:
                    continue
                stuecke = cl.linie(pts, closed)
                if closed and len(stuecke) == 1 and len(stuecke[0]) == len(pts) + 1 and stuecke[0][0] == pts[0]:
                    teil.add_engrave(pts, True)
                    zahl += 1
                    continue
                for s in stuecke:
                    if _plen(s) >= min_len:
                        teil.add_engrave(s, False)
                        zahl += 1
    return zahl
