"""
Werkbank – Paket „Wichtelwelt“.

Die Wichtelwerkstatt: eine Hobelbank mit Plattenmaserung, zwei Bockbeinen, Fußstrebe, Schraubstock vorne und
einer Lochwand hinten. Dazu eine Werkzeugkiste mit Satteldach-Stirnseiten und Griff (alles gesteckt) und
kleines Werkzeug zum Hinlegen: Säge, Hammer, Zollstock, Schraubenschlüssel und ein Holzscheit.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import flag, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtelwelt__lade_werkbank",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.welt()
Z, K = M.Z, M.K

KISTENMOTIVE = [("stern", "Stern"), ("herz", "Herz"), ("tanne", "Tanne"), ("keine", "keins")]

UEBERSETZUNG = {"en": {
    "Werkbank": "Workbench", "Wichtelwelt": "Elf world",
    "Wichtelwerkstatt: Hobelbank mit Schraubstock und Lochwand, Werkzeugkiste mit Griff, Säge, Hammer, Zollstock und Holzscheit.":
        "Elf workshop: workbench with vice and pegboard, toolbox with handle, saw, hammer, folding rule and a log.",
    "Länge": "Length", "Tiefe": "Depth", "Höhe": "Height", "Lochwand": "Pegboard", "Text auf der Lochwand": "Text on the pegboard",
    "Werkzeugkiste": "Toolbox", "Motiv der Kiste": "Toolbox motif", "Werkzeug": "Tools", "Stern": "Star", "Herz": "Heart",
    "Tanne": "Fir", "keins": "none",
    "Die Bockbeine mit ihren Zapfen von unten in die Platte stecken, die Fußstrebe zwischen die Beine schieben.":
        "Push the trestle legs with their tabs into the top from below and slide the foot rail between the legs.",
    "Die Lochwand hinten in die Platte stecken.": "Push the pegboard into the back of the top.",
    "Den Schraubstock vorne links an die Platte leimen (Backen oben bündig).":
        "Glue the vice to the front left of the top (jaws flush at the top).",
    "Werkzeugkiste: Boden, Seitenwände und Griff mit den Zapfen in die Stirnseiten stecken.":
        "Toolbox: push the bottom, side walls and handle with their tabs into the end panels.",
    "Das Werkzeug auf die Bank legen oder an die Lochwand kleben.": "Lay the tools on the bench or glue them to the pegboard.",
}}

INFO = dict(
    label="Werkbank", group="Wichtelwelt",
    desc="Wichtelwerkstatt: Hobelbank mit Schraubstock und Lochwand, Werkzeugkiste mit Griff, Säge, Hammer, Zollstock "
         "und Holzscheit.",
    params=[
        num("laenge", "Länge", 90, 60, 220),
        num("tiefe", "Tiefe", 36, 25, 90),
        num("hoehe", "Höhe", 48, 30, 120),
        flag("lochwand", "Lochwand", True),
        txt("wandtext", "Text auf der Lochwand", "Wichtelwerkstatt", "leer = nur Löcher", maxlen=30,
            when={"lochwand": [True]}, symbols=True),
        flag("kiste", "Werkzeugkiste", True),
        sel("kistenmotiv", "Motiv der Kiste", KISTENMOTIVE, "stern", when={"kiste": [True]}),
        flag("werkzeug", "Werkzeug", True),
    ],
)

EINZUG = 0.3


def bockbein(cfg, name, D, Hb, tw, zs, notes, w, slot):
    """Bockbein (x = Tiefe 0 … D, y 0 … Hb): zwei schräge Beine, Querriegel, Zapfen oben."""
    T = cfg.T
    bb = max(2.6 * T, D * 0.2)                         # Beinbreite
    sp = D * 0.08                                      # Spreizung unten
    fig = Z.Figur()
    fig.add([(-sp, 0), (bb - sp, 0), (bb + D * 0.05, Hb), (D * 0.05 * 0, Hb)])
    fig.add([(D - bb + sp, 0), (D + sp, 0), (D, Hb), (D - bb - D * 0.05, Hb)])
    fig.add(K.rect(0, Hb - max(2.4 * T, Hb * 0.16), D, max(2.4 * T, Hb * 0.16)))       # Kopfriegel
    yq = Hb * 0.3
    hq = max(2.6 * T, Hb * 0.13)
    fig.add(K.rect(bb * 0.5, yq - hq / 2, D - bb, hq))                                  # Querriegel
    # Kopfriegel mit Bogen unten
    fig.cut(K.ellipse(D / 2, Hb - max(2.4 * T, Hb * 0.16), (D - 2 * bb) / 2 * 0.95, Hb * 0.05, 0, 40))
    rand = max(2.0, T * 0.8)
    cx, cy, L, pos = slot
    solid = [Z.schlitz_polster(cx, cy, L, T, rand, math.pi / 2)]
    # Kopfüber bauen, damit die Oberkante exakt gerade ist und die Zapfen tragen kann
    spiegel = lambda p: (p[0], Hb - p[1])
    fig = fig.map(spiegel)
    part = Z.figur_teil(cfg, name, fig, notes, solid=[[spiegel(q) for q in s] for s in solid], unten_flach=True)
    for x, fid, p in zs:
        Z.zapfen_unten(part, x, tw, T, fid, p)
    part = Z.abbilden(part, spiegel)
    return part, yq, hq, bb


def saege(L, w):
    f = Z.Figur()
    hb = L * 0.24
    f.add([(0, 0), (L * 0.78, hb * 0.35), (L * 0.78, hb), (0, hb * 0.55)])           # Blatt
    for k in range(int(L * 0.7 / 2.2)):                                                # Zähne
        x = 1.2 + k * 2.2
        y = 0 + (hb * 0.35) * x / (L * 0.78)
        f.add([(x, y + 0.5), (x + 1.1, y - 1.1), (x + 2.2, y + 0.5)])
    g = Z.abrunden([(L * 0.74, -hb * 0.15), (L, -hb * 0.05), (L * 1.02, hb * 1.15), (L * 0.74, hb * 1.1)], hb * 0.3)
    f.add(g)
    f.cut(K.ellipse(L * 0.89, hb * 0.5, L * 0.06, hb * 0.28, 0.2, 24))
    return f


def hammer(L, w):
    f = Z.Figur()
    f.add(Z.abrunden([(0, 0), (L * 0.1, 0), (L * 0.1, L * 0.78), (0, L * 0.78)], L * 0.04))
    f.add(Z.abrunden([(-L * 0.18, L * 0.72), (L * 0.3, L * 0.72), (L * 0.32, L), (-L * 0.16, L)], L * 0.03))
    f.add([(L * 0.3, L * 0.74), (L * 0.42, L * 0.8), (L * 0.42, L * 0.9), (L * 0.3, L * 0.98)])
    return f


def zollstock(L):
    return Z.Figur().add(K.rect(0, 0, L, L * 0.13))


def schluessel(L, w):
    f = Z.Figur()
    b = L * 0.14
    f.add(Z.abrunden([(0, -b / 2), (L * 0.8, -b / 2), (L * 0.8, b / 2), (0, b / 2)], b * 0.4))
    f.add(K.circle(L * 0.85, 0, b * 1.1, 32))
    f.cut([(L * 0.88, -b * 0.45), (L * 1.2, -b * 0.6), (L * 1.2, b * 0.6), (L * 0.88, b * 0.45)])
    f.add(K.circle(0, 0, b * 0.9, 28))
    f.cut(K.circle(0, 0, b * 0.45, 20))
    return f


def scheit(L, d):
    f = Z.Figur().add(Z.abrunden([(0, 0), (L, 0), (L, d), (0, d)], d * 0.3))
    f.add(K.ellipse(L, d / 2, d * 0.22, d / 2, 0, 28))
    return f


def build(cfg, name="werkbank", laenge=90.0, tiefe=36.0, hoehe=48.0, lochwand=True, wandtext="Wichtelwerkstatt",
          kiste=True, kistenmotiv="stern", werkzeug=True):
    T = cfg.T
    w = Z.wmin(cfg)
    L, D, Hb = cfg.s(laenge), cfg.s(tiefe), cfg.s(hoehe)
    if D < 5 * T + 10 or Hb < 6 * T + 10:
        raise ValueError("Die Werkbank ist für diese Materialstärke zu klein – größer machen")
    notes = []
    asm = Assembly(name, params=dict(laenge=L, tiefe=D, hoehe=Hb))
    tw = M.tabbreite(cfg, D, 0.22)
    m = max(2.2, T * 0.8)
    ub = max(4.0, L * 0.08)                                   # Überstand der Platte über die Beine
    xb = [ub + T / 2, L - ub - T / 2]                         # Beinmitten (Länge)
    zs_x = [D * 0.3, D * 0.7]                                 # Zapfen über die Tiefe
    # --- Bockbeine (stehen unter der Platte: Höhe ohne Plattenstärke) ---
    hl = Hb - T
    hq = max(2.6 * T, hl * 0.13)                              # Querriegel der Beine
    sh = hq * 0.85                                            # Höhe der Fußstrebe
    tws = max(cfg.min_tab_width + 0.6, min(tw, sh - 2.0))     # deren Zapfen
    beine = []
    for k, seite in enumerate(("links", "rechts")):
        part, yq, hq, bb = bockbein(cfg, f"bein_{seite}", D, hl, tw,
                                    [(x, f"zapfen{i}", 10 + 10 * k + i) for i, x in enumerate(zs_x)], notes, w,
                                    (D / 2, hl * 0.3, tw, 0))
        Z.schlitz(part, "strebe", D / 2, yq, tws, T, 30 + k, math.pi / 2)
        Z.gravur(part, M.maserung(1.0, yq - hq / 2 + 0.8, D - 1.0, yq + hq / 2 - 0.8, 5 + k, 0.7, ast=False),
                 rand=0.8, sperr=[Z.schlitz_polster(D / 2, yq, tws, T, 1.2, math.pi / 2)])
        beine.append(part)
        asm.parts.append(part)
    # --- Platte (Draufsicht: x = Länge, y = Tiefe, vorne y = 0) ---
    platte = Z.brett("platte", L, D, T)
    for k, x in enumerate(xb):
        for i, y in enumerate(zs_x):
            Z.schlitz(platte, f"bein{k}{i}", x, y, tw, T, 10 + 10 * k + i, math.pi / 2)
    xs_w = [L * 0.3, L * 0.7]
    if lochwand:
        for i, x in enumerate(xs_w):
            Z.schlitz(platte, f"wand{i}", x, D - m - T / 2, tw, T, 50 + i)
    lin = []
    nb = max(2, int(D / 11))                                    # verleimte Bohlen
    for j in range(nb):
        y0, y1 = D * j / nb, D * (j + 1) / nb
        if j:
            lin.append(([(1.0, y0), (L - 1.0, y0)], False))
        lin += M.maserung(1.5, y0 + 0.8, L - 1.5, y1 - 0.8, 31 + j, 0.8, ast=(j == 1))
    for x in (L * 0.12, L * 0.88):                              # Bankhaken-Löcher als Gravur
        lin.append((K.rect(x - 1.2, D * 0.45, 2.4, 2.4), True))
    sperr = [Z.schlitz_polster(sum(p[0] for p in f.points) / 4, sum(p[1] for p in f.points) / 4, tw, T, 1.0,
                               0 if f.id.startswith("wand") else math.pi / 2) for f in platte.features]
    Z.gravur(platte, lin, rand=0.8, sperr=sperr)
    asm.parts.append(platte)
    for k, seite in enumerate(("links", "rechts")):
        for i in range(2):
            asm.connect(f"bein_{seite}:zapfen{i}", f"platte:bein{k}{i}")
    # --- Fußstrebe zwischen den Beinen ---
    Ls = (xb[1] - xb[0]) - T - EINZUG
    strebe = Z.brett("strebe", Ls, sh, T, links=[(sh / 2, tws, "links", 30)], rechts=[(sh / 2, tws, "rechts", 31)])
    Z.gravur(strebe, M.maserung(1.0, 0.8, Ls - 1.0, sh - 0.8, 41, 0.7, ast=False), rand=0.6)
    asm.parts.append(strebe)
    asm.connect("strebe:links", "bein_links:strebe")
    asm.connect("strebe:rechts", "bein_rechts:strebe")
    asm.notes.append("Die Bockbeine mit ihren Zapfen von unten in die Platte stecken, die Fußstrebe zwischen die "
                     "Beine schieben.")
    # --- Schraubstock (Vorderansicht, an die Plattenkante leimen) ---
    vb = max(16.0, L * 0.22)
    vh = max(10.0, Hb * 0.3)
    vf = Z.Figur()
    vf.add(K.rect(-vb / 2, 0, vb, vh))                                                 # Backe
    vf.add(K.rect(-vb * 0.08, -vh * 0.35, vb * 0.16, vh * 0.4))                        # Spindel
    vf.add(K.rect(-vb * 0.55, -vh * 0.5, vb * 1.1, max(1.6 * w, vh * 0.12)))           # Knebel
    for s in (1, -1):
        vf.add(K.circle(s * vb * 0.55, -vh * 0.44, max(1.2 * w, vh * 0.12), 16))
    sv = Z.figur_teil(cfg, "schraubstock", vf, notes)
    Z.gravur(sv, [([(-vb / 2 + 1.2, vh * 0.55), (vb / 2 - 1.2, vh * 0.55)], False)] +
             [([(x, vh * 0.6), (x, vh - 1.0)], False) for x in (-vb * 0.3, -vb * 0.1, vb * 0.1, vb * 0.3)] +
             [(K.circle(0, vh * 0.25, vh * 0.12, 16), True)], rand=0.6)
    asm.parts.append(sv)
    asm.notes.append("Den Schraubstock vorne links an die Platte leimen (Backen oben bündig).")
    # --- Lochwand ---
    if lochwand:
        Wl = L * 0.8
        Hl = max(28.0, Hb * 0.85)
        wf = Z.Figur().add(K.rect(-Wl / 2, 0, Wl, Hl * 0.86))
        wf.add(Z.abrunden([(-Wl / 2, Hl * 0.8), (Wl / 2, Hl * 0.8), (Wl / 2 - Hl * 0.04, Hl), (-Wl / 2 + Hl * 0.04, Hl)],
                          Hl * 0.04))
        th = min(9.0, Hl * 0.2) if wandtext.strip() else 0.0
        r = max(0.8, w * 0.45)
        a = max(4.5, 2 * r + w + 1.6)
        wt = Z.figur_teil(cfg, "lochwand", wf, notes, unten_flach=True)
        nx = int((Wl - a) / a)
        ny = int((Hl * 0.86 - th - 1.5 - a * 0.8) / a)
        for i in range(nx):
            for j in range(ny):
                wt.add_hole(K.circle(-(nx - 1) * a / 2 + i * a, a * 0.9 + j * a, r, 14))
        for i, x in enumerate(xs_w):
            Z.zapfen_unten(wt, x - L / 2, tw, T, f"fuss{i}", pos=50 + i)
        lin = []
        if th:
            M.text_gravur(wt, wandtext, 0, Hl * 0.86 + (Hl * 0.14 - 1) / 2 - th * 0.35, Wl * 0.86, th, th,
                          "Der Text auf der Lochwand")
        lin.append(([(-Wl / 2 + 1.2, Hl * 0.86 - th - 1.0), (Wl / 2 - 1.2, Hl * 0.86 - th - 1.0)], False))
        Z.gravur(wt, lin, rand=0.7)
        asm.parts.append(wt)
        for i in range(2):
            asm.connect(f"lochwand:fuss{i}", f"platte:wand{i}")
        asm.notes.append("Die Lochwand hinten in die Platte stecken.")
    # --- Werkzeugkiste ---
    if kiste:
        _kiste(cfg, asm, max(34.0, L * 0.42), notes, kistenmotiv, w)
    # --- Werkzeug ---
    if werkzeug:
        g = max(18.0, L * 0.26)
        teile = [("saege", saege(g * 1.4, w)), ("hammer", hammer(g * 0.75, w)), ("zollstock", zollstock(g)),
                 ("schluessel", schluessel(g * 0.75, w)), ("scheit", scheit(g * 1.1, g * 0.32))]
        for nm, f in teile:
            p = Z.figur_teil(cfg, nm, f, notes)
            lin = []
            if nm == "zollstock":
                hz = g * 0.13
                for k in range(1, int(g / 1.6)):
                    x = k * 1.6
                    lin.append(([(x, hz - 0.6), (x, hz - (2.0 if k % 5 == 0 else 1.0))], False))
                for k in range(1, 4):
                    lin.append(([(g * k / 4, 0.6), (g * k / 4, hz * 0.4)], False))
            elif nm == "saege":
                lin.append(([(g * 0.15, g * 1.4 * 0.24 * 0.55), (g * 1.0, g * 1.4 * 0.24 * 0.8)], False))
            elif nm == "scheit":
                d = g * 0.32
                for k in range(3):
                    lin.append((K.ellipse(g * 1.1, d / 2, d * 0.06 * (k + 1), d * 0.14 * (k + 1), 0, 16), True))
                lin += [(K.spline([(1.5 + k * 3.5, d * (0.2 + 0.15 * (k % 3))), (4 + k * 3.5, d * (0.35 + 0.1 * (k % 2))),
                                   (6 + k * 3.5, d * (0.25 + 0.15 * (k % 3)))], n=5), False)
                        for k in range(int(g * 1.1 / 3.5) - 1)]
            elif nm == "hammer":
                lin.append(([(g * 0.75 * 0.05, 1.5), (g * 0.75 * 0.05, g * 0.75 * 0.68)], False))
            Z.gravur(p, lin, rand=0.5)
            asm.parts.append(p)
        asm.notes.append("Das Werkzeug auf die Bank legen oder an die Lochwand kleben.")
    asm.notes += list(dict.fromkeys(notes))
    return asm


def _motiv(art, cx, cy, g):
    """Ein einzelnes Lochpolygon für die Kistenwand."""
    if art == "stern":
        return K.star(cx, cy - g * 0.04, g * 0.52, g * 0.22, 5)
    if art == "herz":
        return Z.herz(cx, cy, g)
    if art == "tanne":
        h = g / 2
        return [(cx - h * 0.18, cy - h), (cx + h * 0.18, cy - h), (cx + h * 0.18, cy - h * 0.72), (cx + h * 0.85, cy - h * 0.72),
                (cx + h * 0.4, cy - h * 0.15), (cx + h * 0.65, cy - h * 0.15), (cx + h * 0.22, cy + h * 0.4),
                (cx + h * 0.42, cy + h * 0.4), (cx, cy + h), (cx - h * 0.42, cy + h * 0.4), (cx - h * 0.22, cy + h * 0.4),
                (cx - h * 0.65, cy - h * 0.15), (cx - h * 0.4, cy - h * 0.15), (cx - h * 0.85, cy - h * 0.72),
                (cx - h * 0.18, cy - h * 0.72)]
    return None


def _kiste(cfg, asm, Lk, notes, motiv, w):
    """Werkzeugkiste: zwei Stirnseiten (Satteldach, Griffschlitz), Boden, zwei Seitenwände, Griff."""
    T = cfg.T
    Dk = max(6 * T + 6, Lk * 0.5)                             # Tiefe der Kiste
    Hw = max(4 * T + 4, Lk * 0.32)                            # Höhe der Seitenwände
    Hs = Hw + Dk * 0.55 + Lk * 0.12                           # Höhe der Stirnseite bis zur Spitze
    m = max(2.0, T * 0.7)
    tw = M.tabbreite(cfg, min(Dk, Hw), 0.3)
    Li = Lk - 2 * T                                           # lichte Länge zwischen den Stirnseiten
    yb = m + T / 2                                            # Boden (Schlitzmitte)
    xs = [m + T / 2, Dk - m - T / 2]                          # Seitenwände
    Hg = Hs - Hw * 0.55                                       # Griffbrett: von Wandmitte bis kurz unter die Spitze
    yg = Hw * 0.55 + Hg / 2
    for k, seite in enumerate(("links", "rechts")):
        fig = Z.Figur().add([(0, 0), (Dk, 0), (Dk, Hw), (Dk / 2, Hs), (0, Hw)])
        slots = [("boden", Dk / 2, yb, tw, 0.0, 60 + k)]
        slots += [(f"wand{i}", x, Hw / 2, tw, math.pi / 2, 62 + 2 * k + i) for i, x in enumerate(xs)]
        slots.append(("griff", Dk / 2, yg, tw, math.pi / 2, 66 + k))
        rand = max(2.0, T * 0.8)
        solid = [Z.schlitz_polster(cx, cy, L, T, rand, a) for _, cx, cy, L, a, _ in slots]
        part = Z.figur_teil(cfg, f"kiste_stirn_{seite}", fig, notes, solid=solid, unten_flach=True)
        for fid, cx, cy, L, a, pos in slots:
            Z.schlitz(part, fid, cx, cy, L, T, pos, a)
        asm.parts.append(part)
    Db = Dk - 2 * m - 2 * T - 0.3                              # Boden zwischen den Seitenwänden
    boden = Z.brett("kiste_boden", Li, Db, T, links=[(Db / 2, tw, "links", 60)], rechts=[(Db / 2, tw, "rechts", 61)])
    asm.parts.append(boden)
    asm.connect("kiste_boden:links", "kiste_stirn_links:boden")
    asm.connect("kiste_boden:rechts", "kiste_stirn_rechts:boden")
    for i in range(2):
        wand = Z.brett(f"kiste_wand{i + 1}", Li, Hw, T, links=[(Hw / 2, tw, "links", 62 + i)],
                       rechts=[(Hw / 2, tw, "rechts", 64 + i)])
        loch = _motiv(motiv, Li / 2, Hw / 2, min(Hw * 0.62, Li * 0.4))
        if loch and min(Hw * 0.62, Li * 0.4) >= 3 * w:
            wand.add_hole(loch)
        Z.gravur(wand, M.bretter(0, 0, Li, Hw, 2, False, seed=50 + i), rand=0.7)
        asm.parts.append(wand)
        asm.connect(f"kiste_wand{i + 1}:links", "kiste_stirn_links:" + f"wand{i}")
        asm.connect(f"kiste_wand{i + 1}:rechts", "kiste_stirn_rechts:" + f"wand{i}")
    griff = Z.brett("kiste_griff", Li, Hg, T, links=[(Hg / 2, tw, "links", 66)], rechts=[(Hg / 2, tw, "rechts", 67)])
    gl = min(Li * 0.5, 30.0)
    gh = max(cfg.T + 1.5, min(Hg * 0.28, 7.0))
    if Hg - gh > 2 * (cfg.min_web + 2) and gl > 8:
        griff.add_hole(Z.abrunden(K.rect(Li / 2 - gl / 2, Hg * 0.62 - gh / 2, gl, gh), gh * 0.49))
    asm.parts.append(griff)
    asm.connect("kiste_griff:links", "kiste_stirn_links:griff")
    asm.connect("kiste_griff:rechts", "kiste_stirn_rechts:griff")
    asm.notes.append("Werkzeugkiste: Boden, Seitenwände und Griff mit den Zapfen in die Stirnseiten stecken.")
