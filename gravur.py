"""
gravur.py – eigene Gravuren auf jedem Bauteil jedes Modells: Fotos, Logos, Motive und Flächenmuster.

Eine Gravur ist ein Eintrag der Liste `gravuren` in der Anfrage (Web, Desktop, Kommandozeile):

  {"quelle": "bild",   "bild": "oma-3f2a1c",  "teil": "auto", "x": 0, "y": 0, "groesse": 0,
   "drehung": 0, "spiegeln": false, "modus": "fehlerstreuung", "form": "oval",
   "helligkeit": 0, "kontrast": 10, "gamma": 1.0, "invertieren": false, "aufloesung": 10, "rand": 1.5}
  {"quelle": "motiv",  "motiv": "stern", "art": "raster" | "umriss" | "flaeche", "schraffur": 0.2, …}
  {"quelle": "muster", "muster": "mandala", "abstand": 6, "form": "rechteck" | "kreis" | …, …}

teil     "auto" = größtes Teil, "alle" = jedes Teil, sonst der Name eines Teils (siehe Antwort „teile“)
x, y     Verschiebung der Mitte in mm gegenüber der Mitte des Teils (y nach oben)
groesse  längere Seite in mm; 0 = automatisch passend (Muster: ganze Fläche)
rand     Abstand zur Kontur und zu Durchbrüchen in mm

Fotos werden zu einer Bild-Ebene (Rastergravur, in XCS „Gravieren“ als Bitmap), alles andere wird zu
Gravurlinien. Was über den Rand oder einen Durchbruch ragen würde, wird weggelassen bzw. maskiert –
eine eigene Gravur kann also nie die Steckverbindungen oder das Layout kaputt machen.
"""
from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import bilder
import motive as mt
from models import _deko as dk
from models import _muster as mu
from models.motivvorlagen import _hatch, tidy
from steckwerk import (Assembly, Part, Point, RasterImage, bbox, clean, inset_polygon, oriented, signed_area)

QUELLEN = [("bild", "Foto / Bild"), ("motiv", "Motiv / Logo"), ("muster", "Muster")]
QUELLEN_KEYS = [k for k, _ in QUELLEN]
MOTIV_ARTEN = [("raster", "flächig, gestochen scharf (Bild)"), ("flaeche", "flächig (Schraffur)"),
               ("umriss", "nur Umriss")]
MOTIV_ARTEN_KEYS = [k for k, _ in MOTIV_ARTEN]
BEREICHE = [("rechteck", "Rechteck"), ("kreis", "Kreis"), ("oval", "Oval"), ("herz", "Herz")]
BEREICH_KEYS = [k for k, _ in BEREICHE]
MAX_GRAVUREN = 8


def optionen() -> Dict[str, Any]:
    """Auswahllisten für Formulare (Web, Desktop)."""
    o = lambda lst: [dict(value=v, label=l) for v, l in lst]          # noqa: E731
    return dict(quellen=o(QUELLEN), modi=o(bilder.MODI), formen=o(bilder.FORMEN), motiv_arten=o(MOTIV_ARTEN),
                muster=o(mu.MUSTER), bereiche=o(BEREICHE), aufloesungen=list(bilder.AUFLOESUNGEN),
                max=MAX_GRAVUREN)


# ---------------------------------------------------------------------------
# Prüfen
# ---------------------------------------------------------------------------

