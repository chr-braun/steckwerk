"""
Lattenzaun – Paket „Wichtelwelt“.

Ein Gartenzaun mit Tor für die Wichtelwelt: zwei Zaunfelder mit Pfosten und Kugelkappen, Latten mit spitzer,
runder oder gotischer Spitze, Querriegel mit Nägeln und Maserung, dazwischen ein Tor mit Bogen, Herz und
Z-Strebe. Auf Wunsch liegt Schnee auf Pfosten und Latten. Alles steht in kleinen Schneehügeln.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import flag, num, sel

_spec = importlib.util.spec_from_file_location("swpaket_wichtelwelt__lade_zaun",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.welt()
Z, K = M.Z, M.K

SPITZEN = [("spitz", "spitz"), ("rund", "rund"), ("gotisch", "gotisch"), ("gerade", "gerade")]
KAPPEN = [("kugel", "Kugel"), ("herz", "Herz"), ("stern", "Stern"), ("dach", "Dach")]

UEBERSETZUNG = {"en": {
    "Lattenzaun": "Picket fence", "Wichtelwelt": "Elf world",
    "Gartenzaun mit Tor: Zaunfelder mit Pfosten und Kappen, Latten mit Maserung und Nägeln, Tor mit Bogen und Herz, auf Wunsch mit Schnee.":
        "Garden fence with gate: fence panels with posts and caps, pickets with grain and nails, arched gate with heart, snow if you like.",
    "Länge": "Length", "Höhe": "Height", "Lattenspitze": "Picket top", "Pfostenkappe": "Post cap", "Tor": "Gate",
    "Schnee": "Snow", "spitz": "pointed", "rund": "round", "gotisch": "gothic", "gerade": "straight", "Kugel": "Ball",
    "Herz": "Heart", "Stern": "Star", "Dach": "Roof",
    "Die Zaunfelder mit den Zapfen unter den Pfosten in die Schneehügel stecken, das Tor in die Schwelle.":
        "Push the fence panels with the tabs under the posts into the snow mounds, and the gate into the threshold.",
    "Das Tor steht zwischen den beiden Feldern – leicht schräg gestellt sieht es aus wie offen.":
        "The gate stands between the two panels – set it at a slight angle and it looks open.",
}}

INFO = dict(
    label="Lattenzaun", group="Wichtelwelt",
    desc="Gartenzaun mit Tor: Zaunfelder mit Pfosten und Kappen, Latten mit Maserung und Nägeln, Tor mit Bogen und "
         "Herz, auf Wunsch mit Schnee.",
    params=[
        num("laenge", "Länge", 180, 80, 400, help="Gesamtlänge beider Felder und des Tors"),
        num("hoehe", "Höhe", 45, 25, 120),
        sel("spitze", "Lattenspitze", SPITZEN, "spitz"),
        sel("kappe", "Pfostenkappe", KAPPEN, "kugel"),
        flag("tor", "Tor", True),
        flag("schnee", "Schnee", False),
    ],
)


def latte(x0: float, b: float, h: float, spitze: str, y0: float = 0.0):
    """Latte von y0 bis h (Spitze inklusive), Breite b ab x0."""
    if spitze == "spitz":
        return [(x0, y0), (x0 + b, y0), (x0 + b, h - b * 0.6), (x0 + b / 2, h), (x0, h - b * 0.6)]
    if spitze == "rund":
        return [(x0, y0), (x0 + b, y0)] + K.arc(x0 + b / 2, h - b / 2, b / 2, 0, math.pi, 12)[:-1] + [(x0, h - b / 2)]
    if spitze == "gotisch":
        return [(x0, y0), (x0 + b, y0), (x0 + b, h - b * 0.9)] + \
            K.bez((x0 + b, h - b * 0.9), (x0 + b, h - b * 0.25), (x0 + b / 2, h), 8)[1:] + \
            K.bez((x0 + b / 2, h), (x0, h - b * 0.25), (x0, h - b * 0.9), 8)[1:-1]
    return [(x0, y0), (x0 + b, y0), (x0 + b, h), (x0, h)]


def kappe(fig, cx: float, y: float, pp: float, art: str):
    if art == "herz":
        fig.add(Z.herz(cx, y + pp * 0.55, pp * 1.5))
    elif art == "stern":
        fig.add(K.star(cx, y + pp * 0.6, pp * 0.95, pp * 0.42, 5))
    elif art == "dach":
        fig.add([(cx - pp * 0.75, y - pp * 0.1), (cx + pp * 0.75, y - pp * 0.1), (cx, y + pp * 0.9)])
    else:
        fig.add(K.rect(cx - pp * 0.3, y - 0.5, pp * 0.6, pp * 0.35 + 0.5))
        fig.add(K.circle(cx, y + pp * 0.75, pp * 0.52, 28))


def schneehaube(fig, cx: float, y: float, b: float, seed: int):
    """Kleine Schneehaube über einer Spitze (überlappt sie)."""
    r = K.rng(seed, "haube")
    fig.add(K.ellipse(cx + K.jitter(r, b * 0.05), y, b * 0.56, b * 0.24, K.jitter(r, 0.12), 20))


def feld(cfg, name: str, Lp: float, Hz: float, spitze: str, kappe_art: str, schnee: bool, notes, w, seed: int,
         pfosten=(True, True)):
    """Zaunfeld x 0 … Lp mit Pfosten an den Enden. Liefert (Teil, Pfostenmitten, Linien für die Gravur)."""
    T = cfg.T
    pp = max(2.6 * T, min(9.0, Hz * 0.17))                   # Pfostenbreite
    b = max(2.2 * T, min(8.0, Hz * 0.14))                    # Lattenbreite
    gp = max(w + 1.2, b * 0.55)                              # Spalt
    fig = Z.Figur()
    ys = (Hz * 0.12, Hz * 0.22)                              # unterer Riegel
    yo = (Hz * 0.58, Hz * 0.68)                              # oberer Riegel
    fig.add(K.rect(0, 0, Lp, ys[1]))                         # Sockelbrett + unterer Riegel
    fig.add(K.rect(0, yo[0], Lp, yo[1] - yo[0]))
    xs_p = []
    a0, a1 = 0.0, Lp
    if pfosten[0]:
        fig.add(K.rect(0, 0, pp, Hz * 1.08))
        kappe(fig, pp / 2, Hz * 1.08, pp, kappe_art)
        xs_p.append(pp / 2)
        a0 = pp + gp
    if pfosten[1]:
        fig.add(K.rect(Lp - pp, 0, pp, Hz * 1.08))
        kappe(fig, Lp - pp / 2, Hz * 1.08, pp, kappe_art)
        xs_p.append(Lp - pp / 2)
        a1 = Lp - pp - gp
    n = max(1, int((a1 - a0 + gp) / (b + gp)))
    gp2 = (a1 - a0 - n * b) / max(1, n - 1) if n > 1 else 0.0
    lx = []
    for i in range(n):
        x = a0 + i * (b + gp2) if n > 1 else (a0 + a1 - b) / 2
        hh = Hz * (0.97 if i % 2 else 1.0)
        fig.add(latte(x, b, hh, spitze))
        lx.append((x, hh))
        if schnee:
            schneehaube(fig, x + b / 2, hh - b * (0.35 if spitze in ("spitz", "gotisch") else 0.15), b, seed * 100 + i)
    if schnee:
        for x in (xs_p if xs_p else []):
            fig.add(K.ellipse(x, Hz * 1.08 + pp * (1.25 if kappe_art == "kugel" else 1.0), pp * 0.55, pp * 0.28, 0, 20))
        # Schneewulst auf dem oberen Riegel
        k = 0
        x = 0.0
        while x + 6.6 < Lp:
            fig.add(K.ellipse(x + 3.3, yo[1], 3.4, 1.4 + (k % 3) * 0.3, 0, 16))
            x += 5.0
            k += 1
    teil = Z.figur_teil(cfg, name, fig, notes, unten_flach=True)
    lin = []
    for x, hh in lx:                                        # Maserung, Nägel
        for yy in ((ys[0] + ys[1]) / 2, (yo[0] + yo[1]) / 2):
            lin.append((K.circle(x + b / 2, yy, 0.45, 8), True))
        lin.append((K.spline([(x + b * 0.35, ys[1] + 1.5), (x + b * 0.45, (ys[1] + yo[0]) / 2), (x + b * 0.38, yo[0] - 1.2)],
                             n=5), False))
    for yy in (ys[0], ys[1], yo[0], yo[1]):                   # Riegelkanten über den Latten
        lin.append(([(a0 - gp * 0.5, yy), (a1 + gp * 0.5, yy)], False))
    lin.append(([(0.8, ys[0] * 0.5), (Lp - 0.8, ys[0] * 0.5)], False))
    for x in xs_p:
        lin.append(([(x, Hz * 0.25), (x + pp * 0.12, Hz * 0.6), (x - pp * 0.08, Hz * 0.95)], False))
    Z.gravur(teil, [l for l in lin if len(l[0]) >= 2], rand=0.6)
    return teil, xs_p, pp, b


def build(cfg, name="lattenzaun", laenge=180.0, hoehe=45.0, spitze="spitz", kappe="kugel", tor=True, schnee=False):
    T = cfg.T
    w = Z.wmin(cfg)
    Lg, Hz = cfg.s(laenge), cfg.s(hoehe)
    if Hz < 6 * T + 8:
        raise ValueError("Der Zaun ist für diese Materialstärke zu niedrig – höher machen")
    notes = []
    asm = Assembly(name, params=dict(laenge=Lg, hoehe=Hz, spitze=spitze, tor=tor))
    tw = M.tabbreite(cfg, max(2.6 * T, min(9.0, Hz * 0.17)), 0.8)
    Bt = max(Hz * 0.9, 32.0) if tor else 0.0
    Lp = (Lg - Bt) / 2 if tor else Lg
    felder = ["feld_links", "feld_rechts"] if tor else ["feld"]
    for k, nm in enumerate(felder):
        teil, xs_p, pp, b = feld(cfg, nm, Lp, Hz, spitze, kappe, schnee, notes, w, k + 1)
        asm.parts.append(teil)
        for i, x in enumerate(xs_p):
            rein = tw / 2 + 3.0                                 # Zapfen nicht direkt an die Außenecke
            x = max(x, rein) if x < Lp / 2 else min(x, Lp - rein)
            Z.zapfen_unten(teil, x, tw, T, f"fuss{i}", pos=10 * (k + 1) + i)
            hg = M.sockel(cfg, f"huegel_{nm[5:] or 'feld'}{i + 1}", max(tw * 1.6, 16.0), max(T * 3 + 5, 10.0),
                          [("pfosten", 0.0, 0.0, tw, 10 * (k + 1) + i)], "", 10 * k + i)
            asm.parts.append(hg)
            asm.connect(f"{nm}:fuss{i}", f"{hg.name}:pfosten")
    if tor:
        tb = Bt - 2.0                                           # etwas Luft zu den Pfosten
        b = max(2.2 * T, min(8.0, Hz * 0.14))
        gp = max(w + 1.2, b * 0.55)
        n = max(3, int((tb + gp) / (b + gp)))
        gp2 = (tb - n * b) / (n - 1)
        fig = Z.Figur()
        ys = (Hz * 0.1, Hz * 0.2)
        yo = (Hz * 0.62, Hz * 0.72)
        fig.add(K.rect(0, ys[0], tb, ys[1] - ys[0]), K.rect(0, yo[0], tb, yo[1] - yo[0]))
        bogen = Hz * 0.18
        for i in range(n):
            x = i * (b + gp2)
            t = (x + b / 2 - tb / 2) / (tb / 2)
            hh = Hz * 0.92 + bogen * (1 - t * t)
            fig.add(latte(x, b, hh, spitze, y0=ys[0] * 0.5))
            if schnee:
                schneehaube(fig, x + b / 2, hh - b * (0.35 if spitze in ("spitz", "gotisch") else 0.15), b, 900 + i)
        fig.add(K.rect(0, 0, tb * 0.3, ys[0] * 0.5 + 0.5), K.rect(tb * 0.7, 0, tb * 0.3, ys[0] * 0.5 + 0.5))
        hz = min(yo[0] - ys[1], tb * 0.45) * 0.75
        fig.cut(Z.herz(tb / 2, (ys[1] + yo[0]) / 2, hz))
        st = Z.figur_teil(cfg, "tor", fig, notes, unten_flach=True)
        xs_t = [tb * 0.15, tb * 0.85]
        twt = max(cfg.min_tab_width + 0.6, min(tw, tb * 0.18))
        for i, x in enumerate(xs_t):
            Z.zapfen_unten(st, x, twt, T, f"fuss{i}", pos=90 + i)
        lin = []
        for yy in (ys[0], ys[1], yo[0], yo[1]):
            lin.append(([(0.6, yy), (tb - 0.6, yy)], False))
        lin.append(([(tb * 0.12, ys[1] + 1.2), (tb * 0.88, yo[0] - 1.2)], False))      # Z-Strebe
        lin.append(([(tb * 0.12 + 2.2, ys[1] + 1.2), (tb * 0.88, yo[0] - 1.2 - 2.0)], False))
        for yy in ((ys[0] + ys[1]) / 2, (yo[0] + yo[1]) / 2):                            # Bänder
            lin.append((Z.abrunden([(0.4, yy - 1.0), (tb * 0.3, yy - 0.6), (tb * 0.3, yy + 0.6), (0.4, yy + 1.0)], 0.4),
                        True))
        lin.append((K.circle(tb * 0.88, (yo[0] + ys[1]) / 2 + 3, 1.0, 10), True))       # Griff
        Z.gravur(st, lin, rand=0.6)
        asm.parts.append(st)
        # Schwelle: flacher Trittstein mit zwei Schlitzen
        sw = M.sockel(cfg, "schwelle", tb * 0.62, max(T * 3 + 5, 10.0),
                      [(f"tor{i}", x - tb / 2, 0.0, twt, 90 + i) for i, x in enumerate(xs_t)], "", 77)
        asm.parts.append(sw)
        for i in range(2):
            asm.connect(f"tor:fuss{i}", f"schwelle:tor{i}")
    asm.notes.append("Die Zaunfelder mit den Zapfen unter den Pfosten in die Schneehügel stecken, das Tor in die Schwelle.")
    if tor:
        asm.notes.append("Das Tor steht zwischen den beiden Feldern – leicht schräg gestellt sieht es aus wie offen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
