"""
Laternen-Häuschen – ein Lichthaus aus Karton zum Falten, mit Fenstern für Transparentpapier.

Die vier Wände hängen in einem Stück zusammen (Vorderseite mit Tür, Seite, Rückseite, Seite, Klebelasche),
unten sitzen Bodenlaschen, die sich wie bei einer Faltschachtel ineinander legen und in der Mitte Platz für
ein LED-Teelicht lassen. Das Dach ist ein eigenes Teil mit Mittelfalz, auf Wunsch mit Zuckerguss-Kante und
gravierten Dachziegeln. Alle Falzlinien werden als feine Gravur geritzt.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, Part
from pakete import flag, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_papier_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


F_ = _sub("_form")
E, K, W = F_.E, F_.K, F_.W

FENSTER = [("sprossen", "Bogenfenster mit Sprossen"), ("rund", "Rundfenster mit Kreuz"),
           ("herz", "Herzen"), ("stern", "Sterne")]

INFO = dict(
    label="Laternen-Häuschen",
    group="Papier",
    desc="Lichthaus aus Karton zum Falten: vier Wände in einem Stück, Dach mit Zuckerguss-Kante, Fenster zum "
         "Hinterkleben mit Transparentpapier und Platz für ein LED-Teelicht.",
    params=[
        num("breite", "Breite", 80, 50, 140),
        num("tiefe", "Tiefe", 70, 50, 140),
        num("hoehe", "Wandhöhe", 75, 50, 140),
        sel("fenster", "Fenster", FENSTER, "sprossen"),
        flag("zuckerguss", "Zuckerguss-Kante am Dach", True),
        flag("verzierung", "Läden, Ziegel und Tür gravieren", True),
    ],
)

UEBERSETZUNG = {"en": {
    "Laternen-Häuschen": "Lantern house", "Papier": "Paper",
    "Lichthaus aus Karton zum Falten: vier Wände in einem Stück, Dach mit Zuckerguss-Kante, Fenster zum "
    "Hinterkleben mit Transparentpapier und Platz für ein LED-Teelicht.":
        "Folding card light house: four walls in one piece, roof with icing edge, windows to back with "
        "tracing paper and room for an LED tea light.",
    "Breite": "Width", "Tiefe": "Depth", "Wandhöhe": "Wall height", "Fenster": "Windows",
    "Bogenfenster mit Sprossen": "Arched windows with bars", "Rundfenster mit Kreuz": "Round windows with cross",
    "Herzen": "Hearts", "Sterne": "Stars", "Zuckerguss-Kante am Dach": "Icing edge on the roof",
    "Läden, Ziegel und Tür gravieren": "Engrave shutters, tiles and door",
}}


def _herz(cx, cy, s, n=60):
    f = s / 32
    return [(cx + 16 * math.sin(t) ** 3 * f,
             cy + (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * f)
            for t in [2 * math.pi * i / n for i in range(n)]]


def _bogen(x, y, w, h, n=18):
    """Fenster mit Rundbogen oben, unten links bei (x, y)."""
    r = w / 2
    pts = [(x, y), (x + w, y)]
    pts += [(x + r + r * math.cos(a), y + h - r + r * math.sin(a)) for a in [math.pi * i / n for i in range(n + 1)]]
    return pts


def _fenster(fig: "K.Figur", cx: float, y: float, w: float, h: float, art: str, steg: float):
    """Schneidet ein Fenster (Mitte unten bei cx, y); gibt den Umriss für die Gravur zurück."""
    if art == "sprossen":
        p = _bogen(cx - w / 2, y, w, h)
        fig.cut(p)
        fig.add(K.rect(cx - steg / 2, y - 0.5, steg, h + 1))
        fig.add(K.rect(cx - w / 2 - 0.5, y + (h - w / 2) * 0.62 - steg / 2, w + 1, steg))
    elif art == "rund":
        p = F_.kreis(cx, y + w / 2, w / 2, 40)
        fig.cut(p)
        fig.add(K.rect(cx - steg / 2, y - 0.5, steg, w + 1))
        fig.add(K.rect(cx - w / 2 - 0.5, y + w / 2 - steg / 2, w + 1, steg))
    elif art == "herz":
        p = _herz(cx, y + w * 0.5, w * 1.05)
        fig.cut(p)
    else:
        p = F_.stern(cx, y + w * 0.5, w * 0.6, w * 0.27, 5)
        fig.cut(p)
    return p


def _wand(fig, x0, b, h, art, steg, tuer, ritz, verz):
    """Fenster (und Tür) einer Wand von x0 bis x0+b."""
    w = min(15.0, b * 0.2) if art in ("sprossen",) else min(14.0, b * 0.19)
    fh = w * 1.45 if art == "sprossen" else w
    rand = max(6.0, b * 0.1)
    if tuer:
        tw, th = min(18.0, b * 0.24), min(h * 0.55, 30.0)
        fig.cut(_bogen(x0 + b / 2 - tw / 2, 2.5, tw, th))
        frei = (b - tw) / 2 - rand
        if verz:
            ritz.append((_bogen(x0 + b / 2 - tw / 2 - 2.0, 0.6, tw + 4.0, th + 3.0)[1:] + [(x0 + b / 2 - tw / 2 - 2.0, 0.6)], False))
        w = min(w, (frei - 3.0) / (1.9 if verz else 1.1))
        fh = w * 1.45 if art == "sprossen" else w
        if w >= 7.0:
            for s in (-1, 1):
                cx = x0 + b / 2 + s * (tw / 2 + frei / 2)
                _fenster(fig, cx, h * 0.42, w, fh, art, steg)
                _laeden(ritz, cx, h * 0.42, w, fh, verz)
        return
    n = max(1, int((b - 2 * rand) // (w * (2.5 if verz else 1.8))))
    for i in range(n):
        cx = x0 + rand + (b - 2 * rand) * (i + 0.5) / n
        _fenster(fig, cx, h * 0.38, w, fh, art, steg)
        _laeden(ritz, cx, h * 0.38, w, fh, verz)


def _laeden(ritz, cx, y, w, h, verz):
    if not verz:
        return
    ritz.append(([(cx - w / 2 - 1.5, y - 2.0), (cx + w / 2 + 1.5, y - 2.0)], False))   # Fensterbank
    for s in (-1, 1):
        a = cx + s * (w / 2 + 2.0)
        b = cx + s * (w / 2 + 2.0 + w * 0.42)
        ritz.append(([(a, y), (b, y), (b, y + h * 0.8), (a, y + h * 0.8)], True))


def _haus(cfg, B, D, H, art, verz, notes, wände=(0, 1, 2, 3), name="haus") -> Part:
    steg = max(1.4, cfg.min_web + cfg.kerf + 0.6)
    G = B / 2                                    # Giebelhöhe bei 45°
    lasche = 8.0
    boden = min(B, D) * 0.36
    xs = [0.0]
    for i in wände:
        xs.append(xs[-1] + (B if i % 2 == 0 else D))
    fig = K.Figur()
    ritz: List = []
    for j, i in enumerate(wände):
        x0, x1 = xs[j], xs[j + 1]
        b = x1 - x0
        giebel = i % 2 == 0
        if giebel:
            fig.add([(x0, 0), (x1, 0), (x1, H), (x0 + b / 2, H + G), (x0, H)])
            # Klebelaschen an den Giebelschrägen
            for (ax, ay), (bx, by) in [((x0, H), (x0 + b / 2, H + G)), ((x0 + b / 2, H + G), (x1, H))]:
                dx, dy = bx - ax, by - ay
                L = math.hypot(dx, dy)
                nx, ny = -dy / L * 7.0, dx / L * 7.0
                ein = 7.0 / L
                fig.add([(ax, ay), (bx, by), (bx - dx * ein + nx, by - dy * ein + ny),
                         (ax + dx * ein + nx, ay + dy * ein + ny)])
                ritz.append(([(ax, ay), (bx, by)], False))
        else:
            fig.add(K.rect(x0, 0, b, H))
        # Bodenlasche
        tief = boden if giebel else min(D, B) * 0.36
        fig.add([(x0 + 2, 0.5), (x1 - 2, 0.5), (x1 - 2 - tief * 0.35, -tief), (x0 + 2 + tief * 0.35, -tief)])
        ritz.append(([(x0 + 2, 0), (x1 - 2, 0)], False))
        if j:
            ritz.append(([(x0, 0), (x0, H)], False))
        _wand(fig, x0, b, H, art, steg, i == 0, ritz, verz)
        if giebel and b > 40:
            gy = H + G * 0.38
            gw = min(10.0, b * 0.13)
            if art == "herz":
                fig.cut(_herz(x0 + b / 2, gy, gw * 1.1))
            elif art == "stern":
                fig.cut(F_.stern(x0 + b / 2, gy, gw * 0.62, gw * 0.28, 5))
            else:
                fig.cut(F_.kreis(x0 + b / 2, gy, gw / 2, 32))
    # seitliche Klebelasche
    x4 = xs[-1]
    fig.add([(x4 - 0.5, 0), (x4 + lasche, 4), (x4 + lasche, H - 4), (x4 - 0.5, H)])
    ritz.append(([(x4, 0), (x4, H)], False))
    lw = E.Leinwand((-4, -boden - 4, x4 + lasche + 4, H + G + 12), W.px_fuer(x4))
    mat = lw.figur(fig).open(lw.px_fuer(0.5))
    p = E.teil_aus_raster(name, lw, mat, cfg.min_web, cfg.kerf, notes)
    from models import _deko as dk
    cv = dk.Canvas(p, margin=0.2)
    for pts, closed in ritz:
        cv.draw(pts, closed)
    return p


def _dach(cfg, B, D, zuckerguss, verz, notes) -> Part:
    ue = max(5.0, B * 0.07)
    L = math.hypot(B / 2, B / 2) + ue
    Bd = D + 2 * ue
    fig = K.Figur()
    if zuckerguss:
        nz = max(4, int(round(Bd / 11)))
        r = Bd / nz / 2
        unten = [(-Bd / 2 + r * (2 * i + 1) + r * math.cos(a), -L + r * 0.2 - r * 0.9 * math.sin(a))
                 for i in range(nz) for a in [math.pi + math.pi * j / 10 for j in range(11)]]
        unten = [(x, y) for x, y in unten]
        unten.sort(key=lambda q: q[0])
        oben = [(x, -y) for x, y in reversed(unten)]
        fig.add([(-Bd / 2, -L + r * 0.2)] + unten + [(Bd / 2, -L + r * 0.2), (Bd / 2, L - r * 0.2)] + oben
                + [(-Bd / 2, L - r * 0.2)])
    else:
        fig.add(K.rect(-Bd / 2, -L, Bd, 2 * L))
    lw = E.Leinwand((-Bd / 2 - 4, -L - 6, Bd / 2 + 4, L + 6), W.px_fuer(2 * L))
    mat = lw.figur(fig).open(lw.px_fuer(0.6))
    p = E.teil_aus_raster("dach", lw, mat, cfg.min_web, cfg.kerf, notes)
    from models import _deko as dk
    cv = dk.Canvas(p, margin=0.4)
    cv.draw([(-Bd / 2, 0.0), (Bd / 2, 0.0)])                     # Firstfalz
    if verz:
        reihe = 7.0
        for s in (-1, 1):
            j = 0
            y = 4.0
            while y < L - (9.0 if zuckerguss else 4.0):
                off = (j % 2) * 4.0
                pts = []
                x = -Bd / 2 + 1 - off
                while x < Bd / 2 - 1:
                    for a in range(9):
                        t = a / 8
                        pts.append((x + 8.0 * t, s * (y + 2.2 * math.sin(math.pi * t))))
                    x += 8.0
                cv.draw([(px, py) for px, py in pts if -Bd / 2 < px < Bd / 2])
                y += reihe
                j += 1
    return p


def build(cfg, name: str = "laternenhaus", breite: float = 80.0, tiefe: float = 70.0, hoehe: float = 75.0,
          fenster: str = "sprossen", zuckerguss: bool = True, verzierung: bool = True):
    if fenster not in dict(FENSTER):
        raise ValueError(f"Unbekannte Fensterform {fenster!r}")
    B, D, H = cfg.s(breite), cfg.s(tiefe), cfg.s(hoehe)
    asm = Assembly(name, params=dict(breite=B, tiefe=D, hoehe=H, fenster=fenster))
    notes: List[str] = []
    if 2 * (B + D) + 8.0 <= cfg.sheet_width - 2 * cfg.sheet_margin - 10:
        asm.parts.append(_haus(cfg, B, D, H, fenster, verzierung, notes))
    else:                                        # zu lang fürs Blatt: zwei Hälften mit je einer Klebelasche
        asm.parts.append(_haus(cfg, B, D, H, fenster, verzierung, notes, (0, 1), "haus_vorne"))
        asm.parts.append(_haus(cfg, B, D, H, fenster, verzierung, notes, (2, 3), "haus_hinten"))
        notes.append("Das Haus ist in zwei Hälften geteilt; jede Lasche klebt an die Giebelwand der anderen Hälfte.")
    asm.parts.append(_dach(cfg, B, D, zuckerguss, verzierung, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    asm.notes += [
        "Falzlinien nur ritzen (Gravur mit wenig Leistung), dann alle Falze nach hinten knicken.",
        "Transparentpapier von innen hinter die Fenster kleben, bevor du das Haus schließt.",
        "Seitliche Lasche an die Vorderwand kleben, Bodenlaschen ineinanderlegen, Dach auf die Giebellaschen kleben.",
        "Nur mit LED-Teelicht beleuchten, niemals mit einer echten Kerze.",
    ]
    if cfg.T > 1.0:
        asm.notes.append(f"Tipp: Gedacht für Karton 200–300 g (ca. 0,3–0,5 mm) – eingestellt sind {cfg.T:g} mm.")
    return asm
