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


def bogenrand(R: float, m: int, tiefe: float, n_je: int = 24) -> Poly:
    """Kreis mit m nach außen gewölbten Spitzenbögen (Scheitel auf R, Kerben auf R − tiefe)."""
    pts = []
    for k in range(m * n_je):
        t = TAU * k / (m * n_je)
        u = abs(math.sin(m * t / 2))
        pts.append(P(R - tiefe * (1 - u ** 0.55), t))
    return oriented(pts, True)


def tropfen(spitze: Point, fuss: Point, b: float, n: int = 18) -> Poly:
    """Tropfen: runder Bauch bei fuss, Spitze bei spitze."""
    dx, dy = spitze[0] - fuss[0], spitze[1] - fuss[1]
    L = math.hypot(dx, dy)
    t = math.atan2(dx, dy)
    form = []
    for k in range(n + 1):
        s = k / n
        form.append((b / 2 * math.sin(math.pi * s) ** 0.7 * (1 - s) ** 0.6, L * (1 - s) - b * 0.15 * (1 - s)))
    form = form + [(-x, y) for x, y in reversed(form[1:-1])]
    return oriented([(fuss[0] + q[0], fuss[1] + q[1]) for q in drehen(form, t)], True)


def oese(top: float, R: float, web: float) -> Tuple[Poly, Poly, float]:
    """Aufhängeöse oben: (Material, Loch, neue Oberkante)."""
    ro = max(3.6, 0.045 * R)
    c = (0.0, top + ro - 1.6)
    ri = max(1.6, ro - max(web + 0.9, 1.6))
    return kreis(c[0], c[1], ro, 48), kreis(c[0], c[1], ri, 32), c[1] + ro


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
        if L < 0.3:
            continue
        dicht = K.resample(pts, min(0.25, L / 3))
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

    def unter(q) -> bool:
        for x0, y0, x1, y1, p in boxen:
            if x0 <= q[0] <= x1 and y0 <= q[1] <= y1 and point_in_polygon(q, p):
                return True
        return False

    out = []
    for pts, closed in linien:
        pts = list(pts) + ([pts[0]] if closed else [])
        if len(pts) < 2:
            continue
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


def text(t: str, cx: float, cy: float, max_w: float, max_h: float, max_cap: float, min_cap: float = 2.2,
         style: str = "normal") -> List[Linie]:
    t = (t or "").strip()
    if not t:
        return []
    st, _ = W.text_in_box(t, cx, cy, max_w, max_h, max_cap, min_cap, gap_faktor=0.08, style=style, case="normal")
    return [(s, False) for s in st]


def doppelkreis(r: float, d: float) -> List[Linie]:
    return [(zu(kreis(0, 0, r)), False), (zu(kreis(0, 0, r - d)), False)]


def perlenkreis(r: float, rp: float, abstand: float) -> List[Linie]:
    n = max(8, int(TAU * r / abstand))
    return [(zu(kreis(*P(r, TAU * k / n), rp, 10)), False) for k in range(n)]


# --------------------------------------------------------------------------------------------------
# Motive als Gravur
# --------------------------------------------------------------------------------------------------

def eiskristall(R: float, art: int = 0) -> List[Linie]:
    """Sechsstrahliger Eiskristall mit Seitenästen, Plättchen und Facetten (Gravur, Mitte 0/0)."""
    arm: List[Linie] = []
    d = max(0.32, R * 0.018)                         # halbe Armbreite: doppelte Linie wirkt wie Eis
    arm.append(([(d, R * 0.16), (d, R * 0.90), (0, R), (-d, R * 0.90), (-d, R * 0.16)], False))
    # Seitenäste: drei Paare, je mit kleinen Zweigen
    for s, L in ((0.36, 0.30), (0.58, 0.24), (0.78, 0.15)):
        if art == 1:
            L *= 1.15
        y = R * s
        for sg in (1, -1):
            a = math.radians(60)
            tip = (sg * (d + R * L * math.sin(a)), y + R * L * math.cos(a))
            arm.append(([(sg * d, y), tip], False))
            for f in (0.45, 0.72):
                bx, by = sg * d + (tip[0] - sg * d) * f, y + (tip[1] - y) * f
                l2 = R * L * 0.32 * (1.1 - f)
                arm.append(([(bx, by), (bx + sg * l2 * math.sin(math.radians(120)) * 0.5, by + l2)], False))
                arm.append(([(bx, by), (bx + sg * l2, by + l2 * 0.1)], False))
    # Plättchen auf dem Arm (kleines Sechseck) und Facette zur Spitze
    hx = R * 0.07
    arm.append((zu([P(hx, TAU * k / 6 + TAU / 12, (0, R * 0.47)) for k in range(6)]), False))
    arm.append(([(0, R * 0.62), (0, R * 0.86)], False))
    if art == 2:                                     # Sternplättchen: Raute am Ende
        arm.append((zu([(0, R * 0.80), (R * 0.05, R * 0.88), (0, R * 0.96), (-R * 0.05, R * 0.88)]), False))
    out = rund_linien(6, arm)
    for f in (0.16, 0.11, 0.06):
        out.append((zu([P(R * f, TAU * k / 6) for k in range(6)]), False))
    for k in range(6):                               # Facetten in der Mitte
        out.append(([P(R * 0.06, TAU * k / 6), P(R * 0.16, TAU * k / 6)], False))
    return out


def zierstern(R: float, zacken: int = 8) -> List[Linie]:
    """Facettierter Stern mit Doppelkontur und Lichtstrahlen (Gravur)."""
    out: List[Linie] = []
    for f in (1.0, 0.86):
        pts = [P(R * f * (1 if k % 2 == 0 else 0.42) * (1 if (k // 2) % 2 == 0 else 0.78), math.pi * k / zacken)
               for k in range(2 * zacken)]
        out.append((zu(pts), False))
    for k in range(2 * zacken):
        rr = R * 0.86 * (1 if k % 2 == 0 else 0.42) * (1 if (k // 2) % 2 == 0 else 0.78)
        out.append(([P(R * 0.08, math.pi * k / zacken), P(rr, math.pi * k / zacken)], False))
    out.append((zu(kreis(0, 0, R * 0.08, 16)), False))
    return out


def nadelzweig(pfad: Sequence[Point], nadel: float, abstand: float, winkel: float = 38.0) -> List[Linie]:
    """Tannenzweig: Mittelast plus Nadeln zu beiden Seiten, zur Spitze hin kürzer (Gravur)."""
    out: List[Linie] = [(list(pfad), False)]
    L = K.path_len(pfad)
    pts = K.resample(list(pfad), abstand)
    a = math.radians(winkel)
    n = len(pts)
    for i in range(1, n - 1):
        s = i / (n - 1)
        q, nx = pts[i], pts[i + 1]
        dx, dy = nx[0] - q[0], nx[1] - q[1]
        dl = math.hypot(dx, dy) or 1
        dx, dy = dx / dl, dy / dl
        ln = nadel * (1.0 - 0.55 * s) * (0.9 + 0.2 * ((i * 7) % 3) / 2)
        for sg in (1, -1):
            vx = dx * math.cos(a) - sg * dy * math.sin(a)
            vy = dy * math.cos(a) + sg * dx * math.sin(a)
            out.append(([q, (q[0] + vx * ln, q[1] + vy * ln)], False))
    if L > 0:
        e = pts[-1]
        out.append(([e, (e[0] + (pts[-1][0] - pts[-2][0]) * 0.8, e[1] + (pts[-1][1] - pts[-2][1]) * 0.8)], False))
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
