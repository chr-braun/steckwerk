"""
Halloween-Anhänger – filigrane Hänger für Zweige, Fenster und Geschenke.

Fledermaus, Gespenst, Totenkopf, Katze, Hexenhut, Kürbis und Spinnennetz – jeweils mit
Durchbrüchen und feinen Gravuren (Flügelknochen, Stofffalten, Schädelnähte, Sterne …) und einer
Aufhängeöse. Mit „alle“ entsteht das ganze Set auf einmal. Ein Name kann eingraviert werden.
"""
import importlib.util
import math
import os
import random
import sys

from steckwerk import Assembly, Part, arc_points, circle, min_distance, oriented, point_in_polygon
from models import _deko as dk
from models._font import STYLES, fit_text, unsupported
from models._shapes import union_circle
from pakete import bibliothek, num, sel, txt


def _lib():
    return bibliothek("verzierungen").G


g = _lib()

MOTIFS = [("fledermaus", "Fledermaus"), ("geist", "Gespenst"), ("totenkopf", "Totenkopf"), ("katze", "Katze"),
          ("hexenhut", "Hexenhut"), ("kuerbis", "Kürbis"), ("spinnennetz", "Spinnennetz")]

UEBERSETZUNG = {"en": g.EN}

INFO = dict(
    label="Halloween-Anhänger",
    group="Halloween",
    desc="Fledermaus, Gespenst, Totenkopf, Katze, Hexenhut, Kürbis, Spinnennetz – filigran, mit Öse.",
    params=[
        sel("motiv", "Motiv", MOTIFS + [("alle", "alle sieben (Set)")], "alle"),
        num("size", "Größe", 80, 45, 160, help="größte Abmessung in mm"),
        txt("text", "Name (Gespenst, Kürbis, Hut)", "", "leer = ohne", section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "normal", section="Schrift und Beschriftung"),
    ],
)


# Figuren aus der Motiv-Bibliothek der Engine: Umriss, Innenformen und Gravurdetails kommen von dort
# (dieselben Motive wie in den Motiv-Vorlagen). Je Motiv: Platz für den Namen (Mitte, Breite, Höhe als
# Anteil der Größe) und die bevorzugte Lage der Öse (x als Anteil der Größe).
BIBLIOTHEK = {
    "fledermaus": dict(),
    "geist": dict(text=((0.0, -0.25), 0.34, 0.08)),
    "totenkopf": dict(),
    "katze": dict(oese=0.05),
    "hexenhut": dict(text=((0.0, -0.33), 0.56, 0.05), oese=0.2),
    "kuerbis": dict(text=((0.0, 0.19), 0.30, 0.06)),
}


def _aus_bibliothek(mid, S):
    import motive as mt
    m = mt.load(mid)
    fl = max(m["flaechen"], key=lambda f: abs(g.signed_area(f["aussen"])))
    poly = mt.place(fl["aussen"], 0.0, 0.0, S)
    holes = [g.dedupe(mt.place(h, 0.0, 0.0, S), 0.25) for h in fl["loecher"]]
    lines = [mt.place(li, 0.0, 0.0, S) for li in m["linien"]]
    return poly, holes, lines


def _oese_x(poly, S, bevorzugt):
    """x der Öse: höchster Punkt nahe der bevorzugten Stelle (sonst der höchste überhaupt)."""
    nah = [p for p in poly if abs(p[0] - bevorzugt * S) < 0.25 * S]
    return max(nah or poly, key=lambda p: p[1])[0]


def _eyelet(outline, x, y_top, r, web):
    """Öse oben anfügen: Ring mit Loch. Liefert (Kontur, Lochkreis)."""
    for dy in (0.35, 0.5, 0.65):
        for dx in (0.0, 0.5, -0.5, 1.0, -1.0):
            cx, cy = x + dx * r, y_top + dy * r
            try:
                out = union_circle(outline, cx, cy, r)
            except ValueError:
                continue
            hole = circle(cx, cy, r - max(web * 1.3, 0.38 * r), 0.05)
            if g.polygon_ok(oriented(out, True)) and min_distance(hole, out, limit=web) >= web:
                return out, hole
    raise ValueError("Öse passt nicht – Anhänger größer wählen")


