"""
Wichtel-Schaukelstuhl – Paket „Wichtel“ (edles Zubehör, ab 1.1.0).

Schaukelstuhl zum Stecken: zwei Seitenteile mit geschwungenen Kufen, gedrechselten Sprossen unter der
Armlehne, Schnecke vorn und Zierkugel oben; Sitz und schräge Sprossenlehne stecken in den Seitenteilen.
Dazu ein gestepptes Sitzkissen und ein Strickkorb mit Wollknäuel und Nadeln (über Kreuz gesteckt).
"""
import importlib.util
import math
import os

from steckwerk import Assembly, Part, oriented
from pakete import flag, num, sel

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_schaukel",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
MO = _m.moebel()
E = _m.modul("_edel")
Z, K = M.Z, M.K

UEBERSETZUNG = {"en": {
    "Wichtel-Schaukelstuhl": "Elf rocking chair",
    "Schaukelstuhl zum Stecken mit geschwungenen Kufen, Sprossen, schräger Lehne und Armlehnen-Schnecken – dazu "
    "Sitzkissen und Strickkorb.":
        "Slot-together rocking chair with curved rockers, spindles, a reclined back and scrolled arms – plus seat "
        "cushion and knitting basket.",
    "Höhe": "Height", "Sitzbreite": "Seat width", "Motiv in der Zarge": "Motif in the apron", "keins": "none",
    "Lehnenneigung": "Back recline", "Sitzkissen": "Seat cushion", "Strickkorb": "Knitting basket",
}}