def pruefen(value: Any) -> List[Dict[str, Any]]:
    """Gravurliste prüfen und mit Standardwerten auffüllen (auch als JSON-Text)."""
    if value in (None, "", []):
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            raise ValueError('Gravuren: erwartet eine Liste wie [{"quelle": "muster", "muster": "mandala"}]')
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        raise ValueError("Gravuren: erwartet eine Liste")
    if len(value) > MAX_GRAVUREN:
        raise ValueError(f"Höchstens {MAX_GRAVUREN} eigene Gravuren")
    out = []
    for i, it in enumerate(value, 1):
        if not isinstance(it, dict):
            raise ValueError(f"Gravur {i}: ungültiger Eintrag")
        pre = f"Gravur {i}"

        def num(k, d, lo, hi):
            v = it.get(k, d)
            if v in (None, ""):
                v = d
            try:
                v = float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
            except (TypeError, ValueError):
                raise ValueError(f"{pre}: {k}={it.get(k)!r} ist keine Zahl")
            if v != v or not lo <= v <= hi:
                raise ValueError(f"{pre}: {k} muss zwischen {lo:g} und {hi:g} liegen")
            return v

        def flag(k):
            v = it.get(k, False)
            return v if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "ja", "yes", "on")

        def choice(k, d, keys):
            v = str(it.get(k) or d)
            if v not in keys:
                raise ValueError(f"{pre}: {k} {v!r} unbekannt – erlaubt: {', '.join(keys)}")
            return v
        q = choice("quelle", "bild", QUELLEN_KEYS)
        g = dict(quelle=q, teil=str(it.get("teil") or "auto")[:60], x=num("x", 0, -1000, 1000),
                 y=num("y", 0, -1000, 1000), groesse=num("groesse", 0, 0, 1000), drehung=num("drehung", 0, -360, 360),
                 spiegeln=flag("spiegeln"), rand=num("rand", 1.5, 0, 20), aktiv=it.get("aktiv", True) is not False)
        if q == "bild":
            bid = str(it.get("bild") or "")
            if not bilder.exists(bid):
                raise ValueError(f"{pre}: Bild {bid!r} gibt es nicht (mehr) – in der Bild-Bibliothek neu wählen")
            g.update(bild=bid, modus=choice("modus", "fehlerstreuung", bilder.MODUS_KEYS),
                     form=choice("form", "rechteck", bilder.FORM_KEYS),
                     helligkeit=num("helligkeit", 0, -100, 100), kontrast=num("kontrast", 0, -100, 100),
                     gamma=num("gamma", 1.0, 0.3, 3.0), invertieren=flag("invertieren"),
                     aufloesung=num("aufloesung", bilder.STANDARD_AUFLOESUNG, 2, 20),
                     auto=it.get("auto", True) is not False)
        elif q == "motiv":
            mid = str(it.get("motiv") or "")
            if not mt.exists(mid):
                raise ValueError(f"{pre}: Motiv {mid!r} gibt es nicht (mehr) – in der Motiv-Bibliothek neu wählen")
            g.update(motiv=mid, art=choice("art", "raster", MOTIV_ARTEN_KEYS),
                     schraffur=num("schraffur", 0.2, 0.08, 3.0),
                     aufloesung=num("aufloesung", bilder.STANDARD_AUFLOESUNG, 2, 20))
        else:
            g.update(muster=choice("muster", "mandala", mu.MUSTER_KEYS), abstand=num("abstand", 6, 1.5, 60),
                     form=choice("form", "rechteck", BEREICH_KEYS), seed=int(num("seed", 1, 0, 99999)))
        out.append(g)
    return out


# ---------------------------------------------------------------------------
# Anwenden
# ---------------------------------------------------------------------------

def teile(assemblies: Sequence[Assembly]) -> List[Dict[str, Any]]:
    """Bauteile zur Auswahl: Name, Breite, Höhe (je Name nur einmal, größtes zuerst)."""
    seen: Dict[str, Tuple[float, float]] = {}
    for asm in assemblies:
        for p in asm.parts:
            if p.name not in seen and len(p.outline) >= 3:
                seen[p.name] = p.size()
    return [dict(name=n, w=round(w, 1), h=round(h, 1))
            for n, (w, h) in sorted(seen.items(), key=lambda kv: -kv[1][0] * kv[1][1])]


def _ziele(asm: Assembly, teil: str) -> List[Part]:
    parts = [p for p in asm.parts if len(p.outline) >= 3]
    if not parts:
        return []
    if teil == "auto":
        return [max(parts, key=lambda p: abs(signed_area(p.outline)))]
    if teil == "alle":                    # Teile mit dichter Gravur (Dachziegel, Holzwand …) auslassen
        return [p for p in parts if _dichte(p) < 0.08]
    return [p for p in parts if p.name == teil]


def _dichte(p: Part) -> float:
    """Gravurlänge je mm² Fläche."""
    from steckwerk import perimeter
    a = abs(signed_area(p.outline)) or 1.0
    return sum(perimeter(s.points, s.closed) for s in p.engrave) / a


