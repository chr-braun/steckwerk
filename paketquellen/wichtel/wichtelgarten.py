"""
Wichtelgarten – Paket „Wichtel“ (edles Zubehör, ab 1.1.0).

Ein Gartenstück zum Bestücken: Wiesenplatte mit Trittsteinen und Gemüsebeet (graviert) und Schlitzen, in die
Schubkarre, Gießkanne, Vogelhaus, Blumen, Fliegenpilze und Kürbisse mit Steckfüßen gesteckt werden. Jedes
Teil steht auf einem Grasstreifen, so passt es auch frei neben die Wichteltür.
"""
import importlib.util
import math
import os

from steckwerk import Assembly
from pakete import flag, num

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_garten",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
MO = _m.moebel()
Z, K = M.Z, M.K

UEBERSETZUNG = {"en": {
    "Wichtelgarten": "Elf garden",
    "Wiesenplatte mit Trittsteinen und Beet, dazu Schubkarre, Gießkanne, Vogelhaus, Blumen, Fliegenpilze und "
    "Kürbisse zum Einstecken.":
        "Lawn plate with stepping stones and a vegetable patch, plus wheelbarrow, watering can, birdhouse, flowers, "
        "toadstools and pumpkins to plug in.",
    "Breite": "Width", "Wiesenplatte": "Lawn plate", "Schubkarre": "Wheelbarrow", "Gießkanne": "Watering can",
    "Vogelhaus": "Birdhouse", "Blumen": "Flowers", "Fliegenpilze": "Toadstools", "Kürbisse": "Pumpkins",
    "Gartenteile": "Garden pieces",
}}

