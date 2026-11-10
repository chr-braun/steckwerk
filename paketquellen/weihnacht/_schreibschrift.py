"""
_schreibschrift.py – echte Schreibschriften für Namen: Umrisse setzen, laserfest machen, füllend gravieren.

Die Umrisse kommen aus _schreibschrift_daten.py (frei lizenzierte Schriften unter der SIL Open Font License,
siehe SCHRIFTEN-LIZENZ.txt). Gesetzt wird mit Laufweite und Unterschneidung der Schrift; die Buchstaben
verbinden sich wie geschrieben.
"""
from __future__ import annotations

import base64
import json
import math
import os
import sys
import zlib
from typing import Dict, List, Optional, Sequence, Tuple

Point = Tuple[float, float]
Poly = List[Point]
_here = os.path.dirname(os.path.abspath(__file__))

SCHRIFTEN = [("elegant", "elegant (Kalligrafie)"), ("schwungvoll", "schwungvoll"), ("rund", "rund und kräftig")]
_cache: Dict[str, dict] = {}


def _daten():
    import importlib.util
    path = os.path.join(_here, "_schreibschrift_daten.py")
    key = "swpaket_weihnacht__schreibschrift_daten"
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod.DATEN


def schrift(key: str) -> dict:
    """Schrift entpacken (einmal je Sitzung): Glyphen als Konturen in Schrifteinheiten, Grundlinie y = 0."""
    if key in _cache:
        return _cache[key]
    roh = _daten().get(key)
    if roh is None:
        raise ValueError(f"Unbekannte Schrift {key!r}")
    d = json.loads(zlib.decompress(base64.b85decode("".join(roh))).decode("utf-8"))
    glyphen = {}
    for c, (adv, konturen) in d["glyphen"].items():
        out = []
        for flach in konturen:
            x = y = 0
            pts = []
            for i in range(0, len(flach), 2):
                x += flach[i]
                y += flach[i + 1]
                pts.append((float(x), float(y)))
            out.append(pts)
        glyphen[c] = (adv, out)
    d["glyphen"] = glyphen
    _cache[key] = d
    return d


_ERSATZ = {"’": "'", "‘": "'", "‚": ",", "“": '"', "”": '"', "„": '"', "–": "-", "—": "-", "ẞ": "ß"}


def _norm(text: str) -> str:
    return "".join(_ERSATZ.get(c, c) for c in " ".join(text.split()))


def fehlende(text: str, key: str) -> List[str]:
    g = schrift(key)["glyphen"]
    return sorted({c for c in _norm(text) if c not in g})


class Satz:
    """Gesetzter Text in Schrifteinheiten: Konturen (Original-Drehsinn, für „nonzero“) und Tintenrahmen."""

    def __init__(self, text: str, key: str, sperrung: float = 0.0):
        d = schrift(key)
        self.d = d
        self.text = _norm(text)
        g, kern = d["glyphen"], d["kern"]
        x = 0.0
        self.konturen: List[Poly] = []
        self.zeichen: List[Tuple[str, float]] = []
        prev = ""
        for c in self.text:
            if c not in g:
                raise ValueError(f"Das Zeichen {c!r} gibt es in der Schreibschrift nicht")
            if prev and prev != " " and c != " ":
                x += kern.get(prev + c, 0) + sperrung * d["upm"]
            adv, kont = g[c]
            self.zeichen.append((c, x))
            for k in kont:
                self.konturen.append([(x + px, py) for px, py in k])
            x += adv
            prev = c
        pts = [p for k in self.konturen for p in k]
        if not pts:
            raise ValueError("Kein Text zum Setzen")
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        self.box = (min(xs), min(ys), max(xs), max(ys))

    @property
    def breite(self) -> float:
        return self.box[2] - self.box[0]

    @property
    def hoehe(self) -> float:
        return self.box[3] - self.box[1]

    def in_mm(self, mitte: Point, k: float) -> List[Poly]:
        """Konturen mit Maßstab k (mm je Schrifteinheit), Tintenmitte auf mitte."""
        bx = (self.box[0] + self.box[2]) / 2
        by = (self.box[1] + self.box[3]) / 2
        return [[(mitte[0] + (x - bx) * k, mitte[1] + (y - by) * k) for x, y in kp] for kp in self.konturen]

    def grundlinie(self, mitte: Point, k: float) -> float:
        """y der Grundlinie in mm bei in_mm(mitte, k)."""
        by = (self.box[1] + self.box[3]) / 2
        return mitte[1] - by * k

    def versal_mm(self, k: float) -> float:
        return self.d["versal"] * k

    def x_mm(self, k: float) -> float:
        return self.d["x"] * k


def raster(lw, polys: Sequence[Poly]):
    """Text in ein Leinwand-Raster füllen – „nonzero“ mit dem Drehsinn der Schrift (Innenformen bleiben frei)."""
    return lw.leer().fill([lw._pp(p) for p in polys if len(p) >= 3], "nonzero")


def schraffur(lw, r, abstand: float) -> List[Poly]:
    """Füllgravur: waagrechte Linien im Abstand abstand (mm) durch die gefüllten Pixel von r."""
    out: List[Poly] = []
    step = max(1, int(round(abstand / lw.px)))
    px = lw.px
    flip = False
    for row in range(step // 2, r.h, step):
        bits = r.rows[row]
        if not bits:
            continue
        y = lw.y_top - (row + 0.5) * px
        runs = []
        x = 0
        while bits:
            low = (bits & -bits).bit_length() - 1            # erstes gesetztes Bit
            bits >>= low
            x += low
            inv = ~bits
            n = (inv & -inv).bit_length() - 1                # Länge des Laufs
            if n * px >= 0.25:
                runs.append((lw.x0 + (x + 0.3) * px, lw.x0 + (x + n - 0.3) * px))
            bits >>= n
            x += n
        if flip:                                             # Zickzack-Reihenfolge, kürzere Leerfahrten
            out += [[(b, y), (a, y)] for a, b in reversed(runs)]
        else:
            out += [[(a, y), (b, y)] for a, b in runs]
        flip = not flip
    return out


def konturen_mm(lw, r) -> List[Tuple[Poly, List[Poly]]]:
    """Umrisse eines Rasters (für Konturgravur)."""
    return [(f["aussen"], f["loecher"]) for f in lw.konturen(r, 0.25)]