_REIHENFOLGE = {"bild": 0, "motiv": 1, "muster": 2}


def anwenden(assemblies: Sequence[Assembly], specs: Any) -> List[Assembly]:
    """Gravuren auf die Bauteile setzen (verändert die Baugruppen). Liefert dieselbe Liste."""
    specs = pruefen(specs)
    if not specs:
        return list(assemblies)
    # Fotos und Motive zuerst setzen: Muster lassen sie dann aus (Nummern bleiben wie eingegeben)
    for i, g in sorted(enumerate(specs, 1), key=lambda ig: _REIHENFOLGE[ig[1]["quelle"]]):
        if not g.get("aktiv", True):
            continue
        treffer = 0
        for asm in assemblies:
            verbund = _verbund(asm, g)
            if verbund:                   # Puzzle: ein Foto läuft über alle Teile
                treffer += len(verbund)
                note = _bild_verbund(verbund, g, i)
                if note and note not in asm.notes:
                    asm.notes.append(note)
                continue
            for p in _ziele(asm, g["teil"]):
                treffer += 1
                note = _eine(p, g, i)
                if note and note not in asm.notes:
                    asm.notes.append(note)
        if not treffer and g["teil"] == "alle":
            if assemblies:
                assemblies[0].notes.append(f"Gravur {i}: alle Teile sind schon dicht graviert – nichts ergänzt.")
        elif not treffer:
            namen = ", ".join(t["name"] for t in teile(assemblies)[:12])
            raise ValueError(f"Gravur {i}: Teil {g['teil']!r} gibt es in diesem Modell nicht – vorhanden: {namen}")
    return list(assemblies)


def _verbund(asm: Assembly, g: Dict[str, Any]) -> List[Part]:
    """Teile, die zusammen eine Fläche bilden (Puzzle: asm.params["verbund"] = Namensanfang der Teile).
    Ein Foto auf „auto“ oder „alle“ wird dann einmal über alle diese Teile gelegt statt auf jedes einzeln."""
    pre = asm.params.get("verbund") if isinstance(asm.params, dict) else None
    if not pre or g["quelle"] != "bild" or g["teil"] not in ("auto", "alle"):
        return []
    return [p for p in asm.parts if p.name.startswith(pre) and len(p.outline) >= 3]


