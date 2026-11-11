"""
Puzzle – Bilderpuzzle zum Lasern: Teile mit Nasen (oder gerade für Kleinkinder), rechteckig oder rund,
auf Wunsch mit Rahmen und Boden. Das Bild läuft über alle Teile hinweg und wird an jedem Teil sauber
vom Schnittrand freigehalten.

Bild: eingebaute Szenen (Winterdorf, Christbaum, Mandala, Sternenhimmel, Waldtiere) oder ein eigenes Motiv
aus der Motiv-Bibliothek (SVG/PNG-Import, z. B. ein Logo), als Umriss oder flächig graviert, auf Wunsch mit
Hintergrundmuster. Andere Pakete können über `puzzle_aus_bild` ein beliebiges Gravurbild zum Puzzle machen.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Sequence, Tuple

from steckwerk import Assembly, Part, circle, oriented, rect
from pakete import integer, motiv, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_spiele_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


S = _sub("_spiel")
P = _sub("_puzzle")
B = _sub("_bilder")

FORMEN = [("rechteck", "rechteckig"), ("rund", "rund")]
BILDWAHL = B.BILDER + [("eigenes", "eigenes Motiv oder Logo"), ("foto", "Foto (über „Eigene Gravur“)"),
                       ("ohne", "ohne Bild (nur Muster)")]
MOTIV_ART = [("flaeche", "flächig gravieren"), ("umriss", "nur Umriss gravieren")]
RAHMEN = [("keiner", "ohne Rahmen"), ("rahmen", "Rahmen mit Boden (Legepuzzle)")]

INFO = dict(
    label="Puzzle",
    group="Spiele",
    desc="Bilderpuzzle mit Nasen, rechteckig oder rund, auf Wunsch mit Rahmen zum Hineinlegen. Das Bild läuft "
         "über alle Teile: Winterdorf, Christbaum, Mandala, Sternenhimmel, Waldtiere oder dein eigenes Motiv "
         "bzw. Logo aus der Motiv-Bibliothek. Jede Nummer ergibt ein neues Schnittmuster.",
    params=[
        sel("form", "Form", FORMEN, "rechteck"),
        num("breite", "Breite / Durchmesser", 200, 60, 380),
        num("hoehe", "Höhe", 150, 60, 380, when={"form": ["rechteck"]}),
        integer("teile", "Teile (ungefähr)", 24, 4, 200, help="Kleinkinder 4–12, Kinder 20–48, Erwachsene ab 60"),
        sel("schnitt", "Schnitt", P.SCHNITTE, "klassisch"),
        integer("nummer", "Schnittmuster-Nr.", 1, 1, 9999, help="jede Nummer ergibt andere Nasen"),
        sel("bild", "Bild", BILDWAHL, "winterdorf", section="Bild",
            help="Fotopuzzle: „Foto“ wählen und unter „Eigene Gravur“ ein Foto hinzufügen – es läuft über alle Teile"),
        motiv("motiv", "Motiv", "stern", "eigenes Bild oder Logo über „Motive importieren“ (SVG oder PNG) laden",
              when={"bild": ["eigenes"]}, section="Bild"),
        sel("motiv_art", "Motiv als", MOTIV_ART, "flaeche", when={"bild": ["eigenes"]}, section="Bild"),
        num("motiv_groesse", "Motivgröße", 80, 20, 100, unit="%", when={"bild": ["eigenes"]}, section="Bild"),
        sel("muster", "Hintergrundmuster", B.MUSTER, "sterne", when={"bild": ["eigenes", "ohne"]}, section="Bild"),
        sel("rahmen", "Rahmen", RAHMEN, "keiner", section="Gestaltung"),
        sel("zierrand", "Zierrand", S.RAENDER, "keiner", section="Gestaltung"),
        txt("beschriftung", "Beschriftung", "", section="Beschriftung",
            help="z. B. ein Name oder „Frohe Weihnachten“ – auf einem Band im Bild bzw. auf dem Rahmen"),
        num("spiel", "Spiel zwischen den Teilen", 0.1, 0.0, 0.4, step=0.02, section="Passung",
            help="0,1 mm für Sperrholz; mehr, wenn die Teile zu stramm sitzen"),
    ],
)

UEBERSETZUNG = {"en": dict(S.UEBERSETZUNG_GEMEINSAM, **{
    "Puzzle": "Jigsaw puzzle",
    INFO["desc"]: "Picture jigsaw with interlocking tabs, rectangular or round, optionally with a frame to lay it in. "
                  "The picture runs across all pieces: winter village, Christmas tree, mandala, starry sky, forest "
                  "animals or your own motif or logo from the motif library. Every number gives a new cut pattern.",
    "Form": "Shape", "rechteckig": "rectangular", "rund": "round", "Breite / Durchmesser": "Width / diameter",
    "Höhe": "Height", "Teile (ungefähr)": "Pieces (approx.)",
    "Kleinkinder 4–12, Kinder 20–48, Erwachsene ab 60": "toddlers 4–12, children 20–48, adults 60+",
    "Schnitt": "Cut", "klassisch mit Nasen": "classic with tabs",
    "verspielt (unregelmäßige Nasen)": "playful (irregular tabs)",
    "gerade Kanten (für Kleinkinder)": "straight edges (for toddlers)",
    "Schnittmuster-Nr.": "Cut pattern no.", "jede Nummer ergibt andere Nasen": "every number gives different tabs",
    "Bild": "Picture", "Winterdorf bei Nacht": "Winter village at night",
    "Christbaum mit Geschenken": "Christmas tree with presents", "Mandala": "Mandala",
    "Sternenhimmel über dem Wald": "Starry sky over the forest",
    "Waldlichtung mit Eule und Igel": "Forest clearing with owl and hedgehog",
    "eigenes Motiv oder Logo": "own motif or logo", "Foto (über „Eigene Gravur“)": "photo (via “Custom engraving”)",
    "Fotopuzzle: „Foto“ wählen und unter „Eigene Gravur“ ein Foto hinzufügen – es läuft über alle Teile":
        "Photo puzzle: choose “photo” and add a photo under “Custom engraving” – it runs across all pieces",
    "Fotopuzzle: unter „Eigene Gravur“ ein Foto hinzufügen (Teil „größtes Teil“ oder „alle Teile“) – es wird einmal über alle Puzzleteile gelegt.":
        "Photo puzzle: add a photo under “Custom engraving” (part “largest part” or “all parts”) – it is laid once across all puzzle pieces.", "ohne Bild (nur Muster)": "no picture (pattern only)",
    "Motiv": "Motif",
    "eigenes Bild oder Logo über „Motive importieren“ (SVG oder PNG) laden":
        "load your own picture or logo via “Import motifs” (SVG or PNG)",
    "Motiv als": "Motif as", "flächig gravieren": "engrave filled", "nur Umriss gravieren": "engrave outline only",
    "Motivgröße": "Motif size", "Hintergrundmuster": "Background pattern", "keins": "none",
    "Schneeflocken": "Snowflakes", "Rauten": "Diamonds", "Punkte": "Dots",
    "Rahmen": "Frame", "ohne Rahmen": "no frame", "Rahmen mit Boden (Legepuzzle)": "frame with base (tray puzzle)",
    "z. B. ein Name oder „Frohe Weihnachten“ – auf einem Band im Bild bzw. auf dem Rahmen":
        "e.g. a name or “Merry Christmas” – on a ribbon in the picture or on the frame",
    "Spiel zwischen den Teilen": "Play between the pieces",
    "0,1 mm für Sperrholz; mehr, wenn die Teile zu stramm sitzen": "0.1 mm for plywood; more if the pieces are too tight",
    "Passung": "Fit",
    "Zum Sortieren erst die Randteile heraussuchen – die Teile tragen ihre Position im Namen (Zeile-Spalte).":
        "To sort, pick out the edge pieces first – each piece carries its position in its name (row-column).",
    "Die Rahmenplatte auf den Boden leimen; die Teile liegen dann in der Mulde.":
        "Glue the frame plate onto the base; the pieces then lie in the recess.",
    "Gravur zuerst lasern, dann schneiden – so verrutschen die kleinen Teile nicht.":
        "Engrave first, then cut – that way the small pieces cannot shift.",
})}


# ---------------------------------------------------------------------------------------------
# Bausteine
# ---------------------------------------------------------------------------------------------

def _band(cx: float, cy: float, w: float, h: float) -> List[Tuple[float, float]]:
    """Schriftband mit Schwalbenschwanz-Enden (Kontur gegen den Uhrzeigersinn)."""
    k = 0.35 * h
    x0, x1 = cx - w / 2, cx + w / 2
    return [(x0, cy - h / 2), (x1, cy - h / 2), (x1 + k * 1.6, cy - h / 2 - 0.1 * h), (x1 + k * 0.6, cy),
            (x1 + k * 1.6, cy + h / 2 - 0.1 * h), (x1, cy + h / 2), (x0, cy + h / 2), (x0 - k * 1.6, cy + h / 2 - 0.1 * h),
            (x0 - k * 0.6, cy), (x0 - k * 1.6, cy - h / 2 - 0.1 * h)]


def _text_striche(text: str, cx: float, cy: float, w: float, h: float, min_cap: float = 3.0):
    striche, cap = S.Z.text_in_box(text, cx, cy, w, h, h, min_cap, gap_faktor=0.08, style="normal", case="normal")
    return [(s, False) for s in striche]


def _motiv_bild(mid: str, art: str, groesse: float, box, muster: str, seed: int):
    """Eigenes Motiv aus der Motiv-Bibliothek mittig in die Box, dahinter ein Muster."""
    import motive as mt
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    m = mt.load(mid)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    size = groesse / 100.0 * min(W / max(m["w"], 1e-6), H / max(m["h"], 1e-6))
    b = B.Bild(box, seed)
    for fl in m["flaechen"]:
        aussen = mt.place(fl["aussen"], cx, cy, size)
        loecher = [mt.place(h, cx, cy, size) for h in fl["loecher"]]
        if art == "flaeche":
            b.schraffur(aussen, 0.3, 0.0, loecher)
        b.linie(aussen, True)
        for h in loecher:
            b.linie(h, True)
    for li in m["linien"]:
        b.linie(mt.place(li, cx, cy, size))
    for fl in m["flaechen"]:                  # Motiv deckt das Muster dahinter ab (mit etwas Luft)
        aussen = mt.place(fl["aussen"], cx, cy, size)
        b.decke(_aufblasen(aussen, 1.2))
    if m["linien"] and not m["flaechen"]:
        lx = [p for li in m["linien"] for p in mt.place(li, cx, cy, size)]
        bx = B._bb(lx)
        b.decke(rect(bx[0] - 1.5, bx[1] - 1.5, bx[2] - bx[0] + 3, bx[3] - bx[1] + 3))
    if muster != "keins":
        B.muster(muster, box, b, groesse=max(6.0, min(W, H) / 14), seed=seed)
    return b.striche


def _aufblasen(poly, d: float):
    """Fläche um d vergrößern – ohne teure Schleifenprüfung (reicht für Verdeckung und Sperren)."""
    from steckwerk import offset_polygon
    return offset_polygon(oriented(list(poly), True), d, miter_limit=2.0)


def puzzle_aus_bild(cfg, name: str, umriss_art: str, W: float, H: float, teile: int, schnitt: str, nummer: int,
                    bild: Sequence[Tuple[list, bool]], oben: Sequence[Tuple[list, bool]] = (),
                    sperren: Sequence[list] = (), spiel: float = 0.1) -> List[Part]:
    """Schnittstelle für andere Pakete: ein beliebiges Gravurbild (Linien um die Mitte (0, 0), in mm) zum
    Puzzle machen. umriss_art: "rechteck" (W × H) oder "rund" (Durchmesser W). Liefert die Teile."""
    T = cfg.T
    if umriss_art == "rund":
        roh = P.rund_teile(W / 2, teile, schnitt, nummer)
        p_mass = (W / 2) / (math.sqrt(max(1, teile)) * 0.9)
    else:
        sp, ze = P.raster_mass(W, H, teile)
        p_mass = min(W / sp, H / ze)
        roh = P.raster_teile(W, H, sp, ze, schnitt, nummer)
    p_min = max(14.0, 4.5 * T)
    if p_mass < p_min:
        raise ValueError(f"Puzzle: Bei {W:.0f} mm und {teile} Teilen würden die Teile nur ca. {p_mass:.0f} mm groß – "
                         f"mindestens {p_min:.0f} mm, also weniger Teile oder ein größeres Puzzle wählen")
    teile_out: List[Part] = []
    for label, kontur in roh:
        teile_out.append(Part(f"{name}_teil_{label}", P.einruecken(kontur, spiel / 2)))
    P.verteilen(teile_out, bild, sperren, oben)
    return teile_out


# ---------------------------------------------------------------------------------------------
# Modell
# ---------------------------------------------------------------------------------------------

def build(cfg, name: str = "puzzle", form: str = "rechteck", breite: float = 200.0, hoehe: float = 150.0,
          teile: int = 24, schnitt: str = "klassisch", nummer: int = 1, bild: str = "winterdorf",
          motiv: str = "stern", motiv_art: str = "flaeche", motiv_groesse: float = 80.0, muster: str = "sterne",
          rahmen: str = "keiner", zierrand: str = "keiner", beschriftung: str = "", spiel: float = 0.1):
    from models import _deko as dk
    dk.check_choice("Form", form, FORMEN)
    dk.check_choice("Schnitt", schnitt, P.SCHNITTE)
    dk.check_choice("Bild", bild, BILDWAHL)
    dk.check_choice("Motiv als", motiv_art, MOTIV_ART)
    dk.check_choice("Hintergrundmuster", muster, B.MUSTER)
    dk.check_choice("Rahmen", rahmen, RAHMEN)
    dk.check_choice("Zierrand", zierrand, S.RAENDER)
    W = cfg.s(breite)
    H = W if form == "rund" else cfg.s(hoehe)
    if not (60 <= W <= 380 and 60 <= H <= 380):
        raise ValueError("Puzzle: Breite und Höhe müssen zwischen 60 und 380 mm liegen")
    teile = int(teile)
    if not 4 <= teile <= 200:
        raise ValueError("Puzzle: 4 bis 200 Teile")
    if not 0.0 <= spiel <= 0.4:
        raise ValueError("Puzzle: Spiel zwischen 0 und 0,4 mm")
    nummer = int(nummer)
    text = (beschriftung or "").strip()
    rund = form == "rund"
    umriss = circle(0.0, 0.0, W / 2, 0.04) if rund else rect(-W / 2, -H / 2, W, H)
    box = (-W / 2, -H / 2, W / 2, H / 2)

    # Rahmen: Breite der Leisten; die Beschriftung kommt bei eckigem Rahmen auf die untere Leiste
    leiste = max(10.0, 0.07 * min(W, H))
    text_auf_rahmen = rahmen == "rahmen" and not rund and bool(text)
    unten_extra = (min(14.0, max(8.0, 0.06 * H)) + 2.0) if text_auf_rahmen else 0.0

    # Gravurbild – bei einem Schriftband im Bild rückt die Szene nach oben, darunter läuft der Boden weiter
    seed = nummer
    band_h = min(14.0, max(7.0, 0.075 * H))
    band_unten = bool(text) and not text_auf_rahmen and not rund and bild in B.SZENEN and bild != "mandala"
    if bild in B.SZENEN:
        if band_unten:
            reserve = band_h + 0.06 * H
            striche = B.szene(bild, (box[0], box[1] + reserve, box[2], box[3]), seed)
            striche += B.boden(bild, (box[0], box[1], box[2], box[1] + reserve))
        else:
            striche = B.szene(bild, box, seed)
    elif bild == "eigenes":
        striche = _motiv_bild(motiv, motiv_art, motiv_groesse, box, muster, seed)
    elif bild == "foto":
        striche = []
    else:
        striche = B.muster(muster, box, None, groesse=max(6.0, min(W, H) / 14), seed=seed)

    oben: List[Tuple[list, bool]] = []
    sperren: List[list] = []
    tafel = Part("_tafel", oriented(list(umriss), True))
    cv = dk.Canvas(tafel, margin=0.8)
    if text and not text_auf_rahmen:
        th = band_h
        tw = 0.62 * W if not rund else 0.55 * W
        cy = -H / 2 + 0.03 * H + th / 2 if band_unten else -H / 2 + 0.11 * H + th / 2 if not rund else -0.3 * W
        st = _text_striche(text, 0.0, cy, tw, th * 0.62, 2.5)
        if not st:
            raise ValueError("Puzzle: Die Beschriftung passt nicht aufs Band – kürzer fassen")
        xs = [p[0] for s, _ in st for p in s]
        bw = max(xs) - min(xs) + 0.9 * th
        band = _band(0.0, cy, bw, th)
        oben.append((band, True))
        innen = _band(0.0, cy, bw - 1.6, th - 1.6)
        oben.append((innen, True))
        oben += st
        sperren.append(_aufblasen(band, 0.8))
    if zierrand not in ("keiner",):
        e = max(4.0, 0.035 * min(W, H))
        k = circle(0.0, 0.0, W / 2 - e * 0.5, 0.04) if rund else rect(-W / 2 + e * 0.5, -H / 2 + e * 0.5, W - e, H - e)
        S.zierrand(cv, k, zierrand, max(3.0, 0.7 * e), seed=nummer)
        oben += [(s.points, s.closed) for s in tafel.engrave]
        tafel.engrave = []
        rand_sperre = circle(0.0, 0.0, W / 2 - e * 1.3, 0.04) if rund else \
            rect(-W / 2 + e * 1.3, -H / 2 + e * 1.3, W - 2.6 * e, H - 2.6 * e)
        # Bild nur innerhalb des Zierrands: Ring außen herum als Sperre
        sperren.append(_ring_sperre(umriss, rand_sperre))

    teile_liste = puzzle_aus_bild(cfg, name, form, W, H, teile, schnitt, nummer, striche, oben, sperren, spiel)

    asm = Assembly(name, params=dict(form=form, breite=W, hoehe=H, teile=len(teile_liste), schnitt=schnitt,
                                     nummer=nummer, bild=bild, verbund=f"{name}_teil_"))
    asm.parts += teile_liste
    if rahmen == "rahmen":
        luft = 0.25 + spiel
        if rund:
            R = W / 2
            aussen = circle(0.0, 0.0, R + luft + leiste, 0.04)
            loch = circle(0.0, 0.0, R + luft, 0.04, ccw=False)
            mitte = circle(0.0, 0.0, R + luft + leiste / 2, 0.04)
        else:
            x0, y0 = -W / 2 - luft - leiste, -H / 2 - luft - leiste - unten_extra
            x1, y1 = W / 2 + luft + leiste, H / 2 + luft + leiste
            aussen = dk.rounded_rect(x0, y0, x1, y1, leiste * 0.6)
            loch = rect(-W / 2 - luft, -H / 2 - luft, W + 2 * luft, H + 2 * luft, ccw=False)
            mitte = dk.rounded_rect(x0 + leiste / 2, y0 + leiste / 2, x1 - leiste / 2, y1 - leiste / 2, leiste * 0.3)
        S.platte_passt(cfg, *_mass(aussen), "Puzzle-Rahmen")
        platte = Part(f"{name}_rahmen", oriented(aussen, True))
        platte.add_hole(loch)
        rcv = dk.Canvas(platte, margin=1.2, hole_margin=1.2)
        if zierrand != "keiner" and not text_auf_rahmen:
            S.zierrand(rcv, mitte, zierrand, max(3.0, 0.4 * leiste), seed=nummer)
        elif zierrand != "keiner":
            rcv.draw(mitte, True)
        if text_auf_rahmen:
            S.text(rcv, text, 0.0, -H / 2 - luft - leiste * 0.25 - unten_extra / 2 - 0.5,
                   W * 0.8, unten_extra - 1.0, unten_extra - 2.5)
        boden = Part(f"{name}_boden", oriented(list(aussen), True))
        asm.parts += [platte, boden]
        asm.notes.append("Die Rahmenplatte auf den Boden leimen; die Teile liegen dann in der Mulde.")
    if bild == "foto":
        asm.notes.append("Fotopuzzle: unter „Eigene Gravur“ ein Foto hinzufügen (Teil „größtes Teil“ oder „alle Teile“) – "
                         "es wird einmal über alle Puzzleteile gelegt.")
    asm.notes += [
        "Gravur zuerst lasern, dann schneiden – so verrutschen die kleinen Teile nicht.",
        "Zum Sortieren erst die Randteile heraussuchen – die Teile tragen ihre Position im Namen (Zeile-Spalte).",
    ]
    return asm


def _ring_sperre(aussen, innen):
    """Fläche zwischen zwei Konturen als ein Polygon (über einen schmalen Schlitz verbunden)."""
    a = oriented(list(aussen), True)
    i = oriented(list(innen), False)
    # an der rechtesten Stelle beider Konturen verbinden
    ka = max(range(len(a)), key=lambda k: a[k][0])
    ki = max(range(len(i)), key=lambda k: i[k][0])
    groesser = [(x * 1.05, y * 1.05) for x, y in a[ka:] + a[:ka]]
    return groesser + [groesser[0]] + i[ki:] + i[:ki] + [i[ki]]


def _mass(pts) -> Tuple[float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys)
