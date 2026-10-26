"""
wichtel.py – Wichtel-Figur auf ovalem Sockel: umgeknickte Zipfelmütze mit Krempe, Knollennase, langer Bart,
ausgestellter Mantel, Fäustlinge und Stiefel.

Die Kontur ist von Hand gezeichnet (Stützpunkte, glatte Catmull-Rom-Kurve, Einheit: Höhe = 1). Krempe, Nase,
Bart mit Strähnen, Mantelsaum, Stiefel und Sterne auf der Mütze werden graviert.
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from steckwerk import Assembly, Config, Part, circle, clean, profile_edge
from models._stand import bottom_tab, stand_base, tab_feature_at

DEFAULTS = dict(height=70.0)
Point = Tuple[float, float]

# Rechte Seite von unten nach oben (Stiefel → Mantel → Fäustling → Krempe), dann die Mütze, die nach rechts
# umknickt, über den Scheitel zurück und die linke Seite hinunter. Stiefelspitzen bei y = 0 schließen an die
# gerade Standfläche an.
KONTUR: List[Point] = [
    (0.300, 0.000), (0.352, 0.026), (0.350, 0.070), (0.300, 0.098), (0.264, 0.114),   # rechter Stiefel
    (0.272, 0.136), (0.286, 0.160), (0.270, 0.215),                             # Mantelsaum, Seite
    (0.300, 0.262), (0.306, 0.318), (0.272, 0.352),                             # rechter Fäustling
    (0.236, 0.405), (0.232, 0.468),                                             # Schulter unter dem Bart
    (0.262, 0.500), (0.258, 0.556),                                             # Krempe rechts
    (0.200, 0.630), (0.188, 0.715), (0.226, 0.790), (0.306, 0.818),             # Mütze, Unterseite des Zipfels
    (0.372, 0.842), (0.384, 0.892),                                             # Zipfel
    (0.322, 0.945), (0.200, 0.988), (0.060, 0.985),                             # Rücken des umgeknickten Zipfels
    (-0.070, 0.920), (-0.168, 0.780), (-0.222, 0.640),                          # linke Mützenseite
    (-0.258, 0.556), (-0.262, 0.500),                                           # Krempe links
    (-0.232, 0.468), (-0.236, 0.405),
    (-0.272, 0.352), (-0.306, 0.318), (-0.300, 0.262),                          # linker Fäustling
    (-0.270, 0.215), (-0.286, 0.160), (-0.272, 0.136),
    (-0.264, 0.114), (-0.300, 0.098), (-0.350, 0.070), (-0.352, 0.026), (-0.300, 0.000),   # linker Stiefel
]

# Feine Einbuchtungen (Knöchel, Fäustlinge): bei sehr kleinen Figuren (Maßstab < 0,4) zu eng für den Kerf.
FEIN = {(0.264, 0.114), (0.272, 0.136), (0.300, 0.262), (0.306, 0.318), (0.272, 0.352)}
FEIN |= {(-x, y) for x, y in FEIN}


def _spline(pts: Sequence[Point], n: int = 8, closed: bool = False) -> List[Point]:
    """Catmull-Rom-Kurve durch die Stützpunkte."""
    P = list(pts)
    m = len(P)
    out: List[Point] = []
    for i in range(m if closed else m - 1):
        p0 = P[(i - 1) % m] if closed or i > 0 else P[0]
        p1, p2 = P[i], P[(i + 1) % m]
        p3 = P[(i + 2) % m] if closed or i + 2 < m else P[-1]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (p2[j] - p0[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (3 * p1[j] - p0[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(P[-1])
    return out


def _stern(cx: float, cy: float, r: float) -> List[Point]:
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else 0.42 * r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts + [pts[0]]


def build(cfg: Config, name: str = "wichtel", height: Optional[float] = None,
          width: Optional[float] = None, text: str = "", schrift: str = "normal",
          schreibweise: str = "gross") -> Assembly:
    """text: Gravur vorne auf dem Sockel (z. B. ein Name)."""
    T = cfg.T
    H = cfg.s(height or DEFAULTS["height"])
    sx = 1.0
    breite = 2 * max(abs(x) for x, _ in KONTUR)
    if width:
        sx = min(1.0, cfg.s(width) / (breite * H))
    tol = cfg.arc_tolerance

    def P(pts: Sequence[Point]) -> List[Point]:                 # Einheit → mm
        return [(x * H * sx, y * H) for x, y in pts]

    fein = H >= 28
    kontur = [p for p in KONTUR if fein or p not in FEIN]
    rand = _spline(kontur[1:-1], n=10)                          # ohne die Ecken auf der Standfläche
    top = max(y for _, y in rand)
    rand = [(x, y / top) for x, y in rand]                      # Mütze genau auf Höhe H
    fw = KONTUR[0][0] * H * sx                                  # halbe Standfläche (Stiefelspitzen)
    tw = max(cfg.min_tab_width, min(cfg.tab_factor * T, 0.5 * fw))
    pts = profile_edge((-fw, 0.0), (fw, 0.0), bottom_tab(2 * fw, tw, T)) + [(fw, 0.0)]
    pts += P(rand)
    fig = Part(f"{name}_figur", clean(pts),
               features=[tab_feature_at("sockel", -tw / 2, 0.0, tw, T)])

    def gravur(pts: Sequence[Point], closed: bool = False):
        fig.add_engrave(P(pts), closed=closed)

    # Krempe: Oberkante durchgehend, Unterkante links und rechts der Nase
    gravur(_spline([(-0.232, 0.552), (-0.12, 0.584), (0.0, 0.594), (0.12, 0.584), (0.232, 0.552)]))
    gravur(_spline([(-0.236, 0.505), (-0.16, 0.522), (-0.082, 0.530)]))
    gravur(_spline([(0.082, 0.530), (0.16, 0.522), (0.236, 0.505)]))
    # Knollennase und Schnurrbart
    fig.add_engrave(circle(0.0, 0.470 * H, 0.068 * H * min(1.0, sx * 1.1), tol), closed=True)
    for s in (-1, 1):
        gravur(_spline([(0.0, 0.405), (s * 0.06, 0.412), (s * 0.120, 0.398), (s * 0.150, 0.420)]))
    # Bart: Rand von der Krempe bis zur Spitze und Strähnen
    bart_r = [(0.205, 0.492), (0.214, 0.420), (0.196, 0.330), (0.148, 0.230), (0.075, 0.150), (0.0, 0.118)]
    gravur(_spline(bart_r + [(-x, y) for x, y in reversed(bart_r[:-1])]))
    for x0, y0, x1, y1 in ((-0.10, 0.375, -0.075, 0.250), (-0.04, 0.380, -0.025, 0.200),
                           (0.04, 0.380, 0.025, 0.200), (0.10, 0.375, 0.075, 0.250),
                           (-0.155, 0.360, -0.120, 0.290), (0.155, 0.360, 0.120, 0.290)):
        gravur(_spline([(x0, y0), ((x0 + x1) / 2 + 0.012 * (1 if x0 < 0 else -1), (y0 + y1) / 2), (x1, y1)]))
    # Mantelsaum, Ärmel und Fäustlinge
    for s in (-1, 1):
        gravur(_spline([(s * 0.250, 0.150), (s * 0.150, 0.138), (s * 0.075, 0.150)]))
        if fein:
            gravur(_spline([(s * 0.228, 0.395), (s * 0.248, 0.330), (s * 0.262, 0.290)]))   # Ärmelkante
            gravur(_spline([(s * 0.262, 0.290), (s * 0.282, 0.300), (s * 0.294, 0.322)]))   # Daumen
    # Stiefel: Schaftkante und Trennung
    for s in (-1, 1):
        gravur(_spline([(s * 0.034, 0.100), (s * 0.140, 0.104), (s * 0.226, 0.104)]))
    fig.add_engrave([(0.0, 0.6), (0.0, 0.100 * H)])
    # Mütze: Falte am Knick und ein paar Sterne
    gravur(_spline([(0.150, 0.800), (0.205, 0.858), (0.290, 0.880), (0.360, 0.870)]))
    if H >= 45:
        for cx, cy, r in ((-0.080, 0.700, 0.034), (0.080, 0.665, 0.030), (-0.020, 0.830, 0.030),
                          (0.100, 0.910, 0.026), (-0.150, 0.640, 0.024)):
            gravur(_stern(cx, cy, r))

    asm = Assembly(name, params={"height": H, **({"text": text} if text else {})})
    asm.parts.append(fig)
    stand_base(asm, fig, "sockel", tw, cfg, rx=fw + 4.0 * sx, ry=max(0.16 * H, 8.0), name=f"{name}_sockel",
               text=text, schrift=schrift, schreibweise=schreibweise)
    asm.notes.append(f"{name}: Figur in den Sockel stecken. Bemalen: Mütze rot, Bart weiß, Mantel grün oder grau, "
                     "Nase rosa.")
    return asm
