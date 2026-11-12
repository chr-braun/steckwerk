"""
vorschau.py – kleine Vorschaubilder der Vorlagen für die Galerie in Steckwerk Desktop.

Ein Vorschaubild ist ein stark vereinfachtes SVG der ersten Platte mit den Startwerten: Schnitt (schwarz) und
Gravur (blau), auf den Inhalt zugeschnitten, Koordinaten in mm auf eine Nachkommastelle gerundet. Es hat dieselbe
Form wie ein Blattplan der Engine (Gruppen „layer-schnitt“ und „layer-gravur“), die App liest es mit demselben Parser.

Reihenfolge: mitgelieferte Bilder im Ordner `vorschau/` (erzeugt von packaging/vorschaubilder.py), dann der
Zwischenspeicher unter ~/.steckwerk/vorschau, sonst wird das Bild einmal berechnet und dort abgelegt – so haben
auch neue Vorlagen und Pakete sofort eine Vorschau.
"""
from __future__ import annotations

import math
import os
import re
import threading
from typing import List, Optional, Tuple

ROOT = os.path.dirname(os.path.abspath(__file__))
MITGELIEFERT = os.path.join(ROOT, "vorschau")
_ID = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
_PFAD = re.compile(r'<path\s[^>]*?d="([^"]+)"[^>]*?>')
_STRICH = re.compile(r'stroke="(#[0-9A-Fa-f]{6})"')
_ZAHL = re.compile(r"-?\d+(?:\.\d+)?(?:e-?\d+)?")
_LOCK = threading.Lock()

Linie = Tuple[List[Tuple[float, float]], bool]


def zwischenspeicher() -> str:
    home = os.environ.get("STECKWERK_HOME") or os.path.expanduser("~/.steckwerk")
    return os.path.join(home, "vorschau")


def _teilpfade(d: str) -> List[Linie]:
    out: List[Linie] = []
    for stueck in re.split(r"(?=[Mm])", d):
        zahlen = [float(z) for z in _ZAHL.findall(stueck)]
        pts = list(zip(zahlen[0::2], zahlen[1::2]))
        if len(pts) >= 2:
            out.append((pts, stueck.strip().upper().endswith("Z")))
    return out


def _abstand(p, a, b) -> float:
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def vereinfachen(pts: List[Tuple[float, float]], eps: float) -> List[Tuple[float, float]]:
    """Douglas-Peucker ohne Rekursion."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        best, k = 0.0, -1
        for m in range(i + 1, j):
            dist = _abstand(pts[m], pts[i], pts[j])
            if dist > best:
                best, k = dist, m
        if best > eps and k > 0:
            keep[k] = True
            stack += [(i, k), (k, j)]
    return [p for p, f in zip(pts, keep) if f]


def kompakt(svg: str, grenze: int = 5000) -> str:
    """Blattplan der Engine → kleines Vorschau-SVG (siehe Modulbeschreibung)."""
    schnitt: List[Linie] = []
    gravur: List[Linie] = []
    for m in _PFAD.finditer(svg):
        tag = m.group(0)
        s = _STRICH.search(tag)
        ziel = gravur if (s and s.group(1).upper() == "#0000FF") else schnitt
        ziel += _teilpfade(m.group(1))
    punkte = [p for pts, _ in schnitt + gravur for p in pts]
    if not punkte:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>'
    x0, y0 = min(p[0] for p in punkte), min(p[1] for p in punkte)
    b, h = max(p[0] for p in punkte) - x0, max(p[1] for p in punkte) - y0

    def pfad(linien: List[Linie], eps: float, minimum: float) -> Tuple[str, int]:
        teile, n = [], 0
        for pts, zu in linien:
            if minimum and max(max(p[0] for p in pts) - min(p[0] for p in pts),
                               max(p[1] for p in pts) - min(p[1] for p in pts)) < minimum:
                continue
            v = vereinfachen(pts, eps)
            if len(v) < 2:
                continue
            n += len(v)
            teile.append("M" + " L".join(f"{x - x0:.1f},{y - y0:.1f}" for x, y in v) + (" Z" if zu else ""))
        return " ".join(teile), n

    eps_s, eps_g = 0.12, 0.2
    for _ in range(6):
        d_s, n_s = pfad(schnitt, eps_s, 0)
        d_g, n_g = pfad(gravur, eps_g, 0.6)
        if n_s + n_g <= grenze:
            break
        eps_s, eps_g = eps_s * 1.8, eps_g * 1.8
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {b:.1f} {h:.1f}">']
    if d_g:
        out.append(f'<g id="layer-gravur" stroke="#0000FF" fill="none"><path d="{d_g}"/></g>')
    if d_s:
        out.append(f'<g id="layer-schnitt" stroke="#000000" fill="none"><path d="{d_s}"/></g>')
    out.append("</svg>")
    return "".join(out)


def berechnen(model_id: str) -> Optional[str]:
    import service
    try:
        res = service.generate({"model": model_id, "params": {}, "config": {}})
        sheets = [s for a in res.get("assemblies") or [] for s in a.get("sheets") or []]
        return kompakt(sheets[0]["svg"]) if sheets else None
    except Exception:                                        # noqa: BLE001 – eine Vorschau darf nie stören
        return None


def svg(model_id: str, berechnen_erlaubt: bool = True) -> Optional[str]:
    """Vorschau-SVG der Vorlage oder None, wenn es die Vorlage nicht gibt oder sie sich nicht berechnen lässt."""
    import service
    if not _ID.match(model_id or "") or model_id not in service.MODEL_INFO:
        return None
    for ordner in (MITGELIEFERT, zwischenspeicher()):
        pfad = os.path.join(ordner, model_id + ".svg")
        if os.path.isfile(pfad):
            with open(pfad, encoding="utf-8") as fh:
                return fh.read()
    if not berechnen_erlaubt:
        return None
    with _LOCK:                                              # höchstens eine Berechnung auf einmal: schont alte Rechner
        pfad = os.path.join(zwischenspeicher(), model_id + ".svg")
        if os.path.isfile(pfad):
            with open(pfad, encoding="utf-8") as fh:
                return fh.read()
        text = berechnen(model_id)
        if text:
            try:
                os.makedirs(os.path.dirname(pfad), exist_ok=True)
                with open(pfad, "w", encoding="utf-8") as fh:
                    fh.write(text)
            except OSError:
                pass
        return text
