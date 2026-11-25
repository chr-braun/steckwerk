"""
Blütenmandala – Frühlingsmedaille aus Blütenblättern, fein graviert.

Außen ein Kranz spitzer Blütenblätter mit ausgeschnittenen Tropfen, darunter eine zweite gravierte Blätterlage,
ein Ring aus ausgeschnittenen Tropfen und Perlen, ein gravierter Frühlingskranz (Blütenranke, Tulpen oder
Kirschzweige) und in der Mitte eine große Blüte, ein Schmetterling oder ein Name.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly
from pakete import flag, integer, num, sel, txt

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
K, P, TAU = J.K, J.P, J.TAU

KRANZ = [("ranke", "Blütenranke"), ("tulpen", "Tulpen"), ("kirsch", "Kirschzweige")]
MITTE = [("bluete", "große Blüte"), ("schmetterling", "Schmetterling"), ("text", "Name oder Gruß")]
ZAHL = [("8", "8 Blätter"), ("12", "12 Blätter"), ("16", "16 Blätter")]

INFO = dict(
    label="Blütenmandala",
    group="Jahreszeiten",
    desc="Frühlingsmedaille: ein Kranz spitzer Blütenblätter mit ausgeschnittenen Tropfen, darunter eine gravierte "
         "Blätterlage und ein Frühlingskranz aus Blütenranke, Tulpen oder Kirschzweigen, in der Mitte Blüte, "
         "Schmetterling oder Name.",
    params=[
        sel("kranz", "Kranz", KRANZ, "ranke"),
        sel("mitte", "Mitte", MITTE, "bluete"),
        txt("text", "Text", "Frühling", maxlen=20, help="leer = ohne", when={"mitte": ["text"]}),
        sel("zaehlig", "Blütenblätter", ZAHL, "12"),
        num("groesse", "Größe", 100, 60, 250, help="Durchmesser ohne Öse"),
        sel("feinheit", "Feinheit", J.FEINHEIT, "mittel"),
        flag("oese", "Öse zum Aufhängen", True),
        integer("anzahl", "Anzahl", 1, 1, 8),
    ],
)

UEBERSETZUNG = {"en": dict(J.FEINHEIT_EN, **{
    "Blütenmandala": "Blossom mandala",
    "Frühlingsmedaille: ein Kranz spitzer Blütenblätter mit ausgeschnittenen Tropfen, darunter eine gravierte "
    "Blätterlage und ein Frühlingskranz aus Blütenranke, Tulpen oder Kirschzweigen, in der Mitte Blüte, "
    "Schmetterling oder Name.":
        "Spring medal: a ring of pointed petals with cut-out drops, an engraved second layer of petals and a spring "
        "wreath of blossom vine, tulips or cherry twigs, with a flower, butterfly or name in the centre.",
    "Kranz": "Wreath", "Blütenranke": "Blossom vine", "Tulpen": "Tulips", "Kirschzweige": "Cherry twigs",
    "Mitte": "Centre", "große Blüte": "large flower", "Schmetterling": "Butterfly", "Name oder Gruß": "Name or greeting",
    "Blütenblätter": "Petals", "8 Blätter": "8 petals", "12 Blätter": "12 petals", "16 Blätter": "16 petals",
    "Durchmesser ohne Öse": "diameter without loop",
    "Aufhängen: Band oder Kordel durch die Öse ziehen.": "To hang: thread a ribbon or cord through the loop.",
})}


def _blaetterrand(R: float, Rd: float, n: int) -> list:
    """Umriss aus n bauchigen, spitz zulaufenden Blütenblättern (Spitze genau oben), CCW."""
    pts = []
    m = n * 48
    for k in range(m):
        t = TAU * k / m
        u = ((n * t / TAU + 0.5) % 1.0) * 2 - 1            # −1 … 1 über ein Blatt, 0 = Spitze
        f = math.cos(math.pi * u / 2) ** 0.62 * (1 - 0.32 * abs(u))
        pts.append(P(Rd + (R - Rd) * f, t))
    return J.oriented(pts, True)


def _ranke(rm: float, band: float, n: int) -> List:
    """Wellenranke mit Blüten und Blättern."""
    stapel = []
    welle = []
    m = 360
    amp = band * 0.3
    for k in range(m + 1):
        t = TAU * k / m
        welle.append(P(rm + amp * (math.sin(n * t) + 0.18 * math.sin(2 * n * t)), t))
    stapel.append((None, [(welle, False), ([P(rm + amp * (math.sin(n * TAU * k / m) + 0.18 * math.sin(2 * n * TAU * k / m)) + 0.5, TAU * k / m)
                                            for k in range(m + 1)], False)]))
    for k in range(n):
        t = TAU * (k + 0.25) / n                       # Wellenberg außen
        tb = TAU * (k + 0.75) / n                      # Wellental innen
        # Blätter am Wellenhang
        for tt, aus in ((TAU * (k + 0.05) / n, 1), (TAU * (k + 0.5) / n, -1)):
            c = P(rm + amp * (math.sin(n * tt) + 0.18 * math.sin(2 * n * tt)), tt)
            L = band * 0.56
            stapel.append(J.platziert(J.blatt(L, L * 0.42, 5), c[0], c[1], tt + aus * math.radians(55)))
        for tt, sg in ((TAU * (k + 0.38) / n, 1), (TAU * (k + 0.88) / n, -1)):   # Rankenspirale
            c = P(rm + amp * (math.sin(n * tt) + 0.18 * math.sin(2 * n * tt)), tt)
            sp = []
            r0 = band * 0.16
            a0 = tt + (math.pi / 2 if sg > 0 else -math.pi / 2)
            mz = (c[0] - r0 * math.sin(a0), c[1] - r0 * math.cos(a0))
            for j in range(48):
                f = j / 47
                a = a0 + sg * f * 1.75 * TAU
                rr = r0 * (1 - 0.82 * f)
                sp.append((mz[0] + rr * math.sin(a), mz[1] + rr * math.cos(a)))
            stapel.append(([], [(sp, False)]))
        c = P(rm + amp, t)
        stapel.append(J.platziert(J.bluete(band * 0.3, 5, True), c[0], c[1], t))
        c = P(rm - amp, tb)
        stapel.append(J.platziert(J.bluete(band * 0.2, 5, False, staub=6), c[0], c[1], tb))
    return J.blaetter_gravur([(s[0] or [], s[1]) for s in stapel])


def _tulpen(rm: float, band: float, n: int) -> List:
    """Tulpenkranz: Tulpen mit Stiel und Blättern aus einem inneren Rankenkreis, dazwischen Blüten und Knospen."""
    stapel = []
    r0 = rm - band * 0.46
    stapel.append(([], [(J.zu(J.kreis(0, 0, r0, 0)), False), (J.zu(J.kreis(0, 0, r0 + 0.5, 0)), False)]))
    for k in range(n):
        t = TAU * k / n
        h = band * 0.46
        fuss = P(r0, t)
        kelch = P(rm + band * 0.0, t)
        stiel = K.bez(fuss, P((r0 + rm) / 2, t + 0.06 * band / rm), kelch, 10)
        stapel.append(([], [(stiel, False)]))
        for sg in (1, -1):
            c = P(r0 + band * 0.04, t)
            stapel.append(J.platziert(J.blatt(band * 0.52, band * 0.17, 4, 1.3), c[0], c[1], t + sg * math.radians(24)))
        stapel.append(J.platziert(J.tulpe(h), kelch[0], kelch[1], t))
        tz = TAU * (k + 0.5) / n
        c = P(rm + band * 0.28, tz)
        stapel.append(J.platziert(J.bluete(band * 0.15, 5, True, staub=6), c[0], c[1], tz))
        for sg in (1, -1):
            c = P(r0 + band * 0.12, tz + sg * 0.12 * band / rm)
            stapel.append(J.platziert(J.blatt(band * 0.3, band * 0.13, 3), c[0], c[1], tz + sg * math.radians(35)))
        c = P(r0 + band * 0.02, tz)
        stapel.append((J.kreis(c[0], c[1], band * 0.06, 12), J.beere(c[0], c[1], band * 0.06)))
    return J.blaetter_gravur(stapel)


def _kirsch(rm: float, band: float, n: int) -> List:
    """Kirschzweige im Kreis: gebogene Äste mit Blüten, Knospen und Blättern."""
    stapel = []
    zweige = max(4, n // 2)
    for k in range(zweige):
        t0 = TAU * k / zweige
        t1 = t0 + TAU / zweige * 1.02
        ast = K.bez3(P(rm - band * 0.3, t0), P(rm + band * 0.35, t0 + (t1 - t0) * 0.3),
                     P(rm - band * 0.25, t0 + (t1 - t0) * 0.7), P(rm + band * 0.12, t1), 30)
        stapel.append(([], [(ast, False), ([(x * 1.012, y * 1.012) for x, y in ast[3:-6]], False)]))
        for i, f in enumerate((0.12, 0.3, 0.48, 0.66, 0.84)):
            q = ast[int(f * (len(ast) - 1))]
            a = math.atan2(q[0], q[1])
            aus = 1 if i % 2 == 0 else -1
            c = P(math.hypot(*q) + aus * band * 0.24, a + 0.03)
            stapel.append(([], [([q, c], False)]))
            if i in (1, 3):
                stapel.append(J.platziert(J.blatt(band * 0.42, band * 0.18, 4), q[0], q[1], a + aus * 1.15))
            if i == 4:
                knospe = J.bluetenblatt(band * 0.22, band * 0.14)
                stapel.append(J.platziert((knospe, [(knospe, True), ([(0, band * 0.03), (0, band * 0.17)], False)]),
                                          c[0], c[1], a))
            else:
                stapel.append(J.platziert(J.bluete(band * (0.24 if i % 2 == 0 else 0.19), 5, True, staub=8),
                                          c[0], c[1], a + i))
    return J.blaetter_gravur(stapel)


def _medaille(cfg, name: str, S: float, kranz: str, mitte: str, text: str, n: int, feinheit: str, oese: bool,
              notes: List[str]):
    R = S / 2
    w = J.steg_breite(cfg, feinheit)
    Rd = 0.82 * R
    fig = K.Figur()
    rand = _blaetterrand(R, Rd, n)
    umriss, oese_loch = J.umriss_mit_oese(fig, rand, R - 0.4, R, w, oese)
    lin: List = []
    lin.append((J.zu(J.versetzt(rand, -max(0.8, 0.016 * R))), False))
    # Tropfen in den Blütenblättern, mit Begleitlinie und Adern
    r_sp = R - max(1.6 * w, 0.07 * R)
    r_fu = Rd - 0.02 * R
    b = min(0.34 * TAU * Rd / n, 0.55 * (r_sp - r_fu))
    for k in range(n):
        t = TAU * k / n
        if oese and k == 0:
            lin.append(([P(r_fu, t), P(r_sp, t)], False))
            continue
        tr = J.tropfen(P(r_sp, t), P(r_fu, t), b)
        fig.cut(tr)
        lin.append((J.versetzt(tr, max(0.7, 0.014 * R)), True))
        for sg in (1, -1):
            for f in (0.22, 0.42, 0.62, 0.8):
                lin.append((K.bez(P(r_fu - 0.01 * R, t + sg * f * 0.28 * TAU / n),
                                  P((r_fu + r_sp) / 2, t + sg * f * 0.75 * TAU / n),
                                  P(r_sp - 0.02 * R, t + sg * f * 0.95 * TAU / n), 12), False))
    # zweite Blätterlage (graviert), schaut zwischen den äußeren Blättern hervor
    r_b0 = 0.64 * R
    stapel = []
    for lage, (f_w, ph, r_top) in enumerate(((0.62, 0.5, Rd - 0.01 * R), (0.42, 0.0, r_fu - 0.06 * R))):
        for k in range(n):
            t = TAU * (k + ph) / n
            L = r_top - r_b0
            bw = min(f_w * TAU * (r_b0 + L * 0.6) / n, 0.62 * L)
            bl = J.bluetenblatt(L, bw)
            um = J.setzen(bl, *P(r_b0, t), 1.0, t)
            ad = [(J.setzen([(0, L * 0.1), (0, L * 0.86)], *P(r_b0, t), 1.0, t), False)]
            for f in (0.28, 0.46, 0.64):
                for sg in (1, -1):
                    ad.append((J.setzen(K.bez((0, L * f), (sg * bw * 0.18, L * (f + 0.06)), (sg * bw * 0.34, L * (f + 0.16)), 6),
                                        *P(r_b0, t), 1.0, t), False))
            stapel.append((um, [(um, True)] + ad))
    lin += J.blaetter_gravur(stapel[n:] + stapel[:n])
    lin += J.doppelkreis(r_b0, max(0.55, 0.011 * R))
    # Ring aus Tropfen und Perlen (ausgeschnitten)
    r_r1 = r_b0 - max(1.6, 0.028 * R)
    r_r0 = r_r1 - 0.068 * R
    m = 2 * n
    for k in range(m):
        t = TAU * (k + 0.5) / m
        if k % 2 == 0:
            fig.cut(J.tropfen(P(r_r1, t), P(r_r0, t), min(0.5 * TAU * r_r0 / m, 0.62 * (r_r1 - r_r0))))
        else:
            rr = max(1.15, min(0.24 * TAU * r_r0 / m, 0.3 * (r_r1 - r_r0)))
            c = P(r_r0 + rr + 0.2, t)
            fig.cut(J.kreis(c[0], c[1], rr, 20))
            lin.append((J.kreis(c[0], c[1], rr + max(0.6, 0.012 * R), 20), True))
    lin += J.perlenkreis(r_r0 - max(1.3, 0.026 * R), max(0.25, 0.005 * R), max(0.9, 0.02 * R))
    # Frühlingskranz
    k1 = r_r0 - max(2.2, 0.045 * R)
    rc = (0.23 if mitte != "text" else 0.27) * R
    k0 = rc + max(1.2, 0.02 * R)
    rm, band = (k0 + k1) / 2, k1 - k0
    zahl = dict(ranke=max(5, n // 2), tulpen=max(10, n), kirsch=n)[kranz]
    gr = dict(ranke=_ranke, tulpen=_tulpen, kirsch=_kirsch)[kranz](rm, band, zahl)
    lin += J.nur_in(gr, J.kreis(0, 0, k1 + band * 0.05, 0))
    # Mitte
    lin += J.doppelkreis(rc, max(0.55, 0.011 * R))
    ri = rc - max(1.0, 0.02 * R)
    if mitte == "bluete":
        _, g = J.bluete(ri * 0.95, max(6, min(n, 10)), False, 2, 16)
        lin += g
    elif mitte == "schmetterling":
        lin += J.schmetterling(ri * 1.6)
    else:
        if text:
            lin += J.text(text, 0, 0, 1.75 * ri, 0.95 * ri, 0.32 * ri, 1.9)
        for sg in (1, -1):
            _, g = J.bluete(ri * 0.15, 5, True, staub=6)
            lin += [([(x, y + sg * ri * 0.74) for x, y in p], c) for p, c in g]
    part, _ = J.bauen(cfg, name, fig, lin, notes, oese_loch, umriss=umriss)
    return part


def build(cfg, name: str = "bluetenmandala", kranz: str = "ranke", mitte: str = "bluete", text: str = "Frühling",
          zaehlig: str = "12", groesse: float = 100.0, feinheit: str = "mittel", oese: bool = True, anzahl: int = 1):
    J.auswahl(kranz, KRANZ, "Kranz")
    J.auswahl(mitte, MITTE, "Mitte")
    zaehlig = J.auswahl(str(zaehlig), ZAHL, "Blütenblätter")
    J.auswahl(feinheit, J.FEINHEIT, "Feinheit")
    text = J.text_pruefen(text) if mitte == "text" else ""
    S = cfg.s(groesse)
    if S < 55:
        raise ValueError("Das Mandala ist zu klein für so feine Arbeit – mindestens 60 mm")
    asm = Assembly(name, params=dict(kranz=kranz, mitte=mitte, zaehlig=zaehlig, groesse=S, feinheit=feinheit))
    notes: List[str] = []
    for i in range(max(1, int(anzahl))):
        tag = name if anzahl <= 1 else f"{name}_{i + 1}"
        asm.parts.append(_medaille(cfg, tag, S, kranz, mitte, text, int(zaehlig), feinheit, oese, notes))
    for t in dict.fromkeys(notes):
        asm.notes.append(t)
    if oese:
        asm.notes.append("Aufhängen: Band oder Kordel durch die Öse ziehen.")
    asm.notes.append("Tipp: Die Blütenadern mit wenig Leistung gravieren; in Birke oder Pappel 3 mm wirkt das Mandala "
                     "besonders hell und frühlingshaft.")
    return asm
