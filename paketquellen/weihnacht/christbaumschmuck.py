"""
Edler Christbaumschmuck – detailreiche Anhänger in Scherenschnitt-Qualität.

Jedes Motiv ist eigens gezeichnet: ausgeschnittene Fenster, Federn, Schuppen und Spitzenkanten tragen die
Form, feine Gravuren (Gesichter, Federkiele, Faltenwurf, Nadeln, Facetten, Perlenränder) geben die Tiefe.
Stege und Fenster werden für den Laser geprüft; die Gravur bleibt immer mit Abstand zu den Schnitten.
Auf Wunsch steht ein Name in echter Schreibschrift auf dem Anhänger.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Optional, Sequence, Tuple

from steckwerk import Assembly, oriented, signed_area
from pakete import bibliothek, integer, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_weihnacht_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


E = bibliothek("verzierungen").E
F = bibliothek("verzierungen").F
K = E.K
Figur = K.Figur
NA = _sub("namensanhaenger")
SS = _sub("_schreibschrift")
SZ = _sub("_szenen")
Poly = List[Tuple[float, float]]
TAU = 2 * math.pi

MOTIVE = [("engel", "Engel mit Federflügeln"), ("stern", "Facettenstern"), ("kugel", "Christbaumkugel mit Winterszene"),
          ("glocke", "Glocke mit Schleife"), ("zapfen", "Tannenzapfen"), ("tannenbaum", "Geschmückter Tannenbaum"),
          ("schneemann", "Schneemann mit Zylinder"), ("herz", "Herz mit Lebensbaum"), ("mond", "Schlafender Mond"),
          ("kerze", "Kerze im Tannengrün"), ("geschenk", "Geschenk mit Schleife"), ("stiefel", "Nikolausstiefel")]
AUSWAHL = [("alle", "alle (Set)")] + MOTIVE
KUGELSZENEN = [k for k in SZ.SZENEN if k[0] != "ohne"]
# Motive mit Platz für einen Namen
MIT_NAMEN = {"stern", "kugel", "glocke", "herz", "schneemann", "geschenk", "stiefel", "engel"}

INFO = dict(
    label="Edler Christbaumschmuck",
    group="Weihnachten",
    desc="Detailreiche Christbaumanhänger: Engel mit Federflügeln, Facettenstern, Kugel mit Winterszene, Glocke, "
         "Tannenzapfen, Tannenbaum, Schneemann, Herz mit Lebensbaum, schlafender Mond, Kerze, Geschenk und "
         "Nikolausstiefel – Scherenschnitt mit feiner Gravur, auf Wunsch mit Namen in Schreibschrift.",
    params=[
        sel("motiv", "Motiv", AUSWAHL, "alle"),
        num("groesse", "Höhe", 90, 60, 180, help="ohne Öse"),
        txt("text", "Name", "", maxlen=20, help="optional, in Schreibschrift graviert (nicht bei Zapfen, Tannenbaum, "
                                                  "Mond und Kerze)", section="Schrift und Beschriftung"),
        sel("schrift", "Schreibschrift", SS.SCHRIFTEN, "schwungvoll", section="Schrift und Beschriftung"),
        sel("szene", "Szene in der Kugel", KUGELSZENEN, "winterdorf", when={"motiv": ["kugel", "alle"]}),
        integer("anzahl", "Anzahl je Motiv", 1, 1, 8),
    ],
)

UEBERSETZUNG = {"en": {
    "Edler Christbaumschmuck": "Fine tree ornaments", "Weihnachten": "Christmas",
    "Detailreiche Christbaumanhänger: Engel mit Federflügeln, Facettenstern, Kugel mit Winterszene, Glocke, "
    "Tannenzapfen, Tannenbaum, Schneemann, Herz mit Lebensbaum, schlafender Mond, Kerze, Geschenk und "
    "Nikolausstiefel – Scherenschnitt mit feiner Gravur, auf Wunsch mit Namen in Schreibschrift.":
        "Richly detailed tree ornaments: angel with feathered wings, faceted star, bauble with winter scene, bell, "
        "pine cone, Christmas tree, snowman, heart with tree of life, sleeping moon, candle, present and Santa "
        "boot – paper-cut style with fine engraving, optionally with a name in script lettering.",
    "Motiv": "Motif", "alle (Set)": "all (set)", "Engel mit Federflügeln": "Angel with feathered wings",
    "Facettenstern": "Faceted star", "Christbaumkugel mit Winterszene": "Bauble with winter scene",
    "Glocke mit Schleife": "Bell with bow", "Tannenzapfen": "Pine cone", "Geschmückter Tannenbaum": "Decorated tree",
    "Schneemann mit Zylinder": "Snowman with top hat", "Herz mit Lebensbaum": "Heart with tree of life",
    "Schlafender Mond": "Sleeping moon", "Kerze im Tannengrün": "Candle with fir sprigs",
    "Geschenk mit Schleife": "Present with bow", "Nikolausstiefel": "Santa boot",
    "Höhe": "Height", "ohne Öse": "without loop", "Name": "Name",
    "optional, in Schreibschrift graviert (nicht bei Zapfen, Tannenbaum, Mond und Kerze)":
        "optional, engraved in script (not on pine cone, tree and moon)",
    "Schrift und Beschriftung": "Font and lettering", "Schreibschrift": "Script font",
    "elegant (Kalligrafie)": "elegant (calligraphy)", "schwungvoll": "flowing", "rund und kräftig": "round and bold",
    "Szene in der Kugel": "Scene inside the bauble", "Anzahl je Motiv": "Count per motif",
    "Winterdorf mit Kirche": "Winter village with church", "Winterwald mit Hirsch": "Winter forest with stag",
    "Schneemann mit Laterne": "Snowman with lantern", "Schlittenfahrt": "Sleigh ride",
    "Adventskranz mit vier Kerzen": "Advent wreath with four candles",
    "Christbaum mit Geschenken": "Christmas tree with presents", "Plätzchen backen": "Baking cookies",
    "Geschenke packen": "Wrapping presents",
    "Aufhängen: Band oder Kordel durch die Öse ziehen.": "To hang: thread a ribbon or cord through the loop.",
}}


# --------------------------------------------------------------------------------------------------
# Werkzeug
# --------------------------------------------------------------------------------------------------

def _sym(right: Sequence[Tuple[float, float]]) -> Poly:
    """Rechte Hälfte (oben → unten, Endpunkte auf x = 0) spiegeln → geschlossener Umriss."""
    return list(right) + [(-x, y) for x, y in reversed(right[1:-1])]


def _spl(pts, n=8, closed=True) -> Poly:
    return K.spline(list(pts), closed=closed, n=n)


def _mx(poly: Sequence[Tuple[float, float]]) -> Poly:
    return [(-x, y) for x, y in poly]


def _rot(poly, a, c=(0.0, 0.0)) -> Poly:
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in poly]


def _blatt(p0, p1, w: float, n: int = 12) -> Poly:
    """Spitzes Blatt / Tropfen von p0 nach p1, größte Breite w."""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1.0
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    nx, ny = -uy, ux
    pts = []
    for side in (1, -1):
        rng = range(n + 1) if side == 1 else range(n - 1, 0, -1)
        for i in rng:
            t = i / n
            b = w / 2 * math.sin(math.pi * t) ** 0.9 * (1.0 - 0.25 * t)
            pts.append((p0[0] + ux * L * t + nx * b * side, p0[1] + uy * L * t + ny * b * side))
    return pts


def _tropfen(p0, p1, w: float, n: int = 14) -> Poly:
    """Tropfen: rundes Ende bei p0, Spitze bei p1."""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1.0
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    nx, ny = -uy, ux
    pts = []
    r = w / 2
    for i in range(n + 1):                                  # Halbkreis am runden Ende
        a = math.pi / 2 + math.pi * i / n
        pts.append((p0[0] + (ux * math.cos(a) + nx * math.sin(a)) * r + ux * r,
                    p0[1] + (uy * math.cos(a) + ny * math.sin(a)) * r + uy * r))
    pts.append(p1)
    return pts


def _herzform(cx: float, cy: float, g: float) -> Poly:
    """Herz der Breite g, Mitte (cx, cy)."""
    pts = []
    for i in range(48):
        t = TAU * i / 48
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * g / 33.0, cy + (y + 2.5) * g / 33.0))
    return pts


def _bogenkette(p0, p1, n: int, tiefe: float) -> Poly:
    """Girlande: n Bögen zwischen p0 und p1, Durchhang tiefe (nach unten)."""
    out = []
    for k in range(n):
        a = (p0[0] + (p1[0] - p0[0]) * k / n, p0[1] + (p1[1] - p0[1]) * k / n)
        b = (p0[0] + (p1[0] - p0[0]) * (k + 1) / n, p0[1] + (p1[1] - p0[1]) * (k + 1) / n)
        c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 2 * tiefe)
        seg = K.bez(a, c, b, 10)
        out += seg if not out else seg[1:]
    return out


def _versatz(poly: Poly, d: float) -> Poly:
    from steckwerk import offset_polygon
    return oriented(offset_polygon(oriented(poly, True), d), True)


class Motiv:
    """Sammelt Material (Figur), Material nach den Durchbrüchen, Gravuren, Öse und Namensfeld."""

    def __init__(self, cfg, S: float, seed: int):
        self.S = S
        self.cfg = cfg
        self.web, self.kerf = cfg.min_web, cfg.kerf
        self.wm = self.web + self.kerf + 0.45              # dünnster Steg, der beim Öffnen sicher bleibt
        self.wb = self.web + self.kerf + 0.55              # Brücken, Fäden
        self.seed = seed
        self.f = Figur()
        self.nach = Figur()
        self.g: List[Tuple[Poly, bool]] = []
        self.oese: Optional[Tuple[float, float, float]] = None
        self.namensfeld: Optional[Tuple[float, float, float, float]] = None   # cx, cy, w, h
        self.feld_rahmen = True
        self.loch_extra: List[Poly] = []
        self.loch_extra2: List[Poly] = []        # Fenster, die auch nach dem Zusatzmaterial frei bleiben
        self.band_gravur: List[Tuple[Poly, bool]] = []   # Zier, die einem Namen Platz macht
        self.nach_g: List[Tuple[Poly, bool]] = []
        self.feld_material: List[Poly] = []      # Schild für den Namen (nur mit Namen)

    def gr(self, pts, closed: bool = False) -> None:
        if len(pts) >= 2:
            self.g.append((list(pts), closed))

    def oese_an(self, x: float, y_top: float, tief: float = 0.5) -> None:
        ro = max(3.4, 0.042 * self.S)
        self.oese = (x, y_top + ro - tief, ro)
        self.nach.add(K.circle(x, y_top + ro - tief, ro, 48))

    def faden(self, a, b) -> None:
        self.nach.add(K.stroke([a, b], self.wb, self.wb, "flach"))

    def perlen(self, path: Poly, r: float, abstand: float, closed: bool = False) -> None:
        """Gravierte Perlenreihe entlang eines Pfades."""
        for q in K.resample(path + ([path[0]] if closed else []), abstand)[:-1 if closed else None]:
            c = K.circle(q[0], q[1], r, 12)
            self.gr(c, True)


# --------------------------------------------------------------------------------------------------
# Motive (Höhe S, unten y = 0, Mitte x = 0)
# --------------------------------------------------------------------------------------------------

def W_abrund(poly, r):
    return bibliothek("verzierungen").W.abrunden(poly, r, 6)


def _kreis_band(cy: float, R: float, y0: float, y1: float) -> Poly:
    """Waagrechtes Band zwischen y0 und y1, seitlich auf den Kreis (Mitte y = cy, Radius R) zugeschnitten."""
    out_r, out_l = [], []
    n = 16
    for i in range(n + 1):
        y = y0 + (y1 - y0) * i / n
        hx = math.sqrt(max(R * R - (y - cy) ** 2, 0))
        out_r.append((hx, y))
        out_l.append((-hx, y))
    return out_r + list(reversed(out_l))


def _facetten(m: Motiv, c, tip, v, abstand: float) -> None:
    """Schattenseite einer Sternzacke: Linien parallel zum Grat (Mitte c → Spitze tip), bis zur Kante v → tip."""
    L = math.hypot(v[0] - c[0], v[1] - c[1])
    d = abs((tip[0] - c[0]) * (v[1] - c[1]) - (tip[1] - c[1]) * (v[0] - c[0])) / max(1e-9, math.hypot(tip[0] - c[0], tip[1] - c[1]))
    n = max(2, int(d / abstand))
    for k in range(1, n):
        t = k / n
        a = (c[0] + t * (v[0] - c[0]), c[1] + t * (v[1] - c[1]))
        b = (a[0] + (1 - t) * (tip[0] - c[0]), a[1] + (1 - t) * (tip[1] - c[1]))
        m.gr([a, b])


def _bogenfenster(x: float, y: float, w: float, h: float) -> Poly:
    """Rundbogenfenster: unten (x ± w/2, y), Scheitel bei y + h."""
    r = w / 2
    return [(x - r, y), (x + r, y)] + K.arc(x, y + h - r, r, 0.0, math.pi, 14)


def _stechpalme(m: Motiv, f: Figur, cx: float, cy: float, L: float, ang: float) -> None:
    """Stechpalmenblatt als Material mit gravierter Mittel- und Seitenrippe."""
    blatt = NA._stechpalme(cx, cy, L, ang)
    f.add(blatt)
    c, s = math.cos(ang), math.sin(ang)
    m.gr([(cx + 0.08 * L * c, cy + 0.08 * L * s), (cx + 0.86 * L * c, cy + 0.86 * L * s)])
    for t in (0.3, 0.5, 0.7):
        for sd in (1, -1):
            a = (cx + t * L * c, cy + t * L * s)
            b = (a[0] + (0.10 * L) * c - sd * 0.10 * L * s, a[1] + 0.10 * L * s + sd * 0.10 * L * c)
            m.gr([a, b])


def _beeren(m: Motiv, f: Figur, pts, r: float) -> None:
    for x, y in pts:
        f.add(K.circle(x, y, r, 18))
        m.gr(K.circle(x - 0.3 * r, y + 0.3 * r, 0.3 * r, 10), True)


def _nadelzweig(m: Motiv, f: Figur, p0, p1, nadel: float, n: int, dicht: float = 1.0) -> None:
    """Tannenzweig: Material-Stiel mit Nadeln (Material) links und rechts, Nadelstriche graviert."""
    w = m.wm
    f.add(K.stroke([p0, p1], w * 1.1, w * 0.9, "rund"))
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1.0
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    for k in range(n):
        t = 0.12 + 0.85 * k / max(1, n - 1)
        b = (p0[0] + ux * L * t, p0[1] + uy * L * t)
        ln = nadel * (1.0 - 0.45 * t)
        for sd in (1, -1):
            a = math.atan2(uy, ux) + sd * math.radians(48)
            e = (b[0] + math.cos(a) * ln, b[1] + math.sin(a) * ln)
            f.add(K.stroke([b, e], w, w * 0.8, "rund"))
            m.gr([(b[0] + (e[0] - b[0]) * 0.2, b[1] + (e[1] - b[1]) * 0.2), (b[0] + (e[0] - b[0]) * 0.85, b[1] + (e[1] - b[1]) * 0.85)])


def _schleife(m: Motiv, f: Figur, cx: float, cy: float, b: float) -> None:
    """Große Schleife (Breite b) mit Fenstern in den Schlaufen, Bändern und gravierten Falten."""
    for sd in (1, -1):
        loop = _spl([(cx, cy), (cx + sd * 0.20 * b, cy + 0.20 * b), (cx + sd * 0.45 * b, cy + 0.26 * b),
                     (cx + sd * 0.50 * b, cy + 0.10 * b), (cx + sd * 0.36 * b, cy - 0.04 * b),
                     (cx + sd * 0.12 * b, cy - 0.03 * b)], 8)
        f.add(loop)
        m.loch_extra.append(_spl([(cx + sd * 0.14 * b, cy + 0.03 * b), (cx + sd * 0.26 * b, cy + 0.14 * b),
                                  (cx + sd * 0.40 * b, cy + 0.16 * b), (cx + sd * 0.40 * b, cy + 0.06 * b),
                                  (cx + sd * 0.27 * b, cy + 0.02 * b)], 6))
        m.gr(_spl([(cx + sd * 0.10 * b, cy + 0.01 * b), (cx + sd * 0.26 * b, cy + 0.18 * b),
                   (cx + sd * 0.44 * b, cy + 0.20 * b), (cx + sd * 0.45 * b, cy + 0.07 * b),
                   (cx + sd * 0.30 * b, cy - 0.01 * b)], 6), True)
        for t in (0.25, 0.35):
            m.gr(K.bez((cx + sd * 0.08 * b, cy), (cx + sd * t * b, cy + 0.10 * b), (cx + sd * (t + 0.15) * b, cy + 0.20 * b), 8))
        tail = [(cx + sd * 0.05 * b, cy - 0.02 * b), (cx + sd * 0.16 * b, cy - 0.16 * b), (cx + sd * 0.24 * b, cy - 0.30 * b)]
        f.add(K.stroke(tail, 0.12 * b, 0.10 * b, "flach"))
        e = tail[-1]
        f.add([(e[0] - 0.06 * b, e[1] + 0.02 * b), (e[0] + 0.06 * b, e[1] + 0.02 * b), (e[0] + sd * 0.07 * b, e[1] - 0.06 * b),
               (e[0], e[1] - 0.02 * b), (e[0] - sd * 0.06 * b, e[1] - 0.07 * b)])
        m.gr(K.spline(tail, n=6))
    f.add(K.ellipse(cx, cy, 0.09 * b, 0.075 * b, 0.0, 24))
    m.gr(K.ellipse(cx, cy, 0.055 * b, 0.045 * b, 0.0, 16), True)


def _engel(m: Motiv) -> None:
    u = m.S
    f = m.f
    hem_y = 0.03 * u
    rechts = [(0.0, 0.62 * u), (0.055 * u, 0.615 * u), (0.085 * u, 0.56 * u), (0.12 * u, 0.40 * u),
              (0.19 * u, 0.20 * u), (0.255 * u, 0.06 * u)]
    kleid = _spl(rechts, 8, closed=False)
    n_b = 7
    x_h = 0.255 * u
    saum = []
    for k in range(n_b):                                   # Bogenkante rechts → links
        xa = x_h - 2 * x_h * k / n_b
        xb = x_h - 2 * x_h * (k + 1) / n_b
        r = (xa - xb) / 2
        saum += K.arc((xa + xb) / 2, 0.06 * u, r, 0.0, -math.pi, 12)[(1 if k else 0):]
    links = [(-x, y) for x, y in reversed(kleid)]
    f.add(kleid + saum + links)
    hy, hr = 0.705 * u, 0.082 * u
    f.add(K.circle(0, hy, hr, 60))
    for side in (-1, 1):                                    # Locken
        for dx, dy, rr in ((0.075, -0.035, 0.03), (0.066, -0.07, 0.027), (0.05, 0.05, 0.028)):
            f.add(K.circle(side * dx * u, hy + dy * u, rr * u, 20))
    for side in (-1, 1):
        P = (side * 0.07 * u, 0.56 * u)
        dek = _spl([(side * 0.04 * u, 0.50 * u), (side * 0.10 * u, 0.70 * u), (side * 0.26 * u, 0.80 * u),
                    (side * 0.41 * u, 0.835 * u), (side * 0.37 * u, 0.70 * u), (side * 0.20 * u, 0.55 * u)], 8)
        f.add(dek)
        m.gr(_spl([(side * 0.10 * u, 0.66 * u), (side * 0.25 * u, 0.765 * u), (side * 0.385 * u, 0.80 * u),
                   (side * 0.35 * u, 0.71 * u), (side * 0.20 * u, 0.585 * u)], 8), True)
        federn = [(16, 0.40, 0.09), (1, 0.40, 0.09), (-14, 0.37, 0.085), (-30, 0.33, 0.08), (-46, 0.28, 0.075),
                  (-62, 0.22, 0.07)]
        for a_deg, L, w in federn:
            a = math.radians(a_deg)
            d = (math.cos(a) * side, math.sin(a))
            q0 = (P[0] + d[0] * 0.05 * u, P[1] + d[1] * 0.05 * u)
            q1 = (P[0] + d[0] * L * u, P[1] + d[1] * L * u)
            f.add(_blatt(q0, q1, w * u, 14))
            a0 = (P[0] + d[0] * (0.42 * L + 0.04) * u, P[1] + d[1] * (0.42 * L + 0.04) * u)
            a1 = (P[0] + d[0] * (0.88 * L) * u, P[1] + d[1] * (0.88 * L) * u)
            if L >= 0.30:
                m.loch_extra.append(_tropfen(a0, a1, 0.032 * u))
                m.gr(_versatz(_tropfen(a0, a1, 0.032 * u), 0.9), True)
            else:
                m.gr(_versatz(_tropfen(a0, a1, 0.03 * u), 0.0), True)
            m.gr([q0, (a0[0] - d[0] * 0.012 * u, a0[1] - d[1] * 0.012 * u)])           # Kiel
        for row, (r0, cnt) in enumerate(((0.12, 3), (0.17, 4), (0.22, 5), (0.27, 5))):   # Deckfedern
            for k in range(cnt):
                t = (k + 0.5) / cnt
                a = math.radians(64 - 70 * t)
                cx = P[0] + side * math.cos(a) * r0 * u
                cy = P[1] + 0.035 * u + math.sin(a) * r0 * u * 0.85 + 0.07 * u * (1 - t) * 0.6
                m.gr(K.arc(cx, cy, 0.02 * u, math.pi * 1.05, math.pi * 1.95, 8))
    hy2 = hy + hr + 0.05 * u
    ring = K.ellipse(0, hy2, 0.095 * u, 0.03 * u, 0.0, 60)
    m.nach.add(K.stroke(ring + [ring[0]], m.wm + 0.15, m.wm + 0.15, "flach"))
    for x in (-0.04 * u, 0.04 * u):
        m.nach.add(K.stroke([(x, hy + hr * 0.8), (x * 1.05, hy2 - 0.02 * u)], m.wb, m.wb, "rund"))
    m.oese_an(0.0, hy2 + 0.03 * u + (m.wm + 0.15) / 2, 0.8)
    sy = 0.43 * u
    m.loch_extra.append(K.star(0, sy, 0.058 * u, 0.025 * u, 5))
    m.gr(K.star(0, sy, 0.085 * u, 0.04 * u, 5), True)
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5 + math.pi / 10
        m.gr([(math.cos(a) * 0.075 * u, sy + math.sin(a) * 0.075 * u), (math.cos(a) * 0.105 * u, sy + math.sin(a) * 0.105 * u)])
    for side in (-1, 1):
        m.gr(K.bez((side * 0.075 * u, 0.585 * u), (side * 0.13 * u, 0.50 * u), (side * 0.075 * u, 0.44 * u), 14))
        m.gr(K.bez((side * 0.04 * u, 0.57 * u), (side * 0.06 * u, 0.50 * u), (side * 0.035 * u, 0.465 * u), 10))
        m.gr(K.bez((side * 0.075 * u, 0.44 * u), (side * 0.06 * u, 0.42 * u), (side * 0.035 * u, 0.465 * u), 8))
        m.gr(K.arc(side * 0.06 * u, 0.42 * u, 0.018 * u, 0, TAU, 12), True)
        m.gr(K.arc(side * 0.03 * u, hy + 0.005 * u, 0.016 * u, math.pi * 1.15, math.pi * 1.85, 8))
        for k in range(3):
            a = math.pi * (1.3 + 0.2 * k)
            x0, y0 = side * 0.03 * u + math.cos(a) * 0.016 * u, hy + 0.005 * u + math.sin(a) * 0.016 * u
            m.gr([(x0, y0), (x0 + math.cos(a) * 0.008 * u, y0 + math.sin(a) * 0.008 * u)])
        m.gr(K.circle(side * 0.045 * u, hy - 0.025 * u, 0.012 * u, 12), True)
    m.gr(K.arc(0, hy - 0.025 * u, 0.018 * u, math.pi * 1.25, math.pi * 1.75, 8))
    for k in range(7):
        a = math.pi * (0.15 + 0.7 * k / 6)
        c = (math.cos(a) * hr * 0.92, hy + math.sin(a) * hr * 0.92)
        m.gr(NA.FG.spiral(c, (c[0] + 0.012 * u, c[1]), 1.0, 0.8, cw=(k % 2 == 0), n=20))
    m.gr(K.bez((-0.09 * u, 0.535 * u), (0, 0.52 * u), (0.09 * u, 0.535 * u), 10))
    m.gr(K.bez((-0.09 * u, 0.515 * u), (0, 0.50 * u), (0.09 * u, 0.515 * u), 10))
    for x in (-0.12, -0.05, 0.05, 0.12):
        m.gr(K.bez((x * 0.45 * u, 0.33 * u), (x * 0.9 * u, 0.22 * u), (x * 1.6 * u, 0.10 * u), 14))
    for k in range(1, n_b - 1):                             # Lochspitze über dem Saum
        xa = x_h - 2 * x_h * k / n_b
        xb = x_h - 2 * x_h * (k + 1) / n_b
        xc = (xa + xb) / 2
        m.loch_extra.append(K.circle(xc, 0.06 * u, 0.012 * u + 0.4, 16))
        m.gr(K.arc(xc, 0.06 * u, 0.024 * u + 0.4, 0, TAU, 14), True)
    m.gr(K.bez((-0.235 * u, 0.105 * u), (0, 0.09 * u), (0.235 * u, 0.105 * u), 20))
    m.perlen(K.bez((-0.21 * u, 0.125 * u), (0, 0.11 * u), (0.21 * u, 0.125 * u), 30), 0.006 * u, 0.025 * u)
    m.namensfeld = (0, 0.25 * u, 0.20 * u, 0.065 * u)
    for x, y in ((-0.10, 0.20), (0.11, 0.24), (-0.06, 0.33), (0.07, 0.32), (0.0, 0.17), (-0.14, 0.15), (0.15, 0.16)):
        m.gr(K.star(x * u, y * u, 0.012 * u, 0.005 * u, 5), True)


def _stern(m: Motiv) -> None:
    S = m.S
    R = S / (1 + math.cos(math.pi / 5))
    cy = S - R
    ri = 0.46 * R
    stern = W_abrund(K.star(0, cy, R, ri, 5), 0.035 * R)
    m.f.add(stern)
    a_sp = [math.pi / 2 + i * TAU / 5 for i in range(5)]
    for a in a_sp:
        ux, uy = math.cos(a), math.sin(a)
        p0 = (ux * 0.40 * R, cy + uy * 0.40 * R)
        p1 = (ux * 0.80 * R, cy + uy * 0.80 * R)
        m.loch_extra.append(_tropfen(p0, p1, 0.10 * R))
        m.gr(_versatz(_tropfen(p0, p1, 0.10 * R), 0.9), True)
        m.gr(K.circle(ux * 0.87 * R, cy + uy * 0.87 * R, 0.018 * R, 10), True)
        tip = (ux * R, cy + uy * R)
        m.gr([(0, cy), tip])
        for sd in (-1, 1):                                  # Grat zum Tal
            v = (math.cos(a + sd * math.pi / 5) * ri, cy + math.sin(a + sd * math.pi / 5) * ri)
            m.gr([(0, cy), v])
        v = (math.cos(a - math.pi / 5) * ri, cy + math.sin(a - math.pi / 5) * ri)
        _facetten(m, (0.0, cy), tip, v, 0.75)
    m.gr(_versatz(stern, -0.04 * R), True)
    m.mitte_stern = (0.0, cy, 0.15 * R)
    m.namensfeld = (0.0, cy, 0.62 * R, 0.24 * R)
    m.feld_rahmen = False
    m.oese_an(0.0, S, 1.5)


def _stern_mitte(m: Motiv, mit_name: bool) -> None:
    x, cy, r = m.mitte_stern
    if mit_name:
        cx, cy2, w, h = m.namensfeld
        m.nach_g = [(W_abrund(K.rect(cx - w / 2 - 1.8, cy2 - h / 2 - 1.8, w + 3.6, h + 3.6), min(h / 2 + 1.8, 5.0)), True)]
        return
    m.loch_extra.append(K.star(x, cy, r, 0.45 * r, 5))
    m.gr(K.circle(x, cy, r * 1.45, 40), True)
    for i in range(10):
        a = math.pi / 2 + i * TAU / 10
        m.gr(K.circle(x + math.cos(a) * r * 1.8, cy + math.sin(a) * r * 1.8, 0.11 * r, 10), True)


def _kugel(m: Motiv) -> None:
    S = m.S
    D = 0.90 * S
    R = D / 2
    cy = R
    f = m.f
    f.add(K.circle(0, cy, R, 180))
    cw, ch = 0.25 * S, 0.075 * S
    f.add(K.rect(-cw / 2, D - 0.02 * S, cw, ch + 0.02 * S))
    f.add(W_abrund(K.rect(-cw / 2 - 0.012 * S, D - 0.004 * S, cw + 0.024 * S, 0.022 * S), 0.008 * S))
    for i in range(1, 7):
        x = -cw / 2 + cw * i / 7
        m.gr([(x, D + 0.026 * S), (x, D + ch - 0.012 * S)])
    m.gr([(-cw / 2 - 0.006 * S, D + 0.008 * S), (cw / 2 + 0.006 * S, D + 0.008 * S)])
    m.oese_an(0.0, D + ch, 1.0)
    rb = max(2 * m.web + m.kerf + 1.4, 0.045 * S)
    Ri = R - rb
    m.loch_extra.append(K.circle(0, cy, Ri, 160))
    m.gr(K.circle(0, cy, R - rb / 2 - 0.9, 160), True)
    m.perlen(K.circle(0, cy, R - rb / 2 + 0.5, 160), max(0.3, 0.12 * rb), max(2.2, 1.1 * rb), closed=True)
    bh = 0.12 * S
    by = cy + 0.02 * S
    m.nach.add(_kreis_band(cy, R - rb * 0.5, by - bh / 2, by + bh / 2))
    for dy in (bh / 2 - 0.9, bh / 2 - 1.8):
        for s in (1, -1):
            y = by + s * dy
            hx = math.sqrt(max(Ri * Ri - (y - cy) ** 2, 0))
            m.gr([(-hx, y), (hx, y)])
    m.namensfeld = (0.0, by, 1.45 * Ri, bh - 4.6)
    m.feld_rahmen = False
    # Girlande im Band (fällt weg, wenn ein Name dort steht)
    hx = math.sqrt(max(Ri * Ri - (by - cy) ** 2, 0)) - 2.0
    gl = _bogenkette((-hx, by + 0.018 * S), (hx, by + 0.018 * S), 5, 0.012 * S)
    m.band_gravur = [(gl, False)]
    for k in range(6):
        x = -hx + 2 * hx * k / 5
        m.band_gravur.append((K.star(x, by + 0.018 * S, 0.016 * S, 0.007 * S, 5), True))
    for k in range(5):
        x = -hx + 2 * hx * (k + 0.5) / 5
        m.band_gravur.append((K.circle(x, by - 0.016 * S, 0.011 * S, 14), True))
        m.band_gravur.append(([(x, by - 0.005 * S), (x, by + 0.003 * S)], False))
    # oben: Sternenhimmel an Fäden und Mondsichel
    for x, l, r in ((-0.17, 0.10, 0.065), (0.02, 0.05, 0.08), (0.20, 0.13, 0.06)):
        xs = x * S
        yt = cy + math.sqrt(max(Ri * Ri - xs * xs, 0)) + rb * 0.4
        sy = yt - rb * 0.4 - l * S - r * S
        rs = r * S
        m.nach.add(K.star(xs, sy, rs, 0.45 * rs, 5))
        m.faden((xs, sy + 0.4 * rs), (xs, yt))
        m.gr(K.star(xs, sy, rs * 0.5, 0.45 * rs * 0.5, 5), True)
        for i in range(5):
            a = math.pi / 2 + i * TAU / 5
            m.gr([(xs, sy), (xs + rs * 0.6 * math.cos(a), sy + rs * 0.6 * math.sin(a))])
    # unten: Szene auf dem Schneehügel
    yb = cy - Ri
    yg = yb + 0.085 * S
    hill = SZ.huegel(-R, R, yg, 0.012 * S, 0.10 * S + rb, phase=0.4 + 0.37 * (m.seed % 7))
    Hs = (by - bh / 2) - yg - 0.02 * S
    il = math.sqrt(max(Ri * Ri - (yg + Hs * 0.5 - cy) ** 2, 0))
    fig, sg = SZ.szene(m.szene, 2 * il * 0.96, Hs, yg, m.seed, wmin=m.wm, wb=m.wb)
    m.szene_fig = (hill, fig)
    m.g += sg
    m.kugel_kreis = (cy, R - rb * 0.4)


def _glocke(m: Motiv) -> None:
    S = m.S
    f = m.f
    rechts = [(0.0, 0.78 * S), (0.10 * S, 0.77 * S), (0.165 * S, 0.70 * S), (0.19 * S, 0.56 * S), (0.215 * S, 0.38 * S),
              (0.27 * S, 0.22 * S), (0.36 * S, 0.135 * S), (0.385 * S, 0.10 * S), (0.37 * S, 0.075 * S), (0.0, 0.075 * S)]
    body = _spl(rechts, 10, closed=False)
    body = body + [(-x, y) for x, y in reversed(body[1:-1])]
    f.add(body)
    f.add(K.circle(0, 0.05 * S, 0.05 * S, 30))                         # Klöppel
    m.gr(K.circle(0, 0.05 * S, 0.03 * S, 20), True)
    # Bänder und Ringe (leicht gewölbt wie auf einer runden Glocke)
    def quer(y, w, bauch=0.012):
        return K.bez((-w, y), (0, y - bauch * S * 2), (w, y), 18)

    def hw(y):
        a, b = E.quer_x(body, y)
        return min(-a, b)
    for y in (0.115, 0.13, 0.30, 0.315, 0.585, 0.60):
        m.gr(quer(y * S, hw(y * S) - 0.6))
    # Rundbogenfenster im Mittelband
    for k, x in enumerate((-0.12, -0.04, 0.04, 0.12)):
        win = _bogenfenster(x * S, 0.36 * S, 0.052 * S, 0.17 * S)
        m.loch_extra.append(win)
        m.gr(_versatz(win, 0.9), True)
    # Lochreihe über dem Rand
    for k in range(9):
        x = (-0.24 + 0.06 * k) * S
        m.loch_extra.append(K.circle(x, 0.20 * S + 0.25 * abs(x), 0.013 * S + 0.3, 14))
    # Ranke zwischen den Bändern unten
    m.gr([(x, 0.165 * S + 0.012 * S * math.sin(x / (0.04 * S))) for x in [(-0.30 + 0.6 * i / 60) * S for i in range(61)]
          if abs(x) < hw(0.165 * S) - 1.0])
    m.namensfeld = (0, 0.665 * S, 0.24 * S, 0.06 * S)
    m.band_gravur.append((_bogenkette((-0.13 * S, 0.68 * S), (0.13 * S, 0.68 * S), 4, 0.01 * S), False))
    for k in range(5):
        x = (-0.13 + 0.065 * k) * S
        m.band_gravur.append((K.star(x, 0.68 * S, 0.014 * S, 0.006 * S, 5), True))
    for k in range(4):
        x = (-0.0975 + 0.065 * k) * S
        m.band_gravur.append((K.circle(x, 0.65 * S, 0.008 * S, 10), True))
    # Stechpalme und Schleife oben
    for sd in (-1, 1):
        _stechpalme(m, m.nach, sd * 0.04 * S, 0.78 * S, 0.17 * S, math.pi / 2 - sd * math.radians(58))
    _beeren(m, m.nach, [(-0.025 * S, 0.80 * S), (0.025 * S, 0.80 * S), (0.0, 0.835 * S)], 0.022 * S)
    _schleife(m, m.nach, 0.0, 0.87 * S, 0.30 * S)
    m.oese_an(0.0, 0.94 * S, 1.0)
    for x, y in ((-0.06, 0.52), (0.07, 0.50), (0.0, 0.545)):
        m.gr(K.star(x * S, y * S, 0.014 * S, 0.006 * S, 5), True)


def _zapfen(m: Motiv) -> None:
    S = m.S
    f = m.f
    top, bot = 0.80 * S, 0.0

    def halb(y):                                            # halbe Breite des Zapfens auf Höhe y
        t = (y - bot) / (top - bot)
        return 0.235 * S * math.sin(math.pi * min(1.0, max(0.0, 0.08 + 0.92 * t))) ** 0.7 * (0.75 + 0.25 * t)
    f.add(_spl([(0, top - 0.02 * S)] + [(halb(y) * 0.86, y) for y in [top - (top - bot) * i / 10 for i in range(1, 10)]]
               + [(0, bot + 0.04 * S)] + [(-halb(y) * 0.86, y) for y in [bot + (top - bot) * i / 10 for i in range(1, 10)]], 6))
    reihen = 8
    for i in range(reihen):
        y = top - 0.06 * S - (top - 0.12 * S) * i / (reihen - 1)
        sh = 0.085 * S * (0.85 + 0.15 * math.sin(math.pi * i / (reihen - 1)))
        hwid = halb(y)
        n = max(2, int(round(2 * hwid / (0.085 * S))))
        off = 0.5 if i % 2 else 0.0
        for k in range(n + (1 if off else 0)):
            x = -hwid + 2 * hwid * (k + 0.5 - off * 0.5 + (0.0 if not off else 0.0)) / (n + (1 if off else 0))
            sw = 2 * hwid / (n + (1 if off else 0)) * 1.08
            schuppe = _spl([(x, y + 0.30 * sh), (x + sw * 0.5, y + 0.05 * sh), (x + sw * 0.30, y - 0.55 * sh),
                            (x, y - 0.72 * sh), (x - sw * 0.30, y - 0.55 * sh), (x - sw * 0.5, y + 0.05 * sh)], 6)
            f.add(schuppe)
            m.gr(_spl([(x + sw * 0.40, y - 0.02 * sh), (x + sw * 0.24, y - 0.50 * sh), (x, y - 0.64 * sh),
                       (x - sw * 0.24, y - 0.50 * sh), (x - sw * 0.40, y - 0.02 * sh)], 6, closed=False))
            if sw > 0.06 * S and abs(x) < hwid - 0.03 * S:
                win = _spl([(x, y - 0.05 * sh), (x + sw * 0.20, y - 0.22 * sh), (x, y - 0.46 * sh),
                            (x - sw * 0.20, y - 0.22 * sh)], 6)
                m.loch_extra.append(win)
            m.gr([(x, y + 0.10 * sh), (x, y - 0.04 * sh)])
    f.add(K.rect(-0.03 * S, top - 0.04 * S, 0.06 * S, 0.10 * S))       # Stiel
    m.gr([(-0.01 * S, top + 0.0 * S), (-0.01 * S, top + 0.05 * S)])
    for sd in (-1, 1):
        _nadelzweig(m, m.nach, (sd * 0.01 * S, top + 0.05 * S), (sd * 0.25 * S, top + 0.01 * S), 0.055 * S, 7)
        _nadelzweig(m, m.nach, (sd * 0.01 * S, top + 0.06 * S), (sd * 0.17 * S, top + 0.12 * S), 0.045 * S, 5)
    _beeren(m, m.nach, [(-0.03 * S, top + 0.075 * S), (0.03 * S, top + 0.075 * S), (0.0, top + 0.11 * S)], 0.024 * S)
    m.oese_an(0.0, top + 0.13 * S, 1.0)


def _tannenbaum(m: Motiv) -> None:
    S = m.S
    f = m.f
    stufen = [(0.62, 0.15, 0.07), (0.45, 0.24, 0.12), (0.28, 0.32, 0.17), (0.11, 0.40, 0.0)]  # (unten, Spitze, Kerbe)

    def bogen(xa, xb, y0, y1, n):
        out = []
        for k in range(n):
            pa = (xa + (xb - xa) * k / n, y0 + (y1 - y0) * k / n)
            pb = (xa + (xb - xa) * (k + 1) / n, y0 + (y1 - y0) * (k + 1) / n)
            seg = K.bez(pa, ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2 + 0.03 * S), pb, 10)
            out += seg[1:]
        return out
    rechts = [(0.0, 0.86 * S)]
    y_alt, x_alt = 0.86 * S, 0.0
    for i, (yb, w, xin) in enumerate(stufen):
        yb, w, xin = yb * S, w * S, xin * S
        rechts += K.bez((x_alt, y_alt), (x_alt + (w - x_alt) * 0.45, y_alt - (y_alt - yb) * 0.42), (w, yb), 14)[1:]
        if xin > 0:
            yi = yb + 0.035 * S
            rechts += bogen(w, xin, yb, yi, 2)
            x_alt, y_alt = xin, yi
        else:
            rechts += bogen(w, 0.0, yb, yb, 5)
    f.add(rechts + [(-x, y) for x, y in reversed(rechts[1:-1])])
    for i, (yb, w, xin) in enumerate(stufen):
        yb, w = yb * S, w * S
        xi = (stufen[i - 1][2] * S) if i else 0.0
        yt = (stufen[i - 1][0] * S + 0.035 * S) if i else 0.86 * S
        for k in range(5 + 2 * i):                          # Nadelstriche über der Zweigkante
            x = -w * 0.92 + 2 * w * 0.92 * (k + 0.5) / (5 + 2 * i)
            m.gr([(x, yb + 0.02 * S), (x * 0.9, yb + 0.085 * S)])
        for yy in (yb + 0.165 * S, yb + 0.215 * S):         # Zweigmuster: feine Winkel
            hw = w * max(0.0, (0.86 * S - yy) / (0.86 * S - yb)) * 0.85
            n_ch = int(2 * hw / (0.032 * S))
            for k in range(n_ch):
                x = -hw + 2 * hw * (k + 0.5) / max(1, n_ch)
                m.gr([(x - 0.011 * S, yy + 0.008 * S), (x, yy - 0.004 * S), (x + 0.011 * S, yy + 0.008 * S)])
        g0 = (-w * 0.72, yb + 0.10 * S)
        g1 = (w * 0.72, yb + 0.13 * S)
        m.gr(K.bez(g0, (0, yb + 0.045 * S), g1, 30))
        m.perlen(K.bez((g0[0], g0[1] - 0.012 * S), (0, yb + 0.033 * S), (g1[0], g1[1] - 0.012 * S), 30),
                 0.0065 * S, 0.022 * S)
    # Kugeln als Fenster mit gravierter Kappe
    for x, y, r in ((0.0, 0.70, 0.022), (-0.08, 0.57, 0.024), (0.09, 0.52, 0.024), (-0.13, 0.385, 0.026),
                    (0.14, 0.35, 0.024), (0.01, 0.43, 0.024), (-0.18, 0.19, 0.026), (0.20, 0.18, 0.026),
                    (0.0, 0.24, 0.026)):
        c = (x * S, y * S)
        m.loch_extra.append(K.circle(c[0], c[1], r * S, 20))
        m.gr(K.circle(c[0], c[1], r * S + 0.9, 20), True)
        m.gr(K.rect(c[0] - 0.008 * S, c[1] + r * S + 0.9, 0.016 * S, 0.012 * S), True)
    # Stern an der Spitze
    sc = (0.0, 0.905 * S)
    f.add(K.stroke([(0, 0.80 * S), (0, 0.87 * S)], 0.035 * S, 0.03 * S, "flach"))
    f.add(W_abrund(K.star(sc[0], sc[1], 0.085 * S, 0.04 * S, 5), 0.004 * S))
    m.loch_extra.append(K.star(sc[0], sc[1], 0.035 * S, 0.015 * S, 5))
    for i in range(5):
        a = math.pi / 2 + i * TAU / 5
        m.gr([(sc[0] + math.cos(a) * 0.045 * S, sc[1] + math.sin(a) * 0.045 * S),
              (sc[0] + math.cos(a) * 0.075 * S, sc[1] + math.sin(a) * 0.075 * S)])
    m.oese_an(0.0, 0.905 * S + 0.085 * S, 1.6)
    # Stamm und Geschenke
    f.add(K.rect(-0.04 * S, 0.04 * S, 0.08 * S, 0.09 * S))
    for x, w, h in ((-0.17, 0.15, 0.10), (0.16, 0.13, 0.085), (0.0, 0.11, 0.06)):
        f.add(K.rect(x * S - w * S / 2, 0.0, w * S, h * S))
        m.gr([(x * S, 0.006 * S), (x * S, h * S - 0.004 * S)])
        m.gr([(x * S - w * S / 2 + 0.006 * S, h * S * 0.55), (x * S + w * S / 2 - 0.006 * S, h * S * 0.55)])
        m.gr(K.rect(x * S - w * S / 2 + 0.006 * S, 0.006 * S, w * S - 0.012 * S, h * S - 0.012 * S), True)
        for sd in (-1, 1):
            m.gr(K.ellipse(x * S + sd * 0.018 * S, h * S + 0.0 * S, 0.016 * S, 0.008 * S, sd * 0.5, 14), True)


def _schneemann(m: Motiv) -> None:
    S = m.S
    f = m.f
    kugeln = [(0.20, 0.20), (0.48, 0.145), (0.695, 0.105)]
    for y, r in kugeln:
        f.add(K.circle(0, y * S, r * S, 80))
    hy, hr = 0.695 * S, 0.105 * S
    # Zylinder
    yb = hy + 0.075 * S
    f.add(W_abrund(K.rect(-0.16 * S, yb, 0.32 * S, 0.028 * S), 0.012 * S))
    hut = [(-0.085 * S, yb + 0.02 * S), (0.085 * S, yb + 0.02 * S), (0.095 * S, yb + 0.20 * S), (-0.095 * S, yb + 0.20 * S)]
    f.add(W_abrund(hut, 0.01 * S))
    m.gr(K.rect(-0.087 * S, yb + 0.04 * S, 0.174 * S, 0.035 * S), True)        # Hutband
    for k in range(4):
        m.gr([(-0.07 * S + 0.012 * S * k, yb + 0.09 * S), (-0.072 * S + 0.012 * S * k, yb + 0.18 * S)])
    m.gr(K.bez((-0.14 * S, yb + 0.012 * S), (0, yb + 0.02 * S), (0.14 * S, yb + 0.012 * S), 12))
    _stechpalme(m, m.nach, 0.06 * S, yb + 0.06 * S, 0.12 * S, math.radians(30))
    _beeren(m, m.nach, [(0.055 * S, yb + 0.06 * S), (0.075 * S, yb + 0.045 * S)], 0.016 * S)
    m.oese_an(-0.0, yb + 0.20 * S, 1.0)
    # Gesicht
    for sd in (-1, 1):
        c = (sd * 0.038 * S, hy + 0.025 * S)
        m.loch_extra.append(K.circle(c[0], c[1], 0.014 * S + 0.3, 14))
        m.gr(K.arc(c[0], c[1] + 0.03 * S, 0.02 * S, math.pi * 0.25, math.pi * 0.75, 6))
    nase = [(0, hy + 0.004 * S), (0.10 * S, hy - 0.012 * S), (0, hy - 0.022 * S)]
    m.gr(nase, True)
    for t in (0.3, 0.55, 0.78):
        x = 0.10 * S * t
        m.gr([(x, hy + 0.004 * S - 0.016 * S * t + 0.004 * S), (x + 0.004 * S, hy - 0.022 * S + 0.010 * S * t - 0.003 * S)])
    for k in range(5):
        a = math.pi * (1.22 + 0.14 * k)
        m.gr(K.circle(math.cos(a) * 0.06 * S, hy - 0.005 * S + math.sin(a) * 0.06 * S, 0.006 * S, 10), True)
    # Schal mit Fransen
    ys = hy - hr * 0.86
    schal = _spl([(-0.11 * S, ys + 0.02 * S), (0, ys + 0.005 * S), (0.11 * S, ys + 0.02 * S), (0.12 * S, ys - 0.025 * S),
                  (0, ys - 0.04 * S), (-0.12 * S, ys - 0.025 * S)], 8)
    f.add(schal)
    ende = [(0.06 * S, ys - 0.02 * S), (0.10 * S, ys - 0.09 * S), (0.13 * S, ys - 0.17 * S)]
    f.add(K.stroke(ende, 0.06 * S, 0.055 * S, "flach"))
    for k in range(5):                                      # Fransen: Schlitze unten
        t = (k + 0.5) / 5
        x0 = ende[-1][0] - 0.026 * S + 0.052 * S * t
        y0 = ende[-1][1]
        m.nach.add(K.stroke([(x0, y0), (x0 + 0.01 * S, y0 - 0.04 * S)], m.wm, m.wm, "rund"))
    for k in range(6):                                      # Streifen im Schal
        x = -0.10 * S + 0.04 * S * k
        m.gr([(x, ys + 0.012 * S), (x + 0.01 * S, ys - 0.032 * S)])
    for t in (0.35, 0.65):
        p = (ende[0][0] + (ende[2][0] - ende[0][0]) * t, ende[0][1] + (ende[2][1] - ende[0][1]) * t)
        m.gr([(p[0] - 0.028 * S, p[1] + 0.01 * S), (p[0] + 0.028 * S, p[1] - 0.004 * S)])
    # Knöpfe
    for y in (0.53, 0.47, 0.41):
        m.loch_extra.append(K.circle(-0.01 * S, y * S, 0.016 * S + 0.3, 16))
        m.gr(K.circle(-0.01 * S, y * S, 0.016 * S + 1.2, 16), True)
    # Arme aus Zweigen mit Handschuhen
    for sd in (-1, 1):
        a0 = (sd * 0.12 * S, 0.52 * S)
        a1 = (sd * 0.30 * S, 0.62 * S)
        f.add(K.stroke([a0, ((a0[0] + a1[0]) / 2, 0.585 * S), a1], m.wm * 1.4, m.wm * 1.1, "rund"))
        f.add(K.stroke([(sd * 0.23 * S, 0.59 * S), (sd * 0.27 * S, 0.66 * S)], m.wm, m.wm, "rund"))
        f.add(K.ellipse(a1[0] + sd * 0.02 * S, a1[1] + 0.01 * S, 0.032 * S, 0.026 * S, sd * 0.4, 20))
        f.add(K.ellipse(a1[0] + sd * 0.005 * S, a1[1] + 0.035 * S, 0.012 * S, 0.02 * S, sd * 0.3, 14))
        m.gr([(a1[0] - sd * 0.01 * S, a1[1] - 0.012 * S), (a1[0] - sd * 0.004 * S, a1[1] + 0.02 * S)])
    # Schneeglitzern und Namensfeld
    m.namensfeld = (0, 0.20 * S, 0.27 * S, 0.075 * S)
    for i in range(6):                                      # Schneeflocke auf dem Bauch (weicht dem Namen)
        a = math.pi / 2 + i * TAU / 6
        c = (0.0, 0.20 * S)
        e = (c[0] + math.cos(a) * 0.06 * S, c[1] + math.sin(a) * 0.06 * S)
        m.band_gravur.append(([c, e], False))
        for t in (0.45, 0.75):
            q = (c[0] + (e[0] - c[0]) * t, c[1] + (e[1] - c[1]) * t)
            for sd in (1, -1):
                b = a + sd * math.radians(45)
                m.band_gravur.append(([q, (q[0] + math.cos(b) * 0.02 * S, q[1] + math.sin(b) * 0.02 * S)], False))
    for x, y in ((-0.11, 0.30), (0.12, 0.27), (-0.13, 0.12), (0.10, 0.10), (0.0, 0.07), (0.08, 0.60), (-0.08, 0.40)):
        c = (x * S, y * S)
        for i in range(3):
            a = i * math.pi / 3
            m.gr([(c[0] - math.cos(a) * 0.014 * S, c[1] - math.sin(a) * 0.014 * S),
                  (c[0] + math.cos(a) * 0.014 * S, c[1] + math.sin(a) * 0.014 * S)])


def _herz(m: Motiv) -> None:
    S = m.S
    umriss, (_, top), yc = NA.FG.form("herz", S)
    ymin = min(p[1] for p in umriss)
    umriss = [(x, y - ymin) for x, y in umriss]
    top -= ymin
    m.f.add(umriss)
    rb = max(2 * m.web + m.kerf + 1.2, 0.042 * S)
    xs = [q[0] for q in umriss]
    lw = E.Leinwand((min(xs) - 2, -2, max(xs) + 2, max(q[1] for q in umriss) + 2), 0.08)
    innen = NA._innen(lw, umriss, rb)                       # über das Raster: die Herzkerbe bleibt sauber
    mitte = NA._innen(lw, umriss, rb * 0.45)
    m.loch_extra.append(innen)
    m.gr(NA._innen(lw, umriss, rb / 2), True)
    m.perlen(NA._innen(lw, umriss, rb / 2 - 0.2), 0.32, max(2.0, rb * 1.05), closed=True)
    n = m.nach
    w = m.wm * 1.15

    def am_rand(x, y):
        return min(mitte, key=lambda q: (q[0] - x) ** 2 + (q[1] - y) ** 2)

    def blaetter(pfad, ts, laenge):
        for t in ts:
            i = max(1, min(len(pfad) - 2, int(t * (len(pfad) - 1))))
            q = pfad[i]
            d = (pfad[i + 1][0] - pfad[i - 1][0], pfad[i + 1][1] - pfad[i - 1][1])
            L = math.hypot(*d) or 1
            ux, uy = d[0] / L, d[1] / L
            for s2 in (1, -1):
                tip = (q[0] - uy * s2 * laenge + ux * laenge * 0.6, q[1] + ux * s2 * laenge + uy * laenge * 0.6)
                n.add(_blatt(q, tip, 0.48 * laenge, 10))
                m.gr([(q[0] + (tip[0] - q[0]) * 0.2, q[1] + (tip[1] - q[1]) * 0.2),
                      (q[0] + (tip[0] - q[0]) * 0.8, q[1] + (tip[1] - q[1]) * 0.8)])

    by = min(p[1] for p in innen)
    n.add(K.stroke([(0, by - 1.0), (0, 0.44 * S)], 2.6 * w, 1.5 * w, "flach"))
    for k in range(3):                                      # Rinde
        m.gr([(-0.004 * S + 0.004 * S * k, by + 0.03 * S), (-0.004 * S + 0.004 * S * k, 0.40 * S)])
    for sd in (-1, 1):
        for y0, ziel, dreh in ((0.17, (0.30, 0.42), 0.8), (0.28, (0.40, 0.66), 0.9), (0.38, (0.22, 0.82), 0.85)):
            p0 = (0, y0 * S)
            p2 = am_rand(sd * ziel[0] * S, ziel[1] * S)
            p1 = (p0[0] + (p2[0] - p0[0]) * 0.55, p0[1] + (p2[1] - p0[1]) * 0.15)
            ast = K.bez(p0, p1, p2, 24)
            n.add(K.stroke(ast, w * 1.35, w, "rund"))
            # Ranke unter dem Ast, eingerollt
            i = int(0.55 * (len(ast) - 1))
            q = ast[i]
            sp = NA.FG.spiral((q[0] + sd * 0.02 * S, q[1] - 0.055 * S), q, dreh, 0.62, cw=(sd < 0), n=40)
            n.add(K.stroke(sp, w, w * 0.9, "rund"))
            blaetter(ast, (0.30, 0.80), 0.075 * S)
            e = sp[-1]
            n.add(K.circle(e[0], e[1], 0.018 * S, 14))
    # Krone: Herz mit Fenster, darüber Lyra-Ranken bis in die Herzkerbe
    hc = (0, 0.50 * S)
    n.add(_herzform(hc[0], hc[1], 0.16 * S))
    m.loch_extra2 = [_herzform(hc[0], hc[1] + 0.003 * S, 0.08 * S)]
    m.gr(_herzform(hc[0], hc[1] + 0.001 * S, 0.12 * S), True)
    n.add(K.stroke([(0, hc[1] + 0.05 * S), (0, top)], w * 1.2, w * 1.2, "flach"))
    for sd in (-1, 1):
        sp = NA.FG.spiral((sd * 0.08 * S, 0.66 * S), (0, 0.585 * S), 0.85, 0.65, cw=(sd > 0), n=40)
        n.add(K.stroke(sp, w * 1.1, w * 0.9, "rund"))
        n.add(K.circle(sp[-1][0], sp[-1][1], 0.016 * S, 12))
        blaetter(K.bez((0, 0.70 * S), (sd * 0.05 * S, 0.76 * S), am_rand(sd * 0.14 * S, 0.84 * S), 16), (0.45,), 0.04 * S)
        n.add(K.stroke(K.bez((0, 0.70 * S), (sd * 0.05 * S, 0.76 * S), am_rand(sd * 0.14 * S, 0.84 * S), 16), w, w, "rund"))
    m.namensfeld = (0, 0.27 * S, 0.30 * S, 0.065 * S)
    m.feld_material = [W_abrund(K.rect(-0.19 * S, 0.27 * S - 0.06 * S, 0.38 * S, 0.12 * S), 0.05 * S)]
    m.feld_rahmen = True
    ro = max(3.4, 0.042 * S)
    m.nach.add(K.circle(0.0, top + 0.6 * ro - 0.01 * S, ro, 48))
    m.oese = (0.0, top + 0.6 * ro - 0.01 * S, ro)
    m.nach.add(K.stroke([(0, top - rb), (0, top + 0.6 * ro)], ro * 1.2, ro * 1.2, "flach"))


def _mond(m: Motiv) -> None:
    S = m.S
    R = 0.40 * S
    cy = 0.42 * S
    d, r2 = 0.42 * R, 0.84 * R
    mond = Figur().add(K.circle(-0.04 * S, cy, R, 140)).cut(K.circle(-0.04 * S + d, cy + 0.04 * R, r2, 140))
    m.f.merge(mond)
    cx = -0.04 * S
    # Schlafmütze auf der oberen Spitze mit Bommel
    tip = (cx + R * math.cos(math.radians(62)), cy + R * math.sin(math.radians(62)))
    muetze = _spl([(cx - 0.05 * S, cy + R * 0.94), (cx + 0.06 * S, cy + R * 1.08), (tip[0] + 0.10 * S, tip[1] + 0.06 * S),
                   (tip[0] + 0.20 * S, tip[1] - 0.04 * S), (tip[0] + 0.08 * S, tip[1] - 0.02 * S),
                   (tip[0] - 0.02 * S, tip[1] - 0.03 * S), (cx + 0.02 * S, cy + R * 0.82)], 8)
    m.nach.add(muetze)
    bom = (tip[0] + 0.21 * S, tip[1] - 0.07 * S)
    m.nach.add(K.circle(bom[0], bom[1], 0.04 * S, 24))
    for k in range(8):
        a = TAU * k / 8
        m.gr([(bom[0] + math.cos(a) * 0.012 * S, bom[1] + math.sin(a) * 0.012 * S),
              (bom[0] + math.cos(a) * 0.032 * S, bom[1] + math.sin(a) * 0.032 * S)])
    krempe = K.bez((cx - 0.05 * S, cy + R * 0.90), (cx + 0.06 * S, cy + R * 0.95), (tip[0] - 0.01 * S, tip[1] - 0.02 * S), 16)
    m.gr(krempe)
    m.gr([(x, y + 0.025 * S) for x, y in krempe])
    for t in (0.3, 0.55, 0.8):                              # Ringel der Mütze
        q = (tip[0] - 0.02 * S + 0.20 * S * t, tip[1] + 0.02 * S - 0.02 * S * t + 0.05 * S * math.sin(math.pi * t))
        m.gr([(q[0] - 0.02 * S, q[1] - 0.03 * S), (q[0] + 0.015 * S, q[1] + 0.035 * S)])
    # Gesicht im Profil an der Innenkante: Nase und Lippen als kleine Wölbungen, Auge mit Wimpern
    ix = cx + d - r2                                        # Innenkante auf Höhe der Mitte
    m.nach.add(_spl([(ix - 0.01 * S, cy + 0.03 * S), (ix + 0.035 * S, cy + 0.0 * S), (ix - 0.01 * S, cy - 0.03 * S)], 6, closed=True))
    m.nach.add(K.circle(ix + 0.0 * S, cy - 0.075 * S, 0.018 * S, 14))
    ex, ey = ix - 0.075 * S, cy + 0.06 * S
    m.gr(K.arc(ex, ey + 0.02 * S, 0.03 * S, math.pi * 1.15, math.pi * 1.85, 10))
    for k in range(4):
        a = math.pi * (1.25 + 0.17 * k)
        q = (ex + math.cos(a) * 0.03 * S, ey + 0.02 * S + math.sin(a) * 0.03 * S)
        m.gr([q, (q[0] + math.cos(a) * 0.014 * S, q[1] + math.sin(a) * 0.014 * S)])
    m.gr(K.arc(ex + 0.005 * S, ey + 0.065 * S, 0.035 * S, math.pi * 1.25, math.pi * 1.7, 8))      # Braue
    m.gr(K.circle(ix - 0.075 * S, cy - 0.04 * S, 0.02 * S, 14), True)                          # Wange
    m.gr(K.arc(ix - 0.03 * S, cy - 0.07 * S, 0.02 * S, math.pi * 0.6, math.pi * 1.3, 8))        # Mundwinkel
    # Sterne als Fenster und Sternenstaub
    for x, y, r in ((-0.27, 0.72, 0.03), (-0.37, 0.30, 0.03), (-0.20, 0.10, 0.026), (-0.38, 0.52, 0.022)):
        m.loch_extra.append(K.star(x * S, y * S, r * S, 0.45 * r * S, 5))
        m.gr(K.star(x * S, y * S, r * S + 1.0, 0.45 * r * S + 0.6, 5), True)
    for k, (x, y) in enumerate(((-0.33, 0.20), (-0.12, 0.08), (-0.40, 0.42), (-0.17, 0.78), (-0.33, 0.64),
                                (-0.28, 0.16), (-0.30, 0.38))):
        m.gr(K.circle(x * S, y * S, (0.006 + 0.003 * (k % 3)) * S, 10), True)
    for x, l, r in ((0.10, 0.12, 0.06), (0.22, 0.22, 0.05)):
        xs = cx + d + x * S - 0.12 * S
        yt = tip[1] - 0.02 * S
        sy = yt - l * S
        m.nach.add(K.star(xs, sy, r * S, 0.45 * r * S, 5))
        m.faden((xs, sy + 0.4 * r * S), (xs, yt + 0.01 * S))
        m.gr(K.star(xs, sy, r * S * 0.5, 0.45 * r * S * 0.5, 5), True)
    m.oese_an(cx - 0.02 * S, cy + R * 1.0, 0.9)


def _kerze(m: Motiv) -> None:
    S = m.S
    f = m.f
    kw, y0, y1 = 0.10 * S, 0.20 * S, 0.66 * S
    kerze = [(-kw, y0), (kw, y0), (kw, y1 - 0.01 * S), (kw * 0.6, y1), (-kw * 0.2, y1 + 0.005 * S), (-kw, y1 - 0.01 * S)]
    f.add(kerze)
    for x, l in ((-0.065, 0.07), (0.02, 0.045), (0.085, 0.10)):      # Wachstropfen
        f.add(K.stroke([(x * S, y1 - 0.005 * S), (x * S, y1 - l * S)], 0.03 * S, 0.03 * S, "rund"))
    m.gr(K.bez((-kw, y1 - 0.02 * S), (0, y1 - 0.06 * S), (kw, y1 - 0.02 * S), 12))
    # Flamme mit Fenster und Strahlenkranz
    fy = y1 + 0.02 * S
    flamme = _spl([(0, fy), (0.045 * S, fy + 0.06 * S), (0.025 * S, fy + 0.15 * S), (0.0, fy + 0.22 * S),
                   (-0.03 * S, fy + 0.13 * S), (-0.045 * S, fy + 0.06 * S)], 8)
    f.add(flamme)
    f.add(K.stroke([(0, y1 - 0.01 * S), (0, fy + 0.02 * S)], m.wm * 1.2, m.wm, "flach"))
    m.loch_extra.append(_spl([(0, fy + 0.035 * S), (0.022 * S, fy + 0.07 * S), (0.008 * S, fy + 0.13 * S),
                              (-0.014 * S, fy + 0.075 * S)], 6))
    for i in range(9):
        a = math.radians(-10 + 200 * i / 8)
        c = (0, fy + 0.09 * S)
        m.nach.add(K.stroke([(c[0] + math.cos(a) * 0.15 * S, c[1] + math.sin(a) * 0.15 * S),
                             (c[0] + math.cos(a) * (0.19 if i % 2 else 0.17) * S, c[1] + math.sin(a) * (0.19 if i % 2 else 0.17) * S)],
                            m.wm, m.wm * 0.8, "rund"))
    ring = K.arc(0, fy + 0.09 * S, 0.15 * S, math.radians(-10), math.radians(190), 40)
    m.nach.add(K.stroke(ring, m.wm, m.wm, "rund"))
    # Verzierung auf der Kerze: Herz-Fenster, Sternchenranke
    m.loch_extra.append(_herzform(0, 0.43 * S, 0.075 * S))
    m.gr(_herzform(0, 0.43 * S, 0.11 * S), True)
    for y in (0.53, 0.33):
        m.gr([(-kw + 0.01 * S, y * S), (kw - 0.01 * S, y * S)])
        m.gr([(-kw + 0.01 * S, y * S + (0.012 if y > 0.4 else -0.012) * S), (kw - 0.01 * S, y * S + (0.012 if y > 0.4 else -0.012) * S)])
    for x, y in ((-0.06, 0.58), (0.05, 0.60), (0.0, 0.29), (-0.06, 0.26), (0.06, 0.25)):
        m.gr(K.star(x * S, y * S, 0.012 * S, 0.005 * S, 5), True)
    # Tannengrün, Stechpalme, Beeren am Fuß
    for sd in (-1, 1):
        _nadelzweig(m, f, (sd * 0.02 * S, 0.19 * S), (sd * 0.36 * S, 0.16 * S), 0.07 * S, 8)
        _nadelzweig(m, f, (sd * 0.04 * S, 0.21 * S), (sd * 0.30 * S, 0.30 * S), 0.06 * S, 6)
        _nadelzweig(m, f, (sd * 0.02 * S, 0.17 * S), (sd * 0.28 * S, 0.04 * S), 0.06 * S, 6)
        _stechpalme(m, m.nach, sd * 0.05 * S, 0.17 * S, 0.17 * S, math.pi / 2 - sd * math.radians(100))
    _beeren(m, m.nach, [(-0.035 * S, 0.17 * S), (0.035 * S, 0.17 * S), (0.0, 0.205 * S), (0.0, 0.14 * S)], 0.024 * S)
    m.oese_an(0.0, fy + 0.22 * S, 1.2)


def _geschenk(m: Motiv) -> None:
    S = m.S
    f = m.f
    bw, bh = 0.34 * S, 0.56 * S
    f.add(W_abrund(K.rect(-bw, 0.0, 2 * bw, bh), 0.02 * S))
    lw_, lh = 0.37 * S, 0.11 * S
    f.add(W_abrund(K.rect(-lw_, bh - 0.03 * S, 2 * lw_, lh), 0.015 * S))
    m.gr(W_abrund(K.rect(-lw_ + 0.012 * S, bh - 0.018 * S, 2 * lw_ - 0.024 * S, lh - 0.024 * S), 0.01 * S), True)
    # Band: senkrecht und quer, graviert doppelt
    for x in (-0.035 * S, 0.035 * S):
        m.gr([(x, 0.01 * S), (x, bh + lh - 0.04 * S)])
    # Muster: Sterne als Fenster in vier Feldern + gravierte Punkte
    for x in (-0.24, -0.14, 0.14, 0.24):
        for y in (0.08, 0.22, 0.36, 0.48):
            c = ((x + (0.02 if x < 0 else -0.02) * (int(y * 50) % 2)) * S, y * S)
            if (int(abs(x) * 100) // 10 + int(y * 100) // 12) % 2 == 0:
                m.loch_extra.append(K.star(c[0], c[1], 0.035 * S, 0.016 * S, 5))
                m.gr(K.star(c[0], c[1], 0.035 * S + 0.9, 0.016 * S + 0.5, 5), True)
            else:
                m.gr(K.circle(c[0], c[1], 0.012 * S, 12), True)
                for i in range(6):
                    a = TAU * i / 6
                    m.gr([(c[0] + math.cos(a) * 0.018 * S, c[1] + math.sin(a) * 0.018 * S),
                          (c[0] + math.cos(a) * 0.028 * S, c[1] + math.sin(a) * 0.028 * S)])
    _schleife(m, m.nach, 0.0, bh + lh - 0.01 * S, 0.62 * S)
    ro = max(3.4, 0.042 * S)
    oy = bh + lh - 0.01 * S + 0.075 * 0.62 * S + ro - 1.0
    m.nach.add(K.circle(0, oy, ro, 48))
    m.oese = (0.0, oy, ro)
    m.namensfeld = (0, 0.22 * S, 0.40 * S, 0.075 * S)


def _stiefel(m: Motiv) -> None:
    S = m.S
    f = m.f
    stiefel = _spl([(-0.20 * S, 0.80 * S), (0.10 * S, 0.80 * S), (0.11 * S, 0.40 * S), (0.16 * S, 0.27 * S),
                    (0.30 * S, 0.20 * S), (0.38 * S, 0.17 * S), (0.42 * S, 0.24 * S), (0.43 * S, 0.12 * S),
                    (0.36 * S, 0.02 * S), (0.10 * S, 0.0 * S), (-0.18 * S, 0.01 * S), (-0.22 * S, 0.10 * S),
                    (-0.21 * S, 0.40 * S)], 8)
    f.add(stiefel)
    f.add(K.circle(0.43 * S, 0.27 * S, 0.04 * S, 24))                  # Bommel an der Spitze
    for k in range(8):
        a = TAU * k / 8
        m.gr([(0.43 * S + math.cos(a) * 0.012 * S, 0.27 * S + math.sin(a) * 0.012 * S),
              (0.43 * S + math.cos(a) * 0.03 * S, 0.27 * S + math.sin(a) * 0.03 * S)])
    # Pelzkrempe: wolkiger Rand
    yk0, yk1 = 0.76 * S, 0.93 * S
    f.add(K.rect(-0.25 * S, yk0, 0.39 * S, yk1 - yk0))
    for k in range(9):
        x = -0.25 * S + 0.39 * S * k / 8
        f.add(K.circle(x, yk1, 0.028 * S, 16))
        f.add(K.circle(x + 0.02 * S, yk0, 0.026 * S, 16))
    f.add(K.circle(-0.25 * S, (yk0 + yk1) / 2, 0.035 * S, 16))
    f.add(K.circle(0.14 * S, (yk0 + yk1) / 2, 0.035 * S, 16))
    for i in range(36):                                     # Pelzstriche
        x = -0.24 * S + 0.37 * S * ((i * 37) % 36) / 36
        y = yk0 + 0.02 * S + (yk1 - yk0 - 0.04 * S) * ((i * 17) % 36) / 36
        a = math.radians(60 + (i * 53) % 60)
        m.gr([(x, y), (x + math.cos(a) * 0.018 * S, y + math.sin(a) * 0.018 * S)])
    m.oese_an(-0.18 * S, yk1 + 0.02 * S, 1.5)
    # Stechpalme an der Krempe
    _stechpalme(m, m.nach, 0.12 * S, 0.88 * S, 0.17 * S, math.radians(15))
    _stechpalme(m, m.nach, 0.12 * S, 0.86 * S, 0.15 * S, math.radians(-30))
    _beeren(m, m.nach, [(0.12 * S, 0.89 * S), (0.145 * S, 0.865 * S), (0.11 * S, 0.855 * S)], 0.02 * S)
    # Naht, Ferse, Kappe
    for line in _strichel_liste(_versatz(stiefel, -0.025 * S), 0.022 * S, 0.012 * S):
        m.gr(line)
    m.gr(K.bez((-0.21 * S, 0.17 * S), (-0.10 * S, 0.17 * S), (-0.08 * S, 0.0), 14))
    m.gr(K.bez((0.30 * S, 0.0), (0.27 * S, 0.12 * S), (0.36 * S, 0.19 * S), 14))
    # Fenster: Sterne und Herz im Schaft
    for x, y, r in ((-0.10, 0.62, 0.04), (0.02, 0.68, 0.028), (-0.02, 0.36, 0.032), (-0.14, 0.30, 0.025),
                    (0.22, 0.10, 0.028)):
        m.loch_extra.append(K.star(x * S, y * S, r * S, 0.45 * r * S, 5))
        m.gr(K.star(x * S, y * S, r * S + 1.0, 0.45 * r * S + 0.6, 5), True)
    m.namensfeld = (-0.05 * S, 0.50 * S, 0.24 * S, 0.07 * S)
    for x, y in ((0.05, 0.42), (-0.15, 0.68), (0.06, 0.60), (-0.16, 0.42), (0.10, 0.12), (-0.08, 0.10)):
        m.gr(K.circle(x * S, y * S, 0.007 * S, 10), True)


def _strichel_liste(poly: Poly, strich: float, luecke: float) -> List[Poly]:
    pts = K.resample(poly + [poly[0]], 0.3)
    out, cur, acc, an = [], [], 0.0, True
    for a, b in zip(pts, pts[1:]):
        dl = math.hypot(b[0] - a[0], b[1] - a[1])
        if an:
            cur.append(a)
        acc += dl
        if an and acc >= strich:
            cur.append(b)
            out.append(cur)
            cur, acc, an = [], 0.0, False
        elif not an and acc >= luecke:
            acc, an = 0.0, True
    return [c for c in out if len(c) >= 2]


# --------------------------------------------------------------------------------------------------
# Zusammenbau
# --------------------------------------------------------------------------------------------------

ZEICHNER = {"engel": _engel, "stern": _stern, "kugel": _kugel, "glocke": _glocke, "zapfen": _zapfen,
            "tannenbaum": _tannenbaum, "schneemann": _schneemann, "herz": _herz, "mond": _mond, "kerze": _kerze,
            "geschenk": _geschenk, "stiefel": _stiefel}


def _name_gravieren(part, lw, m: Motiv, name: str, schrift: str) -> None:
    cx, cy, w, h = m.namensfeld
    s = SS.Satz(name, schrift)
    k = min(h / s.hoehe, w / s.breite)
    if s.x_mm(k) < 1.8:
        raise ValueError(f"Der Name „{name}“ passt nicht auf das Motiv – kürzer fassen oder größer wählen")
    polys = s.in_mm((cx, cy), k)
    NA._text_gravieren(part, lw, polys, "gefuellt")


def _anhaenger(cfg, motiv: str, S: float, tag: str, name: str, schrift: str, szene: str, seed: int,
               notes: List[str]):
    m = Motiv(cfg, S, seed)
    m.szene = szene
    ZEICHNER[motiv](m)
    mit_name = bool(name) and motiv in MIT_NAMEN and m.namensfeld is not None
    if motiv == "stern":
        _stern_mitte(m, mit_name)
    if mit_name and m.feld_material:
        m.nach.add(*m.feld_material)
    if mit_name:                                            # Fenster im Namensfeld weglassen
        cx, cy2, w, h = m.namensfeld
        box = (cx - w / 2 - 2.0, cy2 - h / 2 - 2.0, cx + w / 2 + 2.0, cy2 + h / 2 + 2.0)

        def frei(poly):
            xs = [q[0] for q in poly]
            ys = [q[1] for q in poly]
            gross = max(max(xs) - min(xs), max(ys) - min(ys)) > 0.3 * S   # große Fenster (Kugel, Herz) bleiben
            return gross or max(xs) < box[0] or min(xs) > box[2] or max(ys) < box[1] or min(ys) > box[3]
        m.loch_extra = [q for q in m.loch_extra if frei(q)]
    allfig = Figur(list(m.f.ops) + list(m.nach.ops))
    x0, y0, x1, y1 = allfig.bbox()
    if m.oese:
        y1 = max(y1, m.oese[1] + m.oese[2])
    box = (x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    lw = E.Leinwand(box, max(0.05, min(0.085, max(x1 - x0, y1 - y0) / 1300.0)))
    mat = lw.figur(m.f)
    if m.loch_extra:
        mat = E._andnot(mat, lw.flaechen(m.loch_extra))
    if motiv == "kugel":
        hill, fig = m.szene_fig
        cy, Rk = m.kugel_kreis
        frei = lw.flaechen([K.circle(0, cy, Rk, 160)])
        mat = mat.union(E._and(lw.flaechen([hill]).union(NA._figur_robust(lw, fig, 0.45 * (m.web + m.kerf), 0.22)),
                               frei))
    mat = mat.union(lw.figur(m.nach))
    if m.loch_extra2:
        mat = E._andnot(mat, lw.flaechen(m.loch_extra2))
    mat = NA._inseln_verbinden(lw, mat, m.wb)
    loch = None
    if m.oese:
        ox, oy, ro = m.oese
        loch = K.circle(ox, oy, ro - max(m.web + 0.7, 1.5), 40)
        mat = E._andnot(mat, lw.flaechen([loch]))
    p = E.teil_aus_raster(tag, lw, mat, m.web, m.kerf, notes)
    gravuren = list(m.g) + list(m.nach_g)
    if not mit_name:
        gravuren += m.band_gravur
    if mit_name:
        cx, cy2, w, h = m.namensfeld
        sperr = K.rect(cx - w / 2 - 1.0, cy2 - h / 2 - 1.0, w + 2.0, h + 2.0)
        gravuren = [g for pts, c in gravuren for g in _ausserhalb(pts, c, sperr)]
        if m.feld_rahmen:
            fr = W_abrund(K.rect(cx - w / 2 - 1.6, cy2 - h / 2 - 1.6, w + 3.2, h + 3.2), min(h / 2, 4.0))
            gravuren.append((fr, True))
    NA._gravuren_setzen(p, lw, gravuren)
    if mit_name:
        _name_gravieren(p, lw, m, name, schrift)
    return p


def _ausserhalb(pts, closed: bool, rect_poly):
    """Gravurlinie ohne die Stücke im Rechteck (Platz für den Namen)."""
    xs = [q[0] for q in rect_poly]
    ys = [q[1] for q in rect_poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)

    def drin(q):
        return x0 <= q[0] <= x1 and y0 <= q[1] <= y1
    pts = list(pts) + ([pts[0]] if closed else [])
    if not any(drin(q) for q in K.resample(pts, 0.5)):
        return [(pts[:-1] if closed else pts, closed)]
    out, lauf = [], []
    for q in K.resample(pts, 0.3):
        if drin(q):
            if len(lauf) >= 2:
                out.append((lauf, False))
            lauf = []
        else:
            lauf.append(q)
    if len(lauf) >= 2:
        out.append((lauf, False))
    return out


def build(cfg, name: str = "christbaumschmuck", motiv: str = "alle", groesse: float = 90.0, text: str = "",
          schrift: str = "schwungvoll", szene: str = "winterdorf", anzahl: int = 1):
    for key, val, opts in (("Motiv", motiv, AUSWAHL), ("Schreibschrift", schrift, SS.SCHRIFTEN),
                           ("Szene", szene, KUGELSZENEN)):
        if val not in dict(opts):
            raise ValueError(f"{key}: unbekannte Auswahl {val!r}")
    text = (text or "").strip()
    if text:
        bad = SS.fehlende(text, schrift)
        if bad:
            raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Schreibschrift nicht")
    S = cfg.s(groesse)
    if S < 55:
        raise ValueError("Der Anhänger ist zu klein – mindestens 60 mm Höhe")
    liste = [k for k, _ in MOTIVE] if motiv == "alle" else [motiv]
    asm = Assembly(name, params=dict(motiv=motiv, groesse=S))
    notes: List[str] = []
    for mo in liste:
        for i in range(max(1, int(anzahl))):
            tag = mo if anzahl <= 1 else f"{mo}_{i + 1:02d}"
            asm.parts.append(_anhaenger(cfg, mo, S, tag, text, schrift, szene, cfg.seed + i, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    if text and motiv != "alle" and motiv not in MIT_NAMEN:
        asm.notes.append("Hinweis: Dieses Motiv hat keinen Platz für einen Namen – der Name wurde weggelassen.")
    asm.notes.append("Aufhängen: Band oder Kordel durch die Öse ziehen.")
    asm.notes.append("Tipp: Am edelsten in 3 mm Ahorn, Birke oder Kirsche. Die Gravur mit wenig Leistung lasern, "
                     "dann bleiben die feinen Linien (Federn, Gesichter, Nadeln) scharf; danach dünn ölen.")
    if cfg.T < 2.5:
        asm.notes.append(f"Tipp: Bei {cfg.T:g} mm Material sind die Fäden der Sterne und der Heiligenschein "
                         "empfindlich – 3 mm sind stabiler.")
    return asm
