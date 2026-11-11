#!/usr/bin/env python3
"""
schriften_umwandeln.py – wandelt Schreibschriften (OFL) in die Umrissdaten des Pakets „Weihnachten“ um.

  python3 packaging/schriften_umwandeln.py elegant=GreatVibes.ttf schwungvoll=Dancing-700.ttf rund=Pacifico.ttf

Ergebnis: paketquellen/weihnacht/_schreibschrift_daten.py. Die Schriften werden dabei als Polygone (in
Schrifteinheiten, Grundlinie y = 0) mit Laufweiten und Unterschneidungspaaren abgelegt – Steckwerk braucht
zur Laufzeit weder die Schriftdateien noch fontTools.

Nur für diesen Umwandlungsschritt nötig: pip install fonttools uharfbuzz
Die Unterschneidung (Kerning) wird mit HarfBuzz paarweise ausgemessen; kontextabhängige Varianten (calt,
init, fina) bleiben aus, weil sie die Buchstaben der Schreibschriften oft schlechter verbinden.
"""
from __future__ import annotations

import base64
import json
import math
import os
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(ROOT, "paketquellen", "weihnacht", "_schreibschrift_daten.py")

ZEICHEN = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÖÜäöüß0123456789"
           " -.,&'!?+:/()\"áàâéèêëíìîïóòôúùûçñÁÉÓÚÑ")
TOL = 2.0                  # Abweichung beim Glätten der Kurven in Schrifteinheiten (bei 1000 je Geviert)
VEREINFACHEN = 1.6         # danach Douglas-Peucker mit dieser Toleranz (≈ 0,03 mm bei 15 mm Versalhöhe)
KERN_MIN = 4               # kleinere Unterschneidungen sieht man nicht


def _dp(pts, tol):
    """Douglas-Peucker für einen offenen Linienzug."""
    if len(pts) < 3:
        return list(pts)
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        ax, ay = pts[i]
        bx, by = pts[j]
        L = math.hypot(bx - ax, by - ay) or 1e-9
        best, k = -1.0, -1
        for m in range(i + 1, j):
            d = abs((bx - ax) * (ay - pts[m][1]) - (ax - pts[m][0]) * (by - ay)) / L
            if d > best:
                best, k = d, m
        if best > tol:
            keep[k] = True
            stack += [(i, k), (k, j)]
    return [p for p, f in zip(pts, keep) if f]


def _umriss(glyphset, name):
    from fontTools.pens.basePen import BasePen

    class Flach(BasePen):
        def __init__(self, gs):
            super().__init__(gs)
            self.konturen = []

        def _moveTo(self, p):
            self.konturen.append([p])

        def _lineTo(self, p):
            self.konturen[-1].append(p)

        def _kurve(self, pts, f):
            p0 = self.konturen[-1][-1]
            d = max(math.hypot(q[0] - p0[0], q[1] - p0[1]) for q in pts)
            n = max(2, min(24, int(math.ceil(math.sqrt(d / TOL)))))
            for i in range(1, n + 1):
                self.konturen[-1].append(f(p0, i / n))

        def _curveToOne(self, a, b, c):
            self._kurve((a, b, c), lambda p0, t: tuple((1 - t) ** 3 * p0[k] + 3 * (1 - t) ** 2 * t * a[k]
                                                        + 3 * (1 - t) * t * t * b[k] + t ** 3 * c[k] for k in (0, 1)))

        def _qCurveToOne(self, a, b):
            self._kurve((a, b), lambda p0, t: tuple((1 - t) ** 2 * p0[k] + 2 * (1 - t) * t * a[k] + t * t * b[k]
                                                     for k in (0, 1)))

        def _closePath(self):
            pass

    pen = Flach(glyphset)
    glyphset[name].draw(pen)
    out = []
    for c in pen.konturen:
        pts = [(int(round(x)), int(round(y))) for x, y in c]
        pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        if len(pts) > 2 and pts[0] == pts[-1]:
            pts.pop()
        if len(pts) >= 3:
            far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
            pts = _dp(pts[:far + 1], VEREINFACHEN)[:-1] + _dp(pts[far:] + [pts[0]], VEREINFACHEN)[:-1]
        if len(pts) >= 3:
            flach, lx, ly = [], 0, 0                       # Differenzen packen sich viel kleiner
            for x, y in pts:
                flach += [x - lx, y - ly]
                lx, ly = x, y
            out.append(flach)
    return out


