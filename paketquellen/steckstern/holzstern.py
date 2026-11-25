"""
Holzstern – zwei sechszackige Sternplatten, über Kreuz gesteckt.

Platte A hat den Schlitz unten, Platte B oben. Jede Platte trägt ein Filigran aus vier Mustern
(Eiskristall, Winterranke, Perlenspitze, Sternennacht), auf Wunsch von Zacke zu Zacke im Wechsel.
In der Mitte sitzt eine Rosette mit gravierten Ringen. Ausgelegt für 3–4 mm Sperrholz: kräftige
Schnitte, die Feinheit kommt aus der Gravur.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, JointFeature, Part, offset_polygon, oriented
from pakete import flag, num, sel

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

MUSTER = [("eiskristall", "Eiskristall"), ("ranke", "Winterranke"), ("perlen", "Perlenspitze"),
          ("sternennacht", "Sternennacht")]

INFO = dict(
    label="Holzstern",
    group="Steckstern",
    desc="Räumlicher Stern aus zwei sechszackigen Holzplatten, über Kreuz gesteckt – mit Filigran "
         "aus Eiskristall, Winterranke, Perlenspitze oder Sternennacht und gravierter Rosette.",
    params=[
        num("groesse", "Höhe", 280, 140, 420),
        sel("muster_a", "Muster Platte A", MUSTER, "eiskristall"),
        sel("muster_b", "Muster Platte B", MUSTER, "eiskristall"),
        flag("wechsel", "Muster von Zacke zu Zacke wechseln", False,
             help="Jede Platte zeigt dann abwechselnd Muster A und Muster B"),
        flag("gravur", "Zierlinien gravieren", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Holzstern": "Wooden star", "Steckstern": "Slot-together star",
    "Räumlicher Stern aus zwei sechszackigen Holzplatten, über Kreuz gesteckt – mit Filigran "
    "aus Eiskristall, Winterranke, Perlenspitze oder Sternennacht und gravierter Rosette.":
        "3D star made of two six-pointed wooden plates slotted crosswise – with filigree of ice crystal, "
        "winter vine, pearl lace or starry night and an engraved rosette.",
    "Höhe": "Height", "Muster Platte A": "Pattern plate A", "Muster Platte B": "Pattern plate B",
    "Muster von Zacke zu Zacke wechseln": "Alternate patterns from point to point",
    "Jede Platte zeigt dann abwechselnd Muster A und Muster B": "Each plate then alternates pattern A and pattern B",
    "Zierlinien gravieren": "Engrave decorative lines", "Eiskristall": "Ice crystal", "Winterranke": "Winter vine",
    "Perlenspitze": "Pearl lace", "Sternennacht": "Starry night",
    "Platte B (Schlitz oben) von oben auf Platte A (Schlitz unten) schieben, bis beide Mitten bündig sind.":
        "Slide plate B (slot at the top) down onto plate A (slot at the bottom) until both centres are flush.",
    "Aufhängen: Faden durch das Loch in der oberen Spitze von Platte A.":
        "To hang: thread a string through the hole in the top point of plate A.",
}}

NP = 6


class Stern:
    """Maße eines Sterns der Höhe S für Material T."""

    def __init__(self, cfg, S: float):
        self.R = S / 2
        self.r = self.R * 0.5
        self.k = S / 280.0
        T = cfg.T
        self.steg = max(cfg.min_web + cfg.kerf + 0.6, 0.65 * T, 1.6)
        self.rand = max(1.5 * self.steg, 3.0 * self.k)
        self.rc = self.r * 0.46
        self.band = T / 2 + self.steg
        self.T = T

    def umriss(self) -> List:
        return [((self.R if i % 2 == 0 else self.r) * math.cos(math.pi / 2 + i * math.pi / NP),
                 (self.R if i % 2 == 0 else self.r) * math.sin(math.pi / 2 + i * math.pi / NP)) for i in range(2 * NP)]

    def innen(self):
        return oriented(offset_polygon(oriented(self.umriss(), True), -self.rand), True)

    def zone_test(self, vertikal: bool):
        """Prüft im lokalen Sektor (Zacke nach +y), ob ein Punkt frei für ein Fenster ist."""
        inn = self.innen()
        half = math.pi / NP
        a = (0.0, 0.0)
        bl = (2 * self.R * math.sin(-half), 2 * self.R * math.cos(half))
        br = (2 * self.R * math.sin(half), 2 * self.R * math.cos(half))
        st, rc, band = self.steg, self.rc, self.band

        def ok(p):
            if not S_.pip(p, inn):
                return False
            if math.hypot(*p) < rc + st:
                return False
            if S_.gerade_dist(p, a, bl) < st / 2 + 0.3 or S_.gerade_dist(p, a, br) < st / 2 + 0.3:
                return False
            ang = math.atan2(p[0], p[1])
            if abs(ang) > half:
                return False
            if vertikal and abs(p[0]) < band + 0.3:
                return False
            return True
        return ok

    def breite(self, y: float) -> float:
        """halbe Breite des Sektors in Höhe y (lokal)"""
        hw = y * math.tan(math.pi / NP)
        y_base = self.r * math.cos(math.pi / NP)
        if y > y_base:
            Hp = self.R - y_base
            hw = min(hw, self.r * math.sin(math.pi / NP) * max(0.0, 1 - (y - y_base) / Hp))
        return max(0.0, hw - self.rand)


# ---------- Muster (lokal: Zacke nach +y) ----------

def _eiskristall(st: Stern, fig, ok, seed):
    k, R, rc = st.k, st.R, st.rc
    fig.line([(0, rc), (0, R)], st.steg)
    y = rc + 2 * k
    while y < R * 0.9:
        for sx in (1, -1):
            fig.line([(0, y), (sx * R * 0.5, y + R * 0.4)], st.steg)
        y += 15 * k
    for sx in (1, -1):
        fig.line([(sx * 30 * k, rc), (sx * 4 * k, R * 0.92)], st.steg)
    return []


def _ranke(st: Stern, fig, ok, seed):
    k, R, rc, steg = st.k, st.R, st.rc, st.steg
    holes, belegt = [], []
    vine = lambda y: 3.0 * k * math.sin((y - rc) / (16 * k))
    y = rc + 5 * k
    n = 0
    while y < R - 8 * k:
        for sx in ((1, -1) if n % 2 == 0 else (-1, 1)):
            L = min(13 * k + 0.75 * st.breite(y + 6 * k), 30 * k)
            while L >= 3.2 * steg:
                B = max(L * 0.42, 2 * steg)
                c = (vine(y) + sx * (L * 0.40 + 2.6 * k), y + L * 0.26)
                lf = S_.linse(c[0], c[1], L, B, sx * math.radians(42))
                if S_.innen(lf, ok) and S_.abstand_frei(c, L / 2, belegt, steg * 0.3):
                    holes.append(lf)
                    belegt.append((c[0], c[1], L / 2))
                    break
                L *= 0.86
        for dx, dy in ((0, 0), (3.1, 4.6), (-3.1, 4.6)):
            c = (vine(y + 9 * k) + dx * k, y + 9 * k + dy * k)
            rr = max(1.9 * k, steg * 0.75)
            ring = S_.kreis(c[0], c[1], rr, 16)
            if S_.innen(ring, ok) and S_.abstand_frei(c, rr, belegt, steg):
                holes.append(ring)
                belegt.append((c[0], c[1], rr))
        y += 17 * k
        n += 1
    return holes


def _perlen(st: Stern, fig, ok, seed):
    k, R, rc, steg = st.k, st.R, st.rc, st.steg
    holes = []
    y, row = rc + 5 * k, 0
    while y < R:
        t = (y - rc) / (R - rc)
        d = max(1.25 * steg + 0.8, 10.5 * k * (1 - t) ** 0.75)
        pitch = d + steg
        off = 0 if row % 2 == 0 else pitch / 2
        for j in range(-30, 31):
            c = S_.kreis(j * pitch + off, y, d / 2, 24)
            if S_.innen(c, ok):
                holes.append(c)
        y += pitch * 0.87
        row += 1
    return holes


def _sternennacht(st: Stern, fig, ok, seed):
    k, R, rc, steg = st.k, st.R, st.rc, st.steg
    rnd = S_.zufall(seed, "nacht")
    holes, belegt = [], []
    for xo in (0, 10, -10, 16, -16):
        m = S_.mond(xo * k, rc + 22 * k, 11 * k)
        if S_.innen(m, ok):
            holes.append(m)
            belegt.append((xo * k, rc + 22 * k, 11 * k))
            break
    for _ in range(900):
        y = rnd.uniform(rc, R * 0.9)
        hw = st.breite(y)
        if hw < 4 * k:
            continue
        x = rnd.uniform(-hw, hw)
        s = rnd.uniform(5.5, 10) * k * (1 - 0.45 * (y - rc) / (R - rc))
        if s < 2.2 * steg:
            continue
        p = S_.stern(x, y, s, s * 0.56, 5, rnd.uniform(-0.4, 0.4))
        if S_.innen(p, ok) and S_.abstand_frei((x, y), s, belegt, steg * 0.6):
            holes.append(p)
            belegt.append((x, y, s))
    return holes


def _staub(st: Stern, ok, seed) -> List:
    rnd = S_.zufall(seed, "staub")
    out = []
    for _ in range(140):
        y = rnd.uniform(st.rc, st.R * 0.95)
        hw = st.breite(y)
        if hw < 2:
            continue
        p = (rnd.uniform(-hw, hw), y)
        if ok(p):
            out.append(S_.kreis(p[0], p[1], rnd.uniform(0.4, 0.9) * st.k, 8))
    return out


MUSTERFN = dict(eiskristall=_eiskristall, ranke=_ranke, perlen=_perlen, sternennacht=_sternennacht)


def _platte(cfg, name: str, st: Stern, muster: List[str], schlitz_oben: bool, gravur: bool, notes) -> Part:
    fig = S_.K.Figur()
    holes, gravuren, keile = [], [], []
    for i in range(NP):
        m = muster[i % len(muster)]
        if m == "eiskristall":
            a0 = math.pi / 2 + (i - 0.5) * 2 * math.pi / NP
            a1 = math.pi / 2 + (i + 0.5) * 2 * math.pi / NP
            keile.append([(0, 0)] + [(3 * st.R * math.cos(a0 + (a1 - a0) * t / 8), 3 * st.R * math.sin(a0 + (a1 - a0) * t / 8))
                                     for t in range(9)])
        vertikal = i in (0, 3)
        ok = st.zone_test(vertikal)
        lok = S_.K.Figur()
        hl = MUSTERFN[m](st, lok, ok, 7 + i)
        rot = i * 2 * math.pi / NP
        for s, poly in lok.ops:
            fig.ops.append((s, S_.drehen(poly, rot)))
        holes += [S_.drehen(h, rot) for h in hl]
        if gravur and m == "sternennacht":
            gravuren += [(S_.drehen(c, rot), True) for c in _staub(st, ok, 3 + i)]
        if gravur and m == "ranke":
            vine = [(3.0 * st.k * math.sin((y - st.rc) / (16 * st.k)), y)
                    for y in [st.rc + 2 + j * (st.R - 14 * st.k - st.rc) / 80 for j in range(81)]]
            gravuren.append((S_.drehen(vine, rot), False))
    # Sektorgrenzen als Stege
    for i in range(NP):
        a = math.pi / 2 + (i + 0.5) * 2 * math.pi / NP
        fig.line([(0, 0), (2 * st.R * math.cos(a), 2 * st.R * math.sin(a))], st.steg)
    # Rosette: zwölf Blätter und sechs Perlen, frei vom Schlitzband
    for j in range(12):
        a = math.radians(j * 30 + 15)
        c = (st.rc * 0.62 * math.cos(a), st.rc * 0.62 * math.sin(a))
        L, B = 13 * st.k, max(5.6 * st.k, 1.25 * st.steg + 0.6)
        lf = S_.linse(c[0], c[1], L, B, a, spitz=0.0)
        if min(abs(x) for x, _ in lf) > st.band + 0.3:
            holes.append(lf)
    umriss = st.umriss()
    feld = [st.innen()]
    minus = [S_.kreis(0, 0, st.rc, 64), K.rect(-st.band, -st.R - 5, 2 * st.band, 2 * st.R + 10)]
    if not schlitz_oben:
        rr = max(2.2, st.T * 0.55)
        holes.append(S_.kreis(0, st.R - 4 * st.steg - rr, rr, 24))
    px = W.px_fuer(2 * st.R)
    lw = E.Leinwand((-st.R - 4, -st.R - 4, st.R + 4, st.R + 4), px)
    mat = lw.flaechen([umriss])
    if keile:
        f = E._andnot(E._and(lw.flaechen(feld), lw.flaechen(keile)), lw.flaechen(minus))
        mat = E._andnot(mat, f).union(E._and(lw.figur(fig), f))
    mat = E._andnot(mat, lw.flaechen(holes))
    part = E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes)
    items = []
    if gravur:
        rand = oriented(offset_polygon(oriented(umriss, True), -max(1.2, st.rand * 0.45)), True)
        items.append((rand, True))
        for r in (st.rc - 1.4, 6.5 * st.k):
            items.append((S_.kreis(0, 0, r, 96), True))
        items += gravuren
    return part, items


def _gravieren(part: Part, items) -> None:
    from models import _deko as dk
    cv = dk.Canvas(part, margin=0.5)
    for pts, closed in items:
        cv.draw(pts, closed)


def build(cfg, name: str = "holzstern", groesse: float = 280.0, muster_a: str = "eiskristall",
          muster_b: str = "eiskristall", wechsel: bool = False, gravur: bool = True):
    from models._shapes import cut_axis_slot
    for m in (muster_a, muster_b):
        if m not in MUSTERFN:
            raise ValueError(f"Unbekanntes Muster {m!r}")
    S = cfg.s(groesse)
    st = Stern(cfg, S)
    if st.rc < st.band + 6 * st.steg:
        raise ValueError("Für dieses Material ist der Stern zu klein – Höhe vergrößern")
    asm = Assembly(name, params=dict(groesse=S, muster_a=muster_a, muster_b=muster_b, wechsel=wechsel))
    notes: List[str] = []
    T = cfg.T
    for tag, m, oben in (("platte_a", muster_a, False), ("platte_b", muster_b, True)):
        muster = [m, muster_b if m == muster_a else muster_a] if wechsel else [m]
        p, items = _platte(cfg, tag, st, muster, oben, gravur, notes)
        out, slot = cut_axis_slot(p.outline, T, 0.0, oben)
        ys = [q[1] for q in p.outline]
        span = (0.0, max(ys)) if oben else (min(ys), 0.0)
        q = Part(p.name, out, features=[JointFeature("kreuz", "halving", span[1] - span[0], T, span=span,
                                                     points=slot)])
        for h in p.holes:
            q.add_hole(h)
        _gravieren(q, items)
        asm.parts.append(q)
    asm.connect("platte_a:kreuz", "platte_b:kreuz")
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Platte B (Schlitz oben) von oben auf Platte A (Schlitz unten) schieben, bis beide Mitten bündig sind.")
    asm.notes.append("Aufhängen: Faden durch das Loch in der oberen Spitze von Platte A.")
    return asm
