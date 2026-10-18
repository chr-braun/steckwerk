"""
Straßenlaterne – Paket „Wichtelwelt“.

Eine nostalgische Gaslaterne aus zwei gleich großen Silhouetten, die über Kreuz ineinandergesteckt werden
und so frei stehen: gestufter Sockel, schlanker Mast mit Ringen, geschwungene Konsolen, Laternenkopf mit
Sprossenfenstern, Dach mit Knauf. Auf Wunsch mit Schleife am Mast und Sternen an den Konsolen.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, JointFeature, Part
from pakete import num, sel

_spec = importlib.util.spec_from_file_location("swpaket_wichtelwelt__lade_laterne",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.welt()
Z, K = M.Z, M.K

DEKO = [("schleife", "Schleife am Mast"), ("sterne", "Sterne an den Konsolen"), ("beides", "beides"),
        ("keine", "keine")]
KOEPFE = [("klassisch", "klassisch (sechseckig)"), ("rund", "rund mit Kuppel"), ("spitz", "spitzes Dach")]

UEBERSETZUNG = {"en": {
    "Straßenlaterne": "Street lantern", "Wichtelwelt": "Elf world",
    "Nostalgische Laterne aus zwei Silhouetten, über Kreuz gesteckt: Sockel, Mast mit Ringen, Konsolen, Laternenkopf mit Sprossenfenstern.":
        "Nostalgic lantern made of two silhouettes slotted together crosswise: base, post with rings, brackets, lantern head with barred windows.",
    "Höhe": "Height", "Kopf": "Head", "Schmuck": "Decoration", "Schleife am Mast": "Bow on the post",
    "Sterne an den Konsolen": "Stars on the brackets", "beides": "both", "keine": "none",
    "klassisch (sechseckig)": "classic (hexagonal)", "rund mit Kuppel": "round with dome", "spitzes Dach": "pointed roof",
    "Teil B (Schlitz unten) von oben auf Teil A (Schlitz oben) schieben, bis beide unten bündig stehen.":
        "Slide part B (slot at the bottom) from above onto part A (slot at the top) until both are flush at the bottom.",
    "Tipp: Hinter die Fenster Transparentpapier kleben und ein LED-Teelicht davor stellen.":
        "Tip: glue tracing paper behind the windows and put an LED tea light in front.",
}}

INFO = dict(
    label="Straßenlaterne", group="Wichtelwelt",
    desc="Nostalgische Laterne aus zwei Silhouetten, über Kreuz gesteckt: Sockel, Mast mit Ringen, Konsolen, "
         "Laternenkopf mit Sprossenfenstern.",
    params=[
        num("hoehe", "Höhe", 150, 90, 400),
        sel("kopf", "Kopf", KOEPFE, "klassisch"),
        sel("deko", "Schmuck", DEKO, "beides"),
    ],
)


def silhouette(u: float, kopf: str, deko: str, w: float, cb: float, a: bool):
    """Figur der Laterne (Höhe u, x = 0 Mitte). cb: halbe Breite des Mittelstegs im Kopf (Kreuzschlitz).
    a: Teil A trägt die Schleife (B nicht – sonst stießen sie zusammen)."""
    f = Z.Figur()
    s = lambda pts: [(x * u, y * u) for x, y in pts]
    pm = max(cb + 1.2 * w, 0.03 * u)                                  # halbe Mastbreite
    # Sockel in Stufen
    f.add(Z.abrunden(s([(-0.2, 0), (0.2, 0), (0.2, 0.03), (-0.2, 0.03)]), 0.006 * u))
    f.add(Z.abrunden(s([(-0.15, 0.025), (0.15, 0.025), (0.15, 0.06), (-0.15, 0.06)]), 0.006 * u))
    f.add([(-0.11 * u, 0.055 * u), (0.11 * u, 0.055 * u), (pm * 1.5, 0.17 * u), (-pm * 1.5, 0.17 * u)])
    # Mast (leicht verjüngt) mit Ringen
    f.add([(-pm * 1.15, 0.16 * u), (pm * 1.15, 0.16 * u), (pm, 0.66 * u), (-pm, 0.66 * u)])
    for y, r in ((0.17, 1.9), (0.3, 1.6), (0.5, 1.5), (0.64, 1.8)):
        f.add(K.ellipse(0, y * u, pm * r, 0.012 * u, 0, 24))
    # Konsolen: geschwungene Arme mit Schnecke
    bw = max(1.5 * w, 0.014 * u)
    for sg in (1, -1):
        pfad = K.bez3((sg * pm * 0.8, 0.56 * u), (sg * 0.06 * u, 0.6 * u), (sg * 0.12 * u, 0.62 * u),
                      (sg * 0.125 * u, 0.67 * u), 16)
        f.line(pfad, bw * 1.3, bw)
        sp = Z.spirale(sg * 0.1 * u, 0.6 * u, 0.004 * u, 0.026 * u, 0.85, math.pi / 2 if sg > 0 else math.pi / 2,
                       -sg)
        f.line(list(reversed(sp)), bw, bw * 0.8)
        f.line([(sg * 0.1 * u, 0.626 * u), (sg * 0.124 * u, 0.64 * u)], bw)
        if deko in ("sterne", "beides"):                              # Stern an Kette unter der Konsole
            f.line([(sg * 0.128 * u, 0.665 * u), (sg * 0.128 * u, 0.6 * u)], max(1.3 * w, 0.007 * u))
            f.add(K.star(sg * 0.128 * u, 0.575 * u, 0.036 * u, 0.016 * u, 5))
    # Laternenkopf
    yb, yt = 0.66, 0.85                                               # Fensterbereich
    f.add(Z.abrunden(s([(-0.14, yb), (0.14, yb), (0.14, yb + 0.022), (-0.14, yb + 0.022)]), 0.005 * u))
    if kopf == "rund":
        body = s([(-0.105, yb + 0.02), (0.105, yb + 0.02), (0.11, yt), (-0.11, yt)])
        dach = K.chain(s([(0.14, yt - 0.005), (0.14, yt + 0.02)]),
                       K.arc(0, (yt + 0.02) * u, 0.12 * u, 0, math.pi, 32), s([(-0.14, yt + 0.02), (-0.14, yt - 0.005)]))
        knauf_y = yt + 0.15
    elif kopf == "spitz":
        body = s([(-0.085, yb + 0.02), (0.085, yb + 0.02), (0.11, yt), (-0.11, yt)])
        dach = s([(-0.15, yt - 0.005), (0.15, yt - 0.005), (0.15, yt + 0.012), (0.0, yt + 0.15), (-0.15, yt + 0.012)])
        knauf_y = yt + 0.16
    else:
        body = s([(-0.08, yb + 0.02), (0.08, yb + 0.02), (0.115, yt), (-0.115, yt)])
        dach = K.chain(s([(-0.15, yt - 0.005), (0.15, yt - 0.005), (0.15, yt + 0.015)]),
                       K.bez(((0.15 * u, (yt + 0.015) * u)), (0.06 * u, (yt + 0.03) * u), (0.03 * u, (yt + 0.11) * u), 12),
                       K.bez((-0.03 * u, (yt + 0.11) * u), (-0.06 * u, (yt + 0.03) * u), (-0.15 * u, (yt + 0.015) * u), 12),
                       )
        knauf_y = yt + 0.135
    f.add(body, dach)
    hk = max(0.022 * u, cb + 1.2 * w)                                 # Hals und Knauf: breit genug für den Schlitz
    rk = max(0.026 * u, cb + 1.6 * w)
    f.add(K.rect(-hk, (knauf_y - 0.04) * u, 2 * hk, 0.04 * u))
    f.add(K.circle(0, knauf_y * u, rk, 32))
    # Fenster links und rechts vom Mittelsteg, je zwei Scheiben
    fr = max(1.5 * w, 0.014 * u)
    loecher = []
    y0, y1 = (yb + 0.02) * u + fr, yt * u - fr
    xb = lambda y: (body[1][0] + (body[2][0] - body[1][0]) * (y - body[1][1]) / (body[2][1] - body[1][1])) - fr
    ym = (y0 + y1) / 2
    for sg in (1, -1):
        for ya, yz in ((y0, ym - fr / 2), (ym + fr / 2, y1)):
            if yz - ya < 2 * w:
                continue
            p = [(cb, ya), (xb(ya), ya), (xb(yz), yz), (cb, yz)]
            if xb(ya) - cb < 2 * w:
                continue
            loecher.append([(sg * x, y) for x, y in (p if sg > 0 else reversed(p))])
    f.cut(*loecher)
    # Schleife am Mast (nur Teil A)
    if a and deko in ("schleife", "beides"):
        ys = 0.48 * u
        for sg in (1, -1):
            f.add(K.ellipse(sg * 0.055 * u, ys + 0.012 * u, 0.055 * u, 0.025 * u, sg * 0.35, 28))
            f.line([(sg * 0.012 * u, ys - 0.005 * u), (sg * 0.05 * u, ys - 0.06 * u), (sg * 0.04 * u, ys - 0.1 * u)],
                   0.022 * u, 0.016 * u, "flach")
        f.add(K.ellipse(0, ys + 0.004 * u, 0.02 * u, 0.018 * u, 0, 16))
    return f, (yb + 0.02) * u, yt * u, body


def gravur(u, a: bool, deko: str, body):
    lin = []
    for y in (0.03, 0.06):                                            # Stufenkanten
        lin.append(([(-0.14 * u, y * u - 0.006 * u), (0.14 * u, y * u - 0.006 * u)], False))
    if a and deko in ("schleife", "beides"):
        ys = 0.48 * u
        for sg in (1, -1):
            lin.append((K.ellipse(sg * 0.055 * u, ys + 0.012 * u, 0.03 * u, 0.011 * u, sg * 0.35, 18), True))
    return lin


def build(cfg, name="strassenlaterne", hoehe=150.0, kopf="klassisch", deko="beides"):
    from models._shapes import cut_axis_slot
    T = cfg.T
    w = Z.wmin(cfg)
    u = cfg.s(hoehe)
    cb = T / 2 + cfg.min_web + cfg.kerf + 0.9
    if u < 22 * T:
        raise ValueError("Die Laterne ist für diese Materialstärke zu klein – höher machen oder dünneres Material")
    notes = []
    asm = Assembly(name, params=dict(hoehe=u, kopf=kopf, deko=deko))
    y_mid = 0.5 * u
    for tag, from_top, a in (("a", True, True), ("b", False, False)):
        fig, fy0, fy1, body = silhouette(u, kopf, deko, w, cb, a)
        p = Z.figur_teil(cfg, f"laterne_{tag}", fig, notes, unten_flach=True)
        out, slot = cut_axis_slot(p.outline, T, y_mid, from_top)
        ys = [q[1] for q in p.outline]
        span = (y_mid, max(ys)) if from_top else (min(ys), y_mid)
        q = Part(p.name, out, features=[JointFeature("kreuz", "halving", span[1] - span[0], T, span=span, points=slot)])
        for h in p.holes:
            q.add_hole(h)
        Z.gravur(q, gravur(u, a, deko, body), rand=0.6)
        asm.parts.append(q)
    asm.connect("laterne_a:kreuz", "laterne_b:kreuz")
    asm.notes.append("Teil B (Schlitz unten) von oben auf Teil A (Schlitz oben) schieben, bis beide unten bündig stehen.")
    asm.notes.append("Tipp: Hinter die Fenster Transparentpapier kleben und ein LED-Teelicht davor stellen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
