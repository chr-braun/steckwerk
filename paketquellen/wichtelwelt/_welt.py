"""
_welt.py – gemeinsame Werkzeuge der Wichtelwelt: gemusterte Lagen, Sockel, Holzmaserung, Bretter mit Fugen.
Nutzt die Bibliothek „Verzierungen“.

Koordinaten in mm, y nach oben.
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from steckwerk import Part, inset_polygon, oriented, point_in_polygon
from pakete import bibliothek

Z = bibliothek("verzierungen")
K = Z.K
E = Z.E
Point = Tuple[float, float]
Poly = List[Point]

MUSTER = [("streifen", "Streifen"), ("sterne", "Sterne"), ("punkte", "Punkte"), ("herzen", "Herzen"),
          ("zacken", "Zickzack"), ("glatt", "glatt")]


def tabbreite(cfg, verfuegbar: float, anteil: float = 0.24) -> float:
    """Zapfenbreite: mindestens T + Kerf (+ Luft), höchstens tab_factor · T."""
    return max(cfg.min_tab_width + 0.6, min(cfg.tab_factor * cfg.T, verfuegbar * anteil))


def innen(poly: Sequence[Point], d: float) -> Poly:
    """Kontur um d nach innen (leer, wenn nichts übrig bleibt)."""
    return inset_polygon(oriented(list(poly), True), d)


def ganz_innen(poly: Sequence[Point], maske: Sequence[Point]) -> bool:
    return all(point_in_polygon(p, maske) for p in poly)


def teil(cfg, name: str, fig, notes: List[str], unten_flach: bool = False, solid: Sequence[Poly] = (),
         muster: Sequence[Poly] = (), maske: Sequence[Point] = ()) -> Part:
    """Figur → laserfestes Teil. muster: Löcher, die nur innerhalb von maske ausgeschnitten werden
    (so bleibt der Rand der Lage immer stehen)."""
    if not muster:
        return Z.figur_teil(cfg, name, fig, notes, solid=solid, unten_flach=unten_flach)
    x0, y0, x1, y1 = fig.bbox()
    px = Z.px_fuer(max(x1 - x0, y1 - y0))
    lw = E.Leinwand((x0 - 3, y0 - 3, x1 + 3, y1 + 3), px)
    mat = lw.figur(fig)
    loecher = E._and(lw.flaechen(list(muster)), lw.flaechen([list(maske)]))
    mat = E._andnot(mat, loecher)
    if solid:
        mat = mat.union(lw.flaechen(list(solid)))
    return E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes, unten_flach)


# --------------------------------------------------------------------------------------------------
# Muster für Mützen, Markisen, Kissen
# --------------------------------------------------------------------------------------------------

def muster_loecher(art: str, maske: Sequence[Point], g: float, w: float, achse: float = math.pi / 2,
                   ursprung: Point = (0.0, 0.0)) -> List[Poly]:
    """Löcher eines Musters (Größe g, Mindeststeg w) in der Fläche maske.
    achse: Richtung, quer zu der die Streifen/Zacken laufen (Bogenmaß)."""
    xs = [p[0] for p in maske]
    ys = [p[1] for p in maske]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    out: List[Poly] = []
    ca, sa = math.cos(achse), math.sin(achse)
    ox, oy = ursprung
    R = math.hypot(x1 - x0, y1 - y0) + g

    def welt(u: float, v: float) -> Point:            # u entlang der Achse, v quer dazu
        return (ox + u * ca - v * sa, oy + u * sa + v * ca)

    if art == "streifen":
        b = max(g * 0.42, w * 1.4)                     # Streifenbreite (Loch)
        schritt = b + max(g * 0.5, w * 1.6)
        u = -R + schritt / 2
        while u < R:
            out.append([welt(u, -R), welt(u + b, -R), welt(u + b, R), welt(u, R)])
            u += schritt
        return out
    if art == "zacken":
        b = max(g * 0.3, w * 1.3)
        schritt = b + max(g * 0.62, w * 1.8)
        amp, per = g * 0.32, g * 0.9
        u = -R
        while u < R:
            unten, oben = [], []
            v = -R
            k = 0
            while v <= R + per:
                du = amp if k % 2 else -amp
                unten.append(welt(u + du, v))
                oben.append(welt(u + du + b, v))
                v += per / 2
                k += 1
            out.append(unten + list(reversed(oben)))
            u += schritt
        return out
    # Streumotive auf versetztem Raster, nur ganz innerhalb der Maske
    abst = g * 1.3 + w
    zeile = 0
    v = -R
    while v < R:
        u = -R + (abst / 2 if zeile % 2 else 0.0)
        while u < R:
            cx, cy = welt(u, v)
            if x0 - g < cx < x1 + g and y0 - g < cy < y1 + g:
                if art == "sterne":
                    p = K.star(cx, cy, g * 0.5, g * 0.22, 5, math.pi / 2 + achse - math.pi / 2)
                elif art == "punkte":
                    p = K.circle(cx, cy, g * 0.36, 24)
                elif art == "herzen":
                    p = Z.herz(cx, cy, g * 0.9, achse - math.pi / 2)
                else:
                    p = []
                if p and ganz_innen(p, maske):
                    out.append(p)
            u += abst
        v += abst * 0.87
        zeile += 1
    return out


# --------------------------------------------------------------------------------------------------
# Holz: Maserung, Bretter, Astlöcher
# --------------------------------------------------------------------------------------------------

def maserung(x0: float, y0: float, x1: float, y1: float, seed: int = 1, dichte: float = 1.0,
             quer: bool = False, ast: bool = True) -> List[Tuple[Poly, bool]]:
    """Gravurlinien für Holzmaserung im Rechteck (Fasern längs der längeren Seite, quer=True dreht)."""
    r = K.rng(seed, "maserung", round(x0, 1), round(y0, 1))
    lang_x = (x1 - x0 >= y1 - y0) != quer
    L = (x1 - x0) if lang_x else (y1 - y0)
    B = (y1 - y0) if lang_x else (x1 - x0)

    def P(u, v):
        return (x0 + u, y0 + v) if lang_x else (x0 + v, y0 + u)

    linien: List[Tuple[Poly, bool]] = []
    n = max(1, int(B / 3.2 * dichte))
    ast_pos = None
    if ast and L > 22 and B > 7:
        ast_pos = (L * (0.3 + 0.4 * r.random()), B * (0.35 + 0.3 * r.random()))
    for i in range(n):
        v0 = B * (i + 0.5) / n + K.jitter(r, B / n * 0.2)
        a0, a1 = L * r.random() * 0.25, L * (0.75 + r.random() * 0.25)
        ph = r.random() * 6.3
        pts = []
        steps = max(6, int((a1 - a0) / 2.5))
        for k in range(steps + 1):
            u = a0 + (a1 - a0) * k / steps
            v = v0 + math.sin(u / max(L, 1) * 6.3 * 1.3 + ph) * B * 0.04
            if ast_pos:                                   # Fasern weichen dem Ast aus
                du, dv = u - ast_pos[0], v - ast_pos[1]
                d = math.hypot(du, dv * 2.2)
                if d < B * 0.45:
                    v += (1 if dv >= 0 else -1) * (B * 0.45 - d) * 0.45
            pts.append(P(u, v))
        linien.append((pts, False))
    if ast_pos:
        cx, cy = P(*ast_pos)
        rx, ry = (B * 0.12, B * 0.06) if lang_x else (B * 0.06, B * 0.12)
        linien.append((K.ellipse(cx, cy, max(rx, 0.9), max(ry, 0.6), 0, 20), True))
        linien.append((K.ellipse(cx, cy, max(rx * 0.45, 0.4), max(ry * 0.45, 0.3), 0, 14), True))
    return linien


def bretter(x0: float, y0: float, x1: float, y1: float, n: int, senkrecht: bool = True, seed: int = 1,
            nagel: bool = True) -> List[Tuple[Poly, bool]]:
    """Bretterfugen, je Brett eine zarte Maserung und zwei Nagelköpfe an den Enden."""
    linien: List[Tuple[Poly, bool]] = []
    for i in range(n):
        if senkrecht:
            a, b = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
            if i:
                linien.append(([(a, y0), (a, y1)], False))
            linien += maserung(a + 0.9, y0 + 1.5, b - 0.9, y1 - 1.5, seed + i, 0.6, ast=(i % 3 == 1))
            if nagel and b - a > 4:
                for y in (y0 + 2.6, y1 - 2.6):
                    linien.append((K.circle((a + b) / 2, y, 0.45, 8), True))
        else:
            a, b = y0 + (y1 - y0) * i / n, y0 + (y1 - y0) * (i + 1) / n
            if i:
                linien.append(([(x0, a), (x1, a)], False))
            linien += maserung(x0 + 1.5, a + 0.9, x1 - 1.5, b - 0.9, seed + i, 0.6, ast=(i % 3 == 1))
            if nagel and b - a > 4:
                for x in (x0 + 2.6, x1 - 2.6):
                    linien.append((K.circle(x, (a + b) / 2, 0.45, 8), True))
    return linien


# --------------------------------------------------------------------------------------------------
# Sockel und Schrift
# --------------------------------------------------------------------------------------------------

def schneehuegel(rx: float, ry: float, seed: int = 1) -> Poly:
    """Draufsicht eines Schneehügels: Oval mit sanft welligem Rand."""
    r = K.rng(seed, "huegel")
    ph = r.random() * 6.3
    pts = []
    n = 120
    for i in range(n):
        a = 2 * math.pi * i / n
        f = 1 + 0.035 * math.sin(5 * a + ph) + 0.02 * math.sin(9 * a + 2 * ph)
        pts.append((rx * f * math.cos(a), ry * f * math.sin(a)))
    return pts


def sockel(cfg, name: str, rx: float, ry: float, slots: Sequence[Tuple[str, float, float, float, float]],
           text: str = "", seed: int = 1, deko: str = "schnee") -> Part:
    """Liegende Standplatte (Draufsicht): Schneehügel mit Schlitzen [(fid, x, y, länge, pos)] und Gravur vorne."""
    T = cfg.T
    part = Part(name, oriented(schneehuegel(rx, ry, seed), True))
    for fid, x, y, L, pos in slots:
        Z.schlitz(part, fid, x, y, L, T, pos)
    lin: List[Tuple[Poly, bool]] = []
    sperr = [Z.schlitz_polster(x, y, L, T, 1.6) for _, x, y, L, _ in slots]
    if text.strip():
        y_vorne = min(y - T / 2 for _, x, y, L, _ in slots) if slots else 0.0
        h = (y_vorne + ry * 0.92) * 0.62
        try:
            st, _ = Z.text_in_box(text, 0.0, (y_vorne - ry * 0.92) / 2 + 0.6, rx * 1.25, h, 7.5, 2.5, 0.08)
        except ValueError:
            raise ValueError(f"Der Name „{text.replace('|', ' ')}“ passt nicht auf den Sockel – kürzer fassen")
        lin += [(s, False) for s in st]
    elif deko == "schnee":
        r = K.rng(seed, "flocken")
        for k in range(7):
            a = 2 * math.pi * k / 7 + r.random()
            x, y = math.cos(a) * rx * 0.68, math.sin(a) * ry * 0.6
            if any(abs(x - sx) < L / 2 + 4 and abs(y - sy) < T / 2 + 4 for _, sx, sy, L, _ in slots):
                continue
            s = 1.6 + r.random() * 0.8
            for j in range(3):
                b = math.pi * j / 3
                lin.append(([(x - s * math.cos(b), y - s * math.sin(b)), (x + s * math.cos(b), y + s * math.sin(b))],
                            False))
    lin.append((schneehuegel(rx - 2.2, ry - 2.2, seed), True))
    Z.gravur(part, lin, rand=0.9, sperr=sperr)
    return part


def text_gravur(part, text: str, cx: float, cy: float, max_w: float, max_h: float, max_cap: float = 8.0,
                was: str = "Der Text", style: str = "normal"):
    if not text.strip():
        return
    try:
        st, _ = Z.text_in_box(text, cx, cy, max_w, max_h, max_cap, 2.5, 0.08, style)
    except ValueError:
        raise ValueError(f"{was} „{text.replace('|', ' ')}“ passt nicht drauf – kürzer fassen oder größer machen")
    Z.gravur(part, [(s, False) for s in st], rand=0.8)


def lade_uebersetzung(*dicts):
    out = {}
    for d in dicts:
        out.update(d)
    return {"en": out}