def build_one(cfg, name, motiv, S, text, schrift, rng, web):
    holes = []
    eng = []                                   # (punkte, geschlossen)
    put = []                                   # geschlossene Ornamente (nur ganz)
    text_box = None
    if motiv in BIBLIOTHEK:
        poly, holes, lines = _aus_bibliothek(motiv, S)
        eng += [(li, False) for li in lines]
        bx = BIBLIOTHEK[motiv]
        if bx.get("text"):
            (tx, ty), tw, th = bx["text"]
            text_box = ((tx * S, ty * S), tw * S, th * S)
        eye_x = _oese_x(poly, S, bx.get("oese", 0.0))
        eye_y = max(p[1] for p in poly)
    elif motiv == "spinnennetz":
        R = S / 2
        poly = circle(0.0, 0.0, R, cfg.arc_tolerance)
        holes = g.web(0.0, 0.0, R - max(web, 1.4) * 1.2, math.radians(90), math.radians(450), 5, 12,
                      max(web, 1.4))[1]
        put.append(g.spider(0.0, -0.02 * S, 0.30 * S, 0.5))
        eye_x, eye_y = 0.0, R
        holes = [h for h in holes if not any(point_in_polygon(p, put[-1]) for p in h) and
                 min_distance(h, put[-1], limit=1.0) >= 1.0]
    else:
        raise ValueError(motiv)
    if motiv not in ("spinnennetz",):
        poly = oriented(poly, True)
    # Öse oben
    r_e = max(0.07 * S, 3.4)
    top_pts = [p for p in poly if abs(p[0] - eye_x) < r_e * 0.6]
    y_top = max(p[1] for p in top_pts) if top_pts else eye_y
    outline, eye_hole = _eyelet(poly, eye_x, y_top, r_e, web)
    part = Part(f"{name}", outline)
    part.add_hole(eye_hole)
    for h in holes:
        if g.hole_ok(h, 0.3) and abs(g.signed_area(h)) > 2.0 and \
                min_distance(h, outline, limit=web) >= web and min_distance(h, eye_hole, limit=web) >= web and \
                all(min_distance(h, q, limit=web) >= web for q in part.holes):
            part.add_hole(h)
        elif motiv in BIBLIOTHEK:
            eng.append((h, True))                    # zu fein zum Ausschneiden: als Umriss gravieren
    cv = dk.Canvas(part, margin=0.9, hole_margin=0.9, seed=cfg.seed)
    for p_ in put:
        cv.put(p_, True, reserve=0.6)
    if text and text_box:
        (tx, ty), bw_, bh_ = text_box
        try:
            strokes, _ = fit_text(text, tx, ty, bw_, bh_, min_h=2.2, max_cap=bh_, style=schrift)
            for st in strokes:
                cv.draw(st)
            cv.block_strokes([(st, False) for st in strokes], 0.6)
            xs = [x for st in strokes for x, _ in st]
            ys = [y for st in strokes for _, y in st]
            if xs:
                cv.block_box((min(xs), min(ys), max(xs), max(ys)), 1.2)   # Details nicht durch den Namen
        except ValueError:
            pass
    for pts, closed in eng:
        cv.draw(pts, closed)
    return part


def build(cfg, name="halloween_anhaenger", motiv="alle", size=80.0, text="", schrift="normal"):
    S = cfg.s(size)
    if not 45 <= S <= 160:
        raise ValueError("Anhänger: Größe muss zwischen 45 und 160 mm liegen")
    if motiv != "alle":
        dk.check_choice("Motiv", motiv, MOTIFS)
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    web = max(cfg.min_web * 1.5, 1.5)
    rng = random.Random(cfg.seed)
    motifs = [m for m, _ in MOTIFS] if motiv == "alle" else [motiv]
    asm = Assembly(name, params=dict(motiv=motiv, size=S, **({"text": text} if text else {})))
    for m in motifs:
        asm.parts.append(build_one(cfg, f"{name}_{m}", m, S, text, schrift, rng, web))
    asm.notes.append("Anhänger an einem Faden durch die Öse aufhängen. Tipp: schwarz lasiert vor einem "
                     "hellen Fenster wirken sie wie Scherenschnitte.")
    return asm
