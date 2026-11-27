"""
Leuchtende Schattenbox – geschlossener Holzkasten mit Zinken, darin 3 bis 6 Szenen-Ebenen hintereinander.

Aufbau (3D: x = Breite, y = Tiefe von vorn nach hinten, z = Höhe)
  vorne          Frontrahmen mit Bildfenster (Rundbogen, Spitzbogen, Rechteck …), feine Gravur
  links/rechts   Seitenwände mit Zinken und graviertem Kassettenrahmen
  hinten         Rückwand, Kabelloch unten mittig für eine Lichterkette
  boden          Bodenplatte: Wände stecken mit Tabs darin, dazu je Ebene eine Schlitzreihe
  deckel         abnehmbar, liegt auf den Wand-Tabs
  ebene1 …       Szenen-Ebenen (vorne → hinten), stehen nur mit zwei Zapfen im Boden
  himmel         Hintergrund: Mond und Sterne als Durchbrüche oder Rahmen für Transparentpapier
  …_b            Wechselsatz: zweite Szene mit genau denselben Zapfen, passt in dieselben Schlitze

Hinter dem Hintergrund liegt die Lichtkammer für ein LED-Teelicht (≥ 45 mm tief) oder eine
LED-Lichterkette (≥ 15 mm). Die Szene wechselt man ohne Werkzeug: Deckel ab, Ebenen nach oben heraus.
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from steckwerk import JointFeature, Part, oriented, point_in_polygon, rect, signed_area, slot_feature
from models import _deko as dk
from models._box import build_box
from models._font import STYLES, unsupported
import motive as mt
from pakete import bibliothek, flag, integer, num, sel, txt

Z = bibliothek("verzierungen")
E = Z.E
K = Z.K
S = bibliothek("ebenen", "_szenen")                     # Szenen aus dem Paket Mehrlagig

SZENEN = [("winterwald", "Hirsch im Winterwald"), ("winterdorf", "Winterdorf mit Kirche"),
          ("spukschloss", "Spukschloss mit Hexe"),
          ("weihnachtsnacht", "Weihnachtsnacht mit Rentierschlitten")]
FORMEN = [f for f in E.FORMEN if f[0] != "oval"]
LICHT = [("teelicht", "LED-Teelicht"), ("lichterkette", "LED-Lichterkette")]
HINTERGRUND = [("sterne", "Mond und Sterne leuchten"),
               ("papier", "Rahmen für Transparentpapier")]
ECKEN = [("ranke", "Ranke"), ("blatt", "Blätterzweig"), ("schnoerkel", "Schnörkel"), ("keine", "keine")]

LICHTKAMMER = {"teelicht": 46.0, "lichterkette": 18.0}      # Tiefe hinter dem Hintergrund (mm)
TEELICHT_D = 38.0                                           # übliches LED-Teelicht
KABELLOCH_D = 8.0
SPIEL = 0.5                                                 # Luft der Ebenen zu den Seitenwänden je Seite
LUFT_OBEN = 2.5                                             # Luft der Ebenen unter dem Deckel
ORNAMENT_MIN = 16.0                                         # kleinere Eckornamente werden zu fein
UEBERSTAND = 3.0                                            # Szene reicht so weit hinter den Frontrahmen

INFO = dict(
    label="Leuchtende Schattenbox",
    group="Schattenbox",
    desc="Holzkasten mit Zinken und Bildfenster: 3–6 Szenen-Ebenen stehen hintereinander, dahinter leuchtet "
         "ein LED-Teelicht oder eine Lichterkette. Mit Wechselsatz tauschst du die Szene ohne Werkzeug. "
         "Nur LED – keine echte Kerze.",
    params=[
        num("width", "Breite", 200, 140, 360),
        num("height", "Höhe", 240, 140, 360),
        sel("form", "Fensterform", FORMEN, "bogen"),
        sel("szene", "Szene", SZENEN, "winterwald"),
        integer("ebenen", "Ebenen", 4, 3, 6, help="Szenen-Ebenen ohne Hintergrund"),
        num("abstand", "Abstand der Ebenen", 10, 5, 30),
        sel("licht", "Licht", LICHT, "teelicht"),
        sel("hintergrund", "Hintergrund", HINTERGRUND, "sterne"),
        flag("wechselsatz", "Wechselsatz mit zweiter Szene", False),
        sel("szene2", "Zweite Szene", SZENEN, "weihnachtsnacht", when={"wechselsatz": [True]}),
        num("rand", "Rahmenbreite", 16, 12, 40),
        sel("ecken", "Eckornament", ECKEN, "ranke"),
        txt("text", "Text unten auf dem Rahmen", "", "leer = ohne", section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "normal", section="Schrift und Beschriftung"),
        sel("schreibweise", "Schreibweise", dk.FONT_CASES, "gross", section="Schrift und Beschriftung"),
    ],
)

UEBERSETZUNG = {"en": {
    "Schattenbox": "Shadow box",
    "Leuchtende Schattenbox": "Illuminated shadow box",
    "Holzkasten mit Zinken und Bildfenster: 3–6 Szenen-Ebenen stehen hintereinander, dahinter leuchtet ein "
    "LED-Teelicht oder eine Lichterkette. Mit Wechselsatz tauschst du die Szene ohne Werkzeug. Nur LED – keine "
    "echte Kerze.":
        "Finger-jointed wooden box with a picture window: 3–6 scene layers stand one behind the other, lit from "
        "behind by an LED tea light or a fairy light string. With the swap set you change the scene without "
        "tools. LED only – never a real candle.",
    "Breite": "Width", "Höhe": "Height", "Fensterform": "Window shape", "Szene": "Scene", "Ebenen": "Layers",
    "Szenen-Ebenen ohne Hintergrund": "scene layers, not counting the background",
    "Abstand der Ebenen": "Layer spacing", "Licht": "Light", "Hintergrund": "Background",
    "Wechselsatz mit zweiter Szene": "Swap set with a second scene", "Zweite Szene": "Second scene",
    "Rahmenbreite": "Frame width", "Eckornament": "Corner ornament",
    "Text unten auf dem Rahmen": "Text at the bottom of the frame", "leer = ohne": "empty = none",
    "Schrift und Beschriftung": "Font and lettering", "Schrift": "Font", "Schreibweise": "Letter case",
    "Hirsch im Winterwald": "Stag in the winter forest", "Winterdorf mit Kirche": "Winter village with church",
    "Spukschloss mit Hexe": "Haunted castle with witch",
    "Weihnachtsnacht mit Rentierschlitten": "Christmas night with reindeer sleigh",
    "LED-Teelicht": "LED tea light", "LED-Lichterkette": "LED fairy lights",
    "Mond und Sterne leuchten": "Glowing moon and stars", "Rahmen für Transparentpapier": "Frame for tracing paper",
    "Ranke": "Scroll", "Blätterzweig": "Leafy sprig", "Schnörkel": "Flourish", "keine": "none",
    "Rundbogen": "Round arch", "Rechteck": "Rectangle", "Rechteck, abgerundet": "Rectangle, rounded",
    "Spitzbogen (gotisch)": "Pointed arch (gothic)",
    # Hinweise
    "Seitenwände zwischen Front und Rückwand stecken, alles in den Boden drücken. Dann den Hintergrund in die "
    "hinterste Schlitzreihe stellen und die Ebenen von hinten nach vorn einsetzen – Ebene 1 steht direkt hinter "
    "dem Fenster. Zum Schluss den Deckel aufsetzen.":
        "Fit the side walls between front and back and press everything into the base. Then stand the background "
        "in the rearmost slot row and insert the layers from back to front – layer 1 sits right behind the window. "
        "Finally put the lid on.",
    "Nicht verleimen: die Ebenen stehen nur mit ihren Zapfen im Boden, so bleibt die Szene wechselbar.":
        "Do not glue: the layers stand in the base by their pegs only, so the scene stays swappable.",
    "LED-Teelicht auf die gravierte Markierung hinter dem Hintergrund stellen. Nur LED – keine echte Kerze im "
    "Holzkasten!":
        "Place the LED tea light on the engraved mark behind the background. LED only – never a real candle in a "
        "wooden box!",
    "LED-Lichterkette in die Lichtkammer hinter dem Hintergrund legen, das Kabel durch das Loch in der Rückwand "
    "führen. Nur LED – keine echte Kerze!":
        "Lay the LED fairy lights in the light chamber behind the background and lead the cable through the hole "
        "in the back panel. LED only – never a real candle!",
    "Transparentpapier (Butterbrotpapier geht auch) hinten auf den Hintergrundrahmen kleben – dann leuchtet der "
    "ganze Himmel weich und die Ebenen stehen als Scherenschnitt davor.":
        "Glue tracing paper (baking paper works too) to the back of the background frame – the whole sky then glows "
        "softly and the layers stand in front of it like a paper cut.",
    "Szene wechseln: Deckel abnehmen, Ebenen nach oben herausziehen, den anderen Satz einstecken.":
        "Changing the scene: lift off the lid, pull the layers out upwards, insert the other set.",
    "Der Wechselsatz hat genau dieselben Zapfen wie der erste Satz und passt in dieselben Schlitze.":
        "The swap set has exactly the same pegs as the first set and fits the same slots.",
    "Tipp: Ebenen unterschiedlich hell lasieren – vorn dunkel, hinten hell – dann wirkt die Szene noch tiefer.":
        "Tip: stain the layers in different shades – dark at the front, light at the back – for even more depth.",
    "Der Kasten ist für diese Rahmenbreite zu klein – größer machen oder schmaleren Rahmen wählen":
        "The box is too small for this frame width – make it larger or choose a narrower frame",
}}


def _notiz(name: str, text: str) -> str:
    return f"{name}: {text}"


def _check(form, szene, szene2, licht, hintergrund, ecken, ebenen, text, schrift):
    dk.check_choice("Fensterform", form, FORMEN)
    dk.check_choice("Szene", szene, SZENEN)
    dk.check_choice("Zweite Szene", szene2, SZENEN)
    dk.check_choice("Licht", licht, LICHT)
    dk.check_choice("Hintergrund", hintergrund, HINTERGRUND)
    dk.check_choice("Eckornament", ecken, ECKEN)
    if not 3 <= int(ebenen) <= 6:
        raise ValueError("Ebenen: 3 bis 6")
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    if schrift not in STYLES:
        raise ValueError(f"Schrift {schrift!r} unbekannt")


# --------------------------------------------------------------------------------------------------
# Gravur-Helfer
# --------------------------------------------------------------------------------------------------

def _umriss(fig, px: float = 0.06) -> List[List[Tuple[float, float]]]:
    """Figur → saubere Umrisslinien (überlappende Teilflächen verschmolzen) für die Gravur."""
    xs, ys = [], []
    for s, poly in fig.ops:
        if s == "+":
            xs += [p[0] for p in poly]
            ys += [p[1] for p in poly]
    if not xs:
        return []
    lw = E.Leinwand((min(xs), min(ys), max(xs), max(ys)), px=px)
    out = []
    for a in lw.konturen(lw.figur(fig), tol=0.2):
        out.append(a["aussen"])
        out += a["loecher"]
    return out


def _bogen_weg(poly: Sequence[Tuple[float, float]], d: float) -> List[Tuple[float, float]]:
    return dk.grow(oriented(list(poly), True), d)


def _front_gravur(part: Part, cfg, W: float, H: float, fenster, form: str, rand: float, unten: float,
                  ecken: str, text: str, schrift: str, schreibweise: str) -> None:
    """Frontrahmen: Doppellinie am Fenster, Perlenreihe, Kassettenrand, Eckornamente, Text."""
    T = cfg.T
    cv = dk.Canvas(part, margin=1.2, hole_margin=0.9, seed=cfg.seed)
    # Kassettenrand: doppelte Linie innerhalb der Zinken und Tabs
    b = 2 * T + 1.8
    x0, y0, x1, y1 = b, b, W - b, H - b
    cv.draw(rect(x0, y0, x1 - x0, y1 - y0), True)
    cv.draw(rect(x0 + 1.1, y0 + 1.1, x1 - x0 - 2.2, y1 - y0 - 2.2), True)
    # Fensterkante: zwei feine Linien dicht am Fenster, dahinter eine Perlenreihe
    for d in (1.5, 2.6):
        cv.draw(_bogen_weg(fenster, d), True)
    luft = rand - (2.6 + b + 1.1)
    if luft >= 4.0:
        perl = _bogen_weg(fenster, 2.6 + 0.5 * luft)
        dk.styled_line(cv, perl + [perl[0]], "punkte", min(2.8, 0.7 * luft), side=0, seed=cfg.seed)
    # Eckornamente in den Zwickeln über dem Bogen (bzw. in den Rahmenecken)
    if ecken != "keine":
        sperr = _bogen_weg(fenster, (2.6 + 0.5 * luft + 1.9) if luft >= 4.0 else 3.6)
        ref = 40.0
        einheit = [[(x / ref, y / ref) for x, y in pts] for pts in _umriss(Z.O.ecke(ref, ecken, ref * 0.045))]
        cv2 = dk.Canvas(Part(part.name, part.outline), margin=1.2, seed=cfg.seed)
        cv2.part = part                                       # zeichnet ins echte Teil, Fenster über sperr
        cv2.block(sperr, 0.0)
        ix0, ix1, iy0, iy1 = x0 + 3.2, x1 - 3.2, y0 + 3.2, y1 - 3.2
        gmax = 0.42 * min(x1 - x0, y1 - y0)
        for (cx, sx), (cy, sy) in (((ix0, 1), (iy1, -1)), ((ix0, 1), (iy0, 1))):
            def setzen(g):
                return [[(cx + sx * x * g, cy + sy * y * g) for x, y in pts] for pts in einheit]

            def frei(g):
                return not any(point_in_polygon(q, sperr) for pts in setzen(g) for q in pts)
            lo, hi = 0.0, gmax
            if frei(hi):
                lo = hi
            else:
                for _ in range(14):
                    mid = 0.5 * (lo + hi)
                    lo, hi = (mid, hi) if frei(mid) else (lo, mid)
            g = 0.94 * lo
            if g < ORNAMENT_MIN:
                continue
            for pts in setzen(g):
                cv2.draw(pts, True)
                cv2.draw([(W - x, y) for x, y in pts], True)        # gespiegelt auf die rechte Seite
    if text.strip():
        band = Part(part.name, part.outline)
        band.add_hole(fenster)
        cvt = dk.Canvas(band, margin=1.5, seed=cfg.seed)
        y_lo = y0 + 1.1 + 1.4
        y_hi = unten - ((2.6 + 0.5 * luft + 1.7) if luft >= 4.0 else 3.8)
        bx = 0.5 * (W - 2 * rand) - 2.0
        box = (W / 2 - bx, y_lo, W / 2 + bx, y_hi)
        if dk.sign(cvt, text, "ohne", [box], schrift, schreibweise, min_h=3.0, max_cap=0.7 * (y_hi - y_lo),
                   anchor="mitte", tol=cfg.arc_tolerance) is None:
            raise ValueError(f"Text {text!r} passt nicht auf den Rahmen – kürzer fassen oder breiteren Rahmen wählen")
        part.engrave += band.engrave


def _kassette(part: Part, cfg, w: float, h: float, inset: float) -> None:
    cv = dk.Canvas(part, margin=1.2, seed=cfg.seed)
    for d in (inset, inset + 1.1):
        if w - 2 * d > 10 and h - 2 * d > 10:
            cv.draw(rect(d, d, w - 2 * d, h - 2 * d), True)


# --------------------------------------------------------------------------------------------------
# Modell
# --------------------------------------------------------------------------------------------------

def build(cfg, name="schattenbox", width=200.0, height=240.0, form="bogen", szene="winterwald", ebenen=4,
          abstand=10.0, licht="teelicht", hintergrund="sterne", wechselsatz=False, szene2="weihnachtsnacht",
          rand=16.0, ecken="ranke", text="", schrift="normal", schreibweise="gross"):
    _check(form, szene, szene2, licht, hintergrund, ecken, ebenen, text, schrift)
    T = cfg.T
    W, H = cfg.s(width), cfg.s(height)
    n = int(ebenen)
    abstand = max(float(abstand), cfg.min_web + 2.0)
    rand = max(float(rand), 2 * T + cfg.min_web + 5.0)
    wechselsatz = bool(wechselsatz) and szene2 != szene
    tw = max(cfg.tab_factor * T, 8.0)

    # Fenster: bei Text wächst das untere Rahmenband, das Fenster rückt nach oben
    unten = rand
    if text.strip():
        luft = rand - (2.6 + 2 * T + 1.8 + 1.1)                  # wie in _front_gravur
        ueber = (2.6 + 0.5 * luft + 1.7) if luft >= 4.0 else 3.8
        unten = max(rand, 2 * T + 1.8 + 1.1 + 1.4 + max(7.0, 0.45 * rand) + ueber)
    extra = unten - rand
    flach = 0.6 * W

    def fenster(inset: float):
        return [(x + W / 2, y + extra) for x, y in E.innen(form, W, H - extra, inset, flach)]

    win = fenster(rand)
    Wi, Hi = W - 2 * rand, H - extra - 2 * rand
    if Wi < 90 or Hi < 90:
        raise ValueError("Der Kasten ist für diese Rahmenbreite zu klein – größer machen oder schmaleren Rahmen wählen")

    # Ebenen-Geometrie (lokal: x = 0 … Wl, y = 0 Bodenoberkante)
    Wl = W - 2 * T - 2 * SPIEL
    Hl = H - LUFT_OBEN
    ov = min(UEBERSTAND, rand - T - SPIEL - max(3.0, cfg.min_web + 1.0))
    bereich_poly = fenster(rand - ov)                         # sichtbarer Szenenbereich (+ Überstand)
    Wa, Ha = W - 2 * (rand - ov), H - extra - 2 * (rand - ov)
    xs = [W / 2 - 0.30 * Wl, W / 2 + 0.30 * Wl]               # Zapfen-Mitten in Kasten-x
    outer_l = oriented(rect(T + SPIEL, 0, Wl, Hl), True)

    # Tiefe: Front | Luft | Ebenen + Hintergrund | Lichtkammer | Rückwand
    n_pl = n + 1
    vorn = max(abstand, 2 * T + 1.0)
    kammer = LICHTKAMMER[licht]
    reihen = [T + vorn + k * (T + abstand) + T / 2 for k in range(n_pl)]       # Mitten der Ebenen (3D-y)
    D = reihen[-1] + T / 2 + kammer + T

    asm, info = build_box(name, W, D, H, cfg, top="slots")
    asm.params.update(width=W, height=H, depth=D, form=form, szene=szene, ebenen=n, abstand=abstand, licht=licht,
                      hintergrund=hintergrund, wechselsatz=wechselsatz, szene2=szene2 if wechselsatz else "",
                      rand=rand, text=text)
    vo, hi_ = asm.part(info.name("vorne")), asm.part(info.name("hinten"))
    li, re_ = asm.part(info.name("links")), asm.part(info.name("rechts"))
    boden, deckel = asm.part(info.name("boden")), asm.part(info.name("deckel"))
    m = info.base_margin
    notes: List[str] = []

    # --- Szenen-Ebenen ---------------------------------------------------------------------------
    lw = E.Leinwand((0, 0, W, H), px=0.1 if max(W, H) <= 260 else 0.14)
    bereich = lw.flaechen([bereich_poly])

    sicht = _bogen_weg(win, 0.4)

    def sichtbar(holes):
        """Durchbrüche, die ganz hinter dem Frontrahmen liegen, und Krümel unter 4 mm² weglassen."""
        return [h for h in holes if abs(signed_area(h)) >= 4.0 and any(point_in_polygon(q, sicht) for q in h)]

    def platte(pname: str, holes, mit_features: bool) -> Part:
        out, tabs = E.zapfen_einsetzen(outer_l, xs, tw, T)
        part = Part(pname, out)
        for h in holes:
            part.add_hole(h)
        if mit_features:
            for k, (_seite, _x, pts) in enumerate(tabs):
                part.features.append(JointFeature(f"z{k}", "tab", tw, T, pos=0.0, points=pts))
        return part

    def satz(sz: str, suffix: str, mit_features: bool) -> List[Part]:
        szene_fn, himmel_fn = S.SZENEN[sz]
        figs = szene_fn(Wa, Ha, n, cfg.seed)                  # hinten → vorne
        plates: List[Part] = []
        for d, fig in enumerate(figs):
            mat = lw.figur(fig.place(W / 2, extra + rand - ov, 1.0))
            label = f"{name}_ebene{n - d}{suffix}"
            holes = E.durchbrueche(lw, bereich, mat, cfg.min_web, cfg.kerf, notes, label)
            plates.insert(0, platte(label, sichtbar(holes), mit_features))
        label = f"{name}_himmel{suffix}"
        if hintergrund == "sterne":
            loch, keep = himmel_fn(Wa, Ha, cfg.seed)
            lr = lw.figur(loch.place(W / 2, extra + rand - ov, 1.0))
            mat = lw.figur(keep.place(W / 2, extra + rand - ov, 1.0))
            holes = E.durchbrueche(lw, E._and(lr, bereich), mat, cfg.min_web, cfg.kerf, notes, label)
            plates.append(platte(label, sichtbar(holes), mit_features))
        elif mit_features:                                    # Papierrahmen: für beide Sätze gleich
            plates.append(platte(label, [bereich_poly], True))
        return plates

    plates = satz(szene, "", True)                            # vorne → hinten, letzte = Hintergrund
    asm.parts += plates
    for k, p in enumerate(plates):
        for j, f in enumerate(p.features):
            f.pos = k * 100.0 + j
            x3 = xs[j]
            feat, hole = slot_feature(f"e{k}_{j}", m + x3 - tw / 2, m + reihen[k] - T / 2, tw, T, True, f.pos)
            boden.holes.append(hole)
            boden.features.append(feat)
            asm.connect(f"{p.name}:{f.id}", f"{boden.name}:{feat.id}")
    if wechselsatz:
        asm.parts += satz(szene2, "_b", False)

    # --- Gravur und Löcher am Kasten ---------------------------------------------------------------
    vo.add_hole(oriented(win, True))
    _front_gravur(vo, cfg, W, H, win, form, rand, unten, ecken, text, schrift, schreibweise)
    hy = 2 * T + cfg.min_web + KABELLOCH_D / 2 + 1.0
    hi_.add_hole(K.circle(W / 2, hy, KABELLOCH_D / 2, 48))
    for wand in (li, re_):
        _kassette(wand, cfg, D - 2 * T, H, 2 * T + 1.8)
    _kassette(deckel, cfg, *deckel.bbox()[2:], info.lid_margin + T + 2.5)
    if licht == "teelicht":
        cy = m + reihen[-1] + T / 2 + kammer / 2
        cv = dk.Canvas(boden, margin=1.0, seed=cfg.seed)
        for r in (TEELICHT_D / 2 + 1.0, TEELICHT_D / 2 + 2.2):
            cv.draw(K.circle(m + W / 2, cy, r, 96), True)

    # --- Hinweise ---------------------------------------------------------------------------------
    asm.notes[:] = [nt for nt in asm.notes if not nt.startswith(f"{name}: Seitenwände zwischen")]
    asm.notes.append(_notiz(name, "Seitenwände zwischen Front und Rückwand stecken, alles in den Boden drücken. "
                                  "Dann den Hintergrund in die hinterste Schlitzreihe stellen und die Ebenen von "
                                  "hinten nach vorn einsetzen – Ebene 1 steht direkt hinter dem Fenster. Zum Schluss "
                                  "den Deckel aufsetzen."))
    asm.notes.append(_notiz(name, "Nicht verleimen: die Ebenen stehen nur mit ihren Zapfen im Boden, so bleibt die "
                                  "Szene wechselbar."))
    if licht == "teelicht":
        asm.notes.append(_notiz(name, "LED-Teelicht auf die gravierte Markierung hinter dem Hintergrund stellen. "
                                      "Nur LED – keine echte Kerze im Holzkasten!"))
    else:
        asm.notes.append(_notiz(name, "LED-Lichterkette in die Lichtkammer hinter dem Hintergrund legen, das Kabel "
                                      "durch das Loch in der Rückwand führen. Nur LED – keine echte Kerze!"))
    if hintergrund == "papier":
        asm.notes.append(_notiz(name, "Transparentpapier (Butterbrotpapier geht auch) hinten auf den "
                                      "Hintergrundrahmen kleben – dann leuchtet der ganze Himmel weich und die "
                                      "Ebenen stehen als Scherenschnitt davor."))
    asm.notes.append(_notiz(name, "Szene wechseln: Deckel abnehmen, Ebenen nach oben herausziehen, den anderen "
                                  "Satz einstecken."))
    if wechselsatz:
        asm.notes.append(_notiz(name, "Der Wechselsatz hat genau dieselben Zapfen wie der erste Satz und passt in "
                                      "dieselben Schlitze."))
    asm.notes.append(_notiz(name, "Tipp: Ebenen unterschiedlich hell lasieren – vorn dunkel, hinten hell – dann "
                                  "wirkt die Szene noch tiefer."))
    asm.notes += notes
    return asm


# --------------------------------------------------------------------------------------------------
# Fertige Vorlagen (eigene Galerie-Einträge mit anderen Startwerten)
# --------------------------------------------------------------------------------------------------

PARAM_KEYS = tuple(p["key"] for p in INFO["params"])


def vorlage_info(label: str, desc: str, vorgaben: dict) -> dict:
    """INFO einer fertigen Vorlage: gleiche Einstellungen, andere Startwerte."""
    params = []
    for p in INFO["params"]:
        q = dict(p)
        if p["key"] in vorgaben:
            q["default"] = vorgaben[p["key"]]
        params.append(q)
    return dict(label=label, group=INFO["group"], desc=desc, params=params)


# --------------------------------------------------------------------------------------------------
# Galerie-Vorschau: die fertige Szene durch das Fenster gesehen, statt nur der leeren Front
# --------------------------------------------------------------------------------------------------

def vorschau(cfg, **params) -> List[Tuple[List[Tuple[float, float]], bool, str]]:
    """Linien für das Vorschaubild der Galerie: Front mit Gravur und die Szene, wie man sie durch das Fenster
    sieht (alle Ebenen übereinandergelegt, verdeckte Kanten weggelassen). Liefert [(Punkte, geschlossen, art)]
    mit art = "schnitt" oder "gravur", y nach unten wie im SVG."""
    asm = build(cfg, **params)
    name = asm.name
    W, H = asm.params["width"], asm.params["height"]
    vo = asm.part(f"{name}_vorne")
    lw = E.Leinwand((0, 0, W, H), px=0.25)
    fenster = lw.flaechen(vo.holes)
    ebenen = sorted((p for p in asm.parts if p.name.startswith(f"{name}_ebene") and not p.name.endswith("_b")),
                    key=lambda p: int(p.name.rsplit("ebene", 1)[1]))
    ebenen.append(asm.part(f"{name}_himmel"))
    linien: List[Tuple[List[Tuple[float, float]], bool, str]] = []

    def flip(pts):
        return [(x, H - y) for x, y in pts]

    linien.append((flip(vo.outline), True, "schnitt"))
    linien += [(flip(h), True, "schnitt") for h in vo.holes]
    linien += [(flip(s.points), s.closed, "gravur") for s in vo.engrave]
    davor = lw.leer()
    for p in ebenen:                                          # vorne → hinten
        mat = E._andnot(lw.flaechen([p.outline]), lw.flaechen(p.holes) if p.holes else lw.leer())
        sichtbar = E._andnot(E._and(mat, fenster), davor)
        for lp in sichtbar.trace():                           # ohne Eckenglättung: keine abgeschnittenen Ecken
            if abs(mt.area(lp)) < 6.0:
                continue
            q = mt.simplify(lp, 0.6)
            if len(q) >= 3:
                linien.append(([(lw.x0 + x * lw.px, y * lw.px + (H - lw.y_top)) for x, y in q], True, "schnitt"))
        davor = davor.union(mat)
    return linien
