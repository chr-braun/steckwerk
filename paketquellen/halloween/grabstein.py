"""
Grabstein – schaurige Tischdeko mit graviertem Grabspruch.

Ein Grabstein (rund, gotisch, Kreuz oder schief abgebrochen) mit Zierrahmen, Grabspruch,
Ornament (Totenkopf, Fledermaus, Kreuz), Rissen und Efeuranke. Auf Wunsch schaut ein Gespenst
hinter dem Stein hervor. Steht in einem Erdhügel-Sockel.
"""
import importlib.util
import math
import os
import random
import sys

from steckwerk import Assembly, Part, oriented
from models import _deko as dk
from models._font import STYLES, fit_text, unsupported
from models._stand import stand_base, tab_feature_at
from pakete import bibliothek, flag, num, sel, txt


def _lib():
    return bibliothek("verzierungen").G


g = _lib()

FORMS = [("rund", "rund"), ("gotisch", "gotisch (Spitzbogen)"), ("kreuz", "Kreuz"), ("schief", "schief abgebrochen")]
ORNAMENTS = [("totenkopf", "Totenkopf"), ("fledermaus", "Fledermaus"), ("kreuz", "Kreuz"), ("keins", "keins")]

UEBERSETZUNG = {"en": g.EN}

INFO = dict(
    label="Grabstein",
    group="Halloween",
    desc="Grabstein mit Grabspruch, Ornament, Rissen und Efeu – auf Wunsch mit Gespenst dahinter.",
    params=[
        num("height", "Höhe", 140, 70, 280),
        sel("form", "Form", FORMS, "gotisch"),
        sel("ornament", "Ornament", ORNAMENTS, "totenkopf", when={"form": ["rund", "gotisch", "schief"]}),
        flag("geist", "Gespenst schaut hervor", True),
        flag("efeu", "Efeuranke", True),
        txt("text", "Grabspruch", "R.I.P.|Hier ruht|Graf Dracula|1431-1476", "| = neue Zeile",
            section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "normal", section="Schrift und Beschriftung"),
        txt("sockel_text", "Text auf dem Sockel", "", "leer = ohne", section="Schrift und Beschriftung"),
    ],
)


_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name):
    path = os.path.join(_here, name + ".py")
    key = "swpaket_halloween_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


SP = _sub("_spuk")
K = SP.K


def _stein(form, W, H, sockel):
    """Steinkontur über einem breiteren Sockelblock (Höhe sockel)."""
    if form == "kreuz":
        b = W * 0.30
        arm = H * 0.60
        f = SP.Figur()
        f.add(K.rect(-b / 2, 0.0, b, H - b * 0.4))
        f.add(K.rect(-W / 2 + b * 0.4, arm, W - b * 0.8, b))
        for x, y in ((0.0, H - b * 0.45), (-W / 2 + b * 0.45, arm + b / 2), (W / 2 - b * 0.45, arm + b / 2)):
            for k in range(3):                                        # Kleeblattenden
                a = math.atan2(y - (arm + b / 2), x) if (x or y != H - b * 0.45) else math.pi / 2
                a = math.pi / 2 if x == 0 else (0.0 if x > 0 else math.pi)
                aa = a + (k - 1) * math.radians(75)
                f.add(K.circle(x + math.cos(aa) * b * 0.32, y + math.sin(aa) * b * 0.32, b * 0.36, 32))
        f.add(K.rect(-b * 0.85, 0.0, b * 1.7, sockel * 1.6))
        return f
    f = SP.Figur()
    f.add([(x, y + sockel * 0.6) for x, y in g.tombstone(form, W, H - sockel * 0.6)])
    f.add(K.rect(-W * 0.56, 0.0, W * 1.12, sockel))
    return f


