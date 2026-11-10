"""
Wichtel-Standuhr – Paket „Wichtel“ (edles Zubehör, ab 1.1.0).

Großvateruhr zum Stecken: Gehäuse aus Front (mit Pendelfenster), Rückwand und zwei Seiten zwischen Sockel-
und Deckplatte, davor eine filigrane Zierblende. Oben steht der Uhrenkopf mit graviertem Zifferblatt, Krone
und Zierkugeln; hinter dem Fenster schwingt (aufgeleimt) das Pendel. Auf Wunsch mit Inschrift.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_standuhr",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
MO = _m.moebel()
E = _m.modul("_edel")
Z, K = M.Z, M.K

KRONEN = [("bogen", "Bogen mit Kugeln"), ("giebel", "Giebel"), ("schwan", "Schwanenhals")]
ZIER = [("keine", "keins")] + Z.ROSETTEN

UEBERSETZUNG = {"en": {
    "Wichtel-Standuhr": "Elf grandfather clock",
    "Großvateruhr zum Stecken mit Pendelfenster, Pendel, Zierblende, Uhrenkopf mit Zifferblatt und Krone – auf "
    "Wunsch mit Inschrift.":
        "Slot-together grandfather clock with pendulum window, pendulum, decorative front, clock head with dial and "
        "crown – optional inscription.",
    "Höhe": "Height", "Krone": "Crown", "Bogen mit Kugeln": "Arch with finials", "Giebel": "Pediment",
    "Schwanenhals": "Swan neck", "Zierrosette": "Rosette", "keins": "none", "Inschrift": "Inscription",
    "z. B. ein Name oder eine Jahreszahl": "e.g. a name or a year",
}}

INFO = dict(
    label="Wichtel-Standuhr", group="Wichtel",
    desc="Großvateruhr zum Stecken mit Pendelfenster, Pendel, Zierblende, Uhrenkopf mit Zifferblatt und Krone – auf "
         "Wunsch mit Inschrift.",
    params=[
        num("hoehe", "Höhe", 91, 60, 300),
        sel("krone", "Krone", KRONEN, "bogen"),
        sel("rosette", "Zierrosette", ZIER, "bluete"),
        txt("inschrift", "Inschrift", "", help="z. B. ein Name oder eine Jahreszahl"),
    ],
)
INFO["params"] = M.mit_massstab("standuhr", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _fenster(Wf, y0, y1, x=0.0):
    """Pendelfenster mit Rundbogen oben."""
    r = Wf / 2
    hs = y1 - r
    return [(x - r, y0), (x + r, y0), (x + r, hs)] + \
        [(x + r * math.cos(a), hs + r * math.sin(a)) for a in (math.pi * i / 32 for i in range(1, 32))] + [(x - r, hs)]


def _kopf(cfg, Wh, Hh, krone, tw, xs, notes):
    """Uhrenkopf: Kasten mit Bogen oben, Krone, Zierkugeln; Zapfen unten."""
    w = Z.wmin(cfg)
    T = cfg.T
    hk = Hh * 0.72                                    # Kastenhöhe (bis Beginn der Krone)
    f = Z.Figur().add(Z.abrunden(K.rect(-Wh / 2, 0, Wh, hk), 0.6, 2))
    f.add(K.rect(-Wh / 2 - 1.0, hk - max(1.6, w), Wh + 2.0, max(1.6, w)))               # Gesims
    hc = Hh - hk
    if krone == "giebel":
        f.add([(-Wh / 2 - 1.0, hk - 0.3), (Wh / 2 + 1.0, hk - 0.3), (0, hk + hc * 0.75)])
        if hc * 0.4 > 3 * w:
            f.cut(Z.abrunden([(-Wh * 0.28, hk + hc * 0.12), (Wh * 0.28, hk + hc * 0.12), (0, hk + hc * 0.55)], 0.4, 2))
        rk = max(w * 1.1, hc * 0.12)
        f.add(K.circle(0, hk + hc * 0.75 + rk * 0.8, rk, 20))
    elif krone == "schwan":
        sw = max(w * 1.2, Wh * 0.08)
        for sg in (-1, 1):
            pfad = K.bez3((sg * Wh / 2, hk - 0.5), (sg * Wh * 0.45, hk + hc * 0.6), (sg * Wh * 0.12, hk + hc * 0.75),
                          (sg * Wh * 0.14, hk + hc * 0.45), 20)
            f.add(K.stroke(pfad, sw))
            f.add(K.circle(sg * Wh * 0.14, hk + hc * 0.45, sw * 0.9, 16))
        f.add(K.rect(-Wh / 2, hk - 0.5, Wh, sw * 0.9))
        rk = max(w * 1.1, hc * 0.13)
        f.add(K.rect(-sw * 0.5, hk, sw, hc * 0.6))
        f.add(K.circle(0, hk + hc * 0.6 + rk * 0.7, rk, 20))
    else:
        f.add([(-Wh / 2, hk - 0.3), (Wh / 2, hk - 0.3)] +
              [(Wh / 2 * math.cos(a), hk - 0.3 + hc * 0.55 * math.sin(a)) for a in (math.pi * i / 30 for i in range(1, 30))])
        rk = max(w * 1.1, hc * 0.13)
        for x, y in ((-Wh / 2 + rk * 0.6, hk), (Wh / 2 - rk * 0.6, hk), (0, hk + hc * 0.55)):
            f.add(K.rect(x - w / 2, y - 0.5, w, rk * 1.2 + 0.5))
            f.add(K.circle(x, y + rk * 1.2 + rk * 0.7, rk, 20))
    part = Z.figur_teil(cfg, "kopf", f, notes, unten_flach=True)
    for k, x in enumerate(xs):
        Z.zapfen_unten(part, x, tw, T, f"fuss{k}", 30 + k)
    r = min(Wh * 0.36, hk * 0.4)
    lin = E.zifferblatt(0.0, hk * 0.5, r)
    for sg in (-1, 1):                                                                 # Eckzwickel
        x = sg * (Wh / 2 - 1.6)
        lin.append(([(x, hk - 2.0), (x - sg * min(3.0, Wh * 0.12), hk - 2.0)], False))
        lin.append(([(x, hk * 0.08 + 0.8), (x - sg * min(3.0, Wh * 0.12), hk * 0.08 + 0.8)], False))
    Z.gravur(part, lin, rand=0.5)
    return part


def build(cfg, name="standuhr", hoehe=91.0, krone="bogen", rosette="bluete", inschrift="", massstab="wichtel",
          wichtel=70.0):
    if massstab == "wichtel":
        hoehe = M.mass("standuhr", wichtel, INFO["params"], cfg)["hoehe"]
    T = cfg.T
    w = Z.wmin(cfg)
    H = cfg.s(hoehe)
    notes = []
    asm = Assembly(name, params=dict(hoehe=H, krone=krone))
    Wb = max(H * 0.26, 6 * T + 8)                     # Gehäusebreite
    Dk = max(H * 0.17, 5 * T + 6)                     # Tiefe
    Hb = H * 0.6 - 2 * T                              # Gehäuse zwischen Sockel und Deckplatte
    if Hb < 8 * T + 10:
        raise ValueError("Die Standuhr ist für diese Materialstärke zu klein – größer wählen oder dünneres Holz")
    ov = max(1.6, Wb * 0.07)
    tw = min(M.tabbreite(cfg, Wb, 0.26), Wb * 0.3)
    xf = Wb * 0.27
    ts = min(M.tabbreite(cfg, Dk - 2 * T, 0.5), Dk - 2 * T - 2.0)
    if ts < cfg.min_tab_width:
        raise ValueError("Die Standuhr ist für diese Materialstärke zu klein – größer wählen oder dünneres Holz")
    zl = [(-xf, "l"), (xf, "r")]
    # Fenster: obere Hälfte des Gehäuses
    Wf = Wb * 0.46
    fy0, fy1 = Hb * 0.44, Hb * 0.9
    front = Z.brett("front", Wb, Hb, T,
                    unten=[(Wb / 2 + x, tw, "u" + s, 10 + k) for k, (x, s) in enumerate(zl)],
                    oben=[(Wb / 2 + x, tw, "o" + s, 20 + k) for k, (x, s) in enumerate(zl)])
    front.add_hole(_fenster(Wf, fy0, fy1, Wb / 2))
    asm.parts.append(front)
    rueck = Z.brett("rueckwand", Wb, Hb, T,
                    unten=[(Wb / 2 + x, tw, "u" + s, 12 + k) for k, (x, s) in enumerate(zl)],
                    oben=[(Wb / 2 + x, tw, "o" + s, 22 + k) for k, (x, s) in enumerate(zl)])
    asm.parts.append(rueck)
    Ls = Dk - 2 * T - 0.2
    for k, s in enumerate("lr"):
        sp = Z.brett(f"seite_{s}", Ls, Hb, T, unten=[(Ls / 2, ts, "u", 14 + k)], oben=[(Ls / 2, ts, "o", 24 + k)])
        E.kassette(sp, 0, 0, Ls, Hb * 0.32, max(1.4, Ls * 0.14))
        E.kassette(sp, 0, Hb * 0.32, Ls, Hb, max(1.4, Ls * 0.14))
        asm.parts.append(sp)
    # Sockel- und Deckplatte
    yv, yh = T / 2, Dk - T / 2
    Wh = Wb * 0.92                                     # Uhrenkopf
    Hh = H - Hb - 2 * T - 0.0
    tk = min(M.tabbreite(cfg, Wh, 0.4), Wh * 0.4, Wb - 2 * T - 2 * max(2.0, T * 0.8) - 2.0)
    for pl, z0, extra in (("sockel", 10, []), ("deckel", 20, [("kopf0", 0.0, -Dk / 2, tk, 30, 0.0)])):
        schl = []
        for k, (x, s) in enumerate(zl):
            schl += [(f"f{s}", x, -yv, tw, z0 + k, 0.0), (f"r{s}", x, -yh, tw, z0 + 2 + k, 0.0)]
        for k, s in enumerate("lr"):
            schl.append((f"s{s}", (Wb / 2 - T / 2) * (-1 if s == "l" else 1), -Dk / 2, ts, z0 + 4 + k, math.pi / 2))
        o = max(ov * (1.6 if pl == "sockel" else 1.0), max(2.0, T * 0.8) + 0.6)
        umr = Z.abrunden([(-Wb / 2 - o, -Dk - o), (Wb / 2 + o, -Dk - o), (Wb / 2 + o, o), (-Wb / 2 - o, o)],
                         min(1.5, o * 0.6), 3)
        asm.parts.append(MO.platte(cfg, pl, umr, notes, schl + extra, "keine"))
    for k, (x, s) in enumerate(zl):
        for t, pl in (("u", "sockel"), ("o", "deckel")):
            asm.connect(f"front:{t}{s}", f"{pl}:f{s}")
            asm.connect(f"rueckwand:{t}{s}", f"{pl}:r{s}")
    for s in "lr":
        asm.connect(f"seite_{s}:u", "sockel:s" + s)
        asm.connect(f"seite_{s}:o", "deckel:s" + s)

    # Zierblende: Fenster mit Profil, unten Füllung mit Rosette, Inschrift
    f = Z.Figur().add(K.rect(-Wb / 2, 0, Wb, Hb))
    f.cut(_fenster(Wf, fy0, fy1))
    yr0, yr1 = Hb * 0.06, fy0 - Hb * 0.06
    if inschrift.strip():
        rr = min(Wb * 0.3, (yr1 - yr0) * 0.28)
        yc = yr0 + (yr1 - yr0) * 0.64
    else:
        rr = min(Wb * 0.3, (yr1 - yr0) * 0.38)
        yc = (yr0 + yr1) / 2
    if rosette != "keine" and rr > 2.4 * w:
        f.cut(K.circle(0, yc, rr, 48))
        f.merge(Z.rosette(rr + 0.2, rosette, 8, w).map(lambda p: (p[0], p[1] + yc)))
    blende = Z.figur_teil(cfg, "zierblende", f, notes, unten_flach=True)
    lin = []
    r = Wf / 2
    for d in (1.2, 2.3):
        rr2 = r + d
        hs = fy1 - r
        lin.append(([(-r - d, fy0 - d)] + [(rr2 * math.cos(a), hs + rr2 * math.sin(a))
                                          for a in (math.pi * (1 - i / 32) for i in range(33))] + [(r + d, fy0 - d)],
                    False))
        lin.append(([(-r - d, fy0 - d), (r + d, fy0 - d)], False))
    lin.append((Z.abrunden(K.rect(-Wb / 2 + 1.4, yr0, Wb - 2.8, yr1 - yr0), 1.0, 3), True))
    Z.gravur(blende, lin, rand=0.5)
    if inschrift.strip():
        M.text_gravur(blende, inschrift, 0.0, yr0 + (yr1 - yr0) * 0.16, Wb - 5.0, (yr1 - yr0) * 0.24,
                      max(2.0, (yr1 - yr0) * 0.2), rand=0.3)
    asm.parts.append(blende)

    # Pendel: Aufhängeleiste (breiter als das Fenster, wird innen über das Fenster geleimt), Stange, Scheibe
    fh = fy1 - fy0
    leiste = max(2.6, w * 1.6)
    rp = min(Wf * 0.34, fh * 0.17)
    pf = Z.Figur().add(Z.abrunden(K.rect(-Wf / 2 - 2.0, fh, Wf + 4.0, leiste), 0.5, 2))
    pf.add(K.rect(-w * 0.55, fh * 0.2, w * 1.1, fh * 0.8 + 0.5))
    pf.add(K.circle(0, fh * 0.2, rp, 40))
    if rp > 3 * w:
        pf.cut(K.circle(0, fh * 0.2, rp * 0.45, 32))
        pf.merge(Z.rosette(rp * 0.45 + 0.2, "sonne", 10, w).map(lambda p: (p[0], p[1] + fh * 0.2)))
    pendel = Z.figur_teil(cfg, "pendel", pf, notes)
    if rp <= 3 * w:
        Z.gravur(pendel, [(K.circle(0, fh * 0.2, rp * 0.62, 24), True), (K.circle(0, fh * 0.2, rp * 0.3, 16), True)],
                 rand=0.4)
    asm.parts.append(pendel)
    # Gewichte (zwei Zylinder an Ketten), neben dem Pendel aufleimen
    gl = Z.Figur()
    for sg in (-1, 1):
        x = sg * Wf * 0.3
        gl.add(K.rect(x - w * 0.45, fh * 0.45, w * 0.9, fh * 0.55 + 0.5))
        gl.add(Z.abrunden(K.rect(x - max(w, Wf * 0.08), fh * 0.3, 2 * max(w, Wf * 0.08), fh * 0.18), 0.5, 2))
    gl.add(Z.abrunden(K.rect(-Wf / 2 - 2.0, fh, Wf + 4.0, leiste), 0.5, 2))
    asm.parts.append(Z.figur_teil(cfg, "gewichte", gl, notes))

    asm.parts.append(_kopf(cfg, Wh, Hh, krone, tk, (0.0,), notes))
    asm.connect("kopf:fuss0", "deckel:kopf0")

    asm.notes.append("Seiten, Front und Rückwand in den Sockel stecken, Deckplatte aufsetzen, den Uhrenkopf in die Mitte "
                     "der Deckplatte stecken. Die Zierblende auf die Front leimen.")
    asm.notes.append("Vor dem Zusammenbau Gewichte und Pendel innen über das Fenster leimen (erst die Gewichte, "
                     "dann das Pendel davor). Tipp: Pendelscheibe golden bemalen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
