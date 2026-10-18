"""
Wichtelfigur – Paket „Wichtelwelt“.

Ein Wichtel aus fünf Lagen: hinten die Grundform (Mütze, Bart, Mantel, Schuhe, Arme und was er in der Hand
hält), darauf der Bart mit gravierten Locken, der Schnurrbart, die Mütze mit ausgeschnittenem Muster und
gestrickter Krempe und ganz vorne die Nase. Die Grundform steckt mit einem Zapfen in einem Schneehügel,
auf den der Name graviert werden kann. Auf Wunsch eine ganze Wichtelfamilie in drei Größen.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, offset_polygon, oriented
from pakete import integer, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtelwelt__lade_figur",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.welt()
Z, K = M.Z, M.K

HAELT = [("keins", "nichts"), ("laterne", "Laterne"), ("stern", "Stern am Stab"), ("herz", "Herz"),
         ("geschenk", "Geschenk")]
BAERTE = [("lockig", "lockig"), ("glatt", "glatt"), ("zottelig", "zottelig")]
SPITZE = [("rechts", "nach rechts"), ("links", "nach links")]

UEBERSETZUNG = {"en": {
    "Wichtelfigur": "Gnome figure", "Wichtelwelt": "Elf world",
    "Wichtel aus fünf Lagen: Mütze mit Muster und Strickkrempe, Bart mit Locken, Nase – steht in einem Schneehügel mit Namen.":
        "Gnome made of five layers: patterned hat with knitted brim, curly beard, nose – stands in a snow mound with a name.",
    "Höhe": "Height", "Mützenmuster": "Hat pattern", "Hält": "Holds", "Bart": "Beard", "Mützenspitze": "Hat tip",
    "Name auf dem Sockel": "Name on the base", "Familie": "Family",
    "Streifen": "Stripes", "Sterne": "Stars", "Punkte": "Dots", "Herzen": "Hearts", "Zickzack": "Zigzag",
    "glatt": "plain", "nichts": "nothing", "Laterne": "Lantern", "Stern am Stab": "Star on a stick", "Herz": "Heart",
    "Geschenk": "Present", "lockig": "curly", "zottelig": "shaggy", "nach rechts": "to the right",
    "nach links": "to the left",
    "Anzahl Wichtel: 2 = Paar, 3–4 = Familie in drei Größen mit wechselnden Mustern":
        "Number of gnomes: 2 = couple, 3–4 = family in three sizes with changing patterns",
    "Lagen von hinten nach vorne aufeinanderleimen: Grundform – Bart – Schnurrbart – Mütze – Nase, zuletzt Herz, Stern oder Geschenk. Die Umrisse zeigen, wo jede Lage sitzt.":
        "Glue the layers from back to front: base – beard – moustache – hat – nose, then the heart, star or present. The outlines show where each layer sits.",
    "Die Grundform mit dem Zapfen in den Schneehügel stecken.": "Push the base with its tab into the snow mound.",
    "Tipp: Mütze und Nase vor dem Leimen anmalen oder aus rotem Acryl lasern – durch die Musterlöcher scheint die Grundform.":
        "Tip: paint the hat and nose before gluing or cut them from red acrylic – the base shows through the pattern holes.",
}}

INFO = dict(
    label="Wichtelfigur", group="Wichtelwelt",
    desc="Wichtel aus fünf Lagen: Mütze mit Muster und Strickkrempe, Bart mit Locken, Nase – steht in einem "
         "Schneehügel mit Namen.",
    params=[
        num("hoehe", "Höhe", 110, 60, 300),
        sel("muster", "Mützenmuster", M.MUSTER, "streifen"),
        sel("haelt", "Hält", HAELT, "laterne"),
        sel("bart", "Bart", BAERTE, "lockig"),
        sel("spitze", "Mützenspitze", SPITZE, "rechts"),
        txt("sockeltext", "Name auf dem Sockel", "Fridolin", "leer = Schneeflocken; bei einer Familie die Namen mit | trennen", maxlen=24, symbols=True),
        integer("familie", "Familie", 1, 1, 4,
                help="Anzahl Wichtel: 2 = Paar, 3–4 = Familie in drei Größen mit wechselnden Mustern"),
    ],
)

RAND = 0.9          # so weit schaut die Grundform unter den Lagen hervor (mm)


# --------------------------------------------------------------------------------------------------
# Formen (u = Höhe der Figur ohne Bommel, x = 0 Mitte, y = 0 Boden)
# --------------------------------------------------------------------------------------------------

def _s(u, pts):
    return [(x * u, y * u) for x, y in pts]


def muetze(u: float, unten: float = 0.0) -> list:
    """Zipfelmütze, Spitze nach rechts. unten > 0: nur der Teil oberhalb der Krempe (für das Muster)."""
    b = 0.45
    pts = [(-0.27, b + 0.012), (-0.135, b - 0.02), (0.0, b - 0.03), (0.135, b - 0.02), (0.27, b + 0.012),
           (0.262, 0.55), (0.215, 0.665), (0.18, 0.765), (0.185, 0.85), (0.235, 0.905), (0.31, 0.928),
           (0.25, 0.968), (0.14, 0.982), (0.02, 0.93), (-0.10, 0.83), (-0.20, 0.685), (-0.258, 0.56)]
    poly = K.spline(_s(u, pts), closed=True, n=8, tension=0.55)
    if unten:
        poly = _ueber(poly, unten)
    return poly


def krempe_oben(u: float, x: float) -> float:
    """Oberkante der Strickkrempe über x."""
    t = x / (0.27 * u)
    return u * (0.452 + 0.066 - 0.03 * (1 - t * t))


def krempe_unten(u: float, x: float) -> float:
    t = x / (0.27 * u)
    return u * (0.45 - 0.03 * (1 - t * t))


def _ueber(poly, y_t):
    """Teil eines Polygons oberhalb einer Kurve y_t(x) (Sutherland–Hodgman gegen y > y_t(x))."""
    f = (lambda x: y_t(x)) if callable(y_t) else (lambda x: y_t)
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i - 1], poly[i]
        ia, ib = a[1] > f(a[0]), b[1] > f(b[0])
        if ia != ib:
            lo, hi = 0.0, 1.0
            for _ in range(30):
                m = (lo + hi) / 2
                p = (a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m)
                if (p[1] > f(p[0])) == ia:
                    lo = m
                else:
                    hi = m
            out.append((a[0] + (b[0] - a[0]) * lo, a[1] + (b[1] - a[1]) * lo))
        if ib:
            out.append(b)
    return out


def bart_umriss(u: float) -> list:
    pts = [(-0.245, 0.47), (-0.272, 0.37), (-0.238, 0.25), (-0.155, 0.152), (-0.062, 0.102), (0.0, 0.088),
           (0.062, 0.102), (0.155, 0.152), (0.238, 0.25), (0.272, 0.37), (0.245, 0.47), (0.12, 0.488),
           (0.0, 0.492), (-0.12, 0.488)]
    return K.spline(_s(u, pts), closed=True, n=8, tension=0.5)


def bart_figur(u: float, stil: str, w: float) -> "Z.Figur":
    """Bart mit Lockenkante (lockig) oder Zotteln (zottelig)."""
    p = bart_umriss(u)
    fig = Z.Figur().add(p)
    if stil == "glatt":
        return fig
    unten = [q for q in Z.entlang(p, u * (0.05 if stil == "lockig" else 0.035)) if q[0][1] < 0.40 * u]
    for (x, y), (tx, ty) in unten:
        nx, ny = ty, -tx                                   # außen (Kontur CCW)
        if stil == "lockig":
            r = u * 0.03
            fig.add(K.circle(x - nx * r * 0.35, y - ny * r * 0.35, r, 20))
        else:
            L = u * 0.045
            a = (x - tx * L * 0.3, y - ty * L * 0.3)
            b = (x + tx * L * 0.3, y + ty * L * 0.3)
            fig.add([a, (x + nx * L, y + ny * L), b])
    return fig


def schnurrbart(u: float, w: float) -> list:
    """Zwei geschwungene Bartlocken unter der Nase (eine Fläche)."""
    polys = []
    for s in (1, -1):
        path = K.bez3((0.0, 0.405 * u), (s * 0.07 * u, 0.365 * u), (s * 0.16 * u, 0.355 * u), (s * 0.215 * u, 0.40 * u), 16)
        polys.append(K.stroke(path, 0.075 * u, max(0.024 * u, 1.6 * w), "rund"))
    polys.append(K.ellipse(0, 0.405 * u, 0.055 * u, 0.04 * u, 0, 24))
    return polys


def nase(u: float) -> list:
    return K.ellipse(0, 0.452 * u, 0.072 * u, 0.062 * u, 0, 40)


def mantel(u: float) -> list:
    return Z.abrunden(_s(u, [(-0.25, 0.045), (0.25, 0.045), (0.225, 0.40), (-0.225, 0.40)]), 0.04 * u)


def schuhe(u: float) -> list:
    out = []
    for s in (1, -1):
        p = _s(u, [(0.02, 0.0), (0.27, 0.0), (0.285, 0.03), (0.23, 0.074), (0.02, 0.07)])
        out.append(Z.abrunden([(s * x, y) for x, y in (p if s > 0 else reversed(p))], 0.02 * u))
    out.append(K.rect(-0.04 * u, 0, 0.08 * u, 0.05 * u))
    return out


def faeustling(x: float, y: float, r: float, s: int = 1) -> list:
    return [K.circle(x, y, r, 28), K.ellipse(x + s * r * 0.75, y + r * 0.45, r * 0.42, r * 0.3, s * 0.6, 16)]


# --------------------------------------------------------------------------------------------------
# Was der Wichtel hält
# --------------------------------------------------------------------------------------------------

def haelt_grund(u: float, art: str, w: float):
    """Arme und Gegenstand in der Grundform. Liefert (Figur, Löcher, Ankerpunkte für Gravur)."""
    fig = Z.Figur()
    aw = 0.095 * u
    if art == "laterne":
        fig.line([(-0.19 * u, 0.36 * u), (-0.285 * u, 0.27 * u), (-0.27 * u, 0.2 * u)], aw, aw * 0.85)
        fig.add(*faeustling(-0.265 * u, 0.185 * u, 0.048 * u, -1))
        fig.line([(0.19 * u, 0.36 * u), (0.30 * u, 0.31 * u), (0.335 * u, 0.255 * u)], aw, aw * 0.85)
        fig.add(*faeustling(0.34 * u, 0.24 * u, 0.048 * u, 1))
        # Laterne am Bügel
        cx, top = 0.375 * u, 0.205 * u
        bw, bh = 0.105 * u, 0.12 * u
        fig.line(K.arc(cx, top + 0.005 * u, 0.04 * u, math.pi * 0.05, math.pi * 0.95, 16), max(1.5 * w, 0.012 * u))
        fig.add([(cx - bw * 0.62, top - 0.03 * u), (cx + bw * 0.62, top - 0.03 * u), (cx + bw * 0.15, top + 0.005 * u),
                 (cx - bw * 0.15, top + 0.005 * u)])
        fig.add(K.circle(cx, top + 0.012 * u, 0.014 * u, 12))
        fig.add([(cx - bw / 2, top - 0.03 * u - bh), (cx + bw / 2, top - 0.03 * u - bh),
                 (cx + bw * 0.6, top - 0.03 * u), (cx - bw * 0.6, top - 0.03 * u)])
        fig.add(K.rect(cx - bw * 0.62, top - 0.03 * u - bh - 0.02 * u, bw * 1.24, 0.022 * u))
        g = bh * 0.72
        yy = top - 0.03 * u - bh / 2
        loecher = []
        sp = max(1.4 * w, 0.012 * u)
        for sx in (-1, 1):
            for sy in (-1, 1):
                x0 = cx + (sx * sp / 2 if sx > 0 else -bw * 0.34)
                y0 = yy + (sy * sp / 2 if sy > 0 else -g / 2)
                loecher.append(K.rect(x0, y0, bw * 0.34 - sp / 2, g / 2 - sp / 2))
        fig.cut(*loecher)
        return fig
    if art == "stern":
        fig.line([(-0.19 * u, 0.36 * u), (-0.285 * u, 0.27 * u), (-0.27 * u, 0.2 * u)], aw, aw * 0.85)
        fig.add(*faeustling(-0.265 * u, 0.185 * u, 0.048 * u, -1))
        fig.line([(0.19 * u, 0.37 * u), (0.30 * u, 0.40 * u), (0.34 * u, 0.46 * u)], aw, aw * 0.85)
        fig.line([(0.36 * u, 0.40 * u), (0.40 * u, 0.70 * u)], max(2.2 * w, 0.026 * u))
        fig.add(*faeustling(0.355 * u, 0.475 * u, 0.048 * u, 1))
        fig.add(K.star(0.405 * u, 0.745 * u, 0.1 * u, 0.045 * u, 5))
        return fig
    # keins, herz, geschenk: Arme hängen an den Seiten bzw. kommen nach vorne
    for s in (1, -1):
        if art == "keins":
            fig.line([(s * 0.19 * u, 0.36 * u), (s * 0.285 * u, 0.27 * u), (s * 0.27 * u, 0.2 * u)], aw, aw * 0.85)
            fig.add(*faeustling(s * 0.265 * u, 0.185 * u, 0.048 * u, s))
        else:
            fig.line([(s * 0.19 * u, 0.36 * u), (s * 0.275 * u, 0.28 * u), (s * 0.2 * u, 0.22 * u)], aw, aw * 0.85)
    return fig


def haelt_lage(u: float, art: str, w: float):
    """Gegenstand als eigene Lage vor dem Bart (Herz, Geschenk, Stern) mit Fäustlingen. None = keine Lage."""
    if art == "herz":
        fig = Z.Figur().add(Z.herz(0, 0.2 * u, 0.24 * u))
        for s in (1, -1):
            fig.add(*faeustling(s * 0.112 * u, 0.215 * u, 0.034 * u, -s))
        return fig
    if art == "geschenk":
        fig = Z.Figur().add(Z.abrunden([(-0.12 * u, 0.1 * u), (0.12 * u, 0.1 * u), (0.12 * u, 0.26 * u),
                                        (-0.12 * u, 0.26 * u)], 0.012 * u))
        for s in (1, -1):                              # Schleife
            fig.add(K.ellipse(s * 0.045 * u, 0.285 * u, 0.05 * u, 0.028 * u, s * 0.5, 24))
            fig.add(*faeustling(s * 0.13 * u, 0.17 * u, 0.034 * u, -s))
        fig.add(K.circle(0, 0.27 * u, 0.02 * u, 14))
        return fig
    if art == "stern":
        return Z.Figur().add(K.star(0.405 * u, 0.745 * u, 0.1 * u - RAND, 0.045 * u - RAND * 0.5, 5))
    return None


def haelt_gravur(u: float, art: str):
    lin = []
    if art == "herz":
        lin.append((Z.herz(0, 0.2 * u, 0.17 * u), True))
    elif art == "geschenk":
        lin += [([(0, 0.1 * u), (0, 0.26 * u)], False), ([(-0.12 * u, 0.18 * u), (0.12 * u, 0.18 * u)], False)]
        lin += [([(-0.045 * u, 0.285 * u), (-0.02 * u, 0.275 * u)], False),
                ([(0.045 * u, 0.285 * u), (0.02 * u, 0.275 * u)], False)]
    elif art == "stern":
        lin.append((K.star(0.405 * u, 0.745 * u, 0.055 * u, 0.025 * u, 5), True))
    return lin


# --------------------------------------------------------------------------------------------------
# Gravuren
# --------------------------------------------------------------------------------------------------

def locken(u: float, stil: str):
    """Bartsträhnen von oben zur Spitze, leicht geschwungen."""
    lin = []
    n = 7 if stil != "zottelig" else 9
    for i in range(n):
        t = -1 + 2 * i / (n - 1)
        x0 = t * 0.2 * u
        pts = [(x0, 0.40 * u), (x0 * 0.92 + 0.012 * u, 0.33 * u), (x0 * 0.72 - 0.01 * u, 0.25 * u),
               (x0 * 0.5, 0.17 * u + abs(t) * 0.03 * u)]
        if stil == "lockig":
            ex, ey = pts[-1]
            pts += [(ex + 0.012 * u * (1 if t >= 0 else -1), ey - 0.012 * u),
                    (ex + 0.022 * u * (1 if t >= 0 else -1), ey + 0.002 * u)]
        lin.append((K.spline(pts, n=6), False))
    return lin


def krempe_gravur(u: float):
    lin = []
    xs = [-0.262 * u + i * 0.524 * u / 40 for i in range(41)]
    lin.append(([(x, krempe_oben(u, x)) for x in xs], False))
    n = 15
    for i in range(1, n):
        x = -0.25 * u + 0.5 * u * i / n
        lin.append(([(x, krempe_unten(u, x) + 0.012 * u), (x, krempe_oben(u, x) - 0.01 * u)], False))
    return lin


def falten(u: float):
    """Knautschfalten an der umgeknickten Spitze."""
    return [(K.bez((0.15 * u, 0.83 * u), (0.18 * u, 0.88 * u), (0.24 * u, 0.90 * u), 10), False),
            (K.bez((0.05 * u, 0.86 * u), (0.12 * u, 0.93 * u), (0.2 * u, 0.95 * u), 10), False)]


def _gross(poly, d):
    return offset_polygon(oriented(list(poly), True), d)


# --------------------------------------------------------------------------------------------------
# Bauen
# --------------------------------------------------------------------------------------------------

FAMILIE = [(1.0, None, None), (0.86, "punkte", "herz"), (0.7, "sterne", "stern"), (0.62, "herzen", "geschenk")]


def build(cfg, name="wichtelfigur", hoehe=110.0, muster="streifen", haelt="laterne", bart="lockig",
          spitze="rechts", sockeltext="Fridolin", familie=1):
    text = sockeltext
    familie = max(1, min(4, int(familie)))
    if familie == 1:
        return _wichtel(cfg, name, cfg.s(hoehe), muster, haelt, bart, spitze, text, 1)
    out = []
    namen = [t.strip() for t in text.split("|")] if "|" in text else [text] + [""] * 3
    muster_folge = [m for m, _ in M.MUSTER if m != "glatt"]
    for i in range(familie):
        f, mu, ha = FAMILIE[i]
        if i:
            mu = muster_folge[(muster_folge.index(muster) + i) % len(muster_folge)] if muster in muster_folge else mu
        out.append(_wichtel(cfg, f"{name}_{i + 1}", cfg.s(hoehe) * f, mu or muster, ha or haelt, bart,
                            spitze if i % 2 == 0 else ("links" if spitze == "rechts" else "rechts"),
                            namen[i] if i < len(namen) else "", i + 1))
    return out


def _wichtel(cfg, name, u, muster, haelt, bart, spitze, text, seed):
    T = cfg.T
    w = Z.wmin(cfg)
    if u < 55:
        raise ValueError("Für so viele Details ist der Wichtel zu klein – mindestens 60 mm hoch machen")
    notes = []
    asm = Assembly(name, params=dict(hoehe=u, muster=muster, haelt=haelt, bart=bart))
    spiegel = (lambda p: (-p[0], p[1])) if spitze == "links" else None

    def fertig(part):
        return Z.abbilden(part, spiegel) if spiegel else part

    # --- Grundform ---
    g = Z.Figur()
    g.add(_gross(muetze(u), RAND), K.circle(0.33 * u, 0.93 * u, 0.058 * u + RAND, 32))
    g.add(_gross(bart_umriss(u), RAND), mantel(u), *schuhe(u))
    g.add(*[_gross(p, RAND) for p in schnurrbart(u, w)])
    g.merge(haelt_grund(u, haelt, w))
    grund = Z.figur_teil(cfg, "grundform", g, notes, unten_flach=True)
    tw = M.tabbreite(cfg, 0.3 * u, 0.5)
    Z.zapfen_unten(grund, 0.0, tw, T, "fuss", pos=10)
    lin = [([(0, 0.008 * u), (0, 0.042 * u)], False)]                         # zwischen den Schuhen
    for s in (1, -1):                                                         # Schuhsohlen und Schnürung
        lin.append(([(s * 0.05 * u, 0.018 * u), (s * 0.26 * u, 0.018 * u)], False))
        lin.append(([(s * 0.12 * u, 0.045 * u), (s * 0.15 * u, 0.06 * u), (s * 0.18 * u, 0.045 * u)], False))
    for k in range(9):                                                        # Saumnaht
        x = -0.2 * u + 0.4 * u * k / 8
        lin.append(([(x - 0.012 * u, 0.088 * u), (x + 0.012 * u, 0.088 * u)], False))
    Z.gravur(grund, lin, rand=0.7)
    asm.parts.append(fertig(grund))
    # --- Bart ---
    bt = Z.figur_teil(cfg, "bart", bart_figur(u, bart, w), notes)
    Z.gravur(bt, locken(u, bart), rand=0.9)
    asm.parts.append(fertig(bt))
    # --- Schnurrbart ---
    sb = Z.figur_teil(cfg, "schnurrbart", Z.Figur().add(*schnurrbart(u, w)), notes)
    Z.gravur(sb, [(K.bez3((s * 0.02 * u, 0.395 * u), (s * 0.08 * u, 0.37 * u), (s * 0.14 * u, 0.37 * u),
                          (s * 0.19 * u, 0.40 * u), 12), False) for s in (1, -1)], rand=0.6)
    asm.parts.append(fertig(sb))
    # --- Mütze mit Muster ---
    hut = muetze(u)
    mfig = Z.Figur().add(hut, K.circle(0.33 * u, 0.93 * u, 0.058 * u, 32))
    maske = M.innen(muetze(u, lambda x: krempe_oben(u, x) + 0.012 * u), max(1.6 * w, 0.025 * u))
    loecher = []
    if muster != "glatt" and maske:
        achse = math.atan2(0.93 - 0.48, 0.25)                                 # grob entlang der Mütze
        loecher = M.muster_loecher(muster, maske, max(0.058 * u, 3.2 * w), w, achse, (0, 0.5 * u))
    mu = M.teil(cfg, "muetze", mfig, notes, muster=loecher, maske=maske)
    lin = krempe_gravur(u) + (falten(u) if muster == "glatt" else [])
    for a in range(6):                                                        # Bommel
        aa = math.pi * a / 3
        lin.append(([(0.33 * u, 0.93 * u), (0.33 * u + math.cos(aa) * 0.04 * u, 0.93 * u + math.sin(aa) * 0.04 * u)],
                    False))
    Z.gravur(mu, lin, rand=0.7)
    asm.parts.append(fertig(mu))
    # --- Nase ---
    na = Z.figur_teil(cfg, "nase", Z.Figur().add(nase(u)), notes)
    Z.gravur(na, [(K.arc(0.022 * u, 0.468 * u, 0.02 * u, math.pi * 0.3, math.pi * 0.9, 8), False)], rand=0.5)
    asm.parts.append(fertig(na))
    # --- Gegenstand als Lage ---
    lage = haelt_lage(u, haelt, w)
    if lage is not None:
        hl = Z.figur_teil(cfg, haelt, lage, notes)
        Z.gravur(hl, haelt_gravur(u, haelt), rand=0.8)
        asm.parts.append(fertig(hl))
    # --- Sockel ---
    rx, ry = 0.36 * u, max(0.17 * u, 3 * T + 8)
    so = M.sockel(cfg, "sockel", rx, ry, [("figur", 0.0, ry * 0.3, tw, 10)], text, seed)
    asm.parts.append(so)
    asm.connect("grundform:fuss", "sockel:figur")
    asm.notes.append("Lagen von hinten nach vorne aufeinanderleimen: Grundform – Bart – Schnurrbart – Mütze – Nase, "
                     "zuletzt Herz, Stern oder Geschenk. Die Umrisse zeigen, wo jede Lage sitzt.")
    asm.notes.append("Die Grundform mit dem Zapfen in den Schneehügel stecken.")
    asm.notes.append("Tipp: Mütze und Nase vor dem Leimen anmalen oder aus rotem Acryl lasern – durch die "
                     "Musterlöcher scheint die Grundform.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
