"""
_jz.py – gemeinsame Werkzeuge der Jahreszeiten-Modelle.

Alle Modelle arbeiten gleich: Material wird als Raster auf einer Leinwand (Grundlagen-Bibliothek) aufgebaut –
volle Flächen plus Stege, minus Durchbrüche –, daraus macht `teil()` ein laserfestes Teil (Stege, Kerf und
lose Inseln geprüft). Danach legt `gravieren()` die feinen Gravurlinien nur dorthin, wo sicher Holz ist.

Winkel in Polarform (P) zählen von +y im Uhrzeigersinn: P(r, 0) liegt oben.
"""
from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence, Tuple

from pakete import bibliothek
from steckwerk import Point, oriented, point_in_polygon

Z = bibliothek("verzierungen")
K, E, W = Z.K, Z.E, Z.W
TAU = 2 * math.pi
Poly = List[Point]
Linie = Tuple[Poly, bool]


# --------------------------------------------------------------------------------------------------
# Geometrie
# --------------------------------------------------------------------------------------------------

def P(r: float, t: float, c: Point = (0.0, 0.0)) -> Point:
    return (c[0] + r * math.sin(t), c[1] + r * math.cos(t))


def drehen(poly: Sequence[Point], t: float, c: Point = (0.0, 0.0)) -> Poly:
    """Im Uhrzeigersinn um t drehen (passend zu P)."""
    cs, sn = math.cos(t), math.sin(t)
    return [(c[0] + (x - c[0]) * cs + (y - c[1]) * sn, c[1] - (x - c[0]) * sn + (y - c[1]) * cs) for x, y in poly]


def spiegeln(poly: Sequence[Point]) -> Poly:
    return [(-x, y) for x, y in poly]


def setzen(poly: Sequence[Point], x: float, y: float, s: float, t: float = 0.0, flip: bool = False) -> Poly:
    """Einheitsform skalieren, (spiegeln), im Uhrzeigersinn drehen und verschieben."""
    pts = [(-px * s if flip else px * s, py * s) for px, py in poly]
    return [(x + q[0], y + q[1]) for q in drehen(pts, t)]


def kreis(cx: float, cy: float, r: float, n: int = 0) -> Poly:
    n = n or max(24, int(TAU * r / 0.5))
    return [(cx + r * math.cos(TAU * k / n), cy + r * math.sin(TAU * k / n)) for k in range(n)]


def bogen(r: float, t0: float, t1: float, c: Point = (0.0, 0.0), n: int = 0) -> Poly:
    n = n or max(6, int(abs(t1 - t0) * r / 0.5))
    return [P(r, t0 + (t1 - t0) * k / n, c) for k in range(n + 1)]


def zu(poly: Sequence[Point]) -> Poly:
    """Geschlossene Linie (erster Punkt am Ende wiederholt)."""
    return list(poly) + [poly[0]]


def rund(n: int, polys: Iterable[Sequence[Point]], spiegel: bool = False) -> List[Poly]:
    """Formen n-mal um die Mitte verteilen (optional zusätzlich gespiegelt)."""
    polys = [list(p) for p in polys]
    out = []
    for j in range(n):
        t = TAU * j / n
        for p in polys:
            out.append(drehen(p, t))
            if spiegel:
                out.append(drehen(spiegeln(p), t))
    return out


def rund_linien(n: int, linien: Iterable[Linie], spiegel: bool = False) -> List[Linie]:
    linien = list(linien)
    out = []
    for j in range(n):
        t = TAU * j / n
        for pts, c in linien:
            out.append((drehen(pts, t), c))
            if spiegel:
                out.append((drehen(spiegeln(pts), t), c))
    return out


def spitzoval(L: float, b: float, n: int = 24, spitz: float = 1.0) -> Poly:
    """Blatt-/Blütenblattform von (0, 0) bis (0, L), größte Breite b (CCW). spitz > 1: schlanker."""
    rechts = []
    for k in range(n + 1):
        s = k / n
        rechts.append((b / 2 * math.sin(math.pi * s) ** spitz * (1 - 0.18 * (s - 0.4)), L * s))
    links = [(-x, y) for x, y in reversed(rechts[1:-1])]
    return oriented(rechts + links, True)


def bogenrand(R: float, m: int, tiefe: float, n_je: int = 16, phase: float = 0.0) -> Poly:
    """Kreis aus m Kreisbögen (Scheitel auf R, Kerben auf R − tiefe), CCW. phase 0: ein Scheitel genau oben."""
    Rn = R - tiefe
    pts: Poly = []
    for k in range(m):
        ta = TAU * (k + phase - 0.5) / m
        tb = TAU * (k + phase + 0.5) / m
        tm = (ta + tb) / 2
        A, B, C = P(Rn, ta), P(Rn, tb), P(R, tm)
        # Kreis durch A, C, B
        ax, ay = A
        bx, by = C
        cx, cy = B
        dd = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / dd
        uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / dd
        rr = math.hypot(ax - ux, ay - uy)
        a0 = math.atan2(ay - uy, ax - ux)
        a1 = math.atan2(cy - uy, cx - ux)
        am = math.atan2(by - uy, bx - ux)
        # Richtung so wählen, dass der Bogen über den Scheitel läuft
        def span(x0, x1):
            d = (x1 - x0) % TAU
            return d
        d1 = span(a0, a1)
        if span(a0, am) > d1:                # Scheitel liegt nicht auf dem positiven Bogen → andersherum
            d1 = d1 - TAU
        for j in range(n_je):
            a = a0 + d1 * j / n_je
            pts.append((ux + rr * math.cos(a), uy + rr * math.sin(a)))
    return oriented(pts, True)