def umwandeln(pfad: str) -> dict:
    import uharfbuzz as hb
    from fontTools.ttLib import TTFont
    tt = TTFont(pfad)
    tt.flavor = None
    tmp = pfad + ".tmp.ttf"
    tt.save(tmp)
    try:
        tt = TTFont(tmp)
        gs = tt.getGlyphSet()
        cmap = tt.getBestCmap()
        hmtx = tt["hmtx"]
        face = hb.Face(hb.Blob.from_file_path(tmp))
        font = hb.Font(face)
        aus = {"calt": False, "init": False, "fina": False, "medi": False, "liga": False, "clig": False}
        glyphen, kern = {}, {}
        da = [c for c in ZEICHEN if ord(c) in cmap]
        for c in da:
            g = cmap[ord(c)]
            glyphen[c] = [hmtx[g][0], _umriss(gs, g)]
        for a in da:
            for b in da:
                if a == " " or b == " ":
                    continue
                buf = hb.Buffer()
                buf.add_str(a + b)
                buf.guess_segment_properties()
                hb.shape(font, buf, aus)
                infos, pos = buf.glyph_infos, buf.glyph_positions
                if len(infos) != 2:
                    continue
                k = pos[0].x_advance - hmtx[cmap[ord(a)]][0]
                if abs(k) >= KERN_MIN:
                    kern[a + b] = k
        os2 = tt["OS/2"]
        name = tt["name"].getDebugName(4)
        return dict(name=name, copyright=tt["name"].getDebugName(0), upm=tt["head"].unitsPerEm,
                    versal=os2.sCapHeight, x=os2.sxHeight, ober=tt["hhea"].ascent, unter=tt["hhea"].descent,
                    glyphen=glyphen, kern=kern, fehlen=[c for c in ZEICHEN if ord(c) not in cmap])
    finally:
        os.remove(tmp)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    daten = {}
    for arg in argv:
        key, pfad = arg.split("=", 1)
        daten[key] = umwandeln(pfad)
        d = daten[key]
        print(f"{key}: {d['name']} – {len(d['glyphen'])} Zeichen, {len(d['kern'])} Paare, fehlen: {''.join(d['fehlen'])!r}")
    zeilen = ['"""', "Umrissdaten der Schreibschriften für die Namensanhänger – erzeugt von packaging/schriften_umwandeln.py.",
              "Nicht von Hand bearbeiten. Die Schriften stehen unter der SIL Open Font License 1.1, siehe",
              "SCHRIFTEN-LIZENZ.txt in diesem Paket.", ""]
    for key, d in daten.items():
        zeilen.append(f"{key}: {d['copyright']}")
    zeilen += ['"""', "", "DATEN = {"]
    for key, d in daten.items():
        blob = base64.b85encode(zlib.compress(json.dumps(d, separators=(",", ":"), ensure_ascii=False)
                                              .encode("utf-8"), 9)).decode("ascii")
        teile = [blob[i:i + 110] for i in range(0, len(blob), 110)]
        zeilen.append(f"    {key!r}: (")
        zeilen += [f"        {t!r}" for t in teile]
        zeilen.append("    ),")
    zeilen.append("}")
    with open(ZIEL, "w", encoding="utf-8") as fh:
        fh.write("\n".join(zeilen) + "\n")
    print(f"→ {ZIEL} ({os.path.getsize(ZIEL) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
