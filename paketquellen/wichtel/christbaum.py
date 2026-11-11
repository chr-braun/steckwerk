"""
Wichtel-Christbaum – Paket „Wichtel“ (edles Zubehör, ab 1.1.0).

Tannenbaum aus zwei gleichen Hälften, über Kreuz gesteckt – steht frei und sieht von allen Seiten gleich aus.
Geschwungene Etagen mit Zweigspitzen, Schmuck als Ausschnitte (Sterne, Herzen oder Kugeln), Kugeln an den
Zweigspitzen, Lichterkette als Gravur, Stern oben und ein Baumständer. Dazu Geschenke, ebenfalls über Kreuz
gesteckt, mit Schleife und Namen.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import integer, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_christbaum",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
E = _m.modul("_edel")
Z, K = M.Z, M.K

SCHMUCK = [("sterne", "Sterne"), ("herzen", "Herzen"), ("kugeln", "Kugeln"), ("keiner", "ohne Ausschnitte")]

UEBERSETZUNG = {"en": {
    "Wichtel-Christbaum": "Elf Christmas tree",
    "Tannenbaum aus zwei Hälften über Kreuz gesteckt: Etagen mit Schmuck-Ausschnitten, Kugeln, Lichterkette, "
    "Stern und Ständer – dazu Geschenke mit Namen.":
        "Christmas tree made of two crossed halves: tiers with ornament cut-outs, baubles, fairy lights, star and "
        "stand – plus presents with names.",
    "Höhe": "Height", "Etagen": "Tiers", "Schmuck": "Ornaments", "Sterne": "Stars", "Herzen": "Hearts",
    "Kugeln": "Baubles", "ohne Ausschnitte": "no cut-outs", "Geschenke": "Presents",
    "Namen auf den Geschenken": "Names on the presents", "Mit Komma trennen, z. B. Ida, Paul":
        "Separate with commas, e.g. Ida, Paul",
}}

INFO = dict(
    label="Wichtel-Christbaum", group="Wichtel",
    desc="Tannenbaum aus zwei Hälften über Kreuz gesteckt: Etagen mit Schmuck-Ausschnitten, Kugeln, Lichterkette, "
         "Stern und Ständer – dazu Geschenke mit Namen.",
    params=[
        num("hoehe", "Höhe", 84, 50, 300),
        integer("etagen", "Etagen", 4, 3, 6),
        sel("schmuck", "Schmuck", SCHMUCK, "sterne"),
        integer("geschenke", "Geschenke", 3, 0, 5),
        txt("namen", "Namen auf den Geschenken", "Ida, Paul, Mia", help="Mit Komma trennen, z. B. Ida, Paul",
            when={"geschenke": [1, 2, 3, 4, 5]}),
    ],
)
INFO["params"] = M.mit_massstab("christbaum", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _baum(H, T, w, etagen, schmuck, stern):
    f = Z.Figur()
    mw = T + 2 * max(2.2, w)                       # Mittelband (Kreuzschlitz)
    hst = H * 0.13                                  # Ständer
    bst = H * 0.3
    f.add(Z.abrunden([(-bst / 2, 0), (bst / 2, 0), (bst * 0.38, hst), (-bst * 0.38, hst)], 0.8, 2))
    f.add(Z.abrunden(K.rect(-bst * 0.44, hst - max(1.5, w), bst * 0.88, max(1.8, w * 1.2)), 0.5, 2))
    yb = hst + H * 0.04                             # unterste Zweige
    ys = H * 0.9 if stern else H                    # Spitze
    f.add(K.rect(-mw * 0.6, hst - 0.5, mw * 1.2, yb - hst + 1.0))                       # Stamm
    f.add(K.rect(-mw / 2, hst, mw, ys - hst - 1.0))
    B = H * 0.7                                    # größte Breite
    ht = (ys - yb) / etagen * 1.6                  # Etagenhöhe (überlappend)
    zh = H * 0.04                                   # Tiefe der Zweigspitzen
    lagen = []
    for k in range(etagen):
        y0 = yb + zh + (ys - yb - ht) * k / max(etagen - 1, 1)
        y1 = min(ys, y0 + ht) if k < etagen - 1 else ys
        b = B * (1 - k / etagen * 0.72)
        bt = b * 0.16 if k < etagen - 1 else 0.0
        zack = max(3, int(round(b / max(5.5, H * 0.07))))
        if zack % 2 == 0:
            zack += 1
        unten = []
        for i in range(zack + 1):                   # Unterkante: Zweigspitzen, außen tiefer
            x = -b / 2 + b * i / zack
            unten.append((x, y0 - zh * (1.0 if i in (0, zack) else 0.75)))
            if i < zack:
                unten.append((x + b / zack / 2, y0 + zh * 0.15))
        rechts = K.bez3((b / 2, y0 - zh), (b * 0.24, y0 + (y1 - y0) * 0.22), (b * 0.13, y0 + (y1 - y0) * 0.6), (bt / 2, y1), 18)
        links = [(-x, y) for x, y in reversed(rechts)]
        f.add(unten + rechts[1:] + links[1:-1])
        lagen.append((y0, y1, b, bt))
    # Kugeln an den äußeren Zweigspitzen
    rk = max(w * 1.25, H * 0.024)
    for y0, y1, b, bt in lagen[:-1]:
        for sg in (-1, 1):
            f.add(K.circle(sg * (b / 2 - rk * 0.2), y0 - zh - rk * 0.7, rk, 18))
    # Schmuck-Ausschnitte (außerhalb des Mittelbands)
    if schmuck != "keiner":
        for y0, y1, b, bt in lagen:
            t = 0.22
            yc = y0 + (y1 - y0) * t
            hw = (b / 2) * (1 - t * 1.1)
            g = min((y1 - y0) * 0.3, hw * 0.42)
            x = hw * 0.5
            if g < 2.6 * w or x - g * 0.6 < mw / 2 + w:
                continue
            for sg in (-1, 1):
                if schmuck == "sterne":
                    f.cut(K.star(sg * x, yc, g * 0.58, g * 0.25, 5))
                elif schmuck == "herzen":
                    f.cut(Z.herz(sg * x, yc, g))
                else:
                    f.cut(K.circle(sg * x, yc, g * 0.45, 20))
    if stern:
        rs = H * 0.075
        f.add(K.star(0, H - rs, rs, rs * 0.45, 5))
        f.add(K.rect(-mw * 0.3, ys - 1.5, mw * 0.6, H - rs - ys + 1.5))
    return f, lagen


def build(cfg, name="christbaum", hoehe=84.0, etagen=4, schmuck="sterne", geschenke=3, namen="Ida, Paul, Mia",
          massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        hoehe = M.mass("christbaum", wichtel, INFO["params"], cfg)["hoehe"]
    T = cfg.T
    w = Z.wmin(cfg)
    H = cfg.s(hoehe)
    etagen = max(3, min(6, int(etagen)))
    notes = []
    asm = Assembly(name, params=dict(hoehe=H, etagen=etagen, schmuck=schmuck))
    fa, lagen = _baum(H, T, w, etagen, schmuck, False)
    fb, _ = _baum(H, T, w, etagen, schmuck, True)

    def lichter(part, von_oben):
        lin = []
        for k, (y0, y1, b, bt) in enumerate(lagen):
            yy = y0 + (y1 - y0) * 0.68
            bb = b * 0.5 * (1 - 0.68 * 0.8)
            pfad = [(bb * (2 * t - 1), yy - (y1 - y0) * 0.12 * math.sin(math.pi * t)) for t in (i / 16 for i in range(17))]
            lin.append((pfad, False))
            for t in (0.15, 0.4, 0.6, 0.85):
                px, py = pfad[int(t * 16)]
                lin.append((K.circle(px, py - 0.7, max(0.4, H * 0.006), 8), True))
        Z.gravur(part, lin, rand=0.5)
    asm.parts += E.kreuzpaar(cfg, "baum", fa, fb, notes, H * 0.42, lichter)
    asm.connect("baum_a:kreuz", "baum_b:kreuz")

    liste = [n.strip() for n in str(namen or "").split(",") if n.strip()]
    groessen = [(0.26, 0.18), (0.2, 0.15), (0.3, 0.13), (0.18, 0.2), (0.24, 0.12)]
    for k in range(max(0, int(geschenke))):
        gb, gh = groessen[k % len(groessen)]
        b = max(H * gb, 2 * T + 10)
        h = max(H * gh, 2 * T + 7)
        asm.parts += E.geschenk(cfg, f"geschenk{k + 1}", b, h, liste[k] if k < len(liste) else "", notes)
        asm.connect(f"geschenk{k + 1}_a:kreuz", f"geschenk{k + 1}_b:kreuz")

    asm.notes.append("Baum: Teil B (mit Stern, Schlitz unten) von oben über Kreuz auf Teil A schieben. "
                     "Geschenke genauso – die Hälfte mit der Schleife kommt von oben.")
    asm.notes.append("Tipp: Kugeln und Sterne bunt bemalen, die Lichterkette mit einem goldenen Stift nachziehen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
