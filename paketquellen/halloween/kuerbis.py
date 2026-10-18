"""
Kürbis-Leuchte – geschnitzter Halloween-Kürbis zum Hinstellen.

Ein bauchiger Kürbis aus sieben Rippen-Buckeln mit gekerbtem Stiel, Blatt mit Adern und eingerollter
Ranke. Das Gesicht (oder eine Silhouette) ist ausgeschnitten, um die Schnitzkanten läuft eine gravierte
Schale, Rippen sind als feine Schlitze geschnitten oder graviert. Ein Teelicht (LED) dahinter lässt
das Gesicht leuchten. Steht mit einem Zapfen in einem ovalen Sockel, auf Wunsch mit Text.
"""
import importlib.util
import math
import os
import sys

from steckwerk import Assembly, Part, min_distance, oriented
from models import _deko as dk
from models._font import STYLES, unsupported
from models._stand import stand_base, tab_feature_at
from pakete import bibliothek, flag, num, sel, txt


def _lib():
    return bibliothek("verzierungen").G


g = _lib()

FACES = [("klassisch", "klassisch (Dreiecke)"), ("gruselig", "gruselig mit Fangzähnen"),
         ("froehlich", "fröhlich"), ("katze", "Katzengesicht"), ("fledermaus", "Fledermaus-Silhouette"),
         ("hexe", "Hexe auf dem Besen"), ("spinnennetz", "Spinnennetz")]

UEBERSETZUNG = {"en": g.EN}

INFO = dict(
    label="Kürbis-Leuchte",
    group="Halloween",
    desc="Geschnitzter Kürbis mit Stiel, Blatt und Ranke – Gesicht oder Silhouette leuchtet mit Teelicht.",
    params=[
        num("width", "Breite", 150, 80, 320),
        sel("gesicht", "Gesicht", FACES, "gruselig"),
        flag("rippen", "Rippen gravieren", True),
        flag("blatt", "Blatt und Ranke", True),
        txt("text", "Text auf dem Sockel", "BOO!", "leer = ohne Text", section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "fett", section="Schrift und Beschriftung"),
        sel("schreibweise", "Schreibweise", dk.FONT_CASES, "gross", section="Schrift und Beschriftung"),
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


def build(cfg, name="kuerbis", width=150.0, gesicht="gruselig", rippen=True, blatt=True, text="BOO!",
          schrift="fett", schreibweise="gross"):
    T = cfg.T
    W = cfg.s(width)
    if not 80 <= W <= 320:
        raise ValueError("Kürbis: Breite muss zwischen 80 und 320 mm liegen")
    dk.check_choice("Gesicht", gesicht, FACES)
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    notes = []
    f = SP.kuerbis_gross(W, cfg, gesicht, blatt, rippen, cfg.seed)
    # flache Standfläche: unten abschneiden, Figur auf y = 0 stellen
    yb = -0.335 * W
    f.cut(K.rect(-W, yb - W, 2 * W, W))
    gr = f.gravur
    f = f.place(0.0, -yb, 1.0)
    gr = [([(x, y - yb) for x, y in pts], c) for pts, c in gr]
    part = SP.teil(f"{name}_kuerbis", f, cfg, notes, unten_flach=True, px=max(0.06, min(0.16, W / 2000)))
    # exakter Steckzapfen für den Sockel
    tw = max(0.22 * W, 4 * T)
    outline = g.op2(part.outline, [(-tw / 2, -T), (tw / 2, -T), (tw / 2, 0.6), (-tw / 2, 0.6)], "union")
    holes = part.holes
    part = Part(f"{name}_kuerbis", oriented(g.dedupe(outline, 0.05), True),
                features=[tab_feature_at("fuss", -tw / 2, 0.0, tw, T)])
    for h in holes:
        part.add_hole(h)
    # Schnitzkante: Rand der Kürbisschale um Augen und Mund graviert
    from steckwerk import offset_polygon, signed_area
    rand = []
    for h in part.holes:
        if abs(signed_area(h)) > 0.004 * W * W and gesicht in ("klassisch", "gruselig", "froehlich", "katze"):
            try:
                rand.append((offset_polygon(oriented(h, True), max(1.6, 0.012 * W)), True))
            except Exception:
                pass
    SP.gravur(part, gr + rand, cfg.seed)
    asm = Assembly(name, params=dict(width=W, gesicht=gesicht, **({"text": text} if text else {})))
    asm.parts.append(part)
    stand_base(asm, part, "fuss", tw, cfg, 0.36 * W, 0.16 * W, f"{name}_sockel", text or "", schrift,
               schreibweise)
    asm.notes.extend(dict.fromkeys(notes))
    asm.notes.append(f"{name}: Kürbis in den Sockel stecken, LED-Teelicht dahinter stellen. "
                     "Tipp: Rückseite mit orangem Transparentpapier bekleben, dann leuchtet das Gesicht warm.")
    return asm


def _upper(poly, cut_y):
    P = oriented(poly, True)
    n = len(P)
    hits = []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        if (a[1] - cut_y) * (b[1] - cut_y) < 0:
            t = (cut_y - a[1]) / (b[1] - a[1])
            hits.append((i, (a[0] + t * (b[0] - a[0]), cut_y), b[1] > a[1]))
    up = [h for h in hits if h[2]][0]
    down = [h for h in hits if not h[2]][0]
    out = [up[1]]
    k = up[0] + 1
    while True:
        out.append(P[k % n])
        if k % n == down[0]:
            break
        k += 1
    out.append(down[1])
    return list(reversed(out))


def _round_web(cx, cy, R, t):
    """Rundes Spinnennetz als Löcher (Fäden bleiben stehen)."""
    holes = []
    spokes = 10
    rings = 4
    angs = [2 * math.pi * i / spokes for i in range(spokes + 1)]
    radii = [R * (0.25 + 0.75 * k / rings) for k in range(1, rings + 1)]
    for k in range(rings):
        r_in = radii[k - 1] if k > 0 else 0.0
        r_out = radii[k]
        for i in range(spokes):
            aa, ab = angs[i], angs[i + 1]
            rr = max(r_in * 0.9, t)
            da = (t * 0.6) / rr
            ia, ib = aa + da, ab - da
            if ib - ia < 0.05:
                continue
            o = [(cx + (r_out - t / 2 - 0.12 * r_out * (ab - aa) * math.sin(math.pi * j / 10)) *
                  math.cos(ia + (ib - ia) * j / 10),
                  cy + (r_out - t / 2 - 0.12 * r_out * (ab - aa) * math.sin(math.pi * j / 10)) *
                  math.sin(ia + (ib - ia) * j / 10)) for j in range(11)]
            if k == 0:
                rc = (t * 0.6) / math.sin((ab - aa) / 2)
                inner = [(cx + rc * math.cos((aa + ab) / 2), cy + rc * math.sin((aa + ab) / 2))]
            else:
                inner = [(cx + (r_in + t / 2 - 0.12 * r_in * (ab - aa) * math.sin(math.pi * j / 10)) *
                          math.cos(ib - (ib - ia) * j / 10),
                          cy + (r_in + t / 2 - 0.12 * r_in * (ab - aa) * math.sin(math.pi * j / 10)) *
                          math.sin(ib - (ib - ia) * j / 10)) for j in range(11)]
            cell = g.dedupe(o + inner, 0.08)
            if len(cell) >= 3 and abs(g.signed_area(cell)) > 3.0:
                holes.append(cell)
    # Abstand zwischen Löchern sichern
    out = []
    for h in holes:
        if all(min_distance(h, q, limit=t) >= t * 0.95 for q in out):
            out.append(h)
    return out
