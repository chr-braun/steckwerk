"""
Kugellabyrinth – Geschicklichkeitsspiel aus mehreren Lagen: Grundplatte, Boden mit Fallen-Löchern
und Ziel, darüber die Wandlagen mit dem Irrgarten. Jede Nummer ergibt ein anderes Labyrinth
(perfektes Labyrinth: genau ein Weg von Start zu Ziel). Reine Vektorgeometrie, rechnet sofort.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

import random
from collections import deque

from steckwerk import Assembly, Part
from pakete import integer, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_spiele_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


S = _sub("_spiel")
KUGELN = [("6", "Stahlkugel 6 mm"), ("8", "Stahlkugel 8 mm"), ("10", "Kugel 10 mm"), ("12", "Murmel 12 mm"),
          ("16", "Glasmurmel 16 mm")]

INFO = dict(
    label="Kugellabyrinth",
    group="Spiele",
    desc="Irrgarten zum Kippen: Die Kugel muss vom Start ins Ziel, in den Sackgassen warten Fallen-Löcher. "
         "Jede Nummer ergibt ein neues Labyrinth, die Wandhöhe passt sich der Kugel an.",
    params=[
        num("breite", "Breite", 200, 120, 280),
        num("hoehe", "Höhe", 200, 120, 280),
        sel("kugel", "Kugel", KUGELN, "8"),
        integer("nummer", "Labyrinth Nr.", 1, 1, 9999, help="jede Nummer ergibt einen anderen Irrgarten"),
        integer("fallen", "Fallen", 5, 0, 20, help="Löcher in Sackgassen, in denen die Kugel hängen bleibt"),
        txt("beschriftung", "Beschriftung", "", section="Beschriftung", help="oben auf dem Rahmen"),
    ],
)

UEBERSETZUNG = {"en": dict(S.UEBERSETZUNG_GEMEINSAM, **{
    "Kugellabyrinth": "Marble maze",
    "Irrgarten zum Kippen: Die Kugel muss vom Start ins Ziel, in den Sackgassen warten Fallen-Löcher. "
    "Jede Nummer ergibt ein neues Labyrinth, die Wandhöhe passt sich der Kugel an.":
        "Tilting maze: the ball has to get from start to finish, trap holes wait in the dead ends. "
        "Every number gives a new maze; the wall height adapts to the ball.",
    "Breite": "Width", "Höhe": "Height", "Kugel": "Ball", "Stahlkugel 6 mm": "Steel ball 6 mm",
    "Stahlkugel 8 mm": "Steel ball 8 mm", "Kugel 10 mm": "Ball 10 mm", "Murmel 12 mm": "Marble 12 mm",
    "Glasmurmel 16 mm": "Glass marble 16 mm", "Labyrinth Nr.": "Maze no.",
    "jede Nummer ergibt einen anderen Irrgarten": "every number gives a different maze", "Fallen": "Traps",
    "Löcher in Sackgassen, in denen die Kugel hängen bleibt": "holes in dead ends where the ball gets stuck",
    "oben auf dem Rahmen": "on the top of the frame",
    "Alle Lagen deckungsgleich aufeinanderleimen: Grundplatte, Boden (mit den Löchern), dann die Wandlagen, "
    "die gravierte Lage obenauf. Mit Zwingen oder Büchern pressen.":
        "Glue all layers exactly on top of each other: base plate, floor (with the holes), then the wall "
        "layers, the engraved one on top. Press with clamps or books.",
    "Die Kugel auf das Feld bei START legen und das Brett kippen. Wer ins ZIEL rollt, ohne in eine Falle "
    "zu fallen, hat gewonnen.":
        "Put the ball on the field at START and tilt the board. Whoever rolls into the goal (ZIEL) without "
        "falling into a trap wins.",
})}


def irrgarten(nx: int, ny: int, seed: int):
    """Perfektes Labyrinth (Rücksprung-Suche). Liefert die Menge offener Durchgänge {((i,j),(i2,j2))}."""
    rng = random.Random(seed * 7919 + nx * 31 + ny)
    offen = set()
    besucht = [[False] * ny for _ in range(nx)]
    stapel = [(0, ny - 1)]
    besucht[0][ny - 1] = True
    while stapel:
        i, j = stapel[-1]
        nb = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if 0 <= i + di < nx and 0 <= j + dj < ny and not besucht[i + di][j + dj]]
        if not nb:
            stapel.pop()
            continue
        n = rng.choice(nb)
        besucht[n[0]][n[1]] = True
        offen.add(frozenset(((i, j), n)))
        stapel.append(n)
    return offen


def nachbarn(c, offen, nx, ny):
    i, j = c
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (i + di, j + dj)
        if 0 <= n[0] < nx and 0 <= n[1] < ny and frozenset((c, n)) in offen:
            yield n


def loesung(offen, nx, ny, start, ziel):
    vor = {start: None}
    q = deque([start])
    while q:
        c = q.popleft()
        if c == ziel:
            break
        for n in nachbarn(c, offen, nx, ny):
            if n not in vor:
                vor[n] = c
                q.append(n)
    weg = []
    c = ziel
    while c is not None:
        weg.append(c)
        c = vor[c]
    return weg[::-1]


def wege_umriss(offen, nx: int, ny: int, xs, ys):
    """Umriss der Wegfläche: Gitter mit ungleichen Spalten (Weg/Wand) – exakte Randverfolgung."""
    gx, gy = 2 * nx - 1, 2 * ny - 1

    def voll(a, b):
        if not (0 <= a < gx and 0 <= b < gy):
            return False
        if a % 2 == 0 and b % 2 == 0:
            return True
        if a % 2 == 1 and b % 2 == 1:
            return False
        if a % 2 == 1:
            return frozenset(((a // 2, b // 2), (a // 2 + 1, b // 2))) in offen
        return frozenset(((a // 2, b // 2), (a // 2, b // 2 + 1))) in offen

    nach = {}
    for a in range(gx):
        for b in range(gy):
            if not voll(a, b):
                continue
            if not voll(a, b - 1):
                nach[(a, b)] = (a + 1, b)
            if not voll(a + 1, b):
                nach[(a + 1, b)] = (a + 1, b + 1)
            if not voll(a, b + 1):
                nach[(a + 1, b + 1)] = (a, b + 1)
            if not voll(a - 1, b):
                nach[(a, b + 1)] = (a, b)
    start = min(nach)
    pts = [start]
    p = nach[start]
    while p != start:
        pts.append(p)
        p = nach[p]
    if len(pts) != len(nach):
        raise ValueError("Kugellabyrinth: Wegfläche nicht zusammenhängend")
    # gerade Zwischenpunkte entfernen
    out = []
    n = len(pts)
    for k in range(n):
        a, b, c = pts[k - 1], pts[k], pts[(k + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            out.append((xs[b[0]], ys[b[1]]))
    return out


def build(cfg, name: str = "labyrinth", breite: float = 200.0, hoehe: float = 200.0, kugel: str = "8",
          nummer: int = 1, fallen: int = 5, beschriftung: str = ""):
    from models import _deko as dk
    dk.check_choice("Kugel", kugel, KUGELN)
    B, Hh = cfg.s(breite), cfg.s(hoehe)
    if not (120 <= B <= 280 and 120 <= Hh <= 280):
        raise ValueError("Kugellabyrinth: Breite und Höhe müssen zwischen 120 und 280 mm liegen")
    S.platte_passt(cfg, B, Hh, "Kugellabyrinth")
    nummer, fallen = int(nummer), int(fallen)
    if not 0 <= fallen <= 20:
        raise ValueError("Kugellabyrinth: 0 bis 20 Fallen")
    T = cfg.T
    k = float(kugel)
    w = max(3.0, cfg.min_web + 1.5, 0.35 * k)             # Wandstärke
    pw = k + max(2.0, 0.2 * k)                            # Wegbreite
    f = 13.0                                              # Rahmen (Platz für START/ZIEL)
    nx = int((B - 2 * f + w) // (pw + w))
    ny = int((Hh - 2 * f + w) // (pw + w))
    if nx < 4 or ny < 4:
        raise ValueError("Kugellabyrinth: zu klein für diese Kugel – größer wählen oder kleinere Kugel")
    W = 2 * f + nx * pw + (nx - 1) * w
    H = 2 * f + ny * pw + (ny - 1) * w
    xs, ys = [f], [f]
    for a in range(2 * nx - 1):
        xs.append(xs[-1] + (pw if a % 2 == 0 else w))
    for b in range(2 * ny - 1):
        ys.append(ys[-1] + (pw if b % 2 == 0 else w))
    zx = lambda i: f + i * (pw + w) + pw / 2              # noqa: E731
    zy = lambda j: f + j * (pw + w) + pw / 2              # noqa: E731

    offen = irrgarten(nx, ny, nummer)
    start, ziel = (0, ny - 1), (nx - 1, 0)
    weg = loesung(offen, nx, ny, start, ziel)
    sack = [c for c in ((i, j) for i in range(nx) for j in range(ny))
            if c not in (start, ziel) and len(list(nachbarn(c, offen, nx, ny))) == 1]
    rng = random.Random(nummer * 104729 + 17)
    rng.shuffle(sack)
    sack = sorted(sack[:fallen])

    outline = dk.rounded_rect(0.0, 0.0, W, H, 6.0)
    lagen = max(1, math.ceil(0.6 * k / T - 1e-9))
    umriss = wege_umriss(offen, nx, ny, xs, ys)

    grund = Part(f"{name}_grund", list(outline))
    boden = Part(f"{name}_boden", list(outline))
    dl = k + 1.0
    for c in [ziel] + sack:
        boden.add_hole(dk.circle(zx(c[0]), zy(c[1]), dl / 2, 0.04, ccw=False))
    waende = []
    for n in range(1, lagen + 1):
        p = Part(f"{name}_wand_{n}", list(outline))
        p.add_hole(umriss)
        waende.append(p)
    oben = waende[-1]
    cv = dk.Canvas(oben, margin=1.0, hole_margin=0.8)
    cap = 5.0
    # START über dem Startfeld, ZIEL unter dem Zielfeld, kleine Pfeile
    x_s, x_z = zx(start[0]), zx(ziel[0])
    yt, yb = H - f / 2, f / 2
    S.text(cv, "START", x_s + 20, yt - 0.5, 30, cap + 1, cap)
    cv.draw([(x_s - 2.5, H - f / 2 + 1.2), (x_s, H - f / 2 - 2.0), (x_s + 2.5, H - f / 2 + 1.2)])
    S.text(cv, "ZIEL", x_z - 17, yb + 0.5, 24, cap + 1, cap)
    cv.draw([(x_z - 2.5, f / 2 + 1.6), (x_z, f / 2 - 1.6), (x_z + 2.5, f / 2 + 1.6)])
    if beschriftung.strip():
        x0 = x_s + 40
        S.text(cv, beschriftung, (x0 + W - 8) / 2, yt + 0.4, W - 8 - x0, cap + 2, cap + 1)
    nr = f"Nr. {nummer}"
    S.text(cv, nr, 8 + 12, yb - 0.4, 24, 3.6, 3.6)

    asm = Assembly(name, params=dict(breite=W, hoehe=H, zellen=(nx, ny), wandlagen=lagen, wegbreite=pw,
                                     wand=w, loesung=len(weg), fallen=len(sack)))
    asm.parts += [grund, boden] + waende
    asm.notes += [
        "Alle Lagen deckungsgleich aufeinanderleimen: Grundplatte, Boden (mit den Löchern), dann die Wandlagen, "
        "die gravierte Lage obenauf. Mit Zwingen oder Büchern pressen.",
        "Die Kugel auf das Feld bei START legen und das Brett kippen. Wer ins ZIEL rollt, ohne in eine Falle "
        "zu fallen, hat gewonnen.",
    ]
    return asm