def _zeilen_intervalle(poly: Sequence[Point], y: float) -> List[Tuple[float, float]]:
    xs = []
    n = len(poly)
    for k in range(n):
        (x0, y0), (x1, y1) = poly[k], poly[(k + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    xs.sort()
    return [(xs[k], xs[k + 1]) for k in range(0, len(xs) - 1, 2)]


def _bild_verbund(parts: Sequence[Part], g: Dict[str, Any], i: int) -> str:
    """Ein Foto über alle Teile eines Puzzles: einmal aufbereiten (gleiche Punkte-Rasterung über die Fugen),
    dann je Teil den passenden Ausschnitt nehmen und auf die Teilefläche (innen um „rand“) maskieren."""
    from steckwerk import offset_polygon
    meta = bilder.load(g["bild"])
    xs = [q[0] for p in parts for q in p.outline]
    ys = [q[1] for p in parts for q in p.outline]
    X0, Y0, X1, Y1 = min(xs), min(ys), max(xs), max(ys)
    sw, sh = float(meta["w"]), float(max(1, meta["h"]))
    if g["groesse"] > 0:                  # feste Größe: wie gewohnt um die Mitte (verschoben um x, y)
        L = g["groesse"]
        w, h = (L, L * sh / sw) if sw >= sh else (L * sw / sh, L)
        cx, cy = (X0 + X1) / 2 + g["x"], (Y0 + Y1) / 2 + g["y"]
        tl = (cx - w / 2, cy + h / 2)
        ausschnitt = None
    else:                                 # füllend: das Foto deckt das ganze Puzzle, überstehende Ränder fallen weg
        w, h = X1 - X0, Y1 - Y0
        tl = (X0, Y1)
        t = w / h
        if sw / sh > t:
            f = t / (sw / sh)
            ausschnitt = ((1 - f) / 2, 0.0, (1 + f) / 2, 1.0)
        else:
            f = (sw / sh) / t
            ausschnitt = (0.0, (1 - f) / 2, 1.0, (1 + f) / 2)
    ppmm = min(g["aufloesung"], math.sqrt(3_900_000 / max(1.0, w * h)))
    W, H, png = bilder.aufbereiten(g["bild"], w, h, ppmm=ppmm, modus=g["modus"], helligkeit=g["helligkeit"],
                                   kontrast=g["kontrast"], gamma=g["gamma"], invertieren=g["invertieren"],
                                   form=g["form"], ausschnitt=ausschnitt, auto=g["auto"])
    gw, gh, grau, alpha = bilder._png_rows(png)
    kx, ky = gw / w, gh / h               # Pixel je mm
    name = meta.get("name", g["bild"])
    rand = min(g["rand"], 0.5)            # schmale Fugen: das Bild soll über die Teile hinweg wirken
    n = 0
    for p in parts:
        innen = oriented(offset_polygon(oriented(p.outline, True), -rand, miter_limit=2.0), True) \
            if rand > 0 else oriented(p.outline, True)
        bx0, by0, bx1, by1 = bbox(innen)
        c0 = max(0, int(math.floor((bx0 - tl[0]) * kx)))
        c1 = min(gw, int(math.ceil((bx1 - tl[0]) * kx)))
        r0 = max(0, int(math.floor((tl[1] - by1) * ky)))
        r1 = min(gh, int(math.ceil((tl[1] - by0) * ky)))
        cw, ch = c1 - c0, r1 - r0
        if cw < 2 or ch < 2:
            continue
        g_out = bytearray(b"\xff" * (cw * ch))
        a_out = bytearray(cw * ch)
        voll = False
        for r in range(ch):
            y_mm = tl[1] - (r0 + r + 0.5) / ky
            src = (r0 + r) * gw
            for xa, xb in _zeilen_intervalle(innen, y_mm):
                a = max(c0, int(math.ceil((xa - tl[0]) * kx - 0.5)))
                b = min(c1, int(math.floor((xb - tl[0]) * kx - 0.5)) + 1)
                if b <= a:
                    continue
                o = r * cw
                g_out[o + a - c0:o + b - c0] = grau[src + a:src + b]
                a_out[o + a - c0:o + b - c0] = alpha[src + a:src + b] if alpha else b"\xff" * (b - a)
                voll = True
        if not voll:
            continue
        for k, av in enumerate(a_out):    # durchsichtige Pixel sind weiß (nichts gravieren)
            if av == 0:
                g_out[k] = 255
        ecke = (tl[0] + c0 / kx, tl[1] - r0 / ky)
        ecken = (ecke, (ecke[0] + cw / kx, ecke[1]), (ecke[0], ecke[1] - ch / ky))
        p.images.append(RasterImage(bilder.png_bytes(cw, ch, bytes(g_out), bytes(a_out), kx), ecken,
                                    f"Gravur {i}: {name}"))
        n += 1
    modus = dict(bilder.MODI)[g["modus"]]
    return (f"Foto „{name}“ läuft über alle {n} Puzzleteile: {w:.0f} × {h:.0f} mm, {modus}, {W} × {H} Pixel – "
            f"in XCS die Ebene „Bild“ als Bitmap gravieren.")


def _feld(p: Part, rand: float) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = p.bbox()
    return x0 + rand, y0 + rand, x1 - rand, y1 - rand


def _rahmen(p: Part, g: Dict[str, Any], seiten: float) -> Tuple[Point, float, float, float]:
    """Mitte, Breite, Höhe (mm) und Winkel (rad) eines Gegenstands mit Seitenverhältnis seiten = w/h."""
    x0, y0, x1, y1 = _feld(p, g["rand"])
    cx, cy = (x0 + x1) / 2 + g["x"], (y0 + y1) / 2 + g["y"]
    a = math.radians(g["drehung"])
    if g["groesse"] > 0:
        L = g["groesse"]
    else:                                   # automatisch: 85 % der (gedrehten) Fläche
        fw, fh = max(1.0, x1 - x0), max(1.0, y1 - y0)
        ca, sa = abs(math.cos(a)), abs(math.sin(a))
        best = 0.0
        for L in (fw, fh, math.hypot(fw, fh)):
            w, h = (L, L / seiten) if seiten >= 1 else (L * seiten, L)
            k = min(fw / max(1e-9, w * ca + h * sa), fh / max(1e-9, w * sa + h * ca))
            best = max(best, L * k)
        L = best * 0.85
    w, h = (L, L / seiten) if seiten >= 1 else (L * seiten, L)
    return (cx, cy), w, h, a


def _ecken(c: Point, w: float, h: float, a: float, spiegeln: bool) -> Tuple[Point, Point, Point]:
    ux, uy = math.cos(a) * w / 2, math.sin(a) * w / 2
    vx, vy = -math.sin(a) * h / 2, math.cos(a) * h / 2       # „oben“ im Bauteil (y nach oben)
    if spiegeln:
        ux, uy = -ux, -uy
    tl = (c[0] - ux + vx, c[1] - uy + vy)
    tr = (c[0] + ux + vx, c[1] + uy + vy)
    bl = (c[0] - ux - vx, c[1] - uy - vy)
    return tl, tr, bl


def _in_bild(pts: Sequence[Point], ecken: Tuple[Point, Point, Point]) -> List[Point]:
    """Bauteilpunkte → Bildkoordinaten in mm (Ursprung oben links, y nach unten)."""
    tl, tr, bl = ecken
    ex, ey = tr[0] - tl[0], tr[1] - tl[1]
    fx, fy = bl[0] - tl[0], bl[1] - tl[1]
    w2, h2 = ex * ex + ey * ey, fx * fx + fy * fy
    out = []
    for px, py in pts:
        dx, dy = px - tl[0], py - tl[1]
        out.append(((dx * ex + dy * ey) / w2 * math.sqrt(w2), (dx * fx + dy * fy) / h2 * math.sqrt(h2)))
    return out


def _maske(p: Part, rand: float, ecken) -> List[List[Point]]:
    """Freie Bauteilfläche (Kontur innen um rand, Durchbrüche außen um rand) in Bildkoordinaten."""
    outer = inset_polygon(p.outline, rand) if rand > 0 else oriented(p.outline, True)
    if len(outer) < 3:
        outer = oriented(p.outline, True)
    polys = [_in_bild(outer, ecken)]
    for h in p.holes:
        polys.append(_in_bild(dk.grow(h, rand), ecken))
    return polys


def _eine(p: Part, g: Dict[str, Any], i: int) -> str:
    q = g["quelle"]
    if q == "bild":
        meta = bilder.load(g["bild"])
        c, w, h, a = _rahmen(p, g, meta["w"] / max(1, meta["h"]))
        ecken = _ecken(c, w, h, a, g["spiegeln"])
        W, H, png = bilder.aufbereiten(g["bild"], w, h, ppmm=g["aufloesung"], modus=g["modus"],
                                       helligkeit=g["helligkeit"], kontrast=g["kontrast"], gamma=g["gamma"],
                                       invertieren=g["invertieren"], form=g["form"],
                                       maske=_maske(p, g["rand"], ecken), auto=g["auto"])
        p.images.append(RasterImage(png, ecken, f"Gravur {i}: {meta.get('name', g['bild'])}"))
        modus = dict(bilder.MODI)[g["modus"]]
        return (f"Bild-Gravur „{meta.get('name', g['bild'])}“ auf {p.name}: {w:.0f} × {h:.0f} mm, {modus}, "
                f"{W} × {H} Pixel – in XCS die Ebene „Bild“ als Bitmap gravieren"
                + (" (Graustufen: dort ein Rasterverfahren wählen)." if g["modus"] == "graustufen" else "."))
    if q == "motiv":
        m = mt.load(g["motiv"])
        c, w, h, a = _rahmen(p, g, m["w"] / max(1e-9, m["h"]))
        L = max(w, h)
        flip = g["spiegeln"]
        areas = [(tidy(mt.place(fl["aussen"], c[0], c[1], L, g["drehung"], flip)),
                  [tidy(mt.place(hh, c[0], c[1], L, g["drehung"], flip)) for hh in fl["loecher"]])
                 for fl in m["flaechen"]]
        lines = [mt.place(li, c[0], c[1], L, g["drehung"], flip) for li in m["linien"]]
        cv = dk.Canvas(p, margin=g["rand"])
        name = m.get("name", g["motiv"])
        if g["art"] == "raster" and areas:
            ecken = _ecken(c, w, h, a, False)
            polys = [_in_bild(o, ecken) for o, _ in areas] + [_in_bild(hh, ecken) for _, hs in areas for hh in hs]
            W, H, png = bilder.motiv_raster(polys, w, h, g["aufloesung"], maske=_maske(p, g["rand"], ecken))
            p.images.append(RasterImage(png, ecken, f"Gravur {i}: {name}"))
        else:
            for outer, holes in areas:
                cv.draw(outer, True)
                for hh in holes:
                    cv.draw(hh, True)
                if g["art"] == "flaeche":
                    for seg in _hatch([outer] + holes, g["schraffur"], g["drehung"] + 15.0):
                        cv.draw(seg)
        for li in lines:
            cv.draw(li)
        art = dict(MOTIV_ARTEN)[g["art"]]
        return f"Motiv-Gravur „{name}“ auf {p.name}: {w:.0f} × {h:.0f} mm, {art}."
    # Muster
    x0, y0, x1, y1 = _feld(p, 0.0)
    area = None
    c = ((x0 + x1) / 2 + g["x"], (y0 + y1) / 2 + g["y"])
    if g["groesse"] > 0:
        L = g["groesse"]
        area = _bereich(g["form"], c, L, math.radians(g["drehung"]))
    cv = dk.Canvas(p, margin=g["rand"], area=area, seed=g["seed"])
    rahmen = _innen_rahmen(p, c)
    if rahmen is not None:                                # Zierrahmen vorhanden: Muster nur innen
        cv.inside.append(dk._Poly(rahmen))
    cv.block_strokes(p.engrave, margin=0.7)               # vorhandene Gravuren bleiben frei
    for im in p.images:                                   # … und Bild-Gravuren
        a_, b_, c_ = im.corners
        d_ = (b_[0] + c_[0] - a_[0], b_[1] + c_[1] - a_[1])
        cv.block([a_, b_, d_, c_], 0.7)
    box = bbox(area) if area else (x0, y0, x1, y1)
    n = mu.muster(cv, g["muster"], box, g["abstand"], g["drehung"], g["seed"], zentrum=c)
    return f"Muster „{dict(mu.MUSTER)[g['muster']]}“ auf {p.name}: {n} Gravurlinien, Rapport {g['abstand']:g} mm."


def _innen_rahmen(p: Part, c: Point) -> Optional[List[Point]]:
    """Größte geschlossene Gravur um die Mitte, die mehr als 40 % des Teils umschließt (Zierrahmen),
    um 0,8 mm nach innen versetzt – sonst None."""
    from steckwerk import point_in_polygon
    full = abs(signed_area(p.outline))
    best = None
    for s in p.engrave:
        pts = s.points
        if len(pts) < 8 or not (s.closed or math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 0.05):
            continue
        a = abs(signed_area(s.points))
        if a > 0.4 * full and (best is None or a > best[0]) and point_in_polygon(c, s.points):
            best = (a, s.points)
    if best is None:
        return None
    ins = inset_polygon(oriented(clean(best[1]), True), 0.8)
    return ins if len(ins) >= 3 else None


def _bereich(form: str, c: Point, L: float, a: float) -> List[Point]:
    cx, cy = c
    if form == "kreis":
        pts = [(cx + L / 2 * math.cos(t), cy + L / 2 * math.sin(t)) for t in (2 * math.pi * k / 96 for k in range(96))]
    elif form == "oval":
        pts = [(cx + L / 2 * math.cos(t), cy + L / 3 * math.sin(t)) for t in (2 * math.pi * k / 96 for k in range(96))]
    elif form == "herz":
        pts = dk.heart(cx, cy, L, L * 0.92, 96)
    else:
        pts = [(cx - L / 2, cy - L / 2), (cx + L / 2, cy - L / 2), (cx + L / 2, cy + L / 2), (cx - L / 2, cy + L / 2)]
    if a:
        ca, sa = math.cos(a), math.sin(a)
        pts = [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]
    return oriented(clean(pts), True)
