"""
Eisblumenfenster – Fensterbild mit Eisblumen wie an einer gefrorenen Scheibe.

Ein gravierter Zierrahmen (Rundbogen, Spitzbogen oder Rechteck) mit Eiskristallen und Perlen, auf Wunsch mit
Fenstersprossen. Von Rahmen und Sprossen wachsen verzweigte Eisblumen-Wedel ins Fenster; sie bleiben als feine
Stege stehen, alles dazwischen wird ausgeschnitten. Jeder Startwert lässt andere Eisblumen wachsen.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List, Tuple

from steckwerk import Assembly
from pakete import flag, integer, num, sel

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_jahreszeiten_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


J = _sub("_jz")
K, E, TAU = J.K, J.E, J.TAU

FORMEN = [("rundbogen", "Rundbogen"), ("spitzbogen", "Spitzbogen"), ("rechteck", "Rechteck")]
DICHTE = [("licht", "licht (viel Durchblick)"), ("mittel", "mittel"), ("dicht", "dicht (ganz zugefroren)")]

INFO = dict(
    label="Eisblumenfenster",
    group="Jahreszeiten",
    desc="Fensterbild wie eine gefrorene Scheibe: verzweigte Eisblumen-Wedel wachsen vom gravierten Zierrahmen "
         "und den Sprossen ins Fenster, alles dazwischen wird ausgeschnitten. Jeder Startwert friert anders.",
    params=[
        sel("form", "Form", FORMEN, "rundbogen"),
        flag("sprossen", "Fenstersprossen", True),
        sel("dichte", "Eisblumen", DICHTE, "mittel"),
        integer("startwert", "Startwert", 1, 1, 9999, help="jede Zahl lässt andere Eisblumen wachsen"),
        num("groesse", "Größe", 120, 70, 250, help="Höhe ohne Öse"),
        sel("feinheit", "Feinheit", J.FEINHEIT, "mittel"),
        flag("oese", "Öse zum Aufhängen", True),
        integer("anzahl", "Anzahl", 1, 1, 8, help="mehrere Fenster bekommen je einen eigenen Startwert"),
    ],
)

UEBERSETZUNG = {"en": dict(J.FEINHEIT_EN, **{
    "Eisblumenfenster": "Frost-flower window",
    "Fensterbild wie eine gefrorene Scheibe: verzweigte Eisblumen-Wedel wachsen vom gravierten Zierrahmen "
    "und den Sprossen ins Fenster, alles dazwischen wird ausgeschnitten. Jeder Startwert friert anders.":
        "Window picture like a frozen pane: branching frost-flower fronds grow from the engraved frame and the "
        "glazing bars into the window, everything in between is cut out. Every seed freezes differently.",
    "Form": "Shape", "Rundbogen": "Round arch", "Spitzbogen": "Pointed arch", "Rechteck": "Rectangle",
    "Fenstersprossen": "Glazing bars", "Eisblumen": "Frost flowers", "licht (viel Durchblick)": "light (lots of view)",
    "dicht (ganz zugefroren)": "dense (frozen over)", "Startwert": "Seed",
    "jede Zahl lässt andere Eisblumen wachsen": "every number grows different frost flowers",
    "Höhe ohne Öse": "height without loop",
    "mehrere Fenster bekommen je einen eigenen Startwert": "several windows each get their own seed",
    "Aufhängen: Band oder Kordel durch die Öse ziehen.": "To hang: thread a ribbon or cord through the loop.",
})}


# --------------------------------------------------------------------------------------------------
# Form
# --------------------------------------------------------------------------------------------------

def _umriss(form: str, Wd: float, H: float):
    """Fensterumriss (CCW), unten auf y = 0, mittig um x = 0."""
    h = Wd / 2
    if form == "rundbogen":
        ys = H - h
        pts = [(-h, 0.0), (h, 0.0)] + [(h * math.cos(math.pi * k / 60), ys + h * math.sin(math.pi * k / 60))
                                       for k in range(61)]
    elif form == "spitzbogen":
        ys = H - math.sqrt(3) * h
        pts = [(-h, 0.0), (h, 0.0)]
        pts += [(-h + 2 * h * math.cos(math.pi / 3 * k / 30), ys + 2 * h * math.sin(math.pi / 3 * k / 30))
                for k in range(31)]
        pts += [(h - 2 * h * math.cos(math.pi / 3 * k / 30), ys + 2 * h * math.sin(math.pi / 3 * k / 30))
                for k in range(29, -1, -1)]
    else:
        r = 0.05 * H
        pts = []
        for cx, cy, a0 in ((h - r, r, -90), (h - r, H - r, 0), (-h + r, H - r, 90), (-h + r, r, 180)):
            pts += [(cx + r * math.cos(math.radians(a0 + 90 * k / 10)), cy + r * math.sin(math.radians(a0 + 90 * k / 10)))
                    for k in range(11)]
    pts = [p for i, p in enumerate(pts) if i == 0 or math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) > 1e-6]
    return J.oriented(pts, True)


# --------------------------------------------------------------------------------------------------
# Eisblumen
# --------------------------------------------------------------------------------------------------

def _breite(s: float, hb0: float, w: float) -> float:
    """Halbe Federbreite an der Stelle s (0 = Ansatz, 1 = Spitze): dünner Stiel, dann breit, spitz auslaufend."""
    auf = min(1.0, max(0.0, (s - 0.06) / 0.28)) ** 0.8
    return hb0 * auf * (1 - s) ** 0.65 + w * 0.6


def _feder(r, p0, ang: float, L: float, tiefe: int, w: float, S: float, federn: list, huellen: list,
           abstand: float, mutter=None) -> bool:
    """Eine Eisblumen-Feder: geschnittene Silhouette mit gezahntem Rand um einen leicht gebogenen Kiel, darauf
    fein gravierte Strahlen. Bei tiefe > 0 zweigen kleinere Federn ab. Kollidiert die Feder mit einer schon
    gesetzten, wird sie nicht gesetzt (False). federn sammelt (Silhouette, Gravurlinien), unten → oben."""
    from steckwerk import point_in_polygon
    n = 28
    krumm = r.uniform(-1.0, 1.0) * 0.35 / max(L, 1.0)
    kiel = [p0]
    a = ang
    step = L / n
    for _ in range(n):
        a += krumm * step
        kiel.append((kiel[-1][0] + step * math.cos(a), kiel[-1][1] + step * math.sin(a)))
    winkel = math.radians(r.uniform(54, 60))
    hb0 = min(0.095 * L, 0.04 * S + 1.0) + w * 0.5         # größte halbe Breite
    zahn = max(1.25 * w, 0.022 * S)                        # Zahnteilung am Rand
    # Silhouette: halbe Breite über die Länge, Rand gezahnt (Zähne zeigen zur Spitze)
    links, rechts, strahlen = [], [], []
    Lk = K.path_len(kiel)
    dicht = K.resample(kiel, Lk / 160)
    for i, q in enumerate(dicht):
        s = i / (len(dicht) - 1)
        j = min(len(dicht) - 2, i)
        d = math.atan2(dicht[j + 1][1] - dicht[j][1], dicht[j + 1][0] - dicht[j][0])
        hb = _breite(s, hb0, w)
        phase = (s * Lk / zahn) % 1.0
        hz = hb + zahn * 0.6 * (phase - 0.5) * min(1.0, (1 - s) * 4, max(0.0, (hb - w) / zahn))
        for sg, seite in ((1, links), (-1, rechts)):
            aa = d + sg * math.pi / 2
            seite.append((q[0] + hz * math.cos(aa), q[1] + hz * math.sin(aa)))
    huelle = J.oriented(rechts + [kiel[-1]] + list(reversed(links)), True)
    # Kollision (gegen die Hüllen der anderen Federn, um ‚abstand‘ aufgeweitet geprüft)
    probe = K.resample(huelle + [huelle[0]], 1.0)
    grenze = 0.0 if mutter is None and tiefe < 0 else 0.18      # Überlappen erlaubt, Stapeln nicht
    for h, _ in huellen:
        if h is mutter:
            continue
        xs = [q[0] for q in h]
        ys = [q[1] for q in h]
        box = (min(xs) - abstand, min(ys) - abstand, max(xs) + abstand, max(ys) + abstand)
        nah = [q for q in probe if box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3]]
        if not nah:
            continue
        wachs = J.versetzt(h, abstand)
        if sum(1 for q in nah if point_in_polygon(q, wachs)) > grenze * len(probe):
            return False
    gr: List = [(dicht, False)]
    for sg in (1, -1):                                     # feiner Doppelkiel
        gr.append(([(q[0] - sg * 0.45 * math.sin(math.atan2(dicht[min(i + 1, len(dicht) - 1)][1] - q[1], dicht[min(i + 1, len(dicht) - 1)][0] - q[0] + 1e-9)), q[1] + sg * 0.45 * math.cos(math.atan2(dicht[min(i + 1, len(dicht) - 1)][1] - q[1], dicht[min(i + 1, len(dicht) - 1)][0] - q[0] + 1e-9))) for i, q in enumerate(dicht[:int(len(dicht) * 0.8)])], False))
    # gravierte Strahlen: dicht nebeneinander, leicht zur Spitze gebogen, bis knapp an den Rand
    teil = max(0.62, 0.0065 * S)
    m = int(Lk / teil)
    for k in range(2, m):
        s = k / m
        if s > 0.96:
            break
        i = int(s * (len(dicht) - 1))
        q = dicht[i]
        j = min(len(dicht) - 2, i)
        d = math.atan2(dicht[j + 1][1] - dicht[j][1], dicht[j + 1][0] - dicht[j][0])
        hb = _breite(s, hb0, w)
        lb = (hb - 0.5) / math.sin(winkel)
        if lb < 0.8:
            continue
        for sg in (1, -1):
            a1 = d + sg * winkel
            mid = (q[0] + lb * 0.5 * math.cos(a1 + sg * 0.1), q[1] + lb * 0.5 * math.sin(a1 + sg * 0.1))
            e = (q[0] + lb * math.cos(a1 - sg * 0.05), q[1] + lb * math.sin(a1 - sg * 0.05))
            gr.append(([q, mid, e], False))
            if k % 3 == 0 and lb > 3:                       # kleine Fiedern an jedem dritten Strahl
                f = (q[0] + lb * 0.55 * math.cos(a1), q[1] + lb * 0.55 * math.sin(a1))
                a2 = a1 - sg * 0.7
                gr.append(([f, (f[0] + lb * 0.22 * math.cos(a2), f[1] + lb * 0.22 * math.sin(a2))], False))
    eintrag = (huelle, gr)
    huellen.append((huelle, tiefe == 0))
    pos = len(federn)
    federn.append(eintrag)
    if tiefe > 0:
        stellen = (0.24, 0.44, 0.64) if L > 0.3 * S else ((0.28, 0.54) if L > 0.15 * S else (0.36,))
        sg = 1 if r.random() < 0.5 else -1
        for s0 in stellen:
            s0 += r.uniform(-0.04, 0.04)
            sg = -sg
            i = int(s0 * n)
            d = math.atan2(kiel[i + 1][1] - kiel[i][1], kiel[i + 1][0] - kiel[i][0])
            vorher = len(federn)
            for _ in range(2):
                if _feder(r, kiel[i], d + sg * math.radians(r.uniform(34, 44)), L * (0.62 - 0.5 * s0) * r.uniform(0.9, 1.1), tiefe - 1,
                          w, S, federn, huellen, abstand, huelle):
                    break
                sg = -sg
            if len(federn) > vorher:                     # Zweig unter die Mutterfeder legen
                federn.insert(pos, federn.pop())
                pos += 1
    return True


def _anker(feld, n: int, r, unten_mehr: bool = True):
    """n Startpunkte auf dem Feldrand mit Richtung nach innen (Bogenmaß); unten und an den Seiten mehr."""
    pts = list(feld) + [feld[0]]
    L = K.path_len(pts)
    dicht = K.resample(pts, L / 600)
    ys = [q[1] for q in dicht]
    y0, y1 = min(ys), max(ys)
    gew = []
    for q in dicht:
        h = (q[1] - y0) / max(1e-6, y1 - y0)
        gew.append((1.6 - 1.2 * h) if unten_mehr else 1.0)
    tot = sum(gew)
    out = []
    for k in range(n):
        ziel = (k + r.uniform(0.25, 0.75)) / n * tot
        acc = 0.0
        for i, g in enumerate(gew):
            acc += g
            if acc >= ziel:
                break
        a, b = dicht[i - 1], dicht[(i + 1) % len(dicht)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        innen = math.atan2(tx, -ty)          # CCW-Umriss: links von der Laufrichtung ist innen
        out.append((dicht[i], innen))
    return out


def _fenster(cfg, name: str, form: str, S: float, sprossen: bool, dichte: str, seed: int, feinheit: str, oese: bool,
             notes: List[str]):
    w = J.steg_breite(cfg, feinheit)
    H = S
    Wd = 0.70 * S
    umriss = _umriss(form, Wd, H)
    fb = max(3.2 * w + 1.2, 0.075 * S)                      # Rahmenbreite
    feld = J.versetzt(umriss, -fb)
    fig = K.Figur()
    top = max(q[1] for q in umriss)
    umriss_ex, oese_loch = J.umriss_mit_oese(fig, umriss, top - 0.4, S / 2, w, oese)
    r = K.rng(seed, "eisblumen", form)
    # Sprossen
    xs = [q[0] for q in feld]
    ys = [q[1] for q in feld]
    sw = max(1.5 * w, 0.02 * S)
    y_q = min(ys) + 0.46 * (max(ys) - min(ys)) if form == "rechteck" else min(ys) + 0.42 * (max(ys) - min(ys))
    stege = []
    if sprossen:
        stege.append(K.rect(-sw / 2, min(ys) - 1, sw, max(ys) - min(ys) + 2))
        stege.append(K.rect(min(xs) - 1, y_q - sw / 2, max(xs) - min(xs) + 2, sw))
    # Eisblumen: Federn von unten und den Seiten, die sich nicht überkreuzen
    versuche = dict(licht=11, mittel=20, dicht=30)[dichte]
    breit = max(xs) - min(xs)
    Lmax = breit * dict(licht=0.6, mittel=0.68, dicht=0.74)[dichte]
    abstand = max(w + 0.6, 1.8)
    federn: list = []
    huellen: list = []
    for p, a in _anker(feld, versuche, r):
        p = (p[0] - 1.0 * math.cos(a), p[1] - 1.0 * math.sin(a))      # im Rahmen verankert
        for _ in range(5):
            aa = a + math.radians(r.uniform(-42, 42))
            if _feder(r, p, aa, Lmax * r.uniform(0.6, 1.0), 2, w, S, federn, huellen, abstand):
                break
    for p, a in _anker(feld, versuche, r):                 # kleine Federn in die Lücken
        p = (p[0] - 1.0 * math.cos(a), p[1] - 1.0 * math.sin(a))
        _feder(r, p, a + math.radians(r.uniform(-50, 50)), Lmax * r.uniform(0.25, 0.45), 0, w, S, federn, huellen,
               abstand)
    if sprossen:                                           # auch an den Sprossen friert es
        for k in range(dict(licht=4, mittel=8, dicht=12)[dichte]):
            if k % 2 == 0:
                sg = 1 if k % 4 == 0 else -1
                p = (0.0, min(ys) + r.uniform(0.1, 0.9) * (max(ys) - min(ys)))
                a = 0.0 if sg > 0 else math.pi
            else:
                sg = 1 if k % 4 == 1 else -1
                p = (r.uniform(min(xs), max(xs)) * 0.85, y_q)
                a = sg * math.pi / 2
            for _ in range(3):
                if _feder(r, p, a + math.radians(r.uniform(-50, 50)), Lmax * r.uniform(0.35, 0.55), 0, w, S,
                          federn, huellen, abstand):
                    break
    eis = K.Figur()
    for h, _ in federn:
        eis.add(h)
    eis.add(*stege)
    gravur = J.nur_in(J.blaetter_gravur(federn), J.versetzt(feld, -0.3))
    # Raster: Rahmen + (Eisblumen ∩ Feld)
    x0, y0, x1, y1 = fig.bbox()
    px = max(0.055, min(0.075, max(x1 - x0, y1 - y0) / 2000.0))
    lw = E.Leinwand((x0 - 2, y0 - 2, x1 + 2, y1 + 2), px)
    mat = lw.figur(fig)
    feld_r = lw.flaechen([feld])
    mat = E._andnot(mat, feld_r).union(E._and(lw.figur(eis), feld_r))
    if oese_loch:
        mat = E._andnot(mat, lw.flaechen([oese_loch]))
    part = J.teil(cfg, name, lw, mat, notes)
    part = J.scharf(cfg, part, [oese_loch] if oese_loch else [], umriss_ex)
    J.gravieren(part, lw, _rahmen_gravur(umriss, fb, S, form, sprossen, sw, y_q, feld) + gravur)
    return part


def _rahmen_gravur(umriss, fb: float, S: float, form: str, sprossen: bool, sw: float, y_q: float, feld):
    """Zierrahmen: Doppellinien an beiden Kanten, dazwischen Eiskristalle mit Perlen."""
    lin: List = []
    d = max(0.7, 0.008 * S)
    for off in (-d * 1.3, -d * 2.3, -(fb - d * 1.3), -(fb - d * 2.3)):
        lin.append((J.zu(J.versetzt(umriss, off)), False))
    mitte = J.versetzt(umriss, -fb / 2)
    pts = mitte + [mitte[0]]
    L = K.path_len(pts)
    rk = (fb - 4.6 * d) / 2 * 0.92
    n = max(8, int(L / (rk * 4.2)))
    stellen = K.resample(pts, L / n)[:n]
    for i, q in enumerate(stellen):
        a = stellen[(i + 1) % n]
        t = math.atan2(a[0] - q[0], a[1] - q[1])
        for p, c in J.eiskristall(rk, 2 if i % 2 else 0):
            lin.append(([(q[0] + x, q[1] + y) for x, y in J.drehen(p, t)], c))
        b = ((q[0] + a[0]) / 2, (q[1] + a[1]) / 2)
        for f in (-0.18, 0.0, 0.18):
            m = (b[0] + (a[0] - q[0]) * f, b[1] + (a[1] - q[1]) * f)
            lin.append((J.kreis(m[0], m[1], max(0.3, rk * 0.12) * (1.4 if f == 0 else 1.0), 10), True))
    return lin


def build(cfg, name: str = "eisblumen", form: str = "rundbogen", sprossen: bool = True, dichte: str = "mittel",
          startwert: int = 1, groesse: float = 120.0, feinheit: str = "mittel", oese: bool = True, anzahl: int = 1):
    J.auswahl(form, FORMEN, "Form")
    J.auswahl(dichte, DICHTE, "Eisblumen")
    J.auswahl(feinheit, J.FEINHEIT, "Feinheit")
    S = cfg.s(groesse)
    if S < 65:
        raise ValueError("Das Fenster ist zu klein für Eisblumen – mindestens 70 mm Höhe")
    asm = Assembly(name, params=dict(form=form, sprossen=sprossen, dichte=dichte, startwert=startwert, groesse=S,
                                     feinheit=feinheit))
    notes: List[str] = []
    for i in range(max(1, int(anzahl))):
        tag = name if anzahl <= 1 else f"{name}_{i + 1}"
        asm.parts.append(_fenster(cfg, tag, form, S, sprossen, dichte, int(startwert) + i, feinheit, oese, notes))
        if anzahl > 1:
            asm.notes.append(f"{tag}: Startwert {int(startwert) + i}.")
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    if oese:
        asm.notes.append("Aufhängen: Band oder Kordel durch die Öse ziehen.")
    asm.notes.append("Tipp: Am Fenster mit Gegenlicht wirken die Eisblumen am schönsten. Die feinen Wedel beim "
                     "Herauslösen von hinten drücken, nicht ziehen.")
    return asm