def huelle(pts: Sequence[Point]) -> Poly:
    """Konvexe Hülle (CCW)."""
    q = sorted(set((round(x, 6), round(y, 6)) for x, y in pts))
    if len(q) < 3:
        return list(q)

    def kreuz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    unten: Poly = []
    for p in q:
        while len(unten) >= 2 and kreuz(unten[-2], unten[-1], p) <= 0:
            unten.pop()
        unten.append(p)
    oben: Poly = []
    for p in reversed(q):
        while len(oben) >= 2 and kreuz(oben[-2], oben[-1], p) <= 0:
            oben.pop()
        oben.append(p)
    return unten[:-1] + oben[:-1]


def tropfen(spitze: Point, fuss: Point, b: float, spitz_r: float = 0.0) -> Poly:
    """Tropfen von fuss (runder Bauch, Breite b) bis spitze; die Spitze ist leicht gerundet (Radius spitz_r,
    mindestens 0,3 mm), damit der Laser sie sauber schneidet."""
    dx, dy = spitze[0] - fuss[0], spitze[1] - fuss[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    rb = min(b / 2, L * 0.45)
    rt = max(0.3, spitz_r or 0.11 * b)
    cb = (fuss[0] + ux * rb, fuss[1] + uy * rb)
    ct = (spitze[0] - ux * rt, spitze[1] - uy * rt)
    pts = kreis(cb[0], cb[1], rb, max(24, int(TAU * rb / 0.25))) + kreis(ct[0], ct[1], rt, 12)
    return oriented(huelle(pts), True)


def oese(top: float, R: float, web: float) -> Tuple[Poly, Poly, float]:
    """Aufhängeöse oben: (Material, Loch, neue Oberkante)."""
    c, ro, ri = oese_mass(top, R, web)
    return kreis(c[0], c[1], ro, 48), kreis(c[0], c[1], ri, 32), c[1] + ro


def oese_mass(top: float, R: float, web: float) -> Tuple[Point, float, float]:
    """Mitte, Außen- und Lochradius der Öse über der Oberkante top."""
    ro = max(3.6, 0.042 * R)
    ri = max(1.6, ro - max(web + 0.9, 1.6))
    return (0.0, top + ro - 1.4), ro, ri


def umriss_mit_oese(fig, umriss: Poly, top: float, R: float, web: float, oese: bool):
    """Umriss (ggf. mit Öse) zur Figur geben. Liefert (exakter Umriss, Ösenloch oder None)."""
    if not oese:
        fig.add(umriss)
        return umriss, None
    c, ro, ri = oese_mass(top, R, web)
    u = mit_oese(umriss, c, ro)
    fig.add(u)
    return u, kreis(c[0], c[1], ri, 40)


# --------------------------------------------------------------------------------------------------
# Material
# --------------------------------------------------------------------------------------------------

def steg(fig, path: Sequence[Point], w: float) -> None:
    """Materialsteg entlang path: je Abschnitt ein Viereck, an Knicken und Enden ein Kreis (robust auch
    bei spitzen Ecken, wo ein einziger Umriss sich selbst überschneiden würde)."""
    pts = [q for i, q in enumerate(path) if i == 0 or math.hypot(q[0] - path[i - 1][0], q[1] - path[i - 1][1]) > 1e-6]
    if len(pts) < 2:
        return
    h = w / 2
    polys = []
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * h, dx / L * h
        polys.append([(a[0] + nx, a[1] + ny), (a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny), (b[0] + nx, b[1] + ny)])
    dots = [pts[0], pts[-1]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        u = (b[0] - a[0], b[1] - a[1])
        v = (c[0] - b[0], c[1] - b[1])
        cs = (u[0] * v[0] + u[1] * v[1]) / ((math.hypot(*u) * math.hypot(*v)) or 1)
        if cs < 0.97:
            dots.append(b)
    polys += [K.circle(x, y, h, 12) for x, y in dots]
    fig.add(*polys)


def leinwand(polys: Sequence[Sequence[Point]], rand: float = 3.0):
    xs = [q[0] for p in polys for q in p]
    ys = [q[1] for p in polys for q in p]
    gross = max(max(xs) - min(xs), max(ys) - min(ys))
    px = max(0.07, min(0.11, gross / 1500.0))
    return E.Leinwand((min(xs) - rand, min(ys) - rand, max(xs) + rand, max(ys) + rand), px)


def teil(cfg, name: str, lw, mat, notes: List[str]):
    return E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes)


def wmin(cfg) -> float:
    """Mindest-Stegbreite, die das Ausgleichen der Leinwand sicher übersteht."""
    return cfg.min_web + cfg.kerf + 0.45


# --------------------------------------------------------------------------------------------------
# Gravur
# --------------------------------------------------------------------------------------------------

def gravieren(part, lw, linien: Iterable[Linie], abstand: float = 0.45) -> int:
    """Gravurlinien nur dort, wo nach dem Prüfen sicher Holz ist (Abstand zu jedem Schnitt).
    Liefert die Zahl der gesetzten Linien."""
    r = E._andnot(lw.flaechen([part.outline]), lw.flaechen(part.holes) if part.holes else lw.leer())
    r = r.erode(lw.px_fuer(abstand))
    n0 = len(part.engrave)

    def drin(q) -> bool:
        c = int((q[0] - lw.x0) / lw.px)
        row = int((lw.y_top - q[1]) / lw.px)
        return 0 <= row < r.h and 0 <= c < r.w and (r.rows[row] >> c) & 1 == 1

    for pts, closed in linien:
        pts = list(pts)
        if len(pts) < 2:
            continue
        if closed and pts[0] != pts[-1]:
            pts = pts + [pts[0]]
        L = K.path_len(pts)
        if L < 0.08:
            continue
        dicht = K.resample(pts, min(0.25, L / 3)) if L > 0.3 else pts
        flags = [drin(q) for q in dicht]
        if all(flags):
            part.add_engrave(dicht, False)
            continue
        lauf: Poly = []
        for q, f in zip(dicht, flags):
            if f:
                lauf.append(q)
            else:
                if len(lauf) >= 2 and K.path_len(lauf) > 0.35:
                    part.add_engrave(lauf)
                lauf = []
        if len(lauf) >= 2 and K.path_len(lauf) > 0.35:
            part.add_engrave(lauf)
    return len(part.engrave) - n0


def verdecken(linien: Iterable[Linie], darueber: Sequence[Sequence[Point]]) -> List[Linie]:
    """Linienstücke weglassen, die unter einer der Flächen darüber liegen (überlappende Blätter)."""
    if not darueber:
        return list(linien)
    boxen = []
    for p in darueber:
        xs = [q[0] for q in p]
        ys = [q[1] for q in p]
        boxen.append((min(xs), min(ys), max(xs), max(ys), p))
    out = []
    for pts, closed in linien:
        pts = list(pts) + ([pts[0]] if closed else [])
        if len(pts) < 2:
            continue
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
        lx0, ly0, lx1, ly1 = min(xs), min(ys), max(xs), max(ys)
        nah = [bx for bx in boxen if bx[0] <= lx1 and bx[2] >= lx0 and bx[1] <= ly1 and bx[3] >= ly0]
        if not nah:
            out.append((pts, False))
            continue

        def unter(q) -> bool:
            for x0, y0, x1, y1, p in nah:
                if x0 <= q[0] <= x1 and y0 <= q[1] <= y1 and point_in_polygon(q, p):
                    return True
            return False
        dicht = K.resample(pts, min(0.3, max(0.05, K.path_len(pts) / 3)))
        lauf: Poly = []
        for q in dicht:
            if unter(q):
                if len(lauf) >= 2:
                    out.append((lauf, False))
                lauf = []
            else:
                lauf.append(q)
        if len(lauf) >= 2:
            out.append((lauf, False))
    return out


def nur_in(linien: Iterable[Linie], flaeche: Sequence[Point]) -> List[Linie]:
    """Linienstücke behalten, die in der Fläche liegen."""
    xs = [q[0] for q in flaeche]
    ys = [q[1] for q in flaeche]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    out: List[Linie] = []
    for pts, closed in linien:
        pts = list(pts) + ([pts[0]] if closed else [])
        if len(pts) < 2:
            continue
        dicht = K.resample(pts, min(0.3, max(0.05, K.path_len(pts) / 3)))
        lauf: Poly = []
        for q in dicht:
            if x0 <= q[0] <= x1 and y0 <= q[1] <= y1 and point_in_polygon(q, flaeche):
                lauf.append(q)
            else:
                if len(lauf) >= 2:
                    out.append((lauf, False))
                lauf = []
        if len(lauf) >= 2:
            out.append((lauf, False))
    return out


def text(t: str, cx: float, cy: float, max_w: float, max_h: float, max_cap: float, min_cap: float = 2.2,
         style: str = "normal") -> List[Linie]:
    t = (t or "").strip()
    if not t:
        return []
    versuche = [t]
    if "|" not in t and " " in t:                         # sonst zweizeilig, Umbruch nahe der Mitte
        leer = [i for i, c in enumerate(t) if c == " "]
        i = min(leer, key=lambda i: abs(i - len(t) / 2))
        versuche.append(t[:i] + "|" + t[i + 1:])
    fehler = None
    for v in versuche:
        try:
            st, _ = W.text_in_box(v, cx, cy, max_w, max_h, max_cap, min_cap, gap_faktor=0.08, style=style,
                                  case="normal", zeilenabstand=0.45)
            return [(s, False) for s in st]
        except ValueError as e:
            fehler = e
    raise fehler


def doppelkreis(r: float, d: float) -> List[Linie]:
    return [(zu(kreis(0, 0, r)), False), (zu(kreis(0, 0, r - d)), False)]


def perlenkreis(r: float, rp: float, abstand: float) -> List[Linie]:
    n = max(8, int(TAU * r / abstand))
    return [(zu(kreis(*P(r, TAU * k / n), rp, 10)), False) for k in range(n)]


# --------------------------------------------------------------------------------------------------
# Motive als Gravur
# --------------------------------------------------------------------------------------------------

def eiskristall(R: float, art: int = 0) -> List[Linie]:
    """Sechsstrahliger Eiskristall (Gravur, Mitte 0/0): doppelt gezogene Arme mit gefiederten Seitenästen,
    Plättchen und Facetten, dazwischen kurze Nebenarme. art 0: Farn, 1: Plättchen, 2: Stern."""
    arm: List[Linie] = []
    d = max(0.3, R * 0.016)
    arm.append(([(d, R * 0.17), (d, R * 0.88), (0, R), (-d, R * 0.88), (-d, R * 0.17)], False))
    aeste = ((0.34, 0.30), (0.55, 0.25), (0.74, 0.17), (0.88, 0.08)) if art != 1 else ((0.42, 0.22), (0.70, 0.15))
    for s, L in aeste:
        y = R * s
        for sg in (1, -1):
            a = math.radians(60)
            tip = (sg * (d + R * L * math.sin(a)), y + R * L * math.cos(a))
            arm.append(([(sg * d, y), tip], False))
            if art == 1 or L < 0.1:
                continue
            for f in (0.3, 0.52, 0.74):                     # Fiedern zu beiden Seiten des Asts
                bx, by = sg * d + (tip[0] - sg * d) * f, y + (tip[1] - y) * f
                l2 = R * L * 0.36 * (1.08 - f)
                arm.append(([(bx, by), (bx + sg * l2 * 0.05, by + l2)], False))
                arm.append(([(bx, by), (bx + sg * l2, by - l2 * 0.05)], False))
    for yy, hx in ((0.47, 0.07), (0.66, 0.05)) if art != 2 else ((0.47, 0.07),):
        arm.append((zu([P(R * hx, TAU * k / 6 + TAU / 12, (0, R * yy)) for k in range(6)]), False))
    if art == 1:                                        # breite Plättchen mit Rippen
        for yy, hx in ((0.30, 0.10), (0.84, 0.08)):
            arm.append((zu([P(R * hx, TAU * k / 6, (0, R * yy)) for k in range(6)]), False))
            arm.append(([(0, R * yy - R * hx * 0.7), (0, R * yy + R * hx * 0.7)], False))
    if art == 2:
        arm.append((zu([(0, R * 0.76), (R * 0.06, R * 0.86), (0, R * 0.97), (-R * 0.06, R * 0.86)]), False))
        arm.append((zu([(0, R * 0.80), (R * 0.03, R * 0.86), (0, R * 0.92), (-R * 0.03, R * 0.86)]), False))
    # Nebenarm zwischen zwei Armen
    neben: List[Linie] = [([(0, R * 0.19), (0, R * 0.46)], False)]
    for s, L in ((0.30, 0.07), (0.38, 0.05)):
        for sg in (1, -1):
            neben.append(([(0, R * s), (sg * R * L * 0.87, R * s + R * L * 0.5)], False))
    neben.append((zu([(0, R * 0.46), (R * 0.025, R * 0.5), (0, R * 0.54), (-R * 0.025, R * 0.5)]), False))
    out = rund_linien(6, arm)
    out += [(drehen(p, TAU / 12), c) for p, c in rund_linien(6, neben)]
    for f in (0.17, 0.12, 0.065):
        out.append((zu([P(R * f, TAU * k / 6) for k in range(6)]), False))
    for k in range(6):
        out.append(([P(R * 0.065, TAU * k / 6), P(R * 0.17, TAU * k / 6)], False))
        out.append(([P(R * 0.12, TAU * k / 6), P(R * 0.17 * 0.87, TAU * (k + 0.5) / 6)], False))
    return out


def schraffur(poly: Sequence[Point], abstand: float, winkel: float = 0.0) -> List[Linie]:
    """Parallele Linien im Abstand ‚abstand‘ unter ‚winkel‘ (Bogenmaß, 0 = waagrecht), auf poly beschnitten."""
    cs, sn = math.cos(-winkel), math.sin(-winkel)
    rot = [(x * cs - y * sn, x * sn + y * cs) for x, y in poly]      # Linien werden waagrecht
    ys = [q[1] for q in rot]
    out: List[Linie] = []
    n = len(rot)
    y = min(ys) + abstand / 2
    cb, sb = math.cos(winkel), math.sin(winkel)
    while y < max(ys):
        xs = []
        for i in range(n):
            a, b = rot[i], rot[(i + 1) % n]
            if (a[1] <= y < b[1]) or (b[1] <= y < a[1]):
                xs.append(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
        xs.sort()
        for x0, x1 in zip(xs[0::2], xs[1::2]):
            if x1 - x0 > 0.3:
                out.append(([(x0 * cb - y * sb, x0 * sb + y * cb), (x1 * cb - y * sb, x1 * sb + y * cb)], False))
        y += abstand
    return out


def zierstern(R: float, zacken: int = 8, schatten: float = 0.0) -> List[Linie]:
    """Facettierter Stern mit Doppelkontur und Mittelgraten (Gravur); schatten > 0: je Zacke eine Hälfte fein
    schraffiert (Linienabstand), das gibt Tiefe wie bei geschliffenem Glas."""
    out: List[Linie] = []

    def rr(k, f=1.0):
        return R * f * (1 if k % 2 == 0 else 0.42) * (1 if (k // 2) % 2 == 0 else 0.78)
    for f in (1.0, 0.86):
        out.append((zu([P(rr(k, f), math.pi * k / zacken) for k in range(2 * zacken)]), False))
    for k in range(2 * zacken):
        out.append(([P(R * 0.08, math.pi * k / zacken), P(rr(k, 0.86), math.pi * k / zacken)], False))
    if schatten > 0:
        for k in range(0, 2 * zacken, 2):
            tri = [(0.0, 0.0), P(rr(k, 0.86), math.pi * k / zacken), P(rr(k + 1, 0.86), math.pi * (k + 1) / zacken)]
            tri = [(x * 0.97, y * 0.97) for x, y in tri]
            out += schraffur(tri, schatten, math.pi / 2 - math.pi * k / zacken)
    out.append((zu(kreis(0, 0, R * 0.08, 16)), False))
    return out


def nadelzweig(pfad: Sequence[Point], nadel: float, abstand: float, winkel: float = 38.0, seed: int = 0
               ) -> List[Linie]:
    """Tannenzweig: Mittelast plus leicht gebogene Nadeln zu beiden Seiten, zur Spitze hin kürzer, mit kleiner
    natürlicher Streuung in Länge und Winkel (Gravur, reproduzierbar über seed)."""
    r = K.rng(seed, "nadel", len(pfad), round(nadel, 2))
    out: List[Linie] = [(list(pfad), False)]
    pts = K.resample(list(pfad), abstand)
    n = len(pts)
    for i in range(1, n - 1):
        s = i / (n - 1)
        q, nx = pts[i], pts[i + 1]
        dx, dy = nx[0] - q[0], nx[1] - q[1]
        dl = math.hypot(dx, dy) or 1
        dx, dy = dx / dl, dy / dl
        for sg in (1, -1):
            a = math.radians(winkel + r.uniform(-6, 6))
            ln = nadel * (1.0 - 0.6 * s ** 1.4) * r.uniform(0.82, 1.08)
            if s < 0.08:
                ln *= 0.6
            vx = dx * math.cos(a) - sg * dy * math.sin(a)
            vy = dy * math.cos(a) + sg * dx * math.sin(a)
            # Nadel leicht zur Zweigspitze gebogen
            m = (q[0] + vx * ln * 0.5 + dx * ln * 0.06, q[1] + vy * ln * 0.5 + dy * ln * 0.06)
            e = (q[0] + vx * ln + dx * ln * 0.18, q[1] + vy * ln + dy * ln * 0.18)
            out.append(([q, m, e], False))
    e = pts[-1]
    d = (pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]) if n > 1 else (0.0, 0.0)
    out.append(([e, (e[0] + d[0] * 1.2, e[1] + d[1] * 1.2)], False))
    return out


def beere(cx: float, cy: float, r: float) -> List[Linie]:
    """Beere mit Glanzlicht und Blütenrest (Gravur)."""
    out: List[Linie] = [(zu(kreis(cx, cy, r, 20)), False)]
    out.append((bogen(r * 0.55, -1.2, -0.3, (cx, cy), 6), False))
    out.append(([(cx + r * 0.15, cy - r * 0.45), (cx + r * 0.3, cy - r * 0.3)], False))
    return out


def adern(L: float, b: float, n: int = 5, winkel: float = 50.0) -> List[Linie]:
    """Blattadern für spitzoval(L, b): Mittelrippe und n Seitenadern je Seite (Gravur)."""
    out: List[Linie] = [([(0, L * 0.02), (0, L * 0.9)], False)]
    a = math.radians(winkel)
    for k in range(1, n + 1):
        y = L * (0.12 + 0.68 * k / (n + 1))
        s = y / L
        w = b / 2 * math.sin(math.pi * s) * 0.8
        for sg in (1, -1):
            out.append(([(0, y), (sg * w * 0.55, y + w * 0.55 / math.tan(a) * 0.6),
                         (sg * w, y + w / math.tan(a))], False))
    return out


# --------------------------------------------------------------------------------------------------
# Gemeinsamer Ablauf der Modelle
# --------------------------------------------------------------------------------------------------

FEINHEIT = [("fein", "fein (für 2 mm Holz)"), ("mittel", "mittel"), ("kraeftig", "kräftig (für 4 mm)")]
_DICKE = dict(fein=0.0, mittel=0.25, kraeftig=0.6)
FEINHEIT_EN = {"fein (für 2 mm Holz)": "fine (for 2 mm wood)", "mittel": "medium", "kräftig (für 4 mm)": "bold (for 4 mm)",
               "Feinheit": "Fineness", "Größe": "Size", "Anzahl": "Count", "Öse zum Aufhängen": "Hanging loop",
               "Jahreszeiten": "Seasons", "Text": "Text", "leer = ohne": "empty = none"}


def steg_breite(cfg, feinheit: str) -> float:
    return wmin(cfg) + _DICKE[feinheit]


def auswahl(wert: str, liste, was: str) -> str:
    if wert not in dict(liste):
        raise ValueError(f"{was}: unbekannte Auswahl {wert!r}")
    return wert


def text_pruefen(t: str) -> str:
    from models import _font
    t = (t or "").strip()
    bad = _font.unsupported(t)
    if bad:
        raise ValueError(f"Diese Zeichen kennt die Gravurschrift nicht: {' '.join(bad)}")
    return t


def bauen(cfg, name: str, fig, linien: Iterable[Linie], notes: List[str], oese_loch: Optional[Poly] = None,
          px: Optional[float] = None, umriss: Optional[Poly] = None):
    """Figur → laserfestes Teil mit Gravur. Liefert (Part, Leinwand). Alle Schnittflächen der Figur (und die
    Öse) werden nach dem Prüfen wieder exakt eingesetzt, wo das Prüfen nichts geändert hat."""
    x0, y0, x1, y1 = fig.bbox()
    gross = max(x1 - x0, y1 - y0)
    px = px or max(0.06, min(0.1, gross / 1500.0))
    lw = E.Leinwand((x0 - 2, y0 - 2, x1 + 2, y1 + 2), px)
    mat = lw.figur(fig)
    if oese_loch:
        mat = E._andnot(mat, lw.flaechen([oese_loch]))
    part = teil(cfg, name, lw, mat, notes)
    loecher = [p for sg, p in fig.ops if sg == "-"] + ([oese_loch] if oese_loch else [])
    part = scharf(cfg, part, loecher, umriss)
    gravieren(part, lw, linien)
    return part, lw


def versetzt(poly: Sequence[Point], d: float) -> Poly:
    """Umriss um d nach außen (d < 0: innen) versetzt."""
    from steckwerk import offset_polygon
    return oriented(offset_polygon(oriented(list(poly), True), d), True)


def polar_fenster(r0: float, r1: float, t: float, breite: float, form: str = "rund") -> Poly:
    """Fenster in einem Ring von Radius r0 bis r1 um Winkel t, Breite ‚breite‘ (mm).
    form: rund (Rundbogen), spitz (gotischer Spitzbogen) oder gerade."""
    h = breite / 2
    lokal: Poly = []
    if form == "spitz":
        ys = r1 - math.sqrt(3) * h
        rechts = [(h, r0 + (ys - r0) * k / 6) for k in range(7)]
        rechts += [(-h + 2 * h * math.cos(math.pi / 3 * k / 10), ys + 2 * h * math.sin(math.pi / 3 * k / 10))
                   for k in range(1, 11)]
    elif form == "rund":
        ys = r1 - h
        rechts = [(h, r0 + (ys - r0) * k / 6) for k in range(7)]
        rechts += [(h * math.cos(math.pi / 2 * k / 8), ys + h * math.sin(math.pi / 2 * k / 8)) for k in range(1, 9)]
    else:
        rechts = [(h, r0 + (r1 - r0) * k / 6) for k in range(7)] + [(0.0, r1)]
    lokal = rechts + [(-x, y) for x, y in reversed(rechts[:-1])]
    return oriented([P(y, t + x / y) for x, y in lokal], True)


def stechpalme(L: float, b: float, zacken: int = 3) -> Tuple[Poly, List[Linie]]:
    """Stechpalmenblatt von (0, 0) nach (0, L): Umriss mit Stacheln (CCW) und Gravur (Umriss, Adern)."""
    rechts = []
    for k in range(zacken + 1):
        s = k / zacken
        y = L * (0.06 + 0.84 * s)
        w = b / 2 * math.sin(math.pi * (0.08 + 0.84 * s)) ** 0.8
        rechts.append((w * 1.08, y))                      # Stachel
        if k < zacken:                                    # Bucht dazwischen
            s2 = (k + 0.5) / zacken
            y2 = L * (0.06 + 0.84 * s2)
            w2 = b / 2 * math.sin(math.pi * (0.08 + 0.84 * s2)) ** 0.8
            rechts.append((w2 * 0.62, y2 - L * 0.02))
    pts = [(0, 0)] + rechts + [(0, L)] + [(-x, y) for x, y in reversed(rechts)]
    um = oriented(pts, True)
    lin: List[Linie] = [(um, True), ([(0, L * 0.03), (0, L * 0.94)], False)]
    for x, y in rechts[0::2][:-1]:
        for sg in (1, -1):
            lin.append(([(0, y - L * 0.06), (sg * x * 0.55, y + L * 0.02)], False))
    lin.append(([(0, -L * 0.12), (0, L * 0.03)], False))   # Stiel
    return um, lin


def platziert(form: Tuple[Poly, List[Linie]], x: float, y: float, t: float, s: float = 1.0, flip: bool = False):
    um, lin = form
    return setzen(um, x, y, s, t, flip), [(setzen(p, x, y, s, t, flip), c) for p, c in lin]


def blaetter_gravur(stapel: Sequence[Tuple[Poly, List[Linie]]]) -> List[Linie]:
    """Überlappende Formen (unten → oben): Linien jeder Form ohne die Stücke unter späteren Formen."""
    out: List[Linie] = []
    for i, (um, lin) in enumerate(stapel):
        darueber = [s[0] for s in stapel[i + 1:] if s[0]]
        out += verdecken(lin, darueber) if darueber else [(list(p) + ([p[0]] if c else []), False) for p, c in lin]
    return out


# --------------------------------------------------------------------------------------------------
# Saubere Schnittkanten
# --------------------------------------------------------------------------------------------------

def mit_oese(umriss: Sequence[Point], c: Point, ro: float, n: int = 48) -> Poly:
    """Kreis (Öse) in einen Umriss einsetzen: Punkte im Kreis entfallen, dafür läuft der äußere Kreisbogen."""
    roh = oriented(list(umriss), True)
    pts = K.resample(roh + [roh[0]], 0.5)[:-1]
    N = len(pts)
    drin = [math.hypot(q[0] - c[0], q[1] - c[1]) < ro for q in pts]
    if not any(drin) or all(drin):
        return pts
    start = next(i for i in range(N) if drin[i] and not drin[i - 1])
    ende = start
    while drin[(ende + 1) % N]:
        ende += 1
    if any(drin[(ende + 1 + k) % N] for k in range(N - (ende - start + 1))):
        return pts                                        # mehr als ein Schnittbereich: nicht anfassen

    def schnitt(a, b):
        # Punkt auf a→b mit Abstand ro zu c (a außen, b innen)
        lo, hi = 0.0, 1.0
        for _ in range(40):
            m = (lo + hi) / 2
            q = (a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m)
            if math.hypot(q[0] - c[0], q[1] - c[1]) < ro:
                hi = m
            else:
                lo = m
        return (a[0] + (b[0] - a[0]) * lo, a[1] + (b[1] - a[1]) * lo)
    p0 = schnitt(pts[start - 1], pts[start])
    p1 = schnitt(pts[(ende + 1) % N], pts[ende % N])
    a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
    a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
    if a1 < a0:
        a1 += TAU
    k = max(8, int(n * (a1 - a0) / TAU))
    bogen_pts = [(c[0] + ro * math.cos(a0 + (a1 - a0) * j / k), c[1] + ro * math.sin(a0 + (a1 - a0) * j / k))
                 for j in range(k + 1)]
    rest = [pts[(ende + 1 + j) % N] for j in range(N - (ende - start + 1))]
    return oriented(bogen_pts + rest, True)


def _abstand_zu(q: Point, poly: Sequence[Point]) -> float:
    best = 1e9
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1e-12
        u = max(0.0, min(1.0, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / L2))
        d = math.hypot(a[0] + u * dx - q[0], a[1] + u * dy - q[1])
        if d < best:
            best = d
    return best


def _passt(entwurf: Sequence[Point], ist: Sequence[Point], tol: float, locker: bool = False) -> bool:
    from steckwerk import signed_area
    A0, A1 = abs(signed_area(list(entwurf))), abs(signed_area(list(ist)))
    if A1 <= 0 or abs(A0 / A1 - 1) > 0.08:
        return False
    for a, b in ((entwurf, ist), (ist, entwurf)):
        proben = list(a)[::max(1, len(a) // 60)]
        d = [_abstand_zu(q, b) for q in proben]
        aus = sum(1 for x in d if x > tol)
        if max(d) > (max(1.0, 2 * tol) if locker else tol) or aus > (len(proben) // 50 if locker else 0):
            return False
    return True


def scharf(cfg, part, loecher: Sequence[Sequence[Point]], umriss: Optional[Sequence[Point]] = None):
    """Gerasterte Schnitte durch die exakt gezeichneten Formen ersetzen, wo sie (bis auf Rasterfehler) gleich
    sind: glatte Kreise, Tropfen und Bögen statt Treppchen. Was das Prüfen verändert hat, bleibt gerastert."""
    from steckwerk import Part, offset_polygon
    tol = 0.45
    neu_umriss = part.outline
    if umriss is not None:
        u = oriented(list(umriss), True)
        comp = offset_polygon(u, cfg.kerf / 2)
        if _passt(u, part.outline, tol + 0.1, True) and not E.kreuzungen(comp) and not E._versatz_fehler(u, comp, cfg.kerf / 2):
            neu_umriss = u
    boxen = []
    for d in loecher:
        xs = [q[0] for q in d]
        ys = [q[1] for q in d]
        boxen.append(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, list(d)))
    q = Part(part.name, neu_umriss, features=list(part.features))
    for h in part.holes:
        xs = [p[0] for p in h]
        ys = [p[1] for p in h]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        ersatz = None
        for bx, by, d in boxen:
            if abs(bx - cx) < 0.4 and abs(by - cy) < 0.4 and _passt(d, h, tol):
                if E.probleme(oriented(d, False), cfg.kerf / 2) == []:
                    ersatz = d
                break
        q.add_hole(ersatz if ersatz is not None else h)
    for s in part.engrave:
        q.engrave.append(s)
    return q


# --------------------------------------------------------------------------------------------------
# Pflanzen und Tiere (Gravur mit Umriss zum Verdecken)
# --------------------------------------------------------------------------------------------------

Form = Tuple[Poly, List[Linie]]


def blatt(L: float, b: float, adern_n: int = 5, spitz: float = 1.0) -> Form:
    """Blatt von (0, 0) nach (0, L) mit Umriss, Mittelrippe und Seitenadern."""
    um = spitzoval(L, b, 24, spitz)
    return um, [(um, True)] + adern(L, b, adern_n)


def bluetenblatt(L: float, b: float, kerbe: float = 0.0, n: int = 20) -> Poly:
    """Rundes Blütenblatt von (0, 0) nach (0, L), breiteste Stelle bei 0,65 L, oben auf Wunsch eingekerbt."""
    rechts = []
    for k in range(n + 1):
        s = k / n
        y = L * s
        x = b / 2 * math.sin(math.pi * min(1.0, s / 1.3 + 0.08)) ** 0.7 * (1 - s ** 6) ** 0.5
        rechts.append((x, y))
    if kerbe > 0:
        rechts[-1] = (0.0, L - kerbe)
        rechts[-2] = (rechts[-2][0] * 0.9, L * 0.985)
    pts = rechts + [(-x, y) for x, y in reversed(rechts[1:-1])]
    return oriented(pts, True)


def bluete(r: float, blaetter: int = 5, kerbe: bool = True, lagen: int = 1, staub: int = 10) -> Form:
    """Blüte um (0, 0): Blütenblätter mit Adern, Staubgefäße mit Köpfchen, Mitte mit Punkten."""
    stapel: List[Form] = []
    for lage in range(lagen):
        f = 1.0 - 0.3 * lage
        for k in range(blaetter):
            t = TAU * (k + 0.5 * lage) / blaetter
            bl = bluetenblatt(r * f, r * f * (2.6 / blaetter + 0.55), r * 0.12 * f if kerbe else 0.0)
            um = drehen(bl, t)
            lin = [(um, True)]
            for a in (-0.22, 0.0, 0.22):                         # feine Adern
                lin.append((drehen([(0, r * 0.2 * f), (a * r * f * 0.5, r * 0.55 * f), (a * r * f * 0.8, r * 0.78 * f)], t), False))
            stapel.append((um, lin))
    mitte = kreis(0, 0, r * 0.2, 24)
    lin = [(mitte, True), (kreis(0, 0, r * 0.11, 16), True)]
    for k in range(staub):
        t = TAU * (k + 0.25) / staub
        a, e = P(r * 0.2, t), P(r * 0.42, t)
        lin.append(([a, e], False))
        lin.append((kreis(e[0], e[1], max(0.3, r * 0.045), 10), True))
    for k in range(7):
        q = P(r * 0.06 if k else 0.0, TAU * k / 6)
        lin.append((kreis(q[0], q[1], max(0.25, r * 0.025), 8), True))
    gr = blaetter_gravur(stapel + [(kreis(0, 0, r * 0.2, 24), lin)])
    um = huelle([q for s in stapel for q in s[0]])
    return um, gr


def tulpe(h: float) -> Form:
    """Tulpe von (0, 0) (Stielansatz) nach oben, Höhe h des Kelchs: drei Blütenblätter mit Linien."""
    b = 0.72 * h
    aussen = K.spline([(0, 0), (b * 0.45, h * 0.18), (b * 0.52, h * 0.6), (b * 0.38, h * 1.0), (b * 0.18, h * 0.82),
                       (0, h * 0.98), (-b * 0.18, h * 0.82), (-b * 0.38, h * 1.0), (-b * 0.52, h * 0.6),
                       (-b * 0.45, h * 0.18)], closed=True, n=8)
    um = oriented(aussen, True)
    lin: List[Linie] = [(um, True)]
    lin.append((K.bez3((0, h * 0.04), (b * 0.3, h * 0.3), (b * 0.25, h * 0.7), (0, h * 0.98), 14), False))
    lin.append((K.bez3((0, h * 0.04), (-b * 0.3, h * 0.3), (-b * 0.25, h * 0.7), (0, h * 0.98), 14), False))
    for sg in (1, -1):
        for f in (0.35, 0.6):
            lin.append((K.bez((sg * b * 0.1, h * 0.12), (sg * b * f * 0.6, h * 0.5), (sg * b * f * 0.62, h * 0.85), 10), False))
    return um, lin


def schmetterling(g: float) -> List[Linie]:
    """Schmetterling (Spannweite g) um (0, 0), Kopf oben: gemusterte Flügel, Körper, Fühler (Gravur)."""
    lin: List[Linie] = []
    s = g / 2
    vorder = K.spline([(0.04 * s, 0.05 * s), (0.35 * s, 0.42 * s), (0.82 * s, 0.62 * s), (0.98 * s, 0.48 * s),
                       (0.86 * s, 0.12 * s), (0.5 * s, -0.02 * s), (0.08 * s, -0.04 * s)], closed=True, n=10)
    hinter = K.spline([(0.06 * s, -0.08 * s), (0.5 * s, -0.12 * s), (0.72 * s, -0.36 * s), (0.6 * s, -0.66 * s),
                       (0.36 * s, -0.72 * s), (0.18 * s, -0.5 * s), (0.04 * s, -0.22 * s)], closed=True, n=10)
    fluegel = []
    for sg in (1, -1):
        for fl in (vorder, hinter):
            p = [(sg * x, y) for x, y in fl]
            fluegel.append(p)
            lin.append((p, True))
            try:
                lin.append((zu(versetzt(p, -0.09 * s)), False))
            except Exception:
                pass
        # Adern aus der Flügelwurzel
        for ex, ey in ((0.9, 0.5), (0.8, 0.3), (0.62, 0.1), (0.55, -0.3), (0.45, -0.55), (0.3, -0.6)):
            lin.append((K.bez((sg * 0.05 * s, 0.0), (sg * ex * 0.5 * s, ey * 0.6 * s), (sg * ex * 0.92 * s, ey * 0.95 * s), 10), False))
        # Augenflecken und Perlen am Rand
        for cx, cy, rr in ((0.62, 0.36, 0.11), (0.42, -0.46, 0.08)):
            lin.append((kreis(sg * cx * s, cy * s, rr * s, 20), True))
            lin.append((kreis(sg * cx * s, cy * s, rr * s * 0.45, 14), True))
        for k in range(7):
            q = (sg * (0.86 - 0.06 * k) * s, (0.5 - 0.13 * k) * s)
            if k < 4:
                lin.append((kreis(q[0], q[1], 0.025 * s, 8), True))
    korper = K.ellipse(0, -0.12 * s, 0.05 * s, 0.42 * s, 0, 24)
    lin.append((korper, True))
    for k in range(1, 6):
        y = -0.12 * s - 0.42 * s + 0.12 * s * k
        lin.append(([(-0.045 * s, y), (0.045 * s, y)], False))
    lin.append((kreis(0, 0.34 * s, 0.07 * s, 14), True))
    for sg in (1, -1):
        lin.append((K.bez((sg * 0.02 * s, 0.4 * s), (sg * 0.1 * s, 0.62 * s), (sg * 0.24 * s, 0.74 * s), 10), False))
        lin.append((kreis(sg * 0.25 * s, 0.75 * s, 0.03 * s, 8), True))
    return lin
