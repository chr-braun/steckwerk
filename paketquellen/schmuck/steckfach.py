"""
Christbaumschmuck mit Steckfach – Anhänger mit verstecktem Fach für einen gefalteten Geldschein oder eine
Gutscheinkarte.

Drei Lagen, deckungsgleich verleimt:
  • Vorderseite: Spitzenrand mit Filigran-Durchbrüchen (bzw. Geschenkpapier mit Sternfenstern), in der Mitte
    fein graviert mit Widmung in Schreibschrift, Perlenrand, Stern und Stechpalme.
  • Fachrahmen: liegt in der Mitte, das Fach ist oben offen. Durch die Spitze der Vorderseite sieht man ihn –
    in einer dunkleren Holzart wirkt das wie eine Intarsie.
  • Rückseite: geschlossen, mit graviertem Gruß.
Das Band läuft durch die Ösen von Vorder- und Rückseite und verschließt dabei das Fach.

Die Größe richtet sich nach der Einlage: Das Fach bekommt ringsum Spiel, und der Rahmen bleibt überall
mindestens so breit wie der Spitzenrand, damit durch die Durchbrüche nie etwas vom Inhalt zu sehen ist.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Optional, Tuple

from steckwerk import Assembly, oriented, signed_area
from pakete import bibliothek, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_schmuck_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


E = bibliothek("verzierungen").E
W = bibliothek("verzierungen").W
K = E.K
Figur = K.Figur
NA = _sub("_namen")
FG = NA.FG
SS = _sub("_schreibschrift")
CB = _sub("christbaumschmuck")
Poly = List[Tuple[float, float]]
TAU = 2 * math.pi

FORMEN = [("kugel", "Christbaumkugel"), ("haus", "Lebkuchenhaus"), ("geschenk", "Geschenkpäckchen")]
AUSWAHL = FORMEN + [("alle", "alle drei (Set)")]
EINLAGEN = [("schein", "Geldschein, zweimal gefaltet"), ("karte", "Gutscheinkarte (Scheckkartenformat)"),
            ("eigen", "eigenes Maß")]
# Einlage in mm (Breite × Höhe, liegend). Euro-Scheine bis 200 € (153 × 82 mm), einmal längs und einmal quer
# gefaltet: höchstens 76,5 × 41 mm. Gutscheinkarten haben das Scheckkartenformat ID-1 (85,6 × 54 mm).
EINLAGE_MASS = {"schein": (77.0, 41.0), "karte": (85.6, 54.0)}
EINLAGE_TEXT = {"schein": "einen zweimal gefalteten Geldschein (5 bis 200 €)",
                "karte": "eine Gutscheinkarte im Scheckkartenformat (85,6 × 54 mm)",
                "eigen": "deine Einlage"}
RAHMEN = NA.RAHMEN

INFO = dict(
    label="Christbaumschmuck mit Steckfach",
    group="Schmuck",
    desc="Anhänger mit verstecktem Fach für einen gefalteten Geldschein oder eine Gutscheinkarte: Christbaumkugel, "
         "Lebkuchenhaus oder Geschenkpäckchen aus drei Lagen – Vorderseite mit Filigran-Spitze und fein gravierter "
         "Widmung, Fachrahmen in der Mitte, Rückseite mit Gruß. Das Band verschließt das Fach.",
    params=[
        sel("form", "Form", AUSWAHL, "kugel"),
        sel("einlage", "Einlage", EINLAGEN, "schein", section="Fach"),
        num("einlage_b", "Breite der Einlage", 77.0, 20.0, 160.0, step=0.5, when={"einlage": ["eigen"]}, section="Fach"),
        num("einlage_h", "Höhe der Einlage", 41.0, 20.0, 160.0, step=0.5, when={"einlage": ["eigen"]}, section="Fach"),
        num("spiel", "Spiel je Seite", 1.0, 0.3, 3.0, step=0.1, help="Luft zwischen Einlage und Fachrand", section="Fach"),
        num("rand", "Breite des Zierrands", 14.0, 9.0, 24.0, help="so breit bleibt der Rahmen ums Fach mindestens"),
        sel("rahmen", "Spitzenrand", RAHMEN, "bluetenkranz", when={"form": ["kugel", "alle"]}),
        txt("text", "Widmung vorne", "Für dich", maxlen=24, help="in Schreibschrift graviert, leer = nur Zier",
            section="Schrift und Beschriftung"),
        txt("gruss", "Gruß auf der Rückseite", "Frohe Weihnachten", maxlen=28, help="leer = keine Gravur",
            section="Schrift und Beschriftung"),
        sel("schrift", "Schreibschrift", SS.SCHRIFTEN, "schwungvoll", section="Schrift und Beschriftung"),
    ],
)

UEBERSETZUNG = {"en": {
    "Christbaumschmuck mit Steckfach": "Tree ornament with hidden pocket", "Weihnachten": "Christmas",
    "Anhänger mit verstecktem Fach für einen gefalteten Geldschein oder eine Gutscheinkarte: Christbaumkugel, "
    "Glocke, Herz oder Geschenkpäckchen aus drei Lagen – Vorderseite mit Filigran-Spitze und fein gravierter "
    "Widmung, Fachrahmen in der Mitte, Rückseite mit Gruß. Das Band verschließt das Fach.":
        "Ornament with a hidden pocket for a folded banknote or a gift card: bauble, gingerbread house or present made "
        "of three layers – front with filigree lace and a finely engraved dedication, pocket frame in the middle, "
        "back with a greeting. The ribbon closes the pocket.",
    "Form": "Shape", "Christbaumkugel": "Bauble", "Lebkuchenhaus": "Gingerbread house",
    "Geschenkpäckchen": "Present", "alle drei (Set)": "all three (set)",
    "Fach": "Pocket", "Einlage": "Insert", "Geldschein, zweimal gefaltet": "Banknote, folded twice",
    "Gutscheinkarte (Scheckkartenformat)": "Gift card (credit card size)", "eigenes Maß": "custom size",
    "Breite der Einlage": "Insert width", "Höhe der Einlage": "Insert height",
    "Spiel je Seite": "Clearance per side", "Luft zwischen Einlage und Fachrand": "gap between insert and pocket",
    "Breite des Zierrands": "Border width", "so breit bleibt der Rahmen ums Fach mindestens":
        "minimum frame width around the pocket",
    "Spitzenrand": "Lace border", "Widmung vorne": "Dedication (front)",
    "in Schreibschrift graviert, leer = nur Zier": "engraved in script, empty = ornament only",
    "Gruß auf der Rückseite": "Greeting on the back", "leer = keine Gravur": "empty = no engraving",
    "Schrift und Beschriftung": "Font and lettering", "Schreibschrift": "Script font",
    "Für dich": "For you", "Frohe Weihnachten": "Merry Christmas",
}}


# --------------------------------------------------------------------------------------------------
# Grundform
# --------------------------------------------------------------------------------------------------

class _Zier:
    """Sammelt für die Schleife des Geschenks Fenster und Gravuren (Schnittstelle wie CB.Motiv)."""

    def __init__(self):
        self.loch_extra: List[Poly] = []
        self.g: List[Tuple[Poly, bool]] = []

    def gr(self, pts, closed: bool = False) -> None:
        if len(pts) >= 2:
            self.g.append((list(pts), closed))


class Grund:
    """Umriss (CCW), Zusatz über dem Umriss (Krone, Schleife, Öse), Ösenloch und Fach."""

    def __init__(self, cfg, form: str, S: float, fach: Optional[Tuple[float, float, float]] = None,
                 rand: float = 10.0):
        self.cfg, self.form, self.S = cfg, form, S
        self.krone = None
        self.fm = None
        self.zier = _Zier()
        self.zier_fig = Figur()
        if form == "geschenk":
            self._geschenk(fach, rand)
        elif form == "haus":
            self._haus(fach, rand)
        else:
            fm = NA.Form(cfg, form, S)
            self.fm = fm
            self.umriss, self.extra, self.loch, self.yc = fm.umriss, list(fm.extra), fm.loch, fm.yc
            self.box = fm.box
        self.fach = fach

    def _geschenk(self, fach, rand: float) -> None:
        pw, ph, _ = fach
        cfg = self.cfg
        Wb = pw + 2 * rand
        Hb = ph + 2 * rand
        self.S = S = Hb
        ov = max(2.5, 0.035 * Wb)
        lh = min(max(0.17 * Hb, 9.0), 18.0)
        bw, lw_ = Wb / 2, Wb / 2 + ov
        pts = [(-bw, 0.0), (bw, 0.0), (bw, Hb - lh), (lw_, Hb - lh), (lw_, Hb), (-lw_, Hb), (-lw_, Hb - lh),
               (-bw, Hb - lh)]
        self.umriss = oriented(W.abrunden(pts, 1.2, 6), True)
        self.deckel = (Hb - lh, Hb, lw_)
        self.yc = Hb / 2
        # Schleife auf dem Deckel, Öse zwischen den Schlaufen
        b = min(0.62 * Wb, 2 * lw_ * 0.92)
        ky = Hb + 0.02 * b
        CB._schleife(self.zier, self.zier_fig, 0.0, ky, b)
        ro = max(3.4, 0.042 * S)
        oy = ky + 0.075 * b + ro - 1.0
        self.extra = [K.circle(0.0, oy, ro, 48)]
        self.loch = K.circle(0.0, oy, ro - max(cfg.min_web + 0.7, 1.5), 40)
        x0, y0, x1, y1 = Figur(list(self.zier_fig.ops)).bbox()
        self.box = (min(-lw_, x0) - 2, -2.0, max(lw_, x1) + 2, max(y1, oy + ro) + 2)

    def _haus(self, fach, rand: float) -> None:
        pw, ph, _ = fach
        cfg = self.cfg
        Wb = pw + 2 * rand
        Hb = ph + 2 * rand
        self.S = S = Hb
        bw = Wb / 2
        ov = max(3.0, 0.05 * Wb)                     # Dachüberstand
        rh = 0.42 * Wb                               # Dachhöhe über der Traufe
        ty = Hb - 0.5 * rand                         # Traufe sitzt etwas unter der Wandoberkante
        top = ty + rh * (bw + ov) / bw
        # Schornstein auf der rechten Dachseite
        sx0, sx1 = 0.38 * bw, 0.38 * bw + max(0.14 * Wb, 7.0)
        def dach_y(x):
            return top - (top - ty) * abs(x) / (bw + ov)
        sy1 = dach_y(sx0) + max(0.07 * Wb, 4.0)
        pts = [(-bw, 0.0), (bw, 0.0), (bw, ty), (bw + ov, ty), (sx1, dach_y(sx1)), (sx1, sy1), (sx0, sy1),
               (sx0, dach_y(sx0)), (0.0, top), (-bw - ov, ty), (-bw, ty)]
        self.umriss = oriented(W.abrunden(pts, 1.0, 6), True)
        self.dach = (ty, top, bw + ov, (sx0, sx1, sy1))
        self.yc = Hb / 2
        ro = max(3.4, 0.042 * S)
        oy = top + ro - 2.2
        self.extra = [K.circle(0.0, oy, ro, 48)]
        self.loch = K.circle(0.0, oy, ro - max(cfg.min_web + 0.7, 1.5), 40)
        self.box = (-bw - ov - 2, -2.0, bw + ov + 2, oy + ro + 2)

    def leinwand(self):
        x0, y0, x1, y1 = self.box
        return E.Leinwand(self.box, max(0.06, min(0.09, max(x1 - x0, y1 - y0) / 1300.0)))

    def silhouette(self, lw):
        r = lw.flaechen([self.umriss] + self.extra)
        if len(self.zier_fig.ops):
            r = r.union(lw.figur(self.zier_fig))
        return r

    def fach_rechteck(self) -> Poly:
        pw, ph, yp = self.fach
        return K.rect(-pw / 2, yp - ph / 2, pw, ph)

    def schlitz(self) -> Poly:
        """Fach plus Öffnung nach oben bis über den Anhänger hinaus."""
        pw, ph, yp = self.fach
        top = self.box[3] + 5.0
        z = 0.1                                               # gleicht das Runden im Raster aus (gemessen)
        return K.rect(-pw / 2 - z, yp - ph / 2 - z, pw + 2 * z, top - (yp - ph / 2) + z)

    def krone_gravieren(self, part) -> None:
        if self.fm is not None:
            self.fm.gravur_krone(part)


# --------------------------------------------------------------------------------------------------
# Größe aus der Einlage
# --------------------------------------------------------------------------------------------------

def _innen_pkt(poly: Poly, p) -> bool:
    x, y = p
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def _platz(umriss: Poly, pw: float, ph: float, d: float) -> Optional[Tuple[float, float]]:
    """Beste Höhe (Mitte) für ein Rechteck pw × ph mit Mindestabstand d zum Umriss → (Abstand, y) oder None."""
    dicht = K.resample(list(umriss) + [umriss[0]], 0.8)
    ys = [p[1] for p in umriss]
    lo, hi = min(ys) + ph / 2 + d, max(ys) - ph / 2 - d
    best = None
    y = lo
    while y <= hi + 1e-9:
        x0, x1, y0, y1 = -pw / 2, pw / 2, y - ph / 2, y + ph / 2
        if _innen_pkt(umriss, (0.0, y)):
            m = 1e9
            for qx, qy in dicht:
                dx = max(x0 - qx, 0.0, qx - x1)
                dy = max(y0 - qy, 0.0, qy - y1)
                if dx == 0.0 and dy == 0.0:
                    m = -1.0
                    break
                m = min(m, math.hypot(dx, dy))
            if m >= d and (best is None or m > best[0] + 1e-6):
                best = (m, y)
        y += 0.5
    return best


def _groesse(cfg, form: str, pw: float, ph: float, d: float) -> Tuple[float, float, float, float]:
    """Kleinste Höhe S, in die das Fach passt; probiert liegend und stehend → (S, pw, ph, y_fach)."""
    if form in ("geschenk", "haus"):
        f = 0.3 if form == "geschenk" else 0.45
        kand = []
        for a, b in ((pw, ph), (ph, pw)):
            kand.append((b + 2 * d + f * (a + 2 * d), a, b))    # Höhe mit Schleife, grob – für die Wahl
        _, a, b = min(kand, key=lambda k: (k[0], k[1]))
        return b + 2 * d, a, b, d + b / 2
    if form == "kugel":                                       # Kreis (Radius 0,45 S): Fach stehend, Mitte im Kreis
        a, b = min(pw, ph), max(pw, ph)
        S = math.ceil((math.hypot(a / 2, b / 2) + d + 0.4) / 0.45)
        return S, a, b, 0.0
    beste = None
    for a, b in ((pw, ph), (ph, pw)):
        def passt(S):
            return _platz(FG.form(form, S)[0], a, b, d)
        lo, hi = 50.0, 60.0
        while passt(hi) is None:
            lo, hi = hi, hi * 1.25
            if hi > 600:
                raise ValueError("Das Fach ist für diese Form zu groß")
        for _ in range(18):
            mid = (lo + hi) / 2
            if passt(mid) is None:
                lo = mid
            else:
                hi = mid
        S = math.ceil(hi + 0.5)
        y = passt(S)[1]
        if beste is None or S < beste[0] - 1.5 or (abs(S - beste[0]) <= 1.5 and a < beste[1]):
            beste = (S, a, b, y)
    return beste


# --------------------------------------------------------------------------------------------------
# Spitzenrand (wie beim Namensanhänger, Ränder für das schmale Band angepasst)
# --------------------------------------------------------------------------------------------------

def _spitze(cfg, g: Grund, lw, band: float, rahmen: str):
    web, kerf = cfg.min_web, cfg.kerf
    wmin = web + kerf + 0.45
    w = wmin + 0.25
    rand_a = max(2 * web + 0.8, 0.022 * g.S)
    rand_i = max(1.6 * web + 0.6, 0.016 * g.S)
    kr = g.form == "kugel"
    fenster = NA._innen(lw, g.umriss, band, kr)
    aussen_f = NA._innen(lw, g.umriss, rand_a, kr)
    innen_f = NA._innen(lw, g.umriss, band - rand_i, kr)
    yc = g.yc
    if kr:
        r_a = min(math.hypot(x, y - yc) for x, y in aussen_f)
        r_i = max(math.hypot(x, y - yc) for x, y in innen_f)
    else:
        r_i = min(math.hypot(x, y - yc) for x, y in innen_f)
        r_a = max(math.hypot(x, y - yc) for x, y in aussen_f)
    h = max(r_a - r_i, 3 * w)
    rm = (r_a + r_i) / 2
    bausteine = NA._REZEPT[rahmen]
    hz = h / len(bausteine)
    n = max(8, int(round(TAU * rm / (hz * 1.25) / 2)) * 2)
    M = FG.Muster(w, n, wmin=wmin, R=r_a)
    for i, art in enumerate(bausteine):
        a = r_i - 0.4 * w + hz * i
        b = r_i + hz * (i + 1) + (0.4 * w if i == len(bausteine) - 1 else 0.0)
        FG._baustein(M, art, a, b, 0.0 if i % 2 == 0 else math.pi / n)
        if i < len(bausteine) - 1:
            M.kreis(b, 0.9)
    fig = M.figur(0.0, yc)
    bandflaeche = E._andnot(lw.flaechen([aussen_f]), lw.flaechen([innen_f]))
    mat = E._andnot(g.silhouette(lw), bandflaeche)              # Außenrand, Mitte, Krone, Öse
    mat = mat.union(E._and(lw.figur(fig), bandflaeche))
    return mat, fenster


# --------------------------------------------------------------------------------------------------
# Gravuren
# --------------------------------------------------------------------------------------------------

def _stern_gravur(cx: float, cy: float, r: float) -> List[Tuple[Poly, bool]]:
    """Kleiner Facettenstern: Umriss, innerer Stern und Grate."""
    out = [(K.star(cx, cy, r, 0.42 * r, 5), True), (K.star(cx, cy, 0.55 * r, 0.23 * r, 5), True)]
    for i in range(5):
        a = math.pi / 2 + TAU * i / 5
        out.append(([(cx + math.cos(a) * 0.58 * r, cy + math.sin(a) * 0.58 * r),
                     (cx + math.cos(a) * 0.93 * r, cy + math.sin(a) * 0.93 * r)], False))
    return out


def _flocke_gravur(cx: float, cy: float, r: float, rot: float = 0.0) -> List[Tuple[Poly, bool]]:
    out = []
    for i in range(6):
        a = rot + TAU * i / 6
        ca, sa = math.cos(a), math.sin(a)
        out.append(([(cx, cy), (cx + ca * r, cy + sa * r)], False))
        for t, l in ((0.45, 0.32), (0.72, 0.22)):
            b = (cx + ca * r * t, cy + sa * r * t)
            for sd in (1, -1):
                a2 = a + sd * math.radians(55)
                out.append(([b, (b[0] + math.cos(a2) * r * l, b[1] + math.sin(a2) * r * l)], False))
    return out


def _stechpalme_gravur(cx: float, cy: float, L: float) -> List[Tuple[Poly, bool]]:
    """Zwei Stechpalmenblätter mit Rippen und drei Beeren als feine Gravur."""
    out = []
    for ang in (math.radians(200), math.radians(-20)):
        blatt = NA._stechpalme(cx, cy, L, ang)
        out.append((blatt, True))
        c, s = math.cos(ang), math.sin(ang)
        out.append(([(cx + 0.1 * L * c, cy + 0.1 * L * s), (cx + 0.85 * L * c, cy + 0.85 * L * s)], False))
        for t in (0.35, 0.55, 0.72):
            for sd in (1, -1):
                a = (cx + t * L * c, cy + t * L * s)
                out.append(([a, (a[0] + 0.09 * L * c - sd * 0.09 * L * s, a[1] + 0.09 * L * s + sd * 0.09 * L * c)],
                            False))
    rb = 0.13 * L
    for dx, dy in ((0.0, 0.10), (-0.14, -0.04), (0.14, -0.04)):
        bx, by = cx + dx * L, cy + dy * L
        out.append((K.circle(bx, by, rb, 16), True))
        out.append((K.circle(bx - 0.3 * rb, by + 0.3 * rb, 0.3 * rb, 10), True))
    return out


def _feld_bereich(feld: Poly) -> Tuple[float, float]:
    ys = [p[1] for p in feld]
    return min(ys), max(ys)


def _widmung(feld: Poly, text: str, schrift: str, mitte: float, h_max: float, rand: float):
    s = SS.Satz(text, schrift)
    k = NA._einpassen(s, mitte, feld, h_max, rand)
    if k * SS.schrift(schrift)["x"] < 1.8:
        raise ValueError(f"„{text}“ passt nicht auf den Anhänger – kürzer fassen")
    return s.in_mm((0.0, mitte), k), s.hoehe * k


def _mitte_gravur(g: Grund, lw, feld_aussen: Poly, text: str, schrift: str):
    """Gravuren für die geschlossene Mitte: doppelte Linie, Perlenrand, Stern, Widmung, Stechpalme."""
    gr: List[Tuple[Poly, bool]] = []
    kr = g.form == "kugel"
    l1 = NA._innen(lw, feld_aussen, 1.0, kr)
    l2 = NA._innen(lw, feld_aussen, 1.9, kr)
    gr += [(l1, True), (l2, True)]
    perl = NA._innen(lw, feld_aussen, 3.3, kr)
    for q in K.resample(list(perl) + [perl[0]], 1.7)[:-1]:
        gr.append((K.circle(q[0], q[1], 0.42, 10), True))
    feld = NA._innen(lw, feld_aussen, 4.6, kr)
    y0, y1 = _feld_bereich(feld)
    H = y1 - y0
    pw, ph, yp = g.fach
    mitte = min(max(yp, y0 + 0.42 * H), y1 - 0.42 * H)
    text_polys = []
    th = 0.0
    if text:
        text_polys, th = _widmung(feld, text, schrift, mitte, min(0.21 * H, 0.30 * ph + 3), 2.5)
    else:
        th = 0.12 * H
    # Stern darüber, Stechpalme darunter – Größe nach dem freien Platz
    frei_o = y1 - (mitte + th / 2)
    frei_u = (mitte - th / 2) - y0
    rs = min(0.34 * frei_o, 0.13 * H, 11.0)
    if rs >= 2.5:
        sy = mitte + th / 2 + 0.55 * frei_o
        hb = NA._halbbreite(feld, sy - rs, sy + rs)
        rs = min(rs, hb * 0.8)
        if rs >= 2.5:
            gr += _stern_gravur(0.0, sy, rs)
            for sd in (1, -1):
                for k, (f, rr) in enumerate(((2.2, 0.32), (3.3, 0.22))):
                    fx = sd * rs * f
                    if NA._halbbreite(feld, sy - rr * rs, sy + rr * rs) > abs(fx) + rr * rs + 0.5:
                        gr += _flocke_gravur(fx, sy - 0.2 * rs * k, rr * rs, 0.3 * k)
    L = min(0.40 * frei_u, 0.20 * H, 19.0)
    if L >= 4.0:
        hy = mitte - th / 2 - 0.30 * frei_u
        hb = NA._halbbreite(feld, hy - 0.5 * L, hy + 0.3 * L)
        L = min(L, hb * 0.95)
        if L >= 4.0:
            gr += _stechpalme_gravur(0.0, hy, L)
    return gr, text_polys


def _rueckseite_gravur(g: Grund, lw, gruss: str, schrift: str):
    gr: List[Tuple[Poly, bool]] = []
    kr = g.form == "kugel"
    rand = 2.4
    if kr:                                                    # eckige Formen: Versatzlinie hätte Schleifen
        gr.append((NA._innen(lw, g.umriss, rand, kr), True))
    if not gruss:
        return gr, []
    feld = NA._innen(lw, g.umriss, max(7.0, 0.07 * g.S), kr)
    y0, y1 = _feld_bereich(feld)
    pw, ph, yp = g.fach
    mitte = min(max(yp, y0 + 0.2 * (y1 - y0)), y1 - 0.2 * (y1 - y0))
    worte = gruss.split()
    s1 = SS.Satz(gruss, schrift)
    h1 = min(0.16 * g.S, 12.0)
    k1 = NA._einpassen(s1, mitte, feld, h1, 1.5)
    x_mm = SS.schrift(schrift)["x"]
    if k1 * x_mm >= 2.4 or len(worte) < 2:                      # eine Zeile reicht
        if k1 * x_mm < 1.6:
            raise ValueError(f"Der Gruß „{gruss}“ passt nicht auf die Rückseite – kürzer fassen")
        return gr, [s1.in_mm((0.0, mitte), k1)]
    teilung = (len(worte) + 1) // 2                              # zwei Zeilen
    zeilen = [" ".join(worte[:teilung]), " ".join(worte[teilung:])]
    h2 = min(0.13 * g.S, 10.0)
    polys = []
    for i, z in enumerate(zeilen):
        s = SS.Satz(z, schrift)
        ym = mitte + (0.55 if i == 0 else -0.55) * h2
        k = NA._einpassen(s, ym, feld, h2, 1.5)
        if k * x_mm < 1.6:
            raise ValueError(f"Der Gruß „{gruss}“ passt nicht auf die Rückseite – kürzer fassen")
        polys.append(s.in_mm((0.0, ym), k))
    return gr, polys


# --------------------------------------------------------------------------------------------------
# Geschenkpäckchen: Geschenkpapier mit Sternfenstern im Rand, Band und Schildchen
# --------------------------------------------------------------------------------------------------

def _geschenk_vorne(cfg, g: Grund, lw, text: str, schrift: str):
    pw, ph, yp = g.fach
    S = g.S
    wm = cfg.min_web + cfg.kerf + 0.45
    dk0, dk1, dkw = g.deckel
    xs = [p[0] for p in g.umriss if p[1] < dk0 - 1]
    bw = max(xs)
    rb = max(0.075 * 2 * bw, 4.0)                               # halbe Bandbreite
    fach = g.fach_rechteck()
    fx0, fx1, fy0, fy1 = -pw / 2, pw / 2, yp - ph / 2, yp + ph / 2
    # Schildchen in der Mitte
    sw = min(0.66 * 2 * bw, pw + 6)
    sh = min(max(0.26 * ph, 11.0), 0.5 * ph + 4)
    schild = W.abrunden(K.rect(-sw / 2, yp - sh / 2, sw, sh), min(3.0, sh / 3), 6)
    sperr_schild = K.rect(-sw / 2 - 1.6, yp - sh / 2 - 1.6, sw + 3.2, sh + 3.2)
    loecher: List[Poly] = list(g.zier.loch_extra)
    gr: List[Tuple[Poly, bool]] = list(g.zier.g)
    # Muster: versetztes Raster aus Sternen; im Rand als Fenster, über dem Fach graviert
    sp = min(max(0.10 * 2 * bw, 7.5), 10.5)
    r = 0.30 * sp
    j = 0
    y = sp * 0.55
    while y < dk0 - 0.5 * sp:
        x = -bw + (sp * 0.55 if j % 2 == 0 else sp * 1.05)
        while x < bw - 0.4 * sp:
            if abs(x) < rb + r + 1.2 or abs(y - yp) < rb + r + 1.0 or (abs(x) < sw / 2 + r + 1.5 and abs(y - yp) < sh / 2 + r + 1.5):
                x += sp
                continue
            dx = max(fx0 - x, 0.0, x - fx1)
            dy = max(fy0 - y, 0.0, y - fy1)
            abst_fach = math.hypot(dx, dy) if (dx or dy) else -1.0
            abst_rand = min(x + bw, bw - x, y, dk0 - y)
            rot = math.pi / 2 + (0.2 if j % 2 else 0.0)
            if abst_fach >= r + 1.6 and abst_rand >= r + wm + 0.3:
                loecher.append(K.star(x, y, r, 0.45 * r, 5, rot))
            elif abst_fach < 0 or abst_rand >= r + 1.0:
                if (j + int((x + bw) / sp)) % 2 == 0:
                    gr.append((K.star(x, y, 0.75 * r, 0.34 * r, 5, rot), True))
                    gr.append((K.circle(x, y, 0.12 * r, 8), True))
                else:
                    gr += _flocke_gravur(x, y, 0.6 * r, 0.1 * j)
            x += sp
        y += sp * 0.82
        j += 1
    # Band senkrecht über Kasten und Deckel, waagrecht über den Kasten
    for sd in (1, -1):
        gr.append(([(sd * rb, 0.6), (sd * rb, dk1 - 0.6)], False))
        gr.append(([(sd * (rb - 1.0), 0.6), (sd * (rb - 1.0), dk1 - 0.6)], False))
        gr.append(([(-bw + 0.6, yp + sd * rb), (bw - 0.6, yp + sd * rb)], False))
        gr.append(([(-bw + 0.6, yp + sd * (rb - 1.0)), (bw - 0.6, yp + sd * (rb - 1.0))], False))
    # Deckelkante: doppelte Linie und Perlen
    gr.append(([(-dkw + 0.8, dk0 + 1.0), (dkw - 0.8, dk0 + 1.0)], False))
    gr.append(([(-dkw + 0.8, dk1 - 1.2), (dkw - 0.8, dk1 - 1.2)], False))
    for q in K.resample([(-dkw + 2.0, (dk0 + dk1) / 2), (dkw - 2.0, (dk0 + dk1) / 2)], 2.2):
        if abs(q[0]) > rb + 1.0:
            gr.append((K.circle(q[0], q[1], 0.45, 10), True))
    gr = [x for pts, c in gr for x in CB._ausserhalb(pts, c, sperr_schild)]
    gr.append((schild, True))
    gr.append((W.abrunden(K.rect(-sw / 2 + 1.0, yp - sh / 2 + 1.0, sw - 2.0, sh - 2.0), min(2.2, sh / 3), 6), True))
    text_polys = []
    if text:
        feld = K.rect(-sw / 2 + 2.6, yp - sh / 2 + 2.0, sw - 5.2, sh - 4.0)
        text_polys, _ = _widmung(feld, text, schrift, yp, sh - 4.4, 0.5)
    mat = E._andnot(g.silhouette(lw), lw.flaechen(loecher))
    return mat, gr, text_polys


# --------------------------------------------------------------------------------------------------
# Lebkuchenhaus: Zuckerguss am Dach, Herzfenster in den Wänden, Tür und Fenster graviert
# --------------------------------------------------------------------------------------------------

def _haus_vorne(cfg, g: Grund, lw, text: str, schrift: str):
    pw, ph, yp = g.fach
    wm = cfg.min_web + cfg.kerf + 0.45
    ty, top, ex, (sx0, sx1, sy1) = g.dach
    bw = max(p[0] for p in g.umriss if p[1] < ty - 1)
    fx0, fx1, fy0, fy1 = -pw / 2, pw / 2, yp - ph / 2, yp + ph / 2
    rand = fx0 + bw                                   # Wandbreite neben dem Fach
    loecher: List[Poly] = []
    gr: List[Tuple[Poly, bool]] = []
    # Dach: Zuckerguss-Bögen parallel zu den Dachkanten, darunter eine Reihe runder Fenster
    for sd in (1, -1):
        a = (sd * (ex - 1.6), ty + 1.4)
        b = (0.0, top - 2.6)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(4, int(L / 6.5))
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = (-uy, ux) if sd < 0 else (uy, -ux)          # zeigt ins Dach (nach unten innen)
        nx, ny = (nx, ny) if ny < 0 else (-nx, -ny)
        tiefe = 0.32 * L / n
        a2 = (a[0] + nx * 2.4, a[1] + ny * 2.4)
        b2 = (b[0] + nx * 2.4, b[1] + ny * 2.4)
        kette = []
        for k in range(n):
            p0 = (a2[0] + (b2[0] - a2[0]) * k / n, a2[1] + (b2[1] - a2[1]) * k / n)
            p1 = (a2[0] + (b2[0] - a2[0]) * (k + 1) / n, a2[1] + (b2[1] - a2[1]) * (k + 1) / n)
            c = ((p0[0] + p1[0]) / 2 + nx * 2 * tiefe, (p0[1] + p1[1]) / 2 + ny * 2 * tiefe)
            seg = K.bez(p0, c, p1, 10)
            kette += seg if not kette else seg[1:]
            m = ((p0[0] + p1[0]) / 2 + nx * (tiefe + 2.6), (p0[1] + p1[1]) / 2 + ny * (tiefe + 2.6))
            rr = min(0.17 * L / n, 1.9)
            if rr >= 1.0 and abs(m[0]) > 4.0 and m[1] > ty + rr + wm + 1.0 and not (sx0 - 2 < m[0] < sx1 + 2):
                loecher.append(K.circle(m[0], m[1], rr, 20))
                gr.append((K.circle(m[0], m[1], rr + 0.7, 20), True))
        gr.append((kette, False))
        gr.append(([(a[0] + nx * 1.0, a[1] + ny * 1.0), (b[0] + nx * 1.0, b[1] + ny * 1.0)], False))
    # Giebel: Rundfenster mit Sprossen (Durchbruch)
    gy = ty + 0.42 * (top - ty)
    gR = min(0.17 * (top - ty), 0.12 * 2 * bw, 9.0)
    if gR >= 3.0:
        ring = K.circle(0.0, gy, gR, 40)
        sp = wm / 2
        for qx, qy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            q = [(qx * sp, qy * sp), (qx * (gR + 1), qy * sp), (qx * (gR + 1), qy * (gR + 1)), (qx * sp, qy * (gR + 1))]
            viertel = [p for p in ring if p[0] * qx >= sp and p[1] * 0 + (p[1] - gy) * qy >= sp]
            if len(viertel) >= 3:
                pts = [(qx * sp, gy + qy * sp)] + sorted(viertel, key=lambda p: math.atan2(p[1] - gy, p[0]))
                loecher.append(pts)
        gr.append((K.circle(0.0, gy, gR + 0.9, 40), True))
        gr.append((K.circle(0.0, gy, gR + 1.8, 40), True))
    # Schornstein: Ziegelfugen
    for k in range(1, 4):
        yy = sy1 - k * (sy1 - (top - (top - ty) * abs(sx1) / ex)) / 4
        gr.append(([(sx0 + 0.6, yy), (sx1 - 0.6, yy)], False))
    # Wände neben dem Fach: Herzfenster, mit Zuckergusslinie umrandet
    hs = min(0.55 * rand, 7.5)
    if hs >= 4.0:
        xs_ = (-(bw - rand / 2), bw - rand / 2)
        n = max(1, int((ty - 6) / (hs * 2.0)))
        for i in range(n):
            yy = 5 + hs * 0.6 + (ty - 10 - hs * 1.2) * (i + 0.5) / n
            for x in xs_:
                h = CB._herzform(x, yy - 0.08 * hs, hs)
                loecher.append(h)
    # Mauer: Lebkuchen-Mandeln und Punkte
    mandeln = []
    rnd = K.rng(7, "haus")
    for i in range(400):
        if len(mandeln) >= int(2 * bw * ty / 70):
            break
        x = rnd.uniform(-bw + 2.5, bw - 2.5)
        y = rnd.uniform(2.5, ty - 2.5)
        if all(math.hypot(x - a, y - b) > 5.5 for a, b in mandeln):
            mandeln.append((x, y))
    # Tür mit Rundbogen, Fenster mit Sprossen und Zuckerguss-Sims (über dem Fach graviert)
    tw = min(0.26 * pw, 16.0)
    th = min(0.45 * (fy1 - 2 - 0.0), 1.7 * tw)
    tuer = CB._bogenfenster(0.0, 0.0, tw, th)
    gr.append((tuer + [tuer[0]], False))
    gr.append(([(-tw / 2 + 1.2, 0.0)] + K.arc(0.0, th - tw / 2, tw / 2 - 1.2, math.pi, 0.0, 14)[::-1][::-1] + [(tw / 2 - 1.2, 0.0)], False))
    gr.append((K.circle(tw * 0.28, th * 0.42, 0.7, 10), True))
    sch_h = min(max(0.30 * ph, 11.0), 16.0)
    sch_y = min(fy1 - sch_h / 2 - 1.5, th + sch_h / 2 + 4.0)
    sw = min(pw + 4.0, 2 * bw - 6.0)
    fw = min(0.18 * pw, 13.0)
    fh = fw * 1.15
    fy = th * 0.55
    for sd in (1, -1):
        cx = sd * (tw / 2 + (bw - tw / 2) / 2)
        if abs(cx) + fw / 2 > bw - 1.5:
            continue
        r = W.abrunden(K.rect(cx - fw / 2, fy - fh / 2, fw, fh), 1.0, 4)
        gr.append((r, True))
        gr.append(([(cx, fy - fh / 2), (cx, fy + fh / 2)], False))
        gr.append(([(cx - fw / 2, fy), (cx + fw / 2, fy)], False))
        gr.append((CB._bogenkette((cx - fw / 2 - 1.0, fy + fh / 2 + 0.8), (cx + fw / 2 + 1.0, fy + fh / 2 + 0.8), 4,
                                  0.8), False))
    frei = [(-tw / 2 - 1.5, -1, tw / 2 + 1.5, th + 1.5)]
    for sd in (1, -1):
        cx = sd * (tw / 2 + (bw - tw / 2) / 2)
        frei.append((cx - fw / 2 - 1.5, fy - fh / 2 - 1.5, cx + fw / 2 + 1.5, fy + fh / 2 + 2.5))
    for x, y in mandeln:
        if any(a <= x <= c and b <= y <= d for a, b, c, d in frei):
            continue
        gr.append((K.ellipse(x, y, 1.3, 0.65, rnd.uniform(0, math.pi), 14), True))
        gr.append(([(x - 0.7, y), (x + 0.7, y)], False))
    # Schild für die Widmung
    schild = W.abrunden(K.rect(-sw / 2, sch_y - sch_h / 2, sw, sch_h), min(3.0, sch_h / 3), 6)
    sperr = K.rect(-sw / 2 - 1.4, sch_y - sch_h / 2 - 1.4, sw + 2.8, sch_h + 2.8)
    gr = [x for pts, c in gr for x in CB._ausserhalb(pts, c, sperr)]
    gr.append((schild, True))
    gr.append((CB._bogenkette((-sw / 2 + 2, sch_y + sch_h / 2 - 1.0), (sw / 2 - 2, sch_y + sch_h / 2 - 1.0),
                              max(4, int(sw / 6)), 0.7), False))
    text_polys = []
    if text:
        feld = K.rect(-sw / 2 + 2.4, sch_y - sch_h / 2 + 1.6, sw - 4.8, sch_h - 4.2)
        text_polys, _ = _widmung(feld, text, schrift, sch_y - 0.6, sch_h - 4.6, 0.5)
    mat = E._andnot(g.silhouette(lw), lw.flaechen(loecher))
    return mat, gr, text_polys


# --------------------------------------------------------------------------------------------------
# Zusammenbau
# --------------------------------------------------------------------------------------------------

def _teile(cfg, form: str, pw: float, ph: float, rand: float, rahmen: str, text: str, gruss: str, schrift: str,
           notes: List[str]):
    S, a, b, yp = _groesse(cfg, form, pw, ph, rand + 0.6)
    g = Grund(cfg, form, S, (a, b, yp), rand)
    lw = g.leinwand()
    web, kerf = cfg.min_web, cfg.kerf
    lochr = lw.flaechen([g.loch])
    # Vorderseite
    if form == "geschenk":
        mat, gr, tp = _geschenk_vorne(cfg, g, lw, text, schrift)
    elif form == "haus":
        mat, gr, tp = _haus_vorne(cfg, g, lw, text, schrift)
    else:
        rmat, fenster = _spitze(cfg, g, lw, rand, rahmen)
        mat = rmat.union(lw.flaechen([fenster]))
        gr, tp = _mitte_gravur(g, lw, fenster, text, schrift)
    vorne = E.teil_aus_raster(f"{form}_vorderseite", lw, E._andnot(mat, lochr), web, kerf, notes)
    NA._gravuren_setzen(vorne, lw, gr)
    if tp:
        NA._text_gravieren(vorne, lw, tp, "gefuellt")
    g.krone_gravieren(vorne)
    # Fachrahmen: Umriss ohne Fach und Öffnung; spitze Hörner oben werden gekappt
    wm = web + kerf + 0.45
    rahmen_mat = E._andnot(lw.flaechen([g.umriss]), lw.flaechen([g.schlitz()]))
    rahmen_mat = rahmen_mat.open(lw.px_fuer(wm / 2))
    mitte = E.teil_aus_raster(f"{form}_fachrahmen", lw, rahmen_mat, web, kerf, notes)
    # Rückseite
    hinten = E.teil_aus_raster(f"{form}_rueckseite", lw, E._andnot(g.silhouette(lw), lochr), web, kerf, notes)
    gr_h, tp_h = _rueckseite_gravur(g, lw, gruss, schrift)
    NA._gravuren_setzen(hinten, lw, gr_h)
    for polys in tp_h:
        NA._text_gravieren(hinten, lw, polys, "gefuellt")
    g.krone_gravieren(hinten)
    return [vorne, mitte, hinten], g


def build(cfg, name: str = "steckfach", form: str = "kugel", einlage: str = "schein", einlage_b: float = 77.0,
          einlage_h: float = 41.0, spiel: float = 1.0, rand: float = 14.0, rahmen: str = "bluetenkranz",
          text: str = "Für dich", gruss: str = "Frohe Weihnachten", schrift: str = "schwungvoll"):
    for key, val, opts in (("Form", form, AUSWAHL), ("Einlage", einlage, EINLAGEN), ("Spitzenrand", rahmen, RAHMEN),
                           ("Schreibschrift", schrift, SS.SCHRIFTEN)):
        if val not in dict(opts):
            raise ValueError(f"{key}: unbekannte Auswahl {val!r}")
    text = (text or "").strip()
    gruss = (gruss or "").strip()
    bad = SS.fehlende(text + gruss, schrift)
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Schreibschrift nicht")
    eb, eh = EINLAGE_MASS.get(einlage, (float(einlage_b), float(einlage_h)))
    spiel = min(max(float(spiel), 0.3), 3.0)
    rand = min(max(float(rand), 9.0), 24.0)
    pw, ph = eb + 2 * spiel, eh + 2 * spiel
    liste = [k for k, _ in FORMEN] if form == "alle" else [form]
    asm = Assembly(name, params=dict(form=form, einlage=einlage, fach_b=round(pw, 1), fach_h=round(ph, 1)))
    notes: List[str] = []
    masse = []
    for fo in liste:
        teile, g = _teile(cfg, fo, pw, ph, rand, rahmen, text, gruss, schrift, notes)
        asm.parts += teile
        masse.append((fo, g))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    T = cfg.T
    a, b, _ = masse[0][1].fach
    lage = "stehend" if b > a else "liegend"
    asm.notes.append(f"Fach: innen {a:.1f} × {b:.1f} mm ({lage}), {T:g} mm tief, oben offen – passt für "
                     f"{EINLAGE_TEXT[einlage]}.")
    if einlage == "schein":
        asm.notes.append("Befüllen: Den Schein einmal längs und einmal quer falten und von oben ins Fach schieben.")
    asm.notes.append("Zusammenbau: Den Fachrahmen bündig auf die Rückseite kleben (Öffnung nach oben), dann die "
                     "Vorderseite deckungsgleich darauf – Öse auf Öse. Leim dünn und nur auf den äußeren Rand geben, "
                     "nicht ins Fach, und kurz beschweren.")
    asm.notes.append("Aufhängen: Das Band durch die Ösen von Vorder- und Rückseite ziehen – es läuft quer über die "
                     "Öffnung und verschließt das Fach. Zum Herausnehmen Band lösen und den Anhänger umdrehen.")
    asm.notes.append("Tipp: Den Fachrahmen aus einer dunkleren Holzart lasern (Kirsche oder Nussbaum) und die "
                     "Vorderseite aus Ahorn – durch die Spitze wirkt das wie eine Intarsie.")
    if T >= 3.0:
        asm.notes.append(f"Tipp: Drei Lagen à {T:g} mm ergeben {3 * T:g} mm Dicke. In 2 mm wird der Anhänger "
                         "schlanker, eine Karte oder ein gefalteter Schein passt trotzdem.")
    asm.notes.append("xTool Creative Space: Die Gravur ist als „Linie“ (Ritzen) angelegt; Widmung und Gruß bestehen "
                     "aus dichten Linien. Mit wenig Leistung lasern, dann bleiben Perlen und Stechpalme scharf.")
    return asm
