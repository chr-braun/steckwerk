"""
Lebkuchenstand – Paket „Wichtelwelt“.

Ein Weihnachtsmarktstand zum Stecken: Bodenplatte, zwei Seitenteile mit gedrechselten Pfosten und
Fensterbogen, Theke mit Bretterlook und Thekenbrett, Rückwand mit Regalbrettern, Dach, darauf ein
verziertes Schild mit Schrift und vorne eine Markise mit Bogenkante. Dazu Lebkuchenmänner und
Lebkuchenherzen mit gravierter Zuckerschrift zum Aufkleben oder Aufhängen.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, Part, oriented
from pakete import flag, integer, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtelwelt__lade_stand",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.welt()
Z, K = M.Z, M.K

MARKISEN = [("bogen", "Bögen"), ("zacken", "Zacken"), ("wellen", "Wellen"), ("keine", "keine")]
SCHILDKRONEN = [("herzen", "Herzen"), ("sterne", "Sterne"), ("ranke", "Ranke"), ("glatt", "glatt")]

UEBERSETZUNG = {"en": {
    "Lebkuchenstand": "Gingerbread stall", "Wichtelwelt": "Elf world",
    "Weihnachtsmarktstand zum Stecken: Theke, Rückwand mit Regalen, Dach mit verziertem Schild und Markise, dazu Lebkuchenmänner und -herzen.":
        "Slot-together Christmas market stall: counter, back wall with shelves, roof with decorated sign and awning, plus gingerbread men and hearts.",
    "Breite": "Width", "Höhe": "Height", "Tiefe": "Depth", "Schild": "Sign", "Text auf der Theke": "Text on the counter",
    "Markise": "Awning", "Schmuck auf dem Schild": "Sign decoration", "Lebkuchenmänner": "Gingerbread men",
    "Lebkuchenherzen": "Gingerbread hearts", "Text auf den Herzen": "Text on the hearts",
    "Bögen": "Scallops", "Zacken": "Zigzag", "Wellen": "Waves", "keine": "none", "Herzen": "Hearts", "Sterne": "Stars",
    "Ranke": "Tendril", "glatt": "plain",
    "Die Seitenteile, die Theke und die Rückwand mit ihren Zapfen in die Bodenplatte stecken.":
        "Push the side panels, the counter and the back wall with their tabs into the base plate.",
    "Thekenbrett und Dach mit ihren seitlichen Zapfen zwischen die Seitenteile schieben.":
        "Slide the counter top and the roof with their side tabs between the side panels.",
    "Schild und Markise von oben bzw. unten in die Schlitze des Dachs stecken.":
        "Push the sign from above and the awning from below into the slots of the roof.",
    "Lebkuchen auf Theke und Rückwand kleben oder an einem Faden durch das Loch aufhängen.":
        "Glue the gingerbread onto the counter and back wall or hang it on a thread through the hole.",
}}

INFO = dict(
    label="Lebkuchenstand", group="Wichtelwelt",
    desc="Weihnachtsmarktstand zum Stecken: Theke, Rückwand mit Regalen, Dach mit verziertem Schild und Markise, "
         "dazu Lebkuchenmänner und -herzen.",
    params=[
        num("breite", "Breite", 120, 80, 260),
        num("hoehe", "Höhe", 140, 90, 300),
        num("tiefe", "Tiefe", 50, 35, 120),
        txt("schild", "Schild", "Lebkuchen", "leer = nur Verzierung", maxlen=24, symbols=True),
        sel("krone", "Schmuck auf dem Schild", SCHILDKRONEN, "herzen"),
        sel("markise", "Markise", MARKISEN, "bogen"),
        txt("theke", "Text auf der Theke", "frisch gebacken", "leer = Bretter mit Herz", maxlen=30, symbols=True),
        integer("maenner", "Lebkuchenmänner", 2, 0, 6),
        integer("herzen", "Lebkuchenherzen", 3, 0, 6),
        txt("herztext", "Text auf den Herzen", "Danke|Wichtel|Lecker", "| trennt die Herzen", maxlen=60,
            when={"herzen": [1, 2, 3, 4, 5, 6]}),
    ],
)

EINZUG = 0.3


def lebkuchenmann(h: float, w: float) -> "Z.Figur":
    """Lebkuchenmann, Füße bei y = 0, Höhe h."""
    f = Z.Figur()
    f.add(K.circle(0, h * 0.8, h * 0.19, 40))                                   # Kopf
    f.add(Z.abrunden([(-h * 0.17, h * 0.3), (h * 0.17, h * 0.3), (h * 0.15, h * 0.66), (-h * 0.15, h * 0.66)],
                     h * 0.08))
    for s in (1, -1):
        f.line([(s * h * 0.1, h * 0.58), (s * h * 0.3, h * 0.6), (s * h * 0.4, h * 0.68)], h * 0.15, h * 0.13)
        f.line([(s * h * 0.08, h * 0.36), (s * h * 0.14, h * 0.18), (s * h * 0.2, h * 0.07)], h * 0.17, h * 0.15)
    f.cut(K.circle(0, h * 0.86, max(h * 0.035, w * 0.6), 16))                   # Aufhängeloch
    return f


def lebkuchenmann_gravur(h: float):
    lin = []
    for s in (1, -1):
        lin.append((K.circle(s * h * 0.06, h * 0.79, h * 0.022, 10), True))     # Augen
        # Zuckerguss-Zickzack an Armen und Beinen
        for (x0, y0), (x1, y1) in (((s * h * 0.3, h * 0.66), (s * h * 0.36, h * 0.62)),
                                   ((s * h * 0.14, h * 0.13), (s * h * 0.23, h * 0.13))):
            pts = []
            for k in range(7):
                t = k / 6
                dx, dy = (y1 - y0), -(x1 - x0)
                d = math.hypot(dx, dy) or 1
                a = (0.02 * h) * (1 if k % 2 else -1)
                pts.append((x0 + (x1 - x0) * t + dx / d * a, y0 + (y1 - y0) * t + dy / d * a))
            lin.append((pts, False))
    lin.append((K.arc(0, h * 0.76, h * 0.07, math.pi * 1.15, math.pi * 1.85, 10), False))   # Lächeln
    for y in (h * 0.55, h * 0.46, h * 0.37):
        lin.append((K.circle(0, y, h * 0.025, 10), True))                       # Knöpfe
    return lin


def build(cfg, name="lebkuchenstand", breite=120.0, hoehe=140.0, tiefe=50.0, schild="Lebkuchen", krone="herzen",
          markise="bogen", theke="frisch gebacken", maenner=2, herzen=3, herztext="Danke|Wichtel|Lecker"):
    T = cfg.T
    w = Z.wmin(cfg)
    W, H, D = cfg.s(breite), cfg.s(hoehe), cfg.s(tiefe)
    if D < 6 * T + 12:
        raise ValueError("Der Stand ist für diese Materialstärke zu flach – Tiefe vergrößern")
    notes = []
    asm = Assembly(name, params=dict(breite=W, hoehe=H, tiefe=D))
    Wi = W - 2 * T                                         # lichte Breite zwischen den Seitenteilen
    m = max(2.2, T * 0.8)
    pw = max(2.6 * T, min(9.0, D * 0.16))                 # Pfostenbreite
    Hp = H * 0.74                                          # Oberkante Seitenteil (ohne Knauf)
    bt = max(T + 2 * max(2.4, T * 0.8), H * 0.07)          # Balken oben
    yd = Hp - bt / 2                                       # Dachmitte (Schlitzmitte)
    hc = max(H * 0.34, 3 * T + 20)                         # Thekenhöhe (Oberkante Thekenbrett)
    tw = M.tabbreite(cfg, D, 0.2)
    ss = [D * 0.28, D * 0.72]                              # Zapfen der Seitenteile (Tiefe)
    xs_seite = [-(Wi / 2 + T / 2), Wi / 2 + T / 2]
    Dk = D * 0.42                                          # Tiefe des Thekenbretts
    y_theke = D - m - T / 2                                # Theke steht vorne
    y_rueck = m + T / 2
    if hc + 2 * T + 18 > yd - bt:
        raise ValueError("Der Stand ist zu niedrig für Theke und Fenster – Höhe vergrößern")

    # --- Seitenteile ---
    for k, seite in enumerate(("links", "rechts")):
        fig = Z.Figur().add(K.rect(0, 0, D, Hp))
        for s in (pw / 2, D - pw / 2):                                       # Knäufe auf den Pfosten
            fig.add(K.rect(s - pw * 0.32, Hp - 1, pw * 0.64, pw * 0.5 + 1))
            fig.add(K.circle(s, Hp + pw * 0.75, pw * 0.48, 28))
            fig.add(K.ellipse(s, Hp + pw * 0.38, pw * 0.5, pw * 0.16, 0, 20))
        oy0, oy1 = hc + T / 2 + max(3.0, T), yd - bt / 2
        bog = min((D - 2 * pw) / 2, (oy1 - oy0) * 0.45)
        fen = [(pw, oy0), (D - pw, oy0), (D - pw, oy1 - bog)] + \
            K.arc(D / 2, oy1 - bog, (D - 2 * pw) / 2, 0, math.pi, 32)[1:-1] + [(pw, oy1 - bog)]
        fig.cut(fen)
        hz = min((hc - 3 * T) * 0.5, (D - 2 * pw) * 0.5)
        if hz >= 3 * w:
            fig.merge(Z.ausschnitt("herz", D / 2, (hc - T) * 0.52, hz))
        slots = [(f"dach{i}", s, yd, tw, 30 + 10 * k + i, 0.0) for i, s in enumerate(ss)]
        slots.append(("brett", D - Dk / 2, hc - T / 2, tw, 50 + k, 0.0))
        solid = [Z.schlitz_polster(cx, cy, L, T, max(2.0, T * 0.8)) for _, cx, cy, L, _, _ in slots]
        teil = Z.figur_teil(cfg, f"seite_{seite}", fig, notes, solid=solid, unten_flach=True)
        for i, s in enumerate(ss):
            Z.zapfen_unten(teil, s, tw, T, f"fuss{i}", pos=10 + 10 * k + i)
        for fid, cx, cy, L, pos, _ in slots:
            Z.schlitz(teil, fid, cx, cy, L, T, pos)
        lin = []
        for i in range(1, 4):                                                # Bretter unten
            y = (hc - T) * i / 4
            lin.append(([(1.2, y), (D - 1.2, y)], False))
        lin += M.maserung(1.5, Hp - bt + 1.2, D - 1.5, Hp - 1.2, 7 + k, 0.7, ast=False)
        Z.gravur(teil, lin, rand=0.9)
        asm.parts.append(teil)

    # --- Bodenplatte (Draufsicht: x quer, y Tiefe, vorne = D) ---
    rb = max(4.0, T * 1.5)
    boden = Part("boden", oriented(Z.abrunden([(-W / 2 - rb, -rb), (W / 2 + rb, -rb), (W / 2 + rb, D + rb),
                                                (-W / 2 - rb, D + rb)], rb), True))
    xs_wand = [-Wi * 0.3, Wi * 0.3]
    for k, x in enumerate(xs_seite):
        for i, s in enumerate(ss):
            Z.schlitz(boden, f"seite{k}{i}", x, s, tw, T, 10 + 10 * k + i, math.pi / 2)
    for i, x in enumerate(xs_wand):
        Z.schlitz(boden, f"theke{i}", x, y_theke, tw, T, 60 + i)
        Z.schlitz(boden, f"rueck{i}", x, y_rueck, tw, T, 70 + i)
    lin = []                                                                 # Pflaster
    zeilen = max(2, int((D + 2 * rb) / 7))
    for j in range(zeilen):
        y0 = -rb + 1.5 + j * (D + 2 * rb - 3) / zeilen
        y1 = y0 + (D + 2 * rb - 3) / zeilen - 1.0
        x = -W / 2 - rb + 1.5 + (3.5 if j % 2 else 0)
        while x < W / 2 + rb - 6:
            b = 7.0 + (j * 3 + int(x)) % 3
            lin.append((Z.abrunden([(x, y0), (min(x + b - 1, W / 2 + rb - 1.5), y0),
                                    (min(x + b - 1, W / 2 + rb - 1.5), y1), (x, y1)], 1.2), True))
            x += b
    sperr = [Z.schlitz_polster(f.points[0][0] * 0 + sum(p[0] for p in f.points) / 4,
                               sum(p[1] for p in f.points) / 4, tw + 2, T + 2, 0.5) for f in boden.features]
    Z.gravur(boden, lin, rand=1.0, sperr=sperr)
    asm.parts.append(boden)
    for k in range(2):
        for i in range(2):
            asm.connect(f"seite_{('links', 'rechts')[k]}:fuss{i}", f"boden:seite{k}{i}")

    # --- Theke (Front) und Thekenbrett ---
    Wt = Wi - EINZUG
    Ht = hc - T - 0.2
    th = Z.brett("theke", Wt, Ht, T, unten=[(Wt / 2 + x, tw, f"fuss{i}", 60 + i) for i, x in enumerate(xs_wand)])
    th = Z.abbilden(th, lambda p: (p[0] - Wt / 2, p[1]))
    lin = M.bretter(-Wt / 2, 0, Wt / 2, Ht, max(3, int(Wt / 14)), True, seed=3)
    sperr = []
    if theke.strip():
        bh = min(Ht * 0.36, 17.0)
        schild_poly = [(x, y + Ht * 0.56 - bh / 2) for x, y in Z.kartusche(Wt * 0.8, bh, "kartusche")]
        sperr = [schild_poly]
        Z.gravur(th, lin, rand=0.8, sperr=sperr)
        lin = [(schild_poly, True)]
        try:
            st, _ = Z.text_in_box(theke, 0, Ht * 0.56, Wt * 0.62, bh * 0.6, 7.0, 2.5, 0.08, "kursiv")
        except ValueError:
            raise ValueError(f"Der Text auf der Theke „{theke}“ passt nicht – kürzer fassen oder den Stand breiter machen")
        lin += [(s_, False) for s_ in st]
    Z.gravur(th, lin, rand=0.8)
    asm.parts.append(th)
    for i in range(2):
        asm.connect(f"theke:fuss{i}", f"boden:theke{i}")
    Wb = Wi
    tb = Z.brett("thekenbrett", Wb, Dk, T, links=[(Dk / 2, tw, "links", 50)], rechts=[(Dk / 2, tw, "rechts", 51)])
    Z.gravur(tb, M.maserung(1.2, 1.2, Wb - 1.2, Dk - 1.2, 11, 0.8), rand=0.8)
    asm.parts.append(tb)
    asm.connect("thekenbrett:links", "seite_links:brett")
    asm.connect("thekenbrett:rechts", "seite_rechts:brett")

    # --- Rückwand ---
    Hr = yd - T / 2 - 0.2
    rw = Z.brett("rueckwand", Wt, Hr, T, unten=[(Wt / 2 + x, tw, f"fuss{i}", 70 + i) for i, x in enumerate(xs_wand)])
    rw = Z.abbilden(rw, lambda p: (p[0] - Wt / 2, p[1]))
    lin = M.bretter(-Wt / 2, 0, Wt / 2, Hr, max(3, int(Wt / 12)), True, seed=21, nagel=False)
    regale = [hc + (Hr - hc) * f for f in (0.3, 0.62)]
    for y in regale:                                                         # Regalbretter mit Konsolen
        lin = [l for l in lin if all(abs(p[1] - y) > 3.5 for p in l[0])]
        lin.append((Z.abrunden([(-Wt / 2 + 2, y - 1.5), (Wt / 2 - 2, y - 1.5), (Wt / 2 - 2, y + 1.5),
                                (-Wt / 2 + 2, y + 1.5)], 0.6), True))
        for j in range(5):                                                   # Gläser und Dosen
            x = -Wt * 0.38 + Wt * 0.76 * (j + 0.5) / 5
            hh = 6.5 + (j % 3) * 1.6
            bb = 4.5 + (j % 2) * 1.5
            lin.append((Z.abrunden([(x - bb / 2, y + 1.6), (x + bb / 2, y + 1.6), (x + bb / 2, y + 1.6 + hh),
                                    (x - bb / 2, y + 1.6 + hh)], 1.0), True))
            lin.append(([(x - bb / 2 - 0.4, y + 1.6 + hh), (x + bb / 2 + 0.4, y + 1.6 + hh)], False))
    Z.gravur(rw, lin, rand=0.8)
    asm.parts.append(rw)
    for i in range(2):
        asm.connect(f"rueckwand:fuss{i}", f"boden:rueck{i}")

    # --- Dach ---
    ys_m = D - m - T / 2                                                     # Markise ganz vorne
    ys_s = ys_m - T - 2 * m                                                  # Schild dahinter
    xs_d = [Wi / 2 - Wi * 0.28, Wi / 2 + Wi * 0.28]
    dach = Z.brett("dach", Wi, D, T, links=[(s, tw, f"links{i}", 30 + i) for i, s in enumerate(ss)],
                   rechts=[(s, tw, f"rechts{i}", 40 + i) for i, s in enumerate(ss)])
    for i, x in enumerate(xs_d):
        Z.schlitz(dach, f"schild{i}", x, ys_s, tw, T, 80 + i)
        if markise != "keine":
            Z.schlitz(dach, f"markise{i}", x, ys_m, tw, T, 90 + i)
    lin = []
    for j in range(1, max(3, int(Wi / 9))):                                  # Schindelreihen
        x = Wi * j / max(3, int(Wi / 9))
        lin.append(([(x, 1.2), (x, ys_s - T / 2 - 2.0)], False))
    Z.gravur(dach, lin, rand=0.8)
    asm.parts.append(dach)
    for i in range(2):
        asm.connect(f"dach:links{i}", f"seite_links:dach{i}")
        asm.connect(f"dach:rechts{i}", f"seite_rechts:dach{i}")

    # --- Schild (steht auf dem Dach) ---
    Hs = H - (yd + T / 2)
    Ws = W * 0.92
    hk = Hs * 0.3                                                            # Krone
    hb = Hs - hk
    sfig = Z.Figur().add(Z.abrunden([(-Ws / 2, 0), (Ws / 2, 0), (Ws / 2, hb * 0.8), (Ws * 0.32, hb),
                                     (-Ws * 0.32, hb), (-Ws / 2, hb * 0.8)], min(6.0, hb * 0.2)))
    if krone == "herzen":
        sfig.add(Z.herz(0, hb + hk * 0.42, hk * 1.15))
        for s in (1, -1):
            sfig.add(Z.herz(s * Ws * 0.2, hb + hk * 0.05, hk * 0.75))
    elif krone == "sterne":
        sfig.add(K.star(0, hb + hk * 0.35, hk * 0.75, hk * 0.33, 5))
        for s in (1, -1):
            sfig.add(K.star(s * Ws * 0.2, hb + hk * 0.02, hk * 0.5, hk * 0.22, 5))
    elif krone == "ranke":
        r = Z.ranke(Ws * 0.5, hk * 0.9, w=max(w, hk * 0.08))
        sfig.merge(r.place(-Ws * 0.25, hb - hk * 0.1, 1.0))
    rand_s = max(1.4 * w, 2.0)
    innen = Z.abrunden([(-Ws / 2 + rand_s, rand_s), (Ws / 2 - rand_s, rand_s), (Ws / 2 - rand_s, hb * 0.8 - rand_s * 0.6),
                        (Ws * 0.32 - rand_s * 0.4, hb - rand_s), (-Ws * 0.32 + rand_s * 0.4, hb - rand_s),
                        (-Ws / 2 + rand_s, hb * 0.8 - rand_s * 0.6)], min(5.0, hb * 0.18))
    if not schild.strip():
        sfig.merge(Z.durchbruch(innen, "herzen", max(3 * w, hb * 0.18), ausser=lambda p: p[1] < hb * 0.3))
    st = Z.figur_teil(cfg, "schild", sfig, notes, unten_flach=True,
                      solid=[K.rect(x - Wi / 2 - tw / 2 - 1, 0, tw + 2, 3) for x in xs_d])
    for i, x in enumerate(xs_d):
        Z.zapfen_unten(st, x - Wi / 2, tw, T, f"fuss{i}", pos=80 + i)
    lin = [(innen, True)]
    if schild.strip():
        M.text_gravur(st, schild, 0, hb * 0.48, Ws * 0.76, hb * 0.5, 14.0, "Das Schild", "fett")
    for x in (-Ws / 2 + rand_s * 2.2, Ws / 2 - rand_s * 2.2):
        lin.append((K.circle(x, hb * 0.4, 0.8, 10), True))
    Z.gravur(st, lin, rand=0.7)
    asm.parts.append(st)
    for i in range(2):
        asm.connect(f"schild:fuss{i}", f"dach:schild{i}")

    # --- Markise (hängt vorne unter dem Dach) ---
    if markise != "keine":
        Wm = Wi - EINZUG
        hm = max(10.0, min(H * 0.1, (yd - bt / 2 - hc) * 0.32))
        g = max(3.2 * w, min(11.0, Wm / 9))
        n = max(4, int(round(Wm / max(g * 1.6, 9.0))))
        r = Wm / (2 * n)
        hk = hm - r                                                          # Unterkante der Bahn
        umr = [(-Wm / 2, 0), (Wm / 2, 0)]
        for j in range(n):                                                   # von rechts nach links
            xc = Wm / 2 - r - 2 * r * j
            if markise == "bogen":
                umr += K.arc(xc, hk, r, 0, math.pi, 18)[:-1]
            elif markise == "zacken":
                umr += [(xc + r, hk), (xc, hm)]
            else:
                umr += [(xc + r - 2 * r * t / 12, hk + r * 0.6 * math.sin(math.pi * t / 12)) for t in range(12)]
        umr.append((-Wm / 2, hk))
        mf = Z.Figur().add(umr)
        mt = Z.figur_teil(cfg, "markise", mf, notes, unten_flach=True)
        for i, x in enumerate(xs_d):
            Z.zapfen_unten(mt, x - Wi / 2, tw, T, f"zapfen{i}", pos=90 + i)
        lin = []
        for j in range(n):                                                   # Bahnen (jede zweite schraffiert)
            x0, x1 = -Wm / 2 + Wm * j / n, -Wm / 2 + Wm * (j + 1) / n
            if j:
                lin.append(([(x0, 0.8), (x0, hk - 0.8)], False))
            if j % 2:
                y = 2.0
                while y < hk - 1.0:
                    lin.append(([(x0 + 1.0, y), (x1 - 1.0, y)], False))
                    y += 1.6
        Z.gravur(mt, lin, rand=0.7)
        mt = Z.kopfueber(mt)
        asm.parts.append(mt)
        for i in range(2):
            asm.connect(f"markise:zapfen{i}", f"dach:markise{i}")

    # --- Lebkuchen ---
    hl = max(16.0, min(H * 0.16, 30.0))
    for i in range(int(maenner)):
        teil = Z.figur_teil(cfg, f"lebkuchenmann{i + 1}", lebkuchenmann(hl, w), notes)
        Z.gravur(teil, lebkuchenmann_gravur(hl), rand=0.6)
        asm.parts.append(teil)
    texte = [t.strip() for t in herztext.split("|")]
    for i in range(int(herzen)):
        g = max(hl * 1.5, 32.0)
        hf = Z.Figur().add(Z.herz(0, 0, g))
        hf.cut(K.circle(0, g * 0.3, max(1.1, w * 0.7), 14))
        teil = Z.figur_teil(cfg, f"lebkuchenherz{i + 1}", hf, notes)
        lin = []
        rand_h = Z.herz(0, -g * 0.02, g * 0.8)
        lin.append(([(x, y) for x, y in rand_h], True))
        for (x, y), (tx, ty) in Z.entlang(rand_h, g * 0.08):              # Zuckerguss-Pünktchen
            lin.append((K.circle(x - ty * g * 0.06, y + tx * g * 0.06, 0.35, 6), True))
        Z.gravur(teil, lin, rand=0.6)
        t = texte[i] if i < len(texte) else ""
        if t:
            M.text_gravur(teil, t, 0, -g * 0.06, g * 0.62, g * 0.28, 6.0, "Der Herztext")
        asm.parts.append(teil)

    asm.notes.append("Die Seitenteile, die Theke und die Rückwand mit ihren Zapfen in die Bodenplatte stecken.")
    asm.notes.append("Thekenbrett und Dach mit ihren seitlichen Zapfen zwischen die Seitenteile schieben.")
    asm.notes.append("Schild und Markise von oben bzw. unten in die Schlitze des Dachs stecken.")
    if int(maenner) or int(herzen):
        asm.notes.append("Lebkuchen auf Theke und Rückwand kleben oder an einem Faden durch das Loch aufhängen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
