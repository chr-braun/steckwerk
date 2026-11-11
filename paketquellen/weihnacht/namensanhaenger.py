"""
Edler Namensanhänger – Christbaumanhänger mit Namen in echter Schreibschrift.

Drei Ausführungen:
  schriftzug  Der Name ist als zusammenhängender Schriftzug ausgeschnitten und hängt frei im Kugelring,
              mit Stern oder Stechpalmenzweig unter der Krone und der Jahreszahl auf einem kleinen Schild.
  medaillon   Zwei Lagen: Grundplatte mit füllend graviertem Namen, darauf ein Spitzenrahmen mit
              Fenster. In zwei Holzfarben gelasert wirkt das wie eine Intarsie.
  spitze      Eine Lage: Spitzenrahmen und volle Mitte mit graviertem Namen.

Die Schriften sind echte Kalligrafie- und Schreibschriften (SIL Open Font License, siehe
SCHRIFTEN-LIZENZ.txt). Für den Laser werden feine Haarstriche verstärkt, i-Punkte und Umlautpunkte
mit feinen Brücken gehalten und Namen mit Leerzeichen zu einem Stück verbunden.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Optional, Sequence, Tuple

from steckwerk import Assembly, oriented, signed_area
from pakete import bibliothek, sel, num, txt

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
W = bibliothek("verzierungen").W
FG = _sub("_filigran")
SS = _sub("_schreibschrift")
SZ = _sub("_szenen")
K = E.K
Poly = List[Tuple[float, float]]

AUSFUEHRUNGEN = [("schriftzug", "Schriftzug ausgeschnitten im Kugelring"),
                 ("medaillon", "Medaillon zweilagig (Spitzenrahmen auf Grundplatte)"),
                 ("spitze", "Spitzenrahmen einlagig, Name graviert")]
FORMEN = [("kugel", "Kugel"), ("herz", "Herz")]
RAHMEN = [("bluetenkranz", "Blütenkranz"), ("spitze", "Klöppelspitze"), ("ranken", "Ranken"),
          ("sterne", "Sternenkranz"), ("herzen", "Herzchen"), ("perlen", "Perlen und Bögen")]
_REZEPT = dict(bluetenkranz=["blueten"], spitze=["zickzack"], ranken=["ranken"], sterne=["sterne"],
               herzen=["herzen"], perlen=["perlen", "boegen"])
ZIER = [("stern", "Stern"), ("flocke", "Schneeflocke"), ("mond", "Mond mit Sternen"), ("ohne", "ohne")]
GRAVUR = [("gefuellt", "gefüllt (Linien dicht an dicht)"), ("kontur", "nur Umriss")]
_STIEL = dict(elegant=26.0, schwungvoll=48.0, rund=80.0)   # dünnster Strich der Schrift (Schrifteinheiten)

INFO = dict(
    label="Edler Namensanhänger",
    group="Weihnachten",
    desc="Christbaumanhänger mit Namen in echter Schreibschrift: als ausgeschnittener Schriftzug im Kugelring, "
         "als zweilagiges Medaillon mit Spitzenrahmen oder einlagig mit graviertem Namen – ein Anhänger je Name.",
    params=[
        txt("namen", "Namen", "Emma|Paul", maxlen=120, help="mehrere Namen mit | trennen – ein Anhänger je Name",
            section="Schrift und Beschriftung"),
        sel("schrift", "Schreibschrift", SS.SCHRIFTEN, "schwungvoll", section="Schrift und Beschriftung"),
        txt("jahr", "Jahreszahl", "2026", maxlen=12, help="leer lassen für keine Jahreszahl",
            section="Schrift und Beschriftung"),
        txt("zeile", "Zusatzzeile", "", maxlen=30, help="optional, z. B. „Frohe Weihnachten“",
            section="Schrift und Beschriftung", when={"ausfuehrung": ["medaillon", "spitze"]}),
        sel("ausfuehrung", "Ausführung", AUSFUEHRUNGEN, "schriftzug"),
        sel("form", "Form", FORMEN, "kugel"),
        num("groesse", "Höhe", 90, 60, 180, help="ohne Krone und Öse"),
        sel("szene", "Szene unten", SZ.SZENEN, "winterdorf", when={"ausfuehrung": ["schriftzug"]},
            help="Winterlandschaft oder Weihnachtsvorbereitung; die Jahreszahl steht dann im Schnee"),
        sel("zier", "Zier unter der Krone", ZIER, "stern", when={"ausfuehrung": ["schriftzug"]}),
        sel("rahmen", "Spitzenrahmen", RAHMEN, "bluetenkranz", when={"ausfuehrung": ["medaillon", "spitze"]}),
        sel("gravur", "Gravur", GRAVUR, "gefuellt", when={"ausfuehrung": ["medaillon", "spitze"]}),
    ],
)

UEBERSETZUNG = {"en": {
    "Edler Namensanhänger": "Fine name ornament", "Weihnachten": "Christmas",
    "Christbaumanhänger mit Namen in echter Schreibschrift: als ausgeschnittener Schriftzug im Kugelring, "
    "als zweilagiges Medaillon mit Spitzenrahmen oder einlagig mit graviertem Namen – ein Anhänger je Name.":
        "Tree ornament with a name in real script lettering: as a cut-out script inside a bauble ring, as a "
        "two-layer medallion with a lace frame or as one layer with an engraved name – one ornament per name.",
    "Namen": "Names", "mehrere Namen mit | trennen – ein Anhänger je Name":
        "separate several names with | – one ornament per name",
    "Schrift und Beschriftung": "Font and lettering", "Schreibschrift": "Script font",
    "elegant (Kalligrafie)": "elegant (calligraphy)", "schwungvoll": "flowing", "rund und kräftig": "round and bold",
    "Jahreszahl": "Year", "leer lassen für keine Jahreszahl": "leave empty for no year",
    "Zusatzzeile": "Extra line", "optional, z. B. „Frohe Weihnachten“": "optional, e.g. “Merry Christmas”",
    "Ausführung": "Style", "Schriftzug ausgeschnitten im Kugelring": "Cut-out script inside a bauble ring",
    "Medaillon zweilagig (Spitzenrahmen auf Grundplatte)": "Two-layer medallion (lace frame on a base plate)",
    "Spitzenrahmen einlagig, Name graviert": "Single layer lace frame, engraved name",
    "Form": "Shape", "Kugel": "Bauble", "Herz": "Heart", "Glocke": "Bell", "Höhe": "Height",
    "ohne Krone und Öse": "without cap and loop", "Zier unter der Krone": "Decoration below the cap",
    "Stern": "Star", "Schneeflocke": "Snowflake", "Mond mit Sternen": "Moon with stars", "ohne": "none", "Spitzenrahmen": "Lace frame",
    "Blütenkranz": "Flower wreath", "Klöppelspitze": "Bobbin lace", "Ranken": "Scrolls",
    "Sternenkranz": "Star wreath", "Herzchen": "Little hearts", "Perlen und Bögen": "Pearls and arches",
    "Szene unten": "Scene at the bottom",
    "Winterlandschaft oder Weihnachtsvorbereitung; die Jahreszahl steht dann im Schnee":
        "winter landscape or Christmas preparations; the year is then engraved in the snow",
    "Winterdorf mit Kirche": "Winter village with church", "Winterwald mit Hirsch": "Winter forest with stag",
    "Schneemann mit Laterne": "Snowman with lantern", "Schlittenfahrt": "Sleigh ride",
    "Adventskranz mit vier Kerzen": "Advent wreath with four candles",
    "Christbaum mit Geschenken": "Christmas tree with presents", "Plätzchen backen": "Baking cookies",
    "Geschenke packen": "Wrapping presents", "keine Szene (Schild mit Jahreszahl)": "no scene (plaque with the year)",
    "Gravur": "Engraving", "gefüllt (Linien dicht an dicht)": "filled (lines close together)",
    "nur Umriss": "outline only",
    "Aufhängen: Band oder Kordel durch die Öse ziehen.": "To hang: thread a ribbon or cord through the loop.",
    "Bitte mindestens einen Namen eingeben.": "Please enter at least one name.",
}}


# --------------------------------------------------------------------------------------------------
# Grundform: Umriss, Krone, Öse
# --------------------------------------------------------------------------------------------------

class Form:
    def __init__(self, cfg, form: str, S: float):
        self.umriss, (_, top), self.yc = FG.form(form, S)
        self.S = S
        self.form = form
        web = cfg.min_web
        self.extra: List[Poly] = []
        self.krone: Optional[Tuple[float, float, float, float]] = None
        if form == "kugel":                                    # Krone der Christbaumkugel
            cw, ch = 0.22 * S, 0.065 * S
            self.krone = (-cw / 2, top - 1.5, cw / 2, top + ch)
            self.extra.append(K.rect(-cw / 2, top - 1.5, cw, ch + 1.5))
            top += ch
        self.ro = max(3.4, 0.042 * S)
        self.oese = (0.0, top + self.ro - (1.2 if form == "kugel" else 0.2))
        self.extra.append(K.circle(self.oese[0], self.oese[1], self.ro, 48))
        self.loch = K.circle(self.oese[0], self.oese[1], self.ro - max(web + 0.7, 1.5), 40)
        xs = [p[0] for p in self.umriss]
        ys = [p[1] for p in self.umriss]
        self.box = (min(xs) - 2, min(ys) - 2, max(xs) + 2, max(max(ys), self.oese[1] + self.ro) + 2)

    def leinwand(self):
        x0, y0, x1, y1 = self.box
        return E.Leinwand(self.box, max(0.06, min(0.09, max(x1 - x0, y1 - y0) / 1300.0)))

    def gravur_krone(self, part) -> None:
        if not self.krone:
            return
        x0, y0, x1, y1 = self.krone
        y0 += 1.5
        n = 5
        for i in range(1, n):                                  # Rippen wie an einer echten Kugelkappe
            x = x0 + (x1 - x0) * i / n
            part.add_engrave([(x, y0 + 0.9), (x, y1 - 0.9)])


def _innen(lw, poly: Poly, d: float, kreis: bool = False) -> Poly:
    """Kontur um d nach innen versetzt – über das Raster, damit auch Glocke und Herz sauber bleiben."""
    if d <= 0.05:
        return list(poly)
    if kreis:
        return FG.feld(poly, d)
    r = lw.flaechen([poly]).erode(lw.px_fuer(d))
    areas = lw.konturen(r, 0.3)
    if not areas:
        raise ValueError("Der Anhänger ist für diesen Rahmen zu klein – größer wählen")
    best = max(areas, key=lambda a: abs(signed_area(a["aussen"])))["aussen"]
    return oriented(best, True)


def _halbbreite(poly: Poly, y0: float, y1: float, n: int = 9) -> float:
    """Kleinste halbe Breite (symmetrisch um x = 0) der Kontur zwischen y0 und y1."""
    best = 1e9
    for i in range(n):
        y = y0 + (y1 - y0) * i / (n - 1)
        try:
            a, b = E.quer_x(poly, y)
        except ValueError:
            return 0.0
        best = min(best, -a, b)
    return max(0.0, best)


def _breit_ab(poly: Poly, w: float, y_start: float) -> float:
    """Unterste Höhe ab y_start, auf der die (symmetrische) Kontur mindestens w breit ist."""
    y0, y1 = _ybereich(poly)
    y = max(y_start, y0 + 0.1)
    while y < y1 and 2 * _halbbreite(poly, y, y + 0.01, 2) < w:
        y += 0.4
    return y


def _ybereich(poly: Poly) -> Tuple[float, float]:
    ys = [p[1] for p in poly]
    return min(ys), max(ys)


# --------------------------------------------------------------------------------------------------
# Text
# --------------------------------------------------------------------------------------------------

def _einpassen(satz, mitte_y: float, feld: Poly, h_max: float, rand: float) -> float:
    """Größter Maßstab (mm je Schrifteinheit), mit dem der Satz um mitte_y ins Feld passt."""
    k = h_max / satz.hoehe
    for _ in range(14):
        hh = satz.hoehe * k / 2
        hb = _halbbreite(feld, mitte_y - hh, mitte_y + hh) - rand
        if satz.breite * k / 2 <= hb:
            return k
        k *= max(0.5, min(0.97, hb / (satz.breite * k / 2)))
    return k


def _text_gravieren(part, lw, polys: Sequence[Poly], art: str) -> None:
    r = SS.raster(lw, polys)
    if art == "gefuellt":
        for s in SS.schraffur(lw, r, 0.16):
            part.add_engrave(s)
    for aussen, loecher in SS.konturen_mm(lw, r):              # Umriss immer dazu: saubere Kanten
        part.add_engrave(aussen + [aussen[0]])
        for h in loecher:
            part.add_engrave(h + [h[0]])


# --------------------------------------------------------------------------------------------------
# Spitzenrahmen
# --------------------------------------------------------------------------------------------------

def _spitzenrahmen(cfg, fm: Form, lw, band: float, rahmen: str):
    """Material des Spitzenrahmens (Ring zwischen Umriss und Fenster) und das Fenster als Polygon."""
    web, kerf = cfg.min_web, cfg.kerf
    wmin = web + kerf + 0.45
    w = wmin + 0.25
    rand_a = max(2 * web + 0.8, 0.028 * fm.S)
    rand_i = max(1.6 * web + 0.6, 0.02 * fm.S)
    kr = fm.form == "kugel"
    fenster = _innen(lw, fm.umriss, band, kr)
    aussen_f = _innen(lw, fm.umriss, rand_a, kr)
    innen_f = _innen(lw, fm.umriss, band - rand_i, kr)
    r_a = min(math.hypot(x, y - fm.yc) for x, y in aussen_f)
    r_i = max(math.hypot(x, y - fm.yc) for x, y in innen_f)
    if fm.form != "kugel":
        r_i = min(math.hypot(x, y - fm.yc) for x, y in innen_f)
        r_a = max(math.hypot(x, y - fm.yc) for x, y in aussen_f)
    h = max(r_a - r_i, 3 * w)
    rm = (r_a + r_i) / 2
    bausteine = _REZEPT[rahmen]
    hz = h / len(bausteine)
    n = max(8, int(round(2 * math.pi * rm / (hz * 1.25) / 2)) * 2)
    M = FG.Muster(w, n, wmin=wmin, R=r_a)
    for i, art in enumerate(bausteine):
        a = r_i - 0.4 * w + hz * i
        b = r_i + hz * (i + 1) + (0.4 * w if i == len(bausteine) - 1 else 0.0)
        FG._baustein(M, art, a, b, 0.0 if i % 2 == 0 else math.pi / n)
        if i < len(bausteine) - 1:
            M.kreis(b, 0.9)
    fig = M.figur(0.0, fm.yc)
    shape = lw.flaechen([fm.umriss] + fm.extra)
    bandflaeche = E._andnot(lw.flaechen([aussen_f]), lw.flaechen([innen_f]))
    mat = E._andnot(shape, lw.flaechen([aussen_f]))            # Außenrand + Krone + Öse
    mat = mat.union(E._andnot(lw.flaechen([innen_f]), lw.flaechen([fenster])))   # Innenrand
    mat = mat.union(E._and(lw.figur(fig), bandflaeche))
    return mat, fenster


def _textblock(fm: Form, feld: Poly, name: str, schrift: str, jahr: str, zeile: str):
    """Name groß in die Mitte, Zusatzzeile darüber, Jahreszahl darunter. Liefert [(polys)]."""
    y0, y1 = _ybereich(feld)
    H = y1 - y0
    rand = 0.035 * fm.S
    s_name = SS.Satz(name, schrift)
    s_zeile = SS.Satz(zeile, schrift) if zeile.strip() else None
    s_jahr = SS.Satz(jahr, schrift) if jahr.strip() else None
    klein = 0.13 * H
    luft = 0.03 * H
    for versuch in range(8):
        f = 1.0 - 0.08 * versuch
        h_n = 0.40 * H * f
        top_rest = (klein + luft) if s_zeile else 0.0
        bot_rest = (klein + luft) if s_jahr else 0.0
        mitte = (y0 + y1) / 2 + (bot_rest - top_rest) / 2
        k = _einpassen(s_name, mitte, feld, h_n, rand)
        hn = s_name.hoehe * k
        teile = [s_name.in_mm((0.0, mitte), k)]
        ok = True
        for s, oben in ((s_zeile, True), (s_jahr, False)):
            if s is None:
                continue
            ks = (klein * f) / s.hoehe
            ks = min(ks, k * 0.62)                             # Nebenzeilen klar kleiner als der Name
            hs = s.hoehe * ks
            ym = mitte + (hn / 2 + luft + hs / 2) * (1 if oben else -1)
            ks2 = _einpassen(s, ym, feld, hs, rand)
            if ks2 * s.hoehe < 0.55 * hs or ym + hs / 2 > y1 - 0.5 or ym - hs / 2 < y0 + 0.5:
                ok = False
                break
            teile.append(s.in_mm((0.0, ym), ks2))
        if ok:
            return teile, k
    raise ValueError(f"Der Name „{name}“ passt mit Zusatzzeile und Jahreszahl nicht – kürzer fassen oder größer wählen")


def _flaeche_anhaenger(cfg, fm: Form, lw, tag: str, name: str, schrift: str, jahr: str, zeile: str,
                       rahmen: str, gravur: str, art: str, notes: List[str]):
    band = (0.165 if fm.form == "kugel" else 0.12) * fm.S
    rahmen_mat, fenster = _spitzenrahmen(cfg, fm, lw, band, rahmen)
    lochr = lw.flaechen([fm.loch])
    teile = []
    feld = _innen(lw, fenster, max(0.8, 0.012 * fm.S), fm.form == "kugel")
    block, k = _textblock(fm, feld, name, schrift, jahr, zeile)
    if k * SS.schrift(schrift)["x"] < 2.2:
        raise ValueError(f"Der Name „{name}“ würde zu klein graviert – kürzer fassen oder größer wählen")
    if art == "medaillon":
        grund = E._andnot(lw.flaechen([fm.umriss] + fm.extra), lochr)
        g = E.teil_aus_raster(tag + "_grundplatte", lw, grund, cfg.min_web, cfg.kerf, notes)
        for polys in block:
            _text_gravieren(g, lw, polys, gravur)
        fm.gravur_krone(g)
        d = E.teil_aus_raster(tag + "_spitzenrahmen", lw, E._andnot(rahmen_mat, lochr), cfg.min_web, cfg.kerf, notes)
        fm.gravur_krone(d)
        teile += [g, d]
    else:
        mat = E._andnot(rahmen_mat.union(lw.flaechen([fenster])), lochr)
        p = E.teil_aus_raster(tag, lw, mat, cfg.min_web, cfg.kerf, notes)
        for polys in block:
            _text_gravieren(p, lw, polys, gravur)
        fm.gravur_krone(p)
        teile.append(p)
    return teile


# --------------------------------------------------------------------------------------------------
# Schriftzug im Ring
# --------------------------------------------------------------------------------------------------

def _stechpalme(cx: float, cy: float, L: float, ang: float) -> Poly:
    """Stechpalmenblatt mit Zacken, Stiel bei (cx, cy), Länge L, Richtung ang."""
    pts = []
    n = 5
    for side in (1, -1):
        rng = range(0, 2 * n + 1) if side == 1 else range(2 * n, -1, -1)
        for i in rng:
            t = i / (2 * n)
            wbreit = 0.21 * L * math.sin(math.pi * t) ** 0.8
            spitze = (i % 2 == 1)
            r = wbreit * (1.25 if spitze else 0.78)
            pts.append((t * L, side * r))
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def _gravuren_setzen(part, lw, gravuren) -> None:
    """Gravurlinien nur dort, wo nach dem Prüfen sicher Holz ist (Abstand zu jedem Schnitt)."""
    r = E._andnot(lw.flaechen([part.outline]), lw.flaechen(part.holes) if part.holes else lw.leer())
    r = r.erode(lw.px_fuer(0.4))

    def drin(q) -> bool:
        c = int((q[0] - lw.x0) / lw.px)
        row = int((lw.y_top - q[1]) / lw.px)
        return 0 <= row < r.h and 0 <= c < r.w and (r.rows[row] >> c) & 1 == 1

    for pts, closed in gravuren:
        pts = list(pts) + ([pts[0]] if closed else [])
        L = K.path_len(pts)
        if L < 0.3:
            continue
        dicht = K.resample(pts, min(0.3, L / 2))
        flags = [drin(q) for q in dicht]
        if all(flags):
            part.add_engrave(dicht, False)
            continue
        lauf: Poly = []
        for q, f in zip(dicht, flags):
            if f:
                lauf.append(q)
            else:
                if len(lauf) >= 3:
                    part.add_engrave(lauf)
                lauf = []
        if len(lauf) >= 3:
            part.add_engrave(lauf)


def _figur_robust(lw, fig, d: float, dick: float = 0.0):
    """Wie Leinwand.figur, aber Durchbrüche (Fenster, Augen …) um d geschrumpft: In der kleinen Szene
    bleiben so zwischen Fenster und Kontur genug Holz stehen; zu kleine Fenster entfallen."""
    n = lw.px_fuer(d)
    m = lw.px_fuer(dick)
    acc = lw.leer()
    batch, sign = [], None
    for sg, poly in fig.ops + [("=", [])]:
        if sg != sign and batch:
            r = lw.flaechen(batch)
            acc = acc.union(r.dilate(m) if m else r) if sign == "+" else E._andnot(acc, r.erode(n))
            batch = []
        sign = sg
        if sg != "=":
            batch.append(poly)
    return acc


def _stuecke(lw, r) -> int:
    return sum(1 for a in lw.konturen(r) if abs(signed_area(a["aussen"])) > 0.15)


def _laserfest(lw, txt, dick: float, web: float, kerf: float):
    """Schrift so weit verstärken, dass das spätere Öffnen (Mindeststeg) keine Haarstriche mehr kappt."""
    n_open = lw.px_fuer((web + kerf + 0.15) / 2)
    d = lw.px_fuer(dick)
    schritt = max(1, lw.px_fuer(0.08))
    for _ in range(8):
        r = txt.dilate(d) if d else txt
        o = r.open(n_open)
        if o.count() >= 0.985 * r.count() and _stuecke(lw, o) <= _stuecke(lw, r):
            return r
        d += schritt
    return r


def _inseln_verbinden(lw, mat, wb: float, schutz=None):
    """Lose Teile (i-Punkte, Wörter) mit kurzen Brücken an das größte Stück hängen."""
    for _ in range(8):
        areas = lw.konturen(mat)
        areas = [a for a in areas if abs(signed_area(a["aussen"])) > 0.15]
        if len(areas) <= 1:
            return mat
        areas.sort(key=lambda a: -abs(signed_area(a["aussen"])))
        haupt = list(areas[0]["aussen"])
        for h in areas[0]["loecher"]:
            haupt += h
        brucken = []
        for a in areas[1:]:
            best = None
            pa = a["aussen"][::max(1, len(a["aussen"]) // 60)]
            ph = haupt[::max(1, len(haupt) // 1500)]
            for p in pa:
                for q in ph:
                    d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
                    if best is None or d < best[0]:
                        best = (d, p, q)
            _, p, q = best
            xs = [v[0] for v in a["aussen"]]
            ys = [v[1] for v in a["aussen"]]
            c = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            dx, dy = q[0] - c[0], q[1] - c[1]
            L = math.hypot(dx, dy) or 1.0
            ende = (q[0] + dx / L * 0.6, q[1] + dy / L * 0.6)
            brucken.append(K.stroke([c, ende], wb, wb, "rund"))
        mat = mat.union(lw.flaechen(brucken))
    return mat


def _schriftzug_anhaenger(cfg, fm: Form, lw, tag: str, name: str, schrift: str, jahr: str, zier: str,
                          szene: str, seed: int, notes: List[str]):
    S, web, kerf = fm.S, cfg.min_web, cfg.kerf
    wb = web + kerf + 0.55                                     # Brücken und feinste Stege
    rb = max(2 * web + kerf + 1.2, 0.05 * S)                   # Ringbreite
    innen = _innen(lw, fm.umriss, rb, fm.form == "kugel")
    y0, y1 = _ybereich(innen)
    H = y1 - y0
    shape = lw.flaechen([fm.umriss] + fm.extra)
    mat = E._andnot(shape, lw.flaechen([innen]))
    gravuren: List[Tuple[Poly, bool]] = []
    mitte_ring = _innen(lw, fm.umriss, rb / 2, fm.form == "kugel")
    if rb >= 3.4:
        gravuren.append((mitte_ring + [mitte_ring[0]], False))

    # oben: Zier unter der Krone
    oben = y1
    if zier == "stern":
        rs = 0.08 * S
        cy = y1 - 0.025 * S - rs
        st = K.star(0.0, cy, rs, 0.45 * rs, 5)
        mat = mat.union(lw.flaechen([st, K.stroke([(0.0, cy + rs * 0.6), (0.0, y1 + rb * 0.5)], wb, wb, "flach")]))
        innen_st = K.star(0.0, cy, rs * 0.55, 0.45 * rs * 0.55, 5)
        gravuren.append((innen_st + [innen_st[0]], False))
        for i in range(5):                                     # Grate zur Spitze: wirkt geschliffen
            a = math.pi / 2 + i * 2 * math.pi / 5
            gravuren.append(([(0.0, cy), (rs * 0.62 * math.cos(a), cy + rs * 0.62 * math.sin(a))], False))
        oben = cy - 0.45 * rs * 1.05
    elif zier == "flocke":
        hf = 0.17 * S
        top_y = y1 + rb * 0.4
        fl = SZ.F.schneeflocke(hf, seed).place(0.0, top_y - 0.02 * S - hf, 1.0)
        mat = mat.union(E._and(lw.figur(fl), lw.flaechen([FG.feld(fm.umriss, 0.3)])))
        mat = mat.union(lw.flaechen([K.stroke([(0.0, top_y - 0.02 * S - 0.5), (0.0, top_y + 0.3)], wb, wb, "flach")]))
        oben = top_y - 0.02 * S - hf
    elif zier == "mond":
        rm = 0.085 * S
        cy = y1 - 0.02 * S - rm
        cx = -0.10 * S
        mond = [K.circle(cx, cy, rm, 60)]
        mat = mat.union(E._andnot(lw.flaechen(mond), lw.flaechen([K.circle(cx + 0.45 * rm, cy + 0.2 * rm, 0.82 * rm, 60)])))
        mat = mat.union(lw.flaechen([K.stroke([(cx - 0.2 * rm, cy + rm * 0.7), (cx - 0.3 * rm, y1 + rb * 0.5)], wb, wb, "flach")]))
        for sx, sy, r_, l_ in ((0.06 * S, -0.03 * S, 0.045 * S, 0.035 * S), (0.15 * S, -0.075 * S, 0.032 * S, 0.02 * S)):
            c = (sx, y1 + sy - l_)
            mat = mat.union(lw.flaechen([K.star(c[0], c[1] - r_, r_, r_ * 0.45, 5),
                                         K.stroke([(c[0], c[1] - r_ * 0.4), (c[0], y1 + rb * 0.5)], wb, wb, "flach")]))
        oben = cy - rm
    elif zier != "ohne":
        raise ValueError(f"Zier: unbekannte Auswahl {zier!r}")

    # unten: Szene auf dem Schneehügel (Jahreszahl im Schnee) oder Schild mit Jahreszahl
    unten = y0
    schild_text = None
    if szene != "ohne":
        yg = max(y0 + 0.085 * S, _breit_ab(innen, 0.46 * S, y0))   # Schneehügel
        hh = yg - y0
        il, ir = E.quer_x(innen, yg)
        hill = SZ.huegel(il - rb, ir + rb, yg, 0.012 * S, hh + rb, phase=0.4 + 0.37 * (seed % 7))
        Hs = (0.28 if fm.form == "kugel" else 0.21) * S
        Ws = 2 * _halbbreite(innen, yg, yg + Hs * 0.5)
        fig, sg = SZ.szene(szene, Ws, Hs, yg, seed, wmin=web + kerf + 0.45, wb=wb)
        frei = lw.flaechen([FG.feld(fm.umriss, 0.3)])
        mat = mat.union(E._and(lw.flaechen([hill]).union(_figur_robust(lw, fig, 0.45 * (web + kerf), 0.22)), frei))
        gravuren += sg
        if jahr.strip():
            sj = SS.Satz(jahr, schrift)
            hj = min(0.07 * S, hh * 0.66)
            breit = sj.breite * hj / sj.hoehe + 0.08 * S
            ym = min(max(y0 + hh * 0.48, _breit_ab(innen, breit, y0) + hj / 2), yg - 0.012 * S - hj / 2)
            kj = min(hj / sj.hoehe, (2 * _halbbreite(innen, ym - hj / 2, ym + hj / 2) - 0.08 * S) / sj.breite)
            if kj * sj.hoehe < 2.5:
                raise ValueError("Die Jahreszahl passt nicht in den Schnee – größer wählen oder Jahreszahl weglassen")
            schild_text = sj.in_mm((0.0, ym), kj)
        sx0, sy0, sx1, sy1 = fig.bbox()
        unten = max(yg + 0.02 * S, sy1)
    elif jahr.strip():
        sj = SS.Satz(jahr, schrift)
        hs = 0.13 * S
        ws = 0.32 * S
        ys0 = _breit_ab(innen, ws + 0.06 * S, y0) - rb * 0.5
        sx0 = -ws / 2
        schild = W.abrunden(K.rect(sx0, ys0, ws, hs + rb * 0.5), hs * 0.42, 8)
        mat = mat.union(lw.flaechen([schild]))
        inner_s = W.abrunden(K.rect(sx0 + 0.9, ys0 + rb * 0.5 + 0.9, ws - 1.8, hs - 1.8), hs * 0.32, 8)
        gravuren.append((inner_s + [inner_s[0]], False))
        ym = ys0 + rb * 0.5 + hs / 2
        kj = min((hs - 3.2) / sj.hoehe, (ws - 6.0) / sj.breite)
        schild_text = sj.in_mm((0.0, ym), kj)
        unten = ys0 + rb * 0.5 + hs

    # Mitte: der Name als Schriftzug von Ring zu Ring
    luft = 0.025 * S
    a, b = unten + luft, oben - luft
    if b - a < 0.15 * S:
        raise ValueError("Für Name, Zier und Jahreszahl ist der Anhänger zu klein – größer wählen")
    sn = SS.Satz(name, schrift, sperrung=-0.02)
    mitte = (a + b) / 2
    h_max = min(b - a, 0.42 * H)
    # so breit, dass der Name links und rechts in den Ring reicht – höchstens so hoch wie der Platz erlaubt
    k = h_max / sn.hoehe
    for _ in range(12):
        hh = sn.hoehe * k / 2
        hb = _halbbreite(innen, mitte - hh * 0.4, mitte + hh * 0.4)
        ziel = hb + rb * 0.45
        if sn.breite * k / 2 <= ziel:
            break
        k *= ziel / (sn.breite * k / 2)
    if sn.x_mm(k) < 3.2:
        raise ValueError(f"Der Name „{name}“ ist für einen ausgeschnittenen Schriftzug zu lang – kürzer fassen, "
                         f"größer wählen oder die Ausführung „Medaillon“ nehmen")
    polys = sn.in_mm((0.0, mitte), k)
    txt = _laserfest(lw, SS.raster(lw, polys), max(0.0, (web + kerf + 0.5 - _STIEL[schrift] * k) / 2), web, kerf)
    txt = E._and(txt, lw.flaechen([FG.feld(fm.umriss, 0.3)]))
    # Schwungbänder: vom Ring zur ersten und letzten Buchstabenkante, auf Höhe der Verbindungsstriche
    yb = sn.grundlinie((0.0, mitte), k) + 0.32 * sn.x_mm(k)
    row = int((lw.y_top - yb) / lw.px)
    band = 0
    for r in range(max(0, row - lw.px_fuer(wb / 2)), min(txt.h, row + lw.px_fuer(wb / 2) + 1)):
        band |= txt.rows[r]
    if band:
        xl = lw.x0 + ((band & -band).bit_length() - 1) * lw.px
        xr = lw.x0 + (band.bit_length() - 1) * lw.px
        il, ir = E.quer_x(innen, yb)
        schwung = []
        if xl > il + 0.2:
            schwung.append(K.stroke([(il - rb * 0.4, yb - 0.05 * S * 0.0), ((il + xl) / 2, yb - 0.012 * S),
                                     (xl + 1.2, yb)], wb + 0.5, wb, "rund"))
        if xr < ir - 0.2:
            schwung.append(K.stroke([(xr - 1.2, yb), ((ir + xr) / 2, yb - 0.012 * S), (ir + rb * 0.4, yb)],
                                    wb, wb + 0.5, "rund"))
        if schwung:
            txt = txt.union(lw.flaechen(schwung))
    mat = mat.union(txt)
    mat = _inseln_verbinden(lw, mat, wb)
    mat = E._andnot(mat, lw.flaechen([fm.loch]))
    p = E.teil_aus_raster(tag, lw, mat, web, kerf, notes)
    _gravuren_setzen(p, lw, gravuren)
    if schild_text:
        _text_gravieren(p, lw, schild_text, "gefuellt")
    fm.gravur_krone(p)
    return [p]


# --------------------------------------------------------------------------------------------------

def _namen(namen: str) -> List[str]:
    return [n.strip() for n in namen.replace("\n", "|").split("|") if n.strip()]


def build(cfg, name: str = "namensanhaenger", namen: str = "Emma|Paul", schrift: str = "schwungvoll",
          jahr: str = "2026", zeile: str = "", ausfuehrung: str = "schriftzug", form: str = "kugel",
          groesse: float = 90.0, szene: str = "winterdorf", zier: str = "stern", rahmen: str = "bluetenkranz",
          gravur: str = "gefuellt"):
    for key, val, opts in (("Ausführung", ausfuehrung, AUSFUEHRUNGEN), ("Form", form, FORMEN), ("Zier", zier, ZIER), ("Szene", szene, SZ.SZENEN),
                           ("Spitzenrahmen", rahmen, RAHMEN), ("Gravur", gravur, GRAVUR),
                           ("Schreibschrift", schrift, SS.SCHRIFTEN)):
        if val not in dict(opts):
            raise ValueError(f"{key}: unbekannte Auswahl {val!r}")
    liste = _namen(namen)
    if not liste:
        raise ValueError("Bitte mindestens einen Namen eingeben.")
    if ausfuehrung == "schriftzug":
        zeile = ""
        if form == "herz":                                    # im Herz hängt die Öse in der Kerbe – kein Platz für Zier
            zier = "ohne"
    bad = SS.fehlende(" ".join(liste) + jahr + zeile, schrift)
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Schreibschrift nicht")
    S = cfg.s(groesse)
    if S < 55:
        raise ValueError("Der Anhänger ist zu klein – mindestens 60 mm Höhe")
    asm = Assembly(name, params=dict(ausfuehrung=ausfuehrung, form=form, groesse=S, schrift=schrift))
    notes: List[str] = []
    fm = Form(cfg, form, S)
    lw = fm.leinwand()
    gesehen = {}
    for nm in liste:
        tag = "".join(c if c.isalnum() else "_" for c in nm.lower()) or "name"
        gesehen[tag] = gesehen.get(tag, 0) + 1
        if gesehen[tag] > 1:
            tag += f"_{gesehen[tag]}"
        if ausfuehrung == "schriftzug":
            asm.parts += _schriftzug_anhaenger(cfg, fm, lw, tag, nm, schrift, jahr, zier, szene,
                                               cfg.seed + len(asm.parts), notes)
        else:
            asm.parts += _flaeche_anhaenger(cfg, fm, lw, tag, nm, schrift, jahr, zeile, rahmen, gravur,
                                            ausfuehrung, notes)
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes.append("Aufhängen: Band oder Kordel durch die Öse ziehen.")
    T = cfg.T
    if ausfuehrung == "schriftzug":
        asm.notes.append("Tipp: Den Schriftzug vorsichtig aus der Platte drücken; die feinen Brücken an i-Punkten "
                         "und Umlauten gehören dazu. Am edelsten in 3 mm Ahorn, Kirsche oder Nussbaum, geölt.")
        if T < 2.5:
            asm.notes.append(f"Tipp: Für ausgeschnittene Schriftzüge sind 3 mm stabiler (eingestellt: {T:g} mm).")
    elif ausfuehrung == "medaillon":
        asm.notes.append("Zusammenbau: Den Spitzenrahmen deckungsgleich auf die Grundplatte kleben (Öse auf Öse), "
                         "Holzleim dünn mit einem Zahnstocher nur auf die Ränder geben und kurz beschweren.")
        asm.notes.append("Tipp: Zwei Holzfarben machen den Reiz aus – heller Ahorn als Grundplatte, Kirsche oder "
                         "Nussbaum für den Rahmen. Der Rahmen wirkt in 1,5–2 mm am feinsten.")
    else:
        asm.notes.append("Tipp: Für die Spitze sind 2–3 mm Pappel oder Ahorn ideal. Die Gravur vor dem Herauslösen "
                         "mit Klebeband (Maler-Krepp) abdecken, dann bleibt das Holz um den Namen sauber.")
    if ausfuehrung != "schriftzug":
        asm.notes.append("xTool Creative Space: Die Gravurebene ist für „Linie“ (Ritzen) angelegt; die dichten "
                         "Linien ergeben eine gefüllte Schrift. Niedrige Leistung wählen, sonst brennen sie zusammen.")
    return asm