def build(cfg, name="grabstein", height=140.0, form="gotisch", ornament="totenkopf", geist=True, efeu=True,
          text="R.I.P.|Hier ruht|Graf Dracula|1431-1476", schrift="normal", sockel_text=""):
    T = cfg.T
    H = cfg.s(height)
    if not 70 <= H <= 280:
        raise ValueError("Grabstein: Höhe muss zwischen 70 und 280 mm liegen")
    dk.check_choice("Form", form, FORMS)
    dk.check_choice("Ornament", ornament, ORNAMENTS)
    for t_ in (text, sockel_text):
        bad = unsupported(t_ or "")
        if bad:
            raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    rng = random.Random(cfg.seed)
    w, sw = SP.wmin(cfg), SP.smin(cfg)
    notes = []
    W = 0.66 * H if form != "kreuz" else 0.62 * H
    sockel = 0.075 * H
    gr = []                                                     # Gravur (punkte, geschlossen)
    f = SP.Figur()
    # Gespenst hinter dem Stein (zuerst, der Stein deckt seinen Unterleib zu)
    if geist:
        gh = 0.42 * H
        gf, _ = SP.gespenst(gh, cfg, cfg.seed)
        ang = math.radians(-16)
        gx = 0.40 * W if form != "kreuz" else 0.36 * W
        gy = 0.93 * H if form not in ("schief", "kreuz") else 0.84 * H
        if form == "kreuz":                                       # Kreuz: links hinter dem Querbalken
            gx, ang = -gx, -ang
            gf = gf.place(0.0, 0.0, 1.0, flip=True)
            gf.gravur = []
        gfp = gf.place(gx, gy, 1.0, ang)
        f.merge(gfp)
        gr += [([SP.rot(q, ang) for q in pts], c) for pts, c in getattr(gf, "gravur", [])]
        gr = [([(x + gx, y + gy) for x, y in pts], c) for pts, c in gr]
    stein = _stein(form, W, H, sockel)
    f.merge(stein)
    # abgeplatzte Kanten: kleine Kerben im Umriss
    if form != "kreuz":
        for k in range(5):
            y = rng.uniform(0.20, 0.60) * H
            x = (W / 2) * (1 if k % 2 else -1)
            d = rng.uniform(0.012, 0.022) * H
            f.cut([(x + math.copysign(d * 0.4, x), y + d), (x - math.copysign(d, x), y + d * 0.2),
                   (x + math.copysign(d * 0.4, x), y - d * 0.8)])
    # Ornament oben
    top_text = 0.70 * H if form != "schief" else 0.60 * H
    orn_y = None if form == "kreuz" else (0.79 * H if form != "schief" else 0.66 * H)
    if orn_y and ornament != "keins":
        so = 0.17 * H
        if ornament == "totenkopf":
            sk = SP.totenkopf(so, cfg, risse=False).place(0.0, orn_y, 1.0)
            for sgn, poly in sk.ops:
                if sgn == "+":
                    gr.append((poly, True))
                else:
                    f.cut(poly)
            gr += [([(x, y + orn_y) for x, y in pts], c) for pts, c in SP.totenkopf(so, cfg).gravur]
            for sgn in (-1, 1):                                         # gekreuzte Knochen (graviert)
                a = math.radians(28) * sgn
                L = so * 0.62
                c0 = (0.0, orn_y - 0.40 * so)
                p0 = (c0[0] - L * math.cos(a), c0[1] - L * math.sin(a))
                p1 = (c0[0] + L * math.cos(a), c0[1] + L * math.sin(a))
                gr.append((K.stroke([p0, p1], so * 0.07, so * 0.07, "rund"), True))
                for e in (p0, p1):
                    for d in (-1, 1):
                        n_ = (-math.sin(a) * d * so * 0.05, math.cos(a) * d * so * 0.05)
                        gr.append((K.circle(e[0] + n_[0], e[1] + n_[1], so * 0.05, 16), True))
            top_text = orn_y - 0.62 * so
        elif ornament == "fledermaus":
            bat, _ = SP.fledermaus(so * 1.8, "segeln", cfg, augen=False)
            for sgn, poly in bat.place(0.0, orn_y, 1.0).ops:
                if sgn == "+":
                    f.cut(poly)
            top_text = orn_y - 0.40 * so
        elif ornament == "kreuz":
            c = 0.055 * H
            f.cut(K.stroke([(0.0, orn_y - 1.1 * c), (0.0, orn_y + 1.0 * c)], c * 0.42, c * 0.42, "flach"))
            f.cut(K.stroke([(-0.65 * c, orn_y + 0.3 * c), (0.65 * c, orn_y + 0.3 * c)], c * 0.42, c * 0.42, "flach"))
            for x, y in ((0.0, orn_y + 1.0 * c), (-0.65 * c, orn_y + 0.3 * c), (0.65 * c, orn_y + 0.3 * c)):
                f.cut(K.circle(x, y, c * 0.30, 24))
            top_text = orn_y - 1.4 * c
    # Risse: feine durchgehende Schlitze, die im Stein enden
    if form != "kreuz" and 0.25 * H > 6 * w:
        for k in range(2):
            sgn_ = 1 if k else -1
            px = rng.uniform(0.36, 0.40) * W * sgn_
            py = rng.uniform(0.40, 0.55) * H
            pts = [(px, py)]
            for _ in range(5):
                px += rng.uniform(-0.015, 0.025) * W * -sgn_
                py -= rng.uniform(0.025, 0.04) * H
                pts.append((px, py))
            f.cut(K.stroke(pts, sw, sw * 0.5, "spitz"))
            gr.append(([pts[0], (pts[0][0] + rng.uniform(-0.04, 0.04) * W, pts[0][1] + 0.05 * H)], False))
    # Efeu wächst links am Stein hoch und über die Kante
    if efeu:
        xl = -W / 2 + 0.03 * W if form != "kreuz" else -W * 0.15 + 0.02 * W
        hoch = 0.74 * H if form != "kreuz" else 0.52 * H
        pfad = K.spline([(xl, sockel * 0.5), (xl + 0.02 * W, 0.22 * H), (xl - 0.01 * W, 0.42 * H),
                         (xl + 0.03 * W, 0.60 * H), (xl + 0.08 * W, hoch)], n=10)
        if form == "kreuz":                                       # beim Kreuz rechts, das Gespenst ist links
            pfad = [(-x, y) for x, y in pfad]
        gr += SP.efeuranke(f, pfad, 0.11 * H, cfg, cfg.seed, seite=1 if form == "kreuz" else -1)
    # Grasbüschel an den Sockelecken
    for side in (-1, 1):
        x0 = side * W * 0.56
        for k in range(5):
            bx = x0 - side * k * 0.022 * W
            hgt = (0.05 + 0.03 * rng.random()) * H
            tip = (bx + side * rng.uniform(0.0, 0.03) * W, hgt)
            f.add(K.stroke([(bx, 0.0), ((bx + tip[0]) / 2 + side * 0.01 * W, hgt * 0.5), tip],
                           max(w * 1.1, 0.02 * H), w * 0.9, "spitz"))
    f.cut(K.rect(-H, -H, 2 * H, H))                             # flache Unterkante
    part = SP.teil(f"{name}_stein", f, cfg, notes, unten_flach=True)
    tw = max(0.4 * W, 4 * T) if form != "kreuz" else max(0.25 * W, 4 * T)
    outline = g.op2(part.outline, [(-tw / 2, -T), (tw / 2, -T), (tw / 2, 0.6), (-tw / 2, 0.6)], "union")
    holes = part.holes
    part = Part(f"{name}_stein", oriented(g.dedupe(outline, 0.05), True),
                features=[tab_feature_at("fuss", -tw / 2, 0.0, tw, T)])
    for h in holes:
        part.add_hole(h)
    cv = dk.Canvas(part, margin=1.0, hole_margin=1.0, seed=cfg.seed)
    # Grabspruch zuerst (bekommt Vorrang vor Rahmen und Rissen)
    if text.strip():
        if form == "kreuz":
            lines = text.replace("|", " ").split()
            text_ = " ".join(lines[:1]) if lines else ""
            b = W * 0.30
            try:
                strokes, _ = fit_text(text_, 0.0, 0.60 * H + b * 0.55, W - b * 1.2, b * 0.42, min_h=2.0, max_cap=0.1 * W,
                                      style=schrift)
            except ValueError:
                strokes = []
        else:
            y_lo = sockel + 0.08 * H
            try:
                strokes, _ = fit_text(text, 0.0, (y_lo + top_text) / 2, W * 0.66, top_text - y_lo, min_h=2.2,
                                      max_cap=0.075 * H, style=schrift)
            except ValueError:
                strokes = []
                notes.append("Grabspruch passt nicht – kürzer oder Stein größer wählen.")
        for st in strokes:
            cv.draw(st)
        cv.block_strokes([(st, False) for st in strokes], 0.8)
    # Zierrahmen (doppelt), Sockelfuge, Steinstruktur
    if form != "kreuz":
        for k, (fw, fh, dy) in enumerate(((0.86, 0.88, 0.035), (0.80, 0.83, 0.055))):
            inner = g.tombstone(form, W * fw, (H - sockel * 0.6) * fh)
            cv.draw([(x, y + sockel * 0.6 + dy * H) for x, y in inner], True)
        cv.draw([(-W * 0.54, sockel * 0.62), (W * 0.54, sockel * 0.62)])
        for k in range(7):                                           # Fugen im Sockel
            x = -W * 0.5 + W * (k + 0.5) / 7
            cv.draw([(x, sockel * 0.1), (x, sockel * 0.55)])
    for k in range(14):                                              # Moos in den unteren Ecken (Tüpfel)
        side = 1 if k % 2 else -1
        x = side * rng.uniform(0.26, 0.42) * (W if form != "kreuz" else 0.3 * W)
        y = sockel + rng.uniform(0.02, 0.12) * H
        cv.put(K.circle(x, y, rng.uniform(0.35, 0.7), 10), True)
    for pts, c in gr:
        cv.draw(pts, c)

    asm = Assembly(name, params=dict(height=H, form=form, ornament=ornament, geist=geist))
    asm.parts.append(part)
    stand_base(asm, part, "fuss", tw, cfg, max(0.62 * W, tw / 2 + 12), 0.22 * W, f"{name}_huegel",
               sockel_text or "", schrift, "gross")
    asm.notes.extend(dict.fromkeys(notes))
    asm.notes.append(f"{name}: Stein in den Erdhügel stecken. Tipp: Stein mit grauer Lasur, Gravur dunkel "
                     "auslegen – dann wirkt er wie verwittert.")
    return asm