INFO = dict(
    label="Wichtel-Schaukelstuhl", group="Wichtel",
    desc="Schaukelstuhl zum Stecken mit geschwungenen Kufen, Sprossen, schräger Lehne und Armlehnen-Schnecken – "
         "dazu Sitzkissen und Strickkorb.",
    params=[
        num("hoehe", "Höhe", 64, 40, 220),
        num("breite", "Sitzbreite", 34, 22, 150),
        num("neigung", "Lehnenneigung", 14, 0, 25, unit="°"),
        sel("motiv", "Motiv in der Zarge", MO.MOTIVE, "herz"),
        flag("kissen", "Sitzkissen", True),
        flag("korb", "Strickkorb", True),
    ],
)
INFO["params"] = M.mit_massstab("schaukelstuhl", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _kufe(Ds, rw):
    xa, xb, xm = -0.28 * Ds, 1.3 * Ds, 0.5 * Ds
    R = 1.55 * Ds

    def y(x):
        return rw / 2 + R - math.sqrt(max(R * R - (x - xm) ** 2, 0.0))
    return [(xa + (xb - xa) * i / 40, y(xa + (xb - xa) * i / 40)) for i in range(41)], y


def build(cfg, name="schaukelstuhl", hoehe=64.0, breite=34.0, neigung=14.0, motiv="herz", kissen=True, korb=True,
          massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        _mm = M.mass("schaukelstuhl", wichtel, INFO["params"], cfg)
        hoehe, breite = _mm["hoehe"], _mm["breite"]
    T = cfg.T
    w = Z.wmin(cfg)
    H, B = cfg.s(hoehe), cfg.s(breite)
    notes = []
    asm = Assembly(name, params=dict(hoehe=H, breite=B, neigung=neigung))
    hs = H * 0.38                                   # Sitzoberkante
    Ds = max(H * 0.44, 6 * T + 6)                   # Sitztiefe
    rand = max(1.8, T * 0.6)
    if hs < 4 * T + 8:
        raise ValueError("Der Schaukelstuhl ist für diese Materialstärke zu klein – größer wählen oder dünneres Holz")
    rw = max(w * 1.6, T * 0.9)                      # Kufenstärke
    lw = max(w * 1.5, T * 0.85)                     # Vorderbein
    pw = T + 2 * rand                               # Hinterpfosten (trägt die Lehnenschlitze)
    a = math.radians(max(0.0, min(25.0, float(neigung))))
    d = (-math.sin(a), math.cos(a))
    x0, x1 = 0.1 * Ds, 0.9 * Ds                     # Hinterpfosten / Vorderbein
    kufe, ky = _kufe(Ds, rw)
    P0 = (x0, hs)
    Lp = (H - hs) / math.cos(a)
    Ptop = (x0 + d[0] * Lp, hs + d[1] * Lp)
    ah = (H - hs) * 0.36                            # Armlehnenhöhe über dem Sitz

    tw = min(M.tabbreite(cfg, Ds, 0.22), Ds * 0.24)
    xs_sitz = [x0 + (x1 - x0) * 0.28, x0 + (x1 - x0) * 0.74]
    sb0 = T + 0.8                                   # Lehne beginnt knapp über dem Sitz
    Lb = Lp - pw * 1.2 - sb0
    if Lb < 3 * T + 8:
        raise ValueError("Der Schaukelstuhl ist für diese Materialstärke zu klein – größer wählen oder dünneres Holz")
    tl = min(M.tabbreite(cfg, Lb, 0.2), Lb * 0.22)
    s_lehne = [Lb * 0.24, Lb * 0.66]
    winkel = math.atan2(d[1], d[0])

    # ---------------- Seitenteile ----------------
    f = Z.Figur()
    f.add(K.stroke(kufe, rw))
    for x in (kufe[0], kufe[-1]):                   # Kringel an den Kufenenden
        f.add(K.circle(x[0], x[1] + rw * 0.35, rw * 0.85, 20))
    f.add(K.stroke([(x1, ky(x1)), (x1 + Ds * 0.03, hs + ah)], lw))
    f.add(K.stroke([(x0, ky(x0)), P0, (Ptop[0] - d[0] * pw * 0.5, Ptop[1] - d[1] * pw * 0.5)], pw, pw * 0.8))
    f.add(K.circle(Ptop[0], Ptop[1] - pw * 0.15, pw * 0.55, 24))                       # Zierkugel
    # Sitzzarge mit Bogenausschnitt
    zy0 = hs - T / 2 - rand - max(2.2 * w, hs * 0.22)
    f.add(K.rect(x0, zy0, x1 - x0, hs - zy0 - 0.2))
    f.cut(K.ellipse((x0 + x1) / 2, zy0, (x1 - x0) * 0.36, (hs - zy0) * 0.45, 0, 40))
    if motiv != "keine":
        g = min((hs - zy0) * 0.42, (x1 - x0) * 0.22)
        if g >= 2.6 * w:
            for x in (x0 + (x1 - x0) * 0.2, x0 + (x1 - x0) * 0.8):
                f.merge(Z.ausschnitt(motiv, x, hs - T - rand - g * 0.5 + 0.3, g))
    # Armlehne mit Schnecke
    pa = (x0 + d[0] * ah / math.cos(a), hs + ah)
    pe = (x1 + Ds * 0.08, hs + ah * 0.93)
    aw = max(w * 1.3, lw * 0.85)
    f.add(K.stroke(K.bez(pa, ((pa[0] + pe[0]) / 2, hs + ah * 1.08), pe, 16), aw))
    rs = aw * 1.05
    f.add(K.circle(pe[0], pe[1] - rs * 0.35, rs, 24))
    if rs - w > 0.7:
        f.cut(K.circle(pe[0], pe[1] - rs * 0.35, max(0.7, rs - w * 1.05), 16))
    # gedrechselte Sprossen zwischen Sitz und Armlehne
    n = 3 if (x1 - x0) > 12 * w else 2
    for i in range(n):
        x = x0 + pw / 2 + (x1 - x0 - pw / 2) * (i + 1) / (n + 1)
        y_arm = hs + ah * 1.0
        f.add(K.stroke([(x, hs - 0.5), (x, y_arm)], max(w * 0.95, 1.0)))
        f.add(K.ellipse(x, hs + ah * 0.5, max(w * 0.95, 1.0) * 0.95, ah * 0.12, 0, 16))
    schlitze = [(f"sitz{k}", x, hs - T / 2, tw, 0.0) for k, x in enumerate(xs_sitz)]
    schlitze += [(f"lehne{k}", P0[0] + d[0] * (sb0 + s), P0[1] + d[1] * (sb0 + s), tl, winkel)
                 for k, s in enumerate(s_lehne)]
    solid = [Z.schlitz_polster(cx, cy, L, T, rand, wi) for _, cx, cy, L, wi in schlitze]
    basis = Z.figur_teil(cfg, "seite_l", f, notes, solid=solid)
    for k, s in enumerate("lr"):
        p = Part(f"seite_{s}", list(basis.outline), [list(h) for h in basis.holes])
        for j, (fid, cx, cy, L, wi) in enumerate(schlitze):
            Z.schlitz(p, fid, cx, cy, L, T, 10 * (k + 1) + j, wi)
        asm.parts.append(p)

    # ---------------- Sitz ----------------
    Ls = B - MO.EINZUG
    Dss = x1 - x0 + lw * 0.5
    sitz = Z.brett("sitz", Ls, Dss, T,
                   links=[(x - x0, tw, f"l{k}", 10 + k) for k, x in enumerate(xs_sitz)],
                   rechts=[(x - x0, tw, f"r{k}", 20 + k) for k, x in enumerate(xs_sitz)])
    E.kassette(sitz, 0, 0, Ls, Dss, max(1.6, min(Ls, Dss) * 0.1))
    asm.parts.append(sitz)
    for k in range(2):
        asm.connect(f"sitz:l{k}", f"seite_l:sitz{k}")
        asm.connect(f"sitz:r{k}", f"seite_r:sitz{k}")

    # ---------------- Lehne (exakt konstruiert, Sprossen als Durchbrüche, Bogen oben) ----------------
    Wl = Ls
    Hs = Lb * 0.84
    links, fl = Z.kante_mit_zapfen((0.0, Hs), (0.0, 0.0), [(Hs - s, tl, f"l{k}", 12 + k)
                                                          for k, s in enumerate(s_lehne)], T)
    rechts, fr = Z.kante_mit_zapfen((Wl, 0.0), (Wl, Hs), [(s, tl, f"r{k}", 22 + k) for k, s in enumerate(s_lehne)], T)
    bogen = [(Wl / 2 + Wl / 2 * math.cos(t), Hs + (Lb - Hs) * math.sin(t)) for t in (math.pi * i / 30 for i in range(1, 30))]
    umr = [(0.0, 0.0)] + rechts + [(Wl, Hs)] + bogen + links
    lehne = Part("lehne", oriented(umr, True), features=fl + fr)
    m = max(2.4, T * 0.8, w * 1.6)
    sp = max(w * 1.2, 1.6)
    yl0, yl1 = Lb * 0.1, Hs * 0.86
    ng = max(2, int((Wl - 2 * m + sp) / max(4.0, sp * 3.2)))
    gw = (Wl - 2 * m - (ng - 1) * sp) / ng
    if gw > 1.2 and yl1 - yl0 > 4:
        for i in range(ng):
            gx = m + i * (gw + sp)
            lehne.add_hole(Z.abrunden(K.rect(gx, yl0, gw, yl1 - yl0), min(gw * 0.45, 1.2), 3))
    Z.gravur(lehne, [(Z.herz(Wl / 2, (Hs * 0.86 + Lb) / 2 + 0.2, min(4.5, (Lb - Hs * 0.86) * 0.55)), True),
                     ([(m, yl1 + 0.9), (Wl - m, yl1 + 0.9)], False)], rand=0.5)
    asm.parts.append(lehne)
    for k in range(2):
        asm.connect(f"lehne:l{k}", f"seite_l:lehne{k}")
        asm.connect(f"lehne:r{k}", f"seite_r:lehne{k}")

    # ---------------- Kissen und Strickkorb ----------------
    if kissen:
        kb, kd = Ls * 0.88, Dss * 0.8
        kf = Z.Figur().add(Z.abrunden(K.rect(-kb / 2, -kd / 2, kb, kd), min(kb, kd) * 0.22, 6))
        for sx in (-1, 1):                                                               # Zipfel an den Ecken
            for sy in (-1, 1):
                kf.add(K.circle(sx * kb * 0.47, sy * kd * 0.45, max(w, kd * 0.08), 12))
        kp = Z.figur_teil(cfg, "kissen", kf, notes)
        lin = [(Z.abrunden(K.rect(-kb / 2 + 1.2, -kd / 2 + 1.2, kb - 2.4, kd - 2.4), min(kb, kd) * 0.18, 6), True)]
        for i in (-1, 0, 1):                                                             # Steppung
            for j in (-1, 1):
                cx, cy = i * kb * 0.27, j * kd * 0.18
                lin.append((K.circle(cx, cy, max(0.45, kd * 0.025), 10), True))
        for j in (-1, 1):
            lin.append(([(-kb * 0.27, j * kd * 0.18), (0, -j * kd * 0.18), (kb * 0.27, j * kd * 0.18)], False))
        Z.gravur(kp, lin, rand=0.5)
        asm.parts.append(kp)
    if korb:
        hk = max(14.0, H * 0.3)
        asm.parts += strickkorb(cfg, "strickkorb", hk, notes)
        asm.connect("strickkorb_a:kreuz", "strickkorb_b:kreuz")

    asm.notes.append("Den Sitz in die waagerechten Schlitze beider Seitenteile stecken, dann die Lehne schräg in die "
                     "Schlitze der Hinterpfosten.")
    if kissen:
        asm.notes.append("Das Kissen bemalen und auf den Sitz leimen.")
    if korb:
        asm.notes.append("Strickkorb: Teil B von oben über Kreuz auf Teil A schieben.")
    asm.notes += list(dict.fromkeys(notes))
    return asm


def strickkorb(cfg, name, hk, notes):
    """Strickkorb mit Henkel, Wollknäuel und zwei Stricknadeln – zwei gekreuzte Teile."""
    w = Z.wmin(cfg)
    T = cfg.T
    bk = hk * 0.9
    hb = hk * 0.45                                  # Korbhöhe

    def korbform(nadeln):
        f = Z.Figur()
        f.add([(-bk * 0.36, 0), (bk * 0.36, 0), (bk / 2, hb), (-bk / 2, hb)])
        f.add(Z.abrunden(K.rect(-bk / 2 - 0.6, hb - max(1.4, w), bk + 1.2, max(1.8, w * 1.1)), 0.5, 2))
        rk = hk * 0.24                              # Wollknäuel
        f.add(K.circle(0, hb + rk * 0.7, rk, 36))
        if nadeln:
            for sg in (-1, 1):
                p0 = (sg * rk * 0.2, hb + rk * 0.6)
                p1 = (sg * rk * 1.5, hb + rk * 2.2)
                f.add(K.stroke([p0, p1], max(w * 1.1, 1.2)))
                f.add(K.circle(p1[0], p1[1], max(w * 1.1, 1.2), 12))
        else:                                       # Henkel
            hw = max(w * 1.1, 1.2)
            henkel = [(bk * 0.42 * math.cos(t), hb + hk * 0.5 * math.sin(t)) for t in (math.pi * i / 24 for i in range(25))]
            f.add(K.stroke(henkel, hw))
        return f

    def grav(part, von_oben):
        lin = []
        for k in range(1, 4):                       # Flechtwerk
            y = hb * k / 4.4
            lin.append(([(-bk * 0.5, y), (bk * 0.5, y)], False))
        for i in range(-3, 4):
            x = i * bk * 0.12
            lin.append(([(x * 0.75, 0.4), (x, hb - 1.6)], False))
        rk = hk * 0.24
        for t in (0.35, 0.7):
            lin.append((K.arc(0, hb + rk * 0.7 - rk * 0.4, rk * t + rk * 0.3, math.pi * 0.2, math.pi * 0.8, 10), False))
        Z.gravur(part, lin, rand=0.4)
    return E.kreuzpaar(cfg, name, korbform(True), korbform(False), notes, hb * 0.5, grav)
