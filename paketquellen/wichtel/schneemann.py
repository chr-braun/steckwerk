"""
Wichtel-Schneemann – Paket „Wichtel“ (edles Zubehör, ab 1.1.0).

Schneemann aus zwei Hälften, über Kreuz gesteckt – steht frei und hat von jeder Seite etwas zu zeigen: vorn
Gesicht, Knöpfe und Zweigarme, seitlich die Möhrennase und das wehende Schalende. Zylinder oder Wollmütze,
Schal mit Fransen, auf Wunsch mit Besen oder Laterne in der Hand und einer Schneeplatte mit Schneeflocken.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import flag, num, sel

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_schneemann",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
E = _m.modul("_edel")
Z, K = M.Z, M.K

HUETE = [("zylinder", "Zylinder"), ("muetze", "Wollmütze mit Bommel")]
HAND = [("besen", "Reisigbesen"), ("laterne", "Laterne"), ("keins", "nichts")]

UEBERSETZUNG = {"en": {
    "Wichtel-Schneemann": "Elf snowman",
    "Schneemann aus zwei Hälften über Kreuz gesteckt: Gesicht, Zweigarme, Möhrennase, Schal mit Fransen, Hut und "
    "Besen oder Laterne.":
        "Snowman made of two crossed halves: face, twig arms, carrot nose, fringed scarf, hat and broom or lantern.",
    "Höhe": "Height", "Hut": "Hat", "Zylinder": "Top hat", "Wollmütze mit Bommel": "Bobble hat",
    "In der Hand": "In the hand", "Reisigbesen": "Broom", "Laterne": "Lantern", "nichts": "nothing",
}}

INFO = dict(
    label="Wichtel-Schneemann", group="Wichtel",
    desc="Schneemann aus zwei Hälften über Kreuz gesteckt: Gesicht, Zweigarme, Möhrennase, Schal mit Fransen, Hut "
         "und Besen oder Laterne.",
    params=[
        num("hoehe", "Höhe", 66, 40, 300),
        sel("hut", "Hut", HUETE, "zylinder"),
        sel("hand", "In der Hand", HAND, "besen"),
    ],
)
INFO["params"] = M.mit_massstab("schneemann", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _koerper(H, T, w, hut, vorn, hand):
    """vorn=True: Ansicht von vorn (Arme, Besen/Laterne); False: Seitenansicht (Nase, Schalende)."""
    f = Z.Figur()
    r1, r2, r3 = H * 0.2, H * 0.15, H * 0.115
    y1 = r1 * 0.92
    y2 = y1 + r1 * 0.78 + r2 * 0.78
    y3 = y2 + r2 * 0.75 + r3 * 0.8
    f.add(K.circle(0, y1, r1, 64), K.circle(0, y2, r2, 56), K.circle(0, y3, r3, 48))
    f.add(K.rect(-r1 * 0.75, 0, r1 * 1.5, y1))                                        # Standfläche
    # Hut
    yt = y3 + r3 * 0.72
    if hut == "zylinder":
        f.add(Z.abrunden(K.rect(-r3 * 1.25, yt - 0.4, r3 * 2.5, max(1.6, H * 0.03)), 0.5, 2))
        f.add([(-r3 * 0.8, yt), (r3 * 0.8, yt), (r3 * 0.88, yt + H * 0.15), (-r3 * 0.88, yt + H * 0.15)])
        top = yt + H * 0.15
    else:
        m = K.bez3((r3 * 0.98, yt - r3 * 0.25), (r3 * 0.9, yt + H * 0.1), (r3 * 0.3, yt + H * 0.12),
                   (0.0, yt + H * 0.115), 16)
        f.add(m + [(-x, y) for x, y in reversed(m[:-1])])
        f.add(Z.abrunden(K.rect(-r3 * 1.05, yt - r3 * 0.35, r3 * 2.1, H * 0.035), 0.8, 3))
        f.add(K.circle(0.0, yt + H * 0.115 + H * 0.025, H * 0.04, 24))
        top = yt + H * 0.16
    # Schal um den Hals
    ys = y2 + r2 * 0.72
    f.add(Z.abrunden(K.rect(-r3 * 1.05, ys - H * 0.022, r3 * 2.1, H * 0.044), H * 0.015, 3))
    sw = max(w * 1.3, H * 0.045)
    if vorn:
        # Schalende vorn herunter mit Fransen
        x = r3 * 0.45
        f.add(Z.abrunden(K.rect(x - sw / 2, ys - H * 0.14, sw, H * 0.14), 0.4, 2))
        for i in range(3):
            fx = x - sw / 2 + sw * (i + 0.5) / 3
            f.add(K.rect(fx - w * 0.42, ys - H * 0.14 - H * 0.025, w * 0.84, H * 0.03))
        # Zweigarme
        aw = max(w * 1.4, H * 0.028)
        for sg in (-1, 1):
            p0 = (sg * r2 * 0.6, y2 + r2 * 0.2)
            p1 = (sg * (r2 + H * 0.17), y2 + r2 * 0.75)
            f.add(K.stroke([p0, p1], aw))
            mid = (p0[0] + (p1[0] - p0[0]) * 0.62, p0[1] + (p1[1] - p0[1]) * 0.62)
            f.add(K.stroke([mid, (mid[0] + sg * H * 0.025, mid[1] + H * 0.06)], aw))
            for d in (-1, 1):                                                          # Fingerzweige
                f.add(K.stroke([p1, (p1[0] + sg * H * 0.04, p1[1] + d * H * 0.035 + H * 0.01)], aw))
        if hand == "besen":
            x = -(r2 + H * 0.17)
            hb = max(w * 1.4, H * 0.025)
            f.add(K.rect(x - hb / 2, H * 0.06, hb, y2 + r2 * 1.2 - H * 0.06))
            f.add([(x - H * 0.06, 0), (x + H * 0.06, 0), (x + hb * 0.6, H * 0.12), (x - hb * 0.6, H * 0.12)])
            f.add(K.rect(x - H * 0.06, 0, H * 0.12, max(1.6, w)))
        elif hand == "laterne":
            x = r2 + H * 0.19
            yl = y2 + r2 * 0.75
            lb, lh = H * 0.07, H * 0.11
            f.add(K.stroke([(x, yl), (x, yl - H * 0.04)], max(w * 1.3, 1.0)))
            f.add(Z.abrunden([(x - lb * 0.6, yl - H * 0.04), (x + lb * 0.6, yl - H * 0.04), (x, yl)], 0.3, 1))
            f.add(Z.abrunden(K.rect(x - lb / 2, yl - H * 0.04 - lh, lb, lh), 0.5, 2))
            if lb - 2 * w > 1.4:
                f.cut(Z.abrunden(K.rect(x - lb / 2 + w, yl - H * 0.04 - lh + w * 1.2, lb - 2 * w, lh - 2.4 * w),
                                 0.3, 2))
                f.add(K.rect(x - w * 0.45, yl - H * 0.04 - lh + 0.5, w * 0.9, lh - 1.0))
    else:
        # Möhrennase im Profil
        yn = y3 + r3 * 0.05
        f.add([(r3 * 0.8, yn - H * 0.022), (r3 * 0.8, yn + H * 0.022), (r3 + H * 0.1, yn + H * 0.004)])
        # Schalende wehend nach hinten
        pfad = K.bez3((-r3 * 0.85, ys), (-r3 * 1.4, ys - H * 0.02), (-r3 * 1.6, ys - H * 0.1), (-r3 * 1.9, ys - H * 0.14),
                      14)
        f.add(K.stroke(pfad, sw))
        ex, ey = pfad[-1]
        for i in range(3):
            fx = ex - sw / 2 + sw * (i + 0.5) / 3
            f.add(K.rect(fx - w * 0.42, ey - H * 0.03, w * 0.84, H * 0.03 + 0.4))
    return f, dict(y1=y1, y2=y2, y3=y3, r1=r1, r2=r2, r3=r3, ys=ys, yt=yt, top=top)


def build(cfg, name="schneemann", hoehe=66.0, hut="zylinder", hand="besen", massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        hoehe = M.mass("schneemann", wichtel, INFO["params"], cfg)["hoehe"]
    T = cfg.T
    w = Z.wmin(cfg)
    H = cfg.s(hoehe)
    if H < 11 * T + 6:
        raise ValueError("Der Schneemann ist für diese Materialstärke zu klein – größer wählen oder dünneres Holz")
    notes = []
    asm = Assembly(name, params=dict(hoehe=H, hut=hut, hand=hand))
    # Teil A (Schlitz von oben) = Seitenansicht, Teil B (Schlitz von unten, Hut bleibt ganz) = Vorderansicht
    fa, g = _koerper(H, T, w, hut, False, hand)
    fb, _ = _koerper(H, T, w, hut, True, hand)

    def gesicht(part, von_oben):
        lin = []
        r3, y3, y2, r2, y1, r1 = g["r3"], g["y3"], g["y2"], g["r2"], g["y1"], g["r1"]
        if not von_oben:
            for sg in (-1, 1):
                lin.append((K.circle(sg * r3 * 0.35, y3 + r3 * 0.25, max(0.6, H * 0.012), 10), True))
            for i in range(5):                                                           # Kohlemund
                t = math.pi * (1.2 + 0.6 * i / 4)
                lin.append((K.circle(r3 * 0.5 * math.cos(t), y3 - r3 * 0.05 + r3 * 0.5 * math.sin(t),
                                     max(0.35, H * 0.006), 8), True))
            lin.append(([(r3 * 0.05, y3), (r3 * 0.05, y3 - r3 * 0.12)], False))
            for y in (y2 + r2 * 0.1, y2 - r2 * 0.35, y1 + r1 * 0.35):                  # Knöpfe
                lin.append((K.circle(0, y, max(0.7, H * 0.016), 12), True))
        else:
            lin.append((K.circle(r3 * 0.25, y3 + r3 * 0.25, max(0.6, H * 0.012), 10), True))
            lin.append(([(r3 * 0.85, g["y3"] - H * 0.005), (r3 + H * 0.08, g["y3"] + H * 0.0)], False))
        if not von_oben:
            sw = max(w * 1.3, H * 0.045)
            x = r3 * 0.45
            ys = g["ys"]
            lin.append(([(x - sw / 2, ys - H * 0.022), (x - sw / 2, ys - H * 0.14), (x + sw / 2, ys - H * 0.14),
                         (x + sw / 2, ys - H * 0.022)], False))
            for i in range(4):
                fx = x - sw / 2 + sw * (i + 0.5) / 4
                lin.append(([(fx, ys - H * 0.14), (fx, ys - H * 0.165)], False))
        if hut == "zylinder":
            lin.append(([(-r3 * 0.84, g["yt"] + H * 0.035), (r3 * 0.84, g["yt"] + H * 0.035)], False))
        for x in (-r3 * 0.6, 0.0, r3 * 0.6):                                            # Schalstreifen
            lin.append(([(x, g["ys"] - H * 0.018), (x, g["ys"] + H * 0.018)], False))
        Z.gravur(part, lin, rand=0.4)
    asm.parts += E.kreuzpaar(cfg, "schneemann", fa, fb, notes, g["y1"] + g["r1"] * 0.5, gesicht)
    asm.connect("schneemann_a:kreuz", "schneemann_b:kreuz")
    asm.notes.append("Teil B (Gesicht, Arme, Schlitz unten) von oben über Kreuz auf Teil A (Nase im Profil) "
                     "schieben. Tipp: weiß grundieren, Nase orange, Schal rot, Hut schwarz.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
