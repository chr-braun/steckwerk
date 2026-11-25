"""
Papierstern – gefalteter Fünfzackstern aus zwei Hälften mit aufwendigem Filigran.

Jede Hälfte ist ein Teil mit zehn Flächen, die mit Berg- und Talfalten zur Spitze in der Mitte
aufgefaltet werden. Jede Fläche trägt außen eine Spitzenborte (Perlfenster und Wellenlinie), im Feld
eines von vier Mustern (Lebensblume, Sternmosaik, Eisfeder, Schneeflockenregen) und innen ein Blatt
der Rosette. Die Muster sind an den Zackenfalten gespiegelt; über die Falzlinien läuft kein Fenster.
Gedacht für Karton 160–300 g oder Tonpapier.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Tuple

from steckwerk import Assembly
from pakete import num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_steckstern_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


S_ = _sub("_stern")
E, K, W = S_.E, S_.K, S_.W

MUSTER = [("lebensblume", "Lebensblume"), ("sternmosaik", "Sternmosaik"), ("eisfeder", "Eisfeder"),
          ("schneeflocken", "Schneeflockenregen")]
TIEFE = [("flach", "flach"), ("mittel", "mittel"), ("tief", "tief")]
TEILE = [("beide", "Vorder- und Rückseite"), ("vorne", "nur Vorderseite (Probe)")]

INFO = dict(
    label="Papierstern",
    group="Steckstern",
    desc="Gefalteter Fünfzackstern aus Karton mit Spitzenborte, Rosette und Filigran aus Lebensblume, "
         "Sternmosaik, Eisfeder oder Schneeflocken – innen mit LED beleuchtet.",
    params=[
        num("groesse", "Durchmesser", 280, 160, 380),
        sel("muster", "Muster", MUSTER, "lebensblume"),
        sel("tiefe", "Tiefe", TIEFE, "mittel"),
        sel("teile", "Teile", TEILE, "beide"),
    ],
)

UEBERSETZUNG = {"en": {
    "Papierstern": "Paper star", "Steckstern": "Slot-together star",
    "Gefalteter Fünfzackstern aus Karton mit Spitzenborte, Rosette und Filigran aus Lebensblume, "
    "Sternmosaik, Eisfeder oder Schneeflocken – innen mit LED beleuchtet.":
        "Folded five-pointed card star with lace border, rosette and filigree of flower of life, star mosaic, "
        "frost feather or snowflakes – lit from inside with an LED.",
    "Durchmesser": "Diameter", "Muster": "Pattern", "Tiefe": "Depth", "Teile": "Parts",
    "Lebensblume": "Flower of life", "Sternmosaik": "Star mosaic", "Eisfeder": "Frost feather",
    "Schneeflockenregen": "Snowflake shower", "flach": "flat", "mittel": "medium", "tief": "deep",
    "Vorder- und Rückseite": "Front and back", "nur Vorderseite (Probe)": "Front only (test)",
}}

_H = dict(flach=0.15, mittel=0.20, tief=0.26)


class Geo:
    def __init__(self, cfg, D: float, tiefe: str):
        self.R = D / 2
        self.r = self.R * 0.45
        self.h = self.R * _H[tiefe]
        self.k = D / 280.0
        self.steg = cfg.min_web + cfg.kerf + 0.45
        self.falz = max(1.1, self.steg * 0.9)
        self.rand = max(2.2, self.steg * 1.6)
        self.rm = 24.0 * self.k
        self.bw = max(3.0, self.steg * 2.4)              # Perlfenster der Borte
        self.wel = max(3.2, self.steg * 2.6)             # Wellenreihe der Borte
        self.borte = self.rand + self.bw + self.wel + 1.0
        lt = math.hypot(self.R, self.h)
        li = math.hypot(self.r, self.h)
        tx, ty = self.R * math.cos(math.pi / 2), self.R * math.sin(math.pi / 2)
        a = math.pi / 2 + math.pi / 5
        ix, iy = self.r * math.cos(a), self.r * math.sin(a)
        lti = math.hypot(tx - ix, ty - iy)
        self.ang = math.acos((lt ** 2 + li ** 2 - lti ** 2) / (2 * lt * li))
        self.LT, self.LI, self.LTI = lt, li, lti
        self.C = (0.0, 0.0)
        self.T = (lt, 0.0)
        self.I = (li * math.cos(self.ang), li * math.sin(self.ang))

    # Halbebenen-Schnitte im kanonischen Dreieck C-T-I
    def _linie(self, a, b, d):
        """Gerade a→b, um d ins Dreieck verschoben: (Punkt, Richtung)"""
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        n = (-dy / L, dx / L)
        c = ((self.C[0] + self.T[0] + self.I[0]) / 3, (self.C[1] + self.T[1] + self.I[1]) / 3)
        if (c[0] - a[0]) * n[0] + (c[1] - a[1]) * n[1] < 0:
            n = (-n[0], -n[1])
        return (a[0] + n[0] * d, a[1] + n[1] * d), (dx / L, dy / L)

    @staticmethod
    def _schnitt(l1, l2):
        (p, u), (q, v) = l1, l2
        den = u[0] * v[1] - u[1] * v[0]
        t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / den
        return (p[0] + u[0] * t, p[1] + u[1] * t)

    def zone(self, d_ti: float):
        """Dreieck innerhalb der Falzstreifen und mit Abstand d_ti zur Außenkante."""
        d = self.falz + self.steg / 2
        lct = self._linie(self.C, self.T, d)
        lci = self._linie(self.C, self.I, d)
        lti = self._linie(self.T, self.I, d_ti)
        return [self._schnitt(lct, lci), self._schnitt(lct, lti), self._schnitt(lti, lci)]

    def streifen(self, d0: float, d1: float):
        d = self.falz + self.steg / 2
        lct = self._linie(self.C, self.T, d)
        lci = self._linie(self.C, self.I, d)
        a = self._linie(self.T, self.I, d0)
        b = self._linie(self.T, self.I, d1)
        return [self._schnitt(lct, a), self._schnitt(a, lci), self._schnitt(lci, b), self._schnitt(b, lct)]

    def ti_frame(self):
        e = ((self.I[0] - self.T[0]) / self.LTI, (self.I[1] - self.T[1]) / self.LTI)
        n = (-e[1], e[0])
        if n[0] * (self.C[0] - self.T[0]) + n[1] * (self.C[1] - self.T[1]) < 0:
            n = (-n[0], -n[1])
        return e, n

    def bisektor(self):
        u = (1.0, 0.0)
        v = (self.I[0] / self.LI, self.I[1] / self.LI)
        d = (u[0] + v[0], u[1] + v[1])
        L = math.hypot(*d)
        return d[0] / L, d[1] / L


# ---------- Stegmuster (kanonisch) ----------

def _gitter(g: Geo, sp: float):
    a = (sp, 0.0)
    b = (sp / 2, sp * math.sqrt(3) / 2)
    n = int(max(g.LT, g.I[1]) / sp) + 3
    out = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            p = (i * a[0] + j * b[0], i * a[1] + j * b[1])
            if -sp < p[0] < g.LT + sp and -sp < p[1] < g.I[1] + sp:
                out.append(p)
    return out


def _ring(fig, c, r, w, n=48):
    """Kreislinie als zwei offene Bögen (eine geschlossene Linie würde als volle Scheibe gefüllt)."""
    for a0 in (0.0, math.pi):
        fig.line([(c[0] + r * math.cos(a0 + math.pi * k / (n // 2) * 1.04 - 0.02),
                   c[1] + r * math.sin(a0 + math.pi * k / (n // 2) * 1.04 - 0.02)) for k in range(n // 2 + 1)], w)


def _feld_test(g: Geo):
    zone = g.zone(g.borte + g.steg)

    def ok(p):
        return S_.pip(p, zone) and math.hypot(*p) > g.rm + g.steg * 1.5
    return ok


def _lebensblume(g: Geo, seed: int = 0) -> List:
    """Blume des Lebens: Blütenblätter zwischen überlappenden Kreisen als Fenster."""
    ok = _feld_test(g)
    sp = max(10.0 * g.k, 7.5 * g.steg)
    L = sp - 2.6 * g.steg
    B = max(0.268 * sp - 0.5 * g.steg, 1.3 * g.steg)
    holes = []
    for p in _gitter(g, sp):
        for kk in range(3):
            a = kk * math.pi / 3
            c = (p[0] + math.cos(a) * sp / 2, p[1] + math.sin(a) * sp / 2)
            lf = S_.spitzblatt(c[0], c[1], L, B, a)
            if S_.innen(lf, ok):
                holes.append(lf)
    return holes


def _sternmosaik(g: Geo, seed: int = 0) -> List:
    """Sechsstern-Mosaik: Sterne im Dreiecksgitter, dazwischen Rauten und Perlen."""
    ok = _feld_test(g)
    sp = max(12.0 * g.k, 8.0 * g.steg)
    holes = []
    ro = sp / 2 - g.steg * 0.7
    for p in _gitter(g, sp):
        st = S_.stern(p[0], p[1], ro, ro * 0.52, 6, 0.0)
        if S_.innen(st, ok):
            holes.append(st)
    h = sp * math.sqrt(3) / 2
    rp = max(0.9 * g.steg, sp * 0.09)
    for p in _gitter(g, sp):
        for c in ((p[0] + sp / 2, p[1] + h / 3), (p[0], p[1] + 2 * h / 3)):
            ring = S_.kreis(c[0], c[1], rp, 14)
            if S_.innen(ring, ok):
                holes.append(ring)
    return holes


def _eisfeder(g: Geo, fig):
    d = g.bisektor()
    nrm = (-d[1], d[0])
    fig.line([(0, 0), (d[0] * g.LT, d[1] * g.LT)], g.steg)
    s = g.rm + 3 * g.k
    step = max(9.5 * g.k, 6.5 * g.steg)
    while s < g.LT:
        for sg in (1, -1):
            dd = (d[0] * math.cos(0.663) + sg * nrm[0] * math.sin(0.663), d[1] * math.cos(0.663) + sg * nrm[1] * math.sin(0.663))
            p = (d[0] * s, d[1] * s)
            fig.line([p, (p[0] + dd[0] * 60 * g.k, p[1] + dd[1] * 60 * g.k)], g.steg)
            for f in (0.35, 0.65):
                q = (p[0] + dd[0] * 26 * g.k * f, p[1] + dd[1] * 26 * g.k * f)
                d2 = (d[0] * math.cos(0.17) + sg * nrm[0] * math.sin(0.17), d[1] * math.cos(0.17) + sg * nrm[1] * math.sin(0.17))
                fig.line([q, (q[0] + d2[0] * 6.5 * g.k, q[1] + d2[1] * 6.5 * g.k)], g.steg)
        s += step


def _borte(g: Geo, fig):
    e, n = g.ti_frame()
    T = g.T
    L = g.LTI
    r0 = g.rand + g.bw
    fig.line([(T[0] + n[0] * r0 - e[0] * 30, T[1] + n[1] * r0 - e[1] * 30),
              (T[0] + n[0] * r0 + e[0] * (L + 30), T[1] + n[1] * r0 + e[1] * (L + 30))], g.steg)
    pitch = max(2.6, g.steg * 2.3)
    t = 2.0
    while t < L:
        q = (T[0] + e[0] * t, T[1] + e[1] * t)
        fig.line([q, (q[0] + n[0] * r0, q[1] + n[1] * r0)], g.steg)
        t += pitch
    amp = g.wel * 0.28
    wave = []
    steps = int((L + 20) / 0.6)
    for k in range(steps + 1):
        t = -10 + k * 0.6
        off = r0 + g.wel + amp * math.sin(t / pitch * math.pi)
        wave.append((T[0] + e[0] * t + n[0] * off, T[1] + e[1] * t + n[1] * off))
    fig.line(wave, g.steg)
    t = pitch / 2
    while t < L:
        q = (T[0] + e[0] * t + n[0] * r0, T[1] + e[1] * t + n[1] * r0)
        off = g.wel + amp * math.sin(t / pitch * math.pi)
        fig.line([q, (q[0] + n[0] * off, q[1] + n[1] * off)], g.steg)
        t += pitch


def _schneeflocken(g: Geo, seed: int = 11) -> List:
    rnd = S_.zufall(seed, "flocken")
    zone = g.zone(g.borte + g.steg)
    e, n = g.ti_frame()
    holes, belegt = [], []

    def ok(p):
        return S_.pip(p, zone) and math.hypot(*p) > g.rm + g.steg * 1.5

    rmin = max(3.4 * g.k, g.steg * 2.6)
    for _ in range(5000):
        x = rnd.uniform(0, g.LT)
        y = rnd.uniform(0, g.I[1])
        R0 = rnd.uniform(rmin, max(rmin * 1.2, 8.5 * g.k))
        rot = rnd.uniform(0, math.pi)
        bound = S_.kreis(x, y, R0 + 0.4, 12)
        if not S_.innen(bound, ok) or not S_.abstand_frei((x, y), R0, belegt, g.steg * 1.2):
            continue
        holes += S_.schneeflocke(x, y, R0, rot, g.steg)
        belegt.append((x, y, R0))
    return holes


STEGMUSTER = dict(eisfeder=_eisfeder)
LOCHMUSTER = dict(lebensblume=_lebensblume, sternmosaik=_sternmosaik, schneeflocken=lambda g: _schneeflocken(g))


def _affin(src, dst):
    (c0, t0, i0), (c1, t1, i1) = src, dst
    ax, ay = t0[0] - c0[0], t0[1] - c0[1]
    bx, by = i0[0] - c0[0], i0[1] - c0[1]
    det = ax * by - ay * bx
    ux, uy = t1[0] - c1[0], t1[1] - c1[1]
    vx, vy = i1[0] - c1[0], i1[1] - c1[1]

    def f(pts):
        out = []
        for x, y in pts:
            px, py = x - c0[0], y - c0[1]
            s = (px * by - py * bx) / det
            t = (ax * py - ay * px) / det
            out.append((c1[0] + s * ux + t * vx, c1[1] + s * uy + t * vy))
        return out
    return f


def _haelfte(cfg, name: str, g: Geo, muster: str, rueck: bool, notes) -> object:
    # Fächer der zehn Flächen, Spalt in einem Tal unten
    a0 = -math.pi / 2 + 5 * g.ang
    pts = []
    for j in range(11):
        L = g.LI if j % 2 == 0 else g.LT
        pts.append((L * math.cos(a0 - j * g.ang), L * math.sin(a0 - j * g.ang)))
    C = (0.0, 0.0)
    abb = []
    for j in range(10):
        A, B = pts[j], pts[j + 1]
        T, I = (B, A) if j % 2 == 0 else (A, B)
        abb.append(_affin((g.C, g.T, g.I), (C, T, I)))
    umriss = [[C, pts[j], pts[j + 1]] for j in range(10)]
    # Verschlusslasche am Spalt
    p = pts[10]
    L = math.hypot(*p)
    e = (p[0] / L, p[1] / L)
    n = (e[1], -e[0])
    if n[0] * (pts[9][0] - p[0]) + n[1] * (pts[9][1] - p[1]) > 0:
        n = (-n[0], -n[1])
    lw_ = 6.0 * max(1.0, g.k)
    s0 = g.rm * 0.5
    umriss.append([(e[0] * s0, e[1] * s0), (e[0] * (L - 8), e[1] * (L - 8)),
                   (e[0] * (L - 12) + n[0] * lw_, e[1] * (L - 12) + n[1] * lw_),
                   (e[0] * (s0 + 4) + n[0] * lw_, e[1] * (s0 + 4) + n[1] * lw_)])
    if not rueck:                                       # Klebelaschen an den Außenkanten
        for j in range(10):
            A, B = pts[j], pts[j + 1]
            l = math.hypot(B[0] - A[0], B[1] - A[1])
            e2 = ((B[0] - A[0]) / l, (B[1] - A[1]) / l)
            n2 = (e2[1], -e2[0])
            if n2[0] * (C[0] - A[0]) + n2[1] * (C[1] - A[1]) > 0:
                n2 = (-n2[0], -n2[1])
            umriss.append([(A[0] + e2[0] * 3, A[1] + e2[1] * 3), (B[0] - e2[0] * 3, B[1] - e2[1] * 3),
                           (B[0] - e2[0] * 8 + n2[0] * lw_, B[1] - e2[1] * 8 + n2[1] * lw_),
                           (A[0] + e2[0] * 8 + n2[0] * lw_, A[1] + e2[1] * 8 + n2[1] * lw_)])
    # kanonische Bausteine
    zone = g.zone(g.rand)
    feld_kan = g.zone(g.borte + g.steg / 2)
    streifen = g.streifen(g.rand, g.borte)
    fig_kan = K.Figur()
    borte_kan = K.Figur()
    _borte(g, borte_kan)
    loch_kan = []
    if muster in STEGMUSTER:
        STEGMUSTER[muster](g, fig_kan)
    else:
        loch_kan = LOCHMUSTER[muster](g)
    if not rueck:
        d = g.bisektor()
        L0, B0 = 13.0 * g.k, max(4.6 * g.k, 1.4 * g.steg)
        loch_kan.append(S_.linse(d[0] * 14.5 * g.k, d[1] * 14.5 * g.k, L0, B0, math.atan2(d[1], d[0]), spitz=0.0))
    feld, borte, stege, bstege, loecher = [], [], K.Figur(), K.Figur(), []
    for f in abb:
        feld.append(f(feld_kan))
        borte.append(f(streifen))
        for s, poly in fig_kan.ops:
            stege.ops.append((s, f(poly)))
        for s, poly in borte_kan.ops:
            bstege.ops.append((s, f(poly)))
        loecher += [f(h) for h in loch_kan]
    x0 = min(q[0] for poly in umriss for q in poly)
    x1 = max(q[0] for poly in umriss for q in poly)
    y0 = min(q[1] for poly in umriss for q in poly)
    y1 = max(q[1] for poly in umriss for q in poly)
    px = W.px_fuer(max(x1 - x0, y1 - y0))
    lw = E.Leinwand((x0 - 3, y0 - 3, x1 + 3, y1 + 3), px)
    mat = lw.flaechen(umriss)
    scheibe = lw.flaechen([S_.kreis(0, 0, g.rm + g.steg / 2, 96)])
    fb = E._and(lw.flaechen(borte), lw.flaechen([f(zone) for f in abb]))
    mat = E._andnot(mat, fb).union(E._and(lw.figur(bstege), fb))
    if muster in STEGMUSTER:
        ff = E._andnot(lw.flaechen(feld), scheibe)
        mat = E._andnot(mat, ff).union(E._and(lw.figur(stege), ff))
    mat = E._andnot(mat, lw.flaechen(loecher))
    if rueck:
        mat = E._andnot(mat, lw.flaechen([S_.kreis(0, 0, g.rm - 6 * g.k, 96)]))
    part = E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes)
    # Falzlinien als Gravur (Berg durchgezogen, Tal gestrichelt)
    from models import _deko as dk
    cv = dk.Canvas(part, margin=0.2)
    r_in = g.rm - 6 * g.k + 1.5 if rueck else 1.0
    for j in range(1, 11):
        q = pts[j]
        L = math.hypot(*q)
        u = (q[0] / L, q[1] / L)
        tal = (j % 2 == 0) or j == 10
        if not tal:
            cv.draw([(u[0] * r_in, u[1] * r_in), q])
        else:
            s = r_in
            while s < L:
                cv.draw([(u[0] * s, u[1] * s), (u[0] * min(L, s + 4), u[1] * min(L, s + 4))])
                s += 6.5
    if not rueck:
        for j in range(10):
            cv.draw([pts[j], pts[j + 1]])
    return part


def build(cfg, name: str = "papierstern", groesse: float = 280.0, muster: str = "lebensblume",
          tiefe: str = "mittel", teile: str = "beide"):
    if muster not in dict(MUSTER):
        raise ValueError(f"Unbekanntes Muster {muster!r}")
    if tiefe not in _H:
        raise ValueError(f"Unbekannte Tiefe {tiefe!r}")
    D = cfg.s(groesse)
    g = Geo(cfg, D, tiefe)
    if g.rm < 6 * g.steg:
        raise ValueError("Für dieses Material ist der Stern zu klein – Durchmesser vergrößern")
    asm = Assembly(name, params=dict(groesse=D, muster=muster, tiefe=tiefe, teile=teile))
    notes: List[str] = []
    asm.parts.append(_haelfte(cfg, "vorne", g, muster, False, notes))
    if teile == "beide":
        asm.parts.append(_haelfte(cfg, "hinten", g, muster, True, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Gravurlinien sind Falzlinien: in XCS als „Ritzen“ mit wenig Leistung lasern. "
                     "Durchgezogen = Bergfalte (Spitze nach vorn), gestrichelt = Talfalte.")
    asm.notes.append("Jede Hälfte zur Spitze auffalten und mit der Lasche am Spalt schließen. Dann die "
                     "Vorderseite mit ihren zehn Laschen auf die Rückseite kleben.")
    asm.notes.append("Licht: LED-Kugel oder Lichterkette durch die Öffnung in der Rückseite – keine Kerze.")
    if cfg.T > 1.0:
        asm.notes.append(f"Tipp: Der Papierstern ist für Karton gedacht (0,5 mm, Kerf ca. 0,1, Mindeststeg 0,6) – "
                         f"eingestellt sind {cfg.T:g} mm.")
    return asm
