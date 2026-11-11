"""
_spiel.py – gemeinsame Helfer für das Paket „Spiele“.

  brett_teile    Spielbrett aus zwei Lagen: oben mit Mulden (Löchern), unten geschlossen
  stein          runder Spielstein mit graviertem Motiv
  figur_umriss   ausgeschnittene Spielfigur (X, O, Stern, Herz, Tanne, Glocke)
  motiv_linien   Motiv als Gravurlinien (Ring, Stern, Herz, Tanne, Schneeflocke, schraffiert …)
  zierrand       Zierlinie entlang einer geschlossenen Kontur
  text           Text kollisionsfrei in eine Box gravieren

Alles ist reine Vektorgeometrie (kein Raster) und rechnet deshalb auch auf alten Rechnern sofort.
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from steckwerk import Part, Point, circle, oriented, rect
from pakete import bibliothek

from models import _deko as dk

Z = bibliothek("verzierungen")
Poly = List[Point]

RAENDER = [("keiner", "keiner"), ("linie", "Linie"), ("doppelt", "Doppellinie"), ("punkte", "Punkte"),
           ("wellen", "Wellen"), ("zickzack", "Zickzack"), ("sterne", "Sterne"), ("herzen", "Herzen"),
           ("girlande", "Girlande")]

MOTIVE = [("glatt", "glatt"), ("ring", "Ring"), ("doppelring", "Doppelring"), ("punkt", "Punkt in der Mitte"),
          ("stern", "Stern"), ("herz", "Herz"), ("tanne", "Tanne"), ("flocke", "Schneeflocke"),
          ("schraffiert", "schraffiert (wirkt dunkel)")]

FIGUREN = [("x", "X"), ("o", "O"), ("stern", "Stern"), ("herz", "Herz"), ("tanne", "Tanne"), ("glocke", "Glocke")]

UEBERSETZUNG_GEMEINSAM = {
    "keiner": "none", "Linie": "Line", "Doppellinie": "Double line", "Punkte": "Dots", "Wellen": "Waves",
    "Zickzack": "Zigzag", "Sterne": "Stars", "Herzen": "Hearts", "Girlande": "Garland",
    "glatt": "plain", "Ring": "Ring", "Doppelring": "Double ring", "Punkt in der Mitte": "Dot in the centre",
    "Stern": "Star", "Herz": "Heart", "Tanne": "Fir tree", "Schneeflocke": "Snowflake",
    "schraffiert (wirkt dunkel)": "hatched (looks dark)", "Glocke": "Bell",
    "Zierrand": "Decorative border", "Spiele": "Games", "Beschriftung": "Lettering",
    "Gestaltung": "Design",
}


# ---------------------------------------------------------------------------------------------
# Formen
# ---------------------------------------------------------------------------------------------

def _bbox(pts: Sequence[Point]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def einpassen(pts: Sequence[Point], cx: float, cy: float, r: float) -> Poly:
    """Form so skalieren und verschieben, dass sie mittig in einen Kreis vom Radius r passt."""
    x0, y0, x1, y1 = _bbox(pts)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    rmax = max(math.hypot(x - mx, y - my) for x, y in pts)
    s = r / rmax
    return [(cx + (x - mx) * s, cy + (y - my) * s) for x, y in pts]


def _tanne_einheit() -> Poly:
    """Tanne mit drei Etagen und Stamm (Einheitsgröße, Höhe ≈ 2)."""
    rechts = [(0.0, 1.0), (0.42, 0.42), (0.22, 0.44), (0.62, -0.12), (0.32, -0.1), (0.78, -0.72),
              (0.13, -0.72), (0.13, -1.0)]
    links = [(-x, y) for x, y in reversed(rechts[1:])]
    return rechts + links


def _glocke_einheit() -> Poly:
    """Glocke mit Klöppel, Rand, geschwungener Flanke, Kuppel und Öse (Einheitsgröße)."""
    rechts: Poly = [(0.0, -1.0), (0.17, -0.98), (0.21, -0.84), (0.9, -0.84), (0.86, -0.72)]
    for k in range(1, 9):                                    # geschwungene Flanke
        t = k / 8
        rechts.append((0.78 - 0.38 * t + 0.06 * math.sin(math.pi * t), -0.6 + 1.1 * t))
    for k in range(1, 6):                                    # Kuppel bis kurz vor die Mitte
        a = math.pi / 2 * k / 6
        rechts.append((0.4 * math.cos(a), 0.5 + 0.32 * math.sin(a)))
    rechts += [(0.1, 0.83), (0.1, 0.98)]                     # Öse
    links = [(-x, y) for x, y in reversed(rechts[1:])]
    return rechts + links


def _kreuz_einheit(w: float = 0.36) -> Poly:
    h = w / 2
    plus = [(h, h), (1.0, h), (1.0, -h), (h, -h), (h, -1.0), (-h, -1.0), (-h, -h), (-1.0, -h), (-1.0, h), (-h, h),
            (-h, 1.0), (h, 1.0)]
    c = math.cos(math.pi / 4)
    return [(c * (x - y), c * (x + y)) for x, y in plus]


def figur_umriss(art: str, cx: float, cy: float, r: float) -> Tuple[Poly, List[Poly]]:
    """Umriss (und Innenlöcher) einer Spielfigur, die in einen Kreis vom Radius r passt."""
    if art == "x":
        return einpassen(_kreuz_einheit(), cx, cy, r), []
    if art == "o":
        return circle(cx, cy, r, 0.04), [circle(cx, cy, r * 0.5, 0.04, ccw=False)]
    if art == "stern":
        return einpassen(Z.K.star(0, 0, 1.0, 0.5, 5), cx, cy, r), []
    if art == "herz":
        return einpassen(dk.heart(0, 0, 1.05, 1.0, 64), cx, cy, r), []
    if art == "tanne":
        return einpassen(_tanne_einheit(), cx, cy, r), []
    if art == "glocke":
        return einpassen(_glocke_einheit(), cx, cy, r), []
    raise ValueError(f"Spielfigur {art!r} unbekannt")


def figur_gravur(art: str, cx: float, cy: float, r: float) -> List[Tuple[Poly, bool]]:
    """Feine Zierlinien auf einer ausgeschnittenen Spielfigur."""
    if art == "stern":
        return [(einpassen(Z.K.star(0, 0, 1.0, 0.5, 5), cx, cy, r * 0.55), True)]
    if art == "herz":
        return [(einpassen(dk.heart(0, 0, 1.05, 1.0, 64), cx, cy - 0.04 * r, r * 0.52), True)]
    if art == "o":
        return [(circle(cx, cy, r * 0.75, 0.04), True)]
    if art == "tanne":                                       # zwei Girlanden
        out = []
        for y0, w in ((0.15, 0.32), (-0.42, 0.48)):
            pts = [(cx + (-w + 2 * w * k / 12) * r, cy + (y0 - 0.08 * math.sin(math.pi * k / 12)) * r)
                   for k in range(13)]
            out.append((pts, False))
        return out
    if art == "glocke":
        return [([(cx - 0.5 * r, cy - 0.45 * r), (cx + 0.5 * r, cy - 0.45 * r)], False),
                ([(cx - 0.36 * r, cy - 0.25 * r), (cx + 0.36 * r, cy - 0.25 * r)], False)]
    return []


def motiv_linien(motiv: str, cx: float, cy: float, r: float, spacing: float = 0.7) -> List[Tuple[Poly, bool]]:
    """Gravurmotiv in einem Kreis vom Radius r (für Spielsteine und Felder)."""
    if motiv == "glatt":
        return []
    if motiv == "ring":
        return [(circle(cx, cy, r, 0.03), True)]
    if motiv == "doppelring":
        return [(circle(cx, cy, r, 0.03), True), (circle(cx, cy, r * 0.72, 0.03), True)]
    if motiv == "punkt":
        out = []
        rr = r * 0.42
        while rr > 0.4:
            out.append((circle(cx, cy, rr, 0.03), True))
            rr -= 0.45
        return out
    if motiv == "stern":
        return [(einpassen(Z.K.star(0, 0, 1.0, 0.45, 5), cx, cy, r), True)]
    if motiv == "herz":
        return [(einpassen(dk.heart(0, 0, 1.05, 1.0, 64), cx, cy, r * 0.95), True)]
    if motiv == "tanne":
        return [(einpassen(_tanne_einheit(), cx, cy, r), True)]
    if motiv == "flocke":
        out = []
        for k in range(6):
            a = math.pi / 2 + k * math.pi / 3
            ux, uy = math.cos(a), math.sin(a)
            out.append(([(cx, cy), (cx + ux * r, cy + uy * r)], False))
            for t, L in ((0.5, 0.32), (0.75, 0.22)):
                bx, by = cx + ux * r * t, cy + uy * r * t
                for s in (-1, 1):
                    b = a + s * math.pi / 3.2
                    out.append(([(bx, by), (bx + math.cos(b) * r * L, by + math.sin(b) * r * L)], False))
        return out
    if motiv == "schraffiert":
        out = [(circle(cx, cy, r, 0.03), True)]
        n = int(2 * r / spacing)
        for i in range(1, n):
            y = -r + i * 2 * r / n
            hw = math.sqrt(max(0.0, r * r - y * y)) - 0.15
            if hw > 0.3:
                # Zeilen abwechselnd in Gegenrichtung → kurze Leerwege beim Gravieren
                seg = [(cx - hw, cy + y), (cx + hw, cy + y)]
                out.append((seg if i % 2 else seg[::-1], False))
        return out
    raise ValueError(f"Motiv {motiv!r} unbekannt")


# ---------------------------------------------------------------------------------------------
# Teile
# ---------------------------------------------------------------------------------------------

def stein(name: str, d: float, motiv: str, tol: float = 0.04) -> Part:
    """Runder Spielstein Ø d mit graviertem Motiv."""
    p = Part(name, circle(0.0, 0.0, d / 2, tol))
    rm = d / 2 - max(1.2, 0.12 * d)
    for pts, closed in motiv_linien(motiv, 0.0, 0.0, rm):
        p.add_engrave(pts, closed)
    return p


def figur(name: str, art: str, d: float) -> Part:
    """Ausgeschnittene Spielfigur, passt in einen Kreis Ø d."""
    out, loecher = figur_umriss(art, 0.0, 0.0, d / 2)
    p = Part(name, oriented(out, True))
    for h in loecher:
        p.add_hole(h)
    for pts, closed in figur_gravur(art, 0.0, 0.0, d / 2):
        p.add_engrave(pts, closed)
    return p


def brett_teile(name: str, outline: Poly, mulden: Sequence[Tuple[float, float, float]],
                extra_loecher: Sequence[Poly] = ()) -> Tuple[Part, Part]:
    """Zwei Lagen: Deckplatte mit Mulden (x, y, Ø) und geschlossene Bodenplatte."""
    oben = Part(f"{name}_brett", oriented(outline, True))
    for x, y, d in mulden:
        oben.add_hole(circle(x, y, d / 2, 0.04, ccw=False))
    for h in extra_loecher:
        oben.add_hole(h)
    unten = Part(f"{name}_boden", oriented(list(outline), True))
    return oben, unten


def zierrand(cv, kontur: Poly, stil: str, groesse: float, seed: int = 1) -> None:
    """Zierlinie entlang einer geschlossenen Kontur (CCW); das Band liegt innen."""
    if stil in ("keiner", "", None):
        return
    k = list(oriented(kontur, True))
    pfad = k + [k[0]]
    dk.styled_line(cv, pfad, stil, groesse, side=1, seed=seed, gravity=False)


def text(cv, inhalt: str, cx: float, cy: float, w: float, h: float, max_cap: float, min_cap: float = 2.5,
         stil: str = "normal") -> Optional[Tuple[float, float, float, float]]:
    """Text graviert in die Box; liefert die belegte Box (oder None bei leerem Text)."""
    inhalt = (inhalt or "").strip()
    if not inhalt:
        return None
    striche, cap = Z.text_in_box(inhalt, cx, cy, w, h, max_cap, min_cap, gap_faktor=0.08, style=stil,
                                 case="normal")
    for s in striche:
        cv.draw(s, False, min_len=0.05)
    if not striche:
        return None
    return _bbox([p for s in striche for p in s])


def platte_passt(cfg, w: float, h: float, was: str) -> None:
    bw = cfg.sheet_width - 2 * cfg.sheet_margin
    bh = cfg.sheet_height - 2 * cfg.sheet_margin
    if not ((w <= bw and h <= bh) or (w <= bh and h <= bw)):
        raise ValueError(f"{was}: {w:.0f} × {h:.0f} mm passt nicht auf die Platte "
                         f"({bw:.0f} × {bh:.0f} mm) – kleiner wählen")