INFO = dict(
    label="Wichtelgarten", group="Wichtel",
    desc="Wiesenplatte mit Trittsteinen und Beet, dazu Schubkarre, Gießkanne, Vogelhaus, Blumen, Fliegenpilze und "
         "Kürbisse zum Einstecken.",
    params=[
        num("breite", "Breite", 98, 60, 300),
        flag("platte", "Wiesenplatte", True),
        flag("schubkarre", "Schubkarre", True, section="Gartenteile"),
        flag("giesskanne", "Gießkanne", True, section="Gartenteile"),
        flag("vogelhaus", "Vogelhaus", True, section="Gartenteile"),
        flag("blumen", "Blumen", True, section="Gartenteile"),
        flag("pilze", "Fliegenpilze", True, section="Gartenteile"),
        flag("kuerbisse", "Kürbisse", True, section="Gartenteile"),
    ],
)
INFO["params"] = M.mit_massstab("wichtelgarten", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _gras(f, x0, x1, h, w, seed):
    """Grasstreifen x0 … x1 (unten gerade) mit Halmen."""
    f.add(Z.abrunden(K.rect(x0, 0, x1 - x0, h), min(0.8, h * 0.3), 2))
    r = K.rng(seed, "gras")
    n = max(3, int((x1 - x0) / max(2.6, w * 1.9)))
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        L = h * (0.9 + 0.8 * r.random())
        lean = (r.random() - 0.5) * h * 0.8
        f.add([(x - w * 0.62, h - 0.3), (x + w * 0.62, h - 0.3), (x + lean, h + L)])


def _schubkarre(s, w):
    f = Z.Figur()
    g = 2.0 * s
    _gras(f, -15 * s, 15 * s, g, w, 1)
    rr = 5.5 * s                                    # Rad
    cx, cy = 9 * s, g + rr - 0.6
    f.add(K.circle(cx, cy, rr, 40))
    ri = rr - max(1.5 * w, 1.2 * s)
    if ri > 3 * w:                                  # Speichenrad
        f.cut(K.circle(cx, cy, ri, 40))
        f.add(K.circle(cx, cy, max(1.3 * w, 1.0 * s), 20))
        for k in range(5):
            a = 2 * math.pi * k / 5 + 0.3
            f.add(K.stroke([(cx, cy), (cx + (ri + 0.4) * math.cos(a), cy + (ri + 0.4) * math.sin(a))], max(1.3 * w, 0.9 * s)))
    # Wanne
    yw0, yw1 = cy + rr * 0.35, cy + rr * 0.35 + 8 * s
    f.add(Z.abrunden([(-6 * s, yw0), (cx + 1 * s, yw0), (cx + 5 * s, yw1), (-10 * s, yw1)], 0.6, 2))
    # Holme und Stütze
    hw = max(w * 1.2, 1.4 * s)
    f.add(K.stroke([(cx, cy), (-6 * s, yw0 + 0.5), (-16 * s, yw0 + 3.5 * s)], hw))
    f.add(K.stroke([(-4 * s, yw0), (-6 * s, g - 0.3)], hw))
    # Erde und Kürbis in der Wanne
    f.add(K.ellipse(-1 * s, yw1, 6.5 * s, 2.4 * s, 0, 30))
    f.add(K.circle(2.5 * s, yw1 + 2 * s, 2.6 * s, 24))
    return f, (yw0, yw1)


def _giesskanne(s, w):
    f = Z.Figur()
    g = 2.0 * s
    _gras(f, -10 * s, 10 * s, g, w, 2)
    kb, kh = 9 * s, 10 * s
    f.add(Z.abrunden([(-kb / 2, g - 0.3), (kb / 2, g - 0.3), (kb * 0.42, g + kh), (-kb * 0.42, g + kh)], 1.0 * s, 3))
    # Tülle mit Brause
    sw = max(w * 1.15, 1.5 * s)
    f.add(K.stroke([(kb * 0.35, g + kh * 0.3), (kb * 0.95, g + kh * 1.05)], sw))
    f.add(K.ellipse(kb * 1.0, g + kh * 1.1, 1.6 * s, 2.3 * s, -0.6, 20))
    # Bügel
    bw = max(w * 1.15, 1.3 * s)
    bg = [(-kb * 0.38 + kb * 0.76 * (0.5 - 0.5 * math.cos(t)), g + kh + 4.5 * s * math.sin(t))
          for t in (math.pi * i / 20 for i in range(21))]
    f.add(K.stroke(bg, bw))
    # seitlicher Griff
    f.add(K.stroke(K.bez((-kb * 0.45, g + kh * 0.85), (-kb * 0.95, g + kh * 0.6), (-kb * 0.48, g + kh * 0.25), 12), bw))
    return f, (g, g + kh, kb)


def _vogelhaus(s, w):
    f = Z.Figur()
    g = 2.0 * s
    _gras(f, -8 * s, 8 * s, g, w, 3)
    pw = max(w * 1.3, 2.0 * s)
    f.add(K.rect(-pw / 2, g - 0.3, pw, 22 * s))
    for sg in (-1, 1):                              # Streben
        f.add(K.stroke([(0, g + 15 * s), (sg * 4.5 * s, g + 21 * s)], max(w, 1.2 * s)))
    hb, hh = 11 * s, 8 * s
    y0 = g + 21 * s
    f.add(Z.abrunden(K.rect(-hb / 2, y0, hb, hh), 0.5, 2))
    f.add(Z.abrunden([(-hb / 2 - 2.2 * s, y0 + hh - 0.5), (hb / 2 + 2.2 * s, y0 + hh - 0.5), (0, y0 + hh + 6 * s)],
                     0.6, 2))
    rl = 1.9 * s                                    # Einflugloch und Sitzstange
    if rl > 1.1:
        f.cut(K.circle(0, y0 + hh * 0.58, rl, 20))
    f.add(K.stroke([(0, y0 + hh * 0.2), (4 * s, y0 + hh * 0.2)], max(w, 1.0 * s)))
    # Vögelchen auf dem Dach
    vx, vy = 2.8 * s, y0 + hh + 3.6 * s
    f.add(K.ellipse(vx, vy + 1.2 * s, 2.0 * s, 1.3 * s, 0.2, 20))
    f.add(K.circle(vx + 1.8 * s, vy + 2.3 * s, 1.0 * s, 14))
    f.add([(vx + 2.6 * s, vy + 2.6 * s), (vx + 3.8 * s, vy + 2.3 * s), (vx + 2.6 * s, vy + 1.9 * s)])
    f.add([(vx - 1.6 * s, vy + 1.4 * s), (vx - 3.6 * s, vy + 2.6 * s), (vx - 3.3 * s, vy + 1.2 * s)])
    return f, (y0, hh, hb)


def _blumen(s, w):
    f = Z.Figur()
    g = 2.0 * s
    _gras(f, -11 * s, 11 * s, g, w, 4)
    sw = max(w * 1.05, 1.2 * s)
    for k, (x, h, art, n) in enumerate(((-6.5 * s, 14 * s, "bluete", 6), (0.5 * s, 19 * s, "bluete", 7),
                                        (7 * s, 12 * s, "bluete", 5))):
        top = (x + (k - 1) * 1.2 * s, g + h)
        f.add(K.stroke(K.bez((x, g - 0.3), (x, g + h * 0.5), top, 10), sw))
        rb = (3.2 + 0.7 * (k == 1)) * s
        rp = max(1.1 * w, rb * 0.42)
        for j in range(n):
            aa = 2 * math.pi * j / n + 0.3 * k
            f.add(K.circle(top[0] + (rb - rp) * math.cos(aa), top[1] + (rb - rp) * math.sin(aa), rp, 16))
        f.add(K.circle(top[0], top[1], rb - rp + 0.3, 16))
        f.add(Z.blatt((x, g + h * 0.35), math.pi / 4 if k != 1 else 3 * math.pi / 4, 5 * s, 1.9 * s))
    return f


def _pilze(s, w):
    f = Z.Figur()
    g = 2.0 * s
    _gras(f, -10 * s, 10 * s, g, w, 5)
    lin = []
    for x, h, r in ((-4 * s, 9 * s, 5.5 * s), (5 * s, 6 * s, 4.0 * s)):
        st = r * 0.62
        f.add(Z.abrunden([(x - st / 2, g - 0.3), (x + st / 2, g - 0.3), (x + st * 0.4, g + h), (x - st * 0.4, g + h)],
                         0.4, 2))
        hut = [(x + r * math.cos(a), g + h - r * 0.15 + r * 0.82 * math.sin(a)) for a in (math.pi * i / 30 for i in range(31))]
        f.add(hut)
        rp = r * 0.12
        if rp >= 0.75 and r * 0.82 > 6 * rp + 3 * w:
            for dx, dy in ((-0.42, 0.3), (0.06, 0.52), (0.46, 0.28)):
                f.cut(K.circle(x + dx * r, g + h + dy * r * 0.8, rp, 12))
        else:
            for dx, dy in ((-0.5, 0.25), (-0.1, 0.55), (0.35, 0.45), (0.62, 0.15)):
                lin.append((K.circle(x + dx * r, g + h + dy * r * 0.8, max(0.6, r * 0.1), 12), True))
        lin.append(([(x - r * 0.85, g + h - r * 0.05), (x + r * 0.85, g + h - r * 0.05)], False))
    return f, lin


def _kuerbisse(s, w):
    f = Z.Figur()
    g = 2.0 * s
    _gras(f, -10 * s, 10 * s, g, w, 6)
    lin = []
    for x, b, h in ((-4 * s, 10 * s, 7 * s), (5 * s, 7 * s, 5.2 * s)):
        f.add(Z.G.pumpkin(x, g - 0.5, b, h, 5, True))
        for d in (-0.22, 0.22):
            lin.append((K.bez((x + d * b * 0.5, g + 0.4), (x + d * b * 1.6, g + h * 0.45), (x + d * b * 0.5, g + h * 0.88), 12),
                        False))
        lin.append(([(x, g + 0.4), (x, g + h * 0.88)], False))
    return f, lin


def _steckteil(cfg, name, fig, tw, pos, notes, gravur=()):
    part = Z.figur_teil(cfg, name, fig, notes, unten_flach=True)
    if tw:
        Z.zapfen_unten(part, 0.0, tw, cfg.T, "fuss", pos)
    if gravur:
        Z.gravur(part, list(gravur), rand=0.4)
    return part


def build(cfg, name="wichtelgarten", breite=98.0, platte=True, schubkarre=True, giesskanne=True, vogelhaus=True,
          blumen=True, pilze=True, kuerbisse=True, massstab="wichtel", wichtel=70.0):
    if massstab == "wichtel":
        breite = M.mass("wichtelgarten", wichtel, INFO["params"], cfg)["breite"]
    T = cfg.T
    w = Z.wmin(cfg)
    Bp = cfg.s(breite)
    s = Bp / 68.0                                   # Maßstab der Gartenteile (etwas größer als echt: mehr Details)
    q = Bp / 98.0                                   # Maßstab der Plätze auf der Wiese
    if 2.0 * s < 1.2 or 20 * s < 6 * T:
        raise ValueError("Der Garten ist für diese Materialstärke zu klein – größer wählen oder dünneres Holz")
    notes = []
    asm = Assembly(name, params=dict(breite=Bp))
    tw = max(cfg.min_tab_width + 0.6, min(cfg.tab_factor * T, 6.0 * s))
    teile = []
    if schubkarre:
        fig, (yw0, yw1) = _schubkarre(s, w)
        lin = [([(-8 * s, yw0 + (yw1 - yw0) * t), (9 * s, yw0 + (yw1 - yw0) * t)], False) for t in (0.33, 0.66)]
        teile.append(("schubkarre", fig, (-28 * q, 12 * q), lin))
    if giesskanne:
        fig, (y0, y1, kb) = _giesskanne(s, w)
        lin = [([(-kb * 0.44, y0 + (y1 - y0) * t), (kb * 0.44, y0 + (y1 - y0) * t)], False) for t in (0.2, 0.8)]
        teile.append(("giesskanne", fig, (26 * q, -10 * q), lin))
    if vogelhaus:
        fig, (y0, hh, hb) = _vogelhaus(s, w)
        lin = [([(-hb / 2 + 0.8, y0 + hh * t), (hb / 2 - 0.8, y0 + hh * t)], False) for t in (0.3,)]
        teile.append(("vogelhaus", fig, (36 * q, 8 * q), lin))
    if blumen:
        teile.append(("blumen", _blumen(s, w), (0.0, 16 * q), []))
    if pilze:
        fig, lin = _pilze(s, w)
        teile.append(("fliegenpilze", fig, (-30 * q, -12 * q), lin))
    if kuerbisse:
        fig, lin = _kuerbisse(s, w)
        teile.append(("kuerbisse", fig, (2 * q, -16 * q), lin))
    for k, (n, fig, _, lin) in enumerate(teile):
        asm.parts.append(_steckteil(cfg, n, fig, tw if platte else 0.0, 50 + k, notes, lin))
    if platte:
        D = Bp * 0.55
        umr = K.ellipse(0, 0, Bp / 2, D / 2, 0, 120)
        schl = [(n, x, y, tw, 50 + k, 0.0) for k, (n, _, (x, y), _) in enumerate(teile)]
        wiese = MO.platte(cfg, "wiese", umr, notes, schl, "keine")
        lin = []
        # Trittsteine quer durch den Garten
        for i in range(6):
            t = i / 5
            x = -Bp * 0.42 + Bp * 0.84 * t
            y = math.sin(t * math.pi * 1.2) * D * 0.05 - D * 0.02
            lin.append((Z.abrunden(K.rect(x - 3.2 * q, y - 2.2 * q, 6.4 * q, 4.4 * q), 1.6 * q, 3), True))
        # Gemüsebeet mit Reihen
        bx0, by0, bx1, by1 = 8 * q, 6 * q, 24 * q, D * 0.4
        if by1 - by0 > 6:
            lin.append((K.rect(bx0, by0, bx1 - bx0, by1 - by0), True))
            for j in range(1, 4):
                yy = by0 + (by1 - by0) * j / 4
                lin.append(([(bx0 + 1.2, yy), (bx1 - 1.2, yy)], False))
        # Grasbüschel
        r = K.rng(7, "wiese")
        for i in range(14):
            a = r.random() * 2 * math.pi
            rr = 0.55 + 0.38 * r.random()
            x, y = math.cos(a) * Bp / 2 * rr, math.sin(a) * D / 2 * rr
            lin.append(([(x - 1.0 * q, y), (x - 0.3 * q, y + 1.6 * q), (x, y), (x + 0.4 * q, y + 1.8 * q),
                         (x + 1.0 * q, y)], False))
        Z.gravur(wiese, lin, rand=0.8, loch_rand=1.2)
        asm.parts.append(wiese)
        for n, *_ in teile:
            asm.connect(f"{n}:fuss", f"wiese:{n}")
        asm.notes.append("Die Gartenteile mit ihren Steckfüßen in die Schlitze der Wiesenplatte stecken. Die Platte "
                         "grün bemalen, Trittsteine grau, das Beet braun.")
    else:
        asm.notes.append("Ohne Wiesenplatte stehen die Gartenteile frei auf ihrem Grasstreifen – mit einem Leimpunkt "
                         "halten sie fest, z. B. neben der Wichteltür.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
