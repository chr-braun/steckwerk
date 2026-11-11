"""
Vier in einer Reihe – Stehgestell aus vier Lagen mit 7 × 6 Feldern und Auslöse-Schieber.
Vorder- und Rückwand mit Sichtlöchern, dazwischen zwei Lagen Stege (Spalten). Unten läuft ein
Schieber durch einen Kanal; zieht man ihn heraus, fallen alle Scheiben auf einmal unten heraus.
Die Wand steht mit Steckfüßen in zwei Fußplatten.
"""
from __future__ import annotations

import math
import os
import sys
from typing import List

from steckwerk import Assembly, Part, rect
from pakete import flag, num, sel, txt

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

INFO = dict(
    label="Vier in einer Reihe",
    group="Spiele",
    desc="Stehgestell mit 7 Spalten und 6 Reihen, 42 Scheiben mit Motiv und einem Schieber unten: "
         "herausziehen, und alle Scheiben fallen heraus. Oben auf Wunsch Spaltenzahlen und ein Name.",
    params=[
        num("scheibe", "Scheiben-Ø", 30, 24, 34),
        sel("motiv_a", "Scheiben Spieler 1", S.MOTIVE, "ring", section="Gestaltung"),
        sel("motiv_b", "Scheiben Spieler 2", S.MOTIVE, "stern", section="Gestaltung"),
        sel("rand", "Zierrand", S.RAENDER, "linie", section="Gestaltung"),
        flag("zahlen", "Spaltenzahlen 1–7", True, section="Gestaltung"),
        txt("beschriftung", "Beschriftung", "", section="Beschriftung", help="oben auf der Vorderwand"),
    ],
)

UEBERSETZUNG = {"en": dict(S.UEBERSETZUNG_GEMEINSAM, **{
    "Vier in einer Reihe": "Four in a row",
    "Stehgestell mit 7 Spalten und 6 Reihen, 42 Scheiben mit Motiv und einem Schieber unten: "
    "herausziehen, und alle Scheiben fallen heraus. Oben auf Wunsch Spaltenzahlen und ein Name.":
        "Standing frame with 7 columns and 6 rows, 42 discs with a motif and a slider at the bottom: "
        "pull it out and all discs drop out. Optional column numbers and a name at the top.",
    "Scheiben-Ø": "Disc diameter", "Scheiben Spieler 1": "Discs player 1", "Scheiben Spieler 2": "Discs player 2",
    "Spaltenzahlen 1–7": "Column numbers 1–7", "oben auf der Vorderwand": "at the top of the front wall",
    "Die Rückwand mit der gravierten Seite nach innen legen und die Stege beider Mittellagen auf die "
    "Markierungen leimen, die obere Lage deckungsgleich darauf. Den Kanal unten frei von Leim halten.":
        "Lay the back wall engraved side up (it faces inwards) and glue the strips of both middle layers onto "
        "the marks, the second layer exactly on top. Keep the channel at the bottom free of glue.",
    "Vorderwand aufleimen, mit Zwingen pressen. Die beiden Schieberstreifen aufeinanderleimen.":
        "Glue the front wall on and clamp. Glue the two slider strips together.",
    "Die Steckfüße unten in die Fußplatten stecken (bei Bedarf ein Tropfen Leim). Den Schieber von rechts "
    "einschieben, bis der Griff anliegt.":
        "Push the feet tabs into the foot plates (a drop of glue if needed). Insert the slider from the right "
        "until the handle touches.",
    "Zum Leeren den Schieber nach rechts herausziehen – alle Scheiben fallen unten heraus.":
        "To empty, pull the slider out to the right – all discs drop out at the bottom.",
})}


def masse(cfg, d: float, zahlen: bool, text: bool) -> dict:
    T = cfg.T
    cw = d + 1.6                                   # Spaltenbreite (Scheibe mit Luft)
    sw = max(5.0, 1.6 * T)                         # Steg zwischen den Spalten
    sp = max(12.0, 3.4 * T)                        # Seitenpfosten
    tw = sp - 6.0                                  # Steckfuß
    W = 2 * sp + 7 * cw + 6 * sw
    yl = d + 6.0                                   # Auslauf unten (Fußplatte hebt um T an)
    hb = max(8.0, 2.5 * T)                         # Schieberhöhe
    kanal = hb + 0.6
    band = 7.0 + (8.0 if zahlen else 0.0) + (max(11.0, 0.4 * d) if text else 0.0)
    H = yl + hb + 6 * d + band
    return dict(T=T, cw=cw, sw=sw, sp=sp, tw=tw, W=W, H=H, yl=yl, hb=hb, kanal=kanal, d=d,
                xs=[sp + i * (cw + sw) + cw / 2 for i in range(7)],
                ys=[yl + hb + d / 2 + k * d for k in range(6)])


def _wand_umriss(M) -> list:
    T, W, H, sp, tw, yl = M["T"], M["W"], M["H"], M["sp"], M["tw"], M["yl"]
    a0, a1 = sp / 2 - tw / 2, sp / 2 + tw / 2
    return [(a0, -T), (a1, -T), (a1, 0), (sp, 0), (sp, yl), (W - sp, yl), (W - sp, 0), (W - a1, 0), (W - a1, -T),
            (W - a0, -T), (W - a0, 0), (W, 0), (W, H), (0, H), (0, 0), (a0, 0)]


def _pfosten(name: str, M, x0: float, unten: bool) -> Part:
    T, sp, tw = M["T"], M["sp"], M["tw"]
    if unten:
        a0, a1 = x0 + sp / 2 - tw / 2, x0 + sp / 2 + tw / 2
        pts = [(a0, -T), (a1, -T), (a1, 0), (x0 + sp, 0), (x0 + sp, M["yl"]), (x0, M["yl"]), (x0, 0), (a0, 0)]
    else:
        y0 = M["yl"] + M["kanal"]
        pts = [(x0, y0), (x0 + sp, y0), (x0 + sp, M["H"]), (x0, M["H"])]
    return Part(name, pts)


def _steg(name: str, M, x0: float) -> Part:
    y0, H, sw = M["yl"] + M["kanal"], M["H"], M["sw"]
    f = min(1.5, sw / 3)
    return Part(name, [(x0, y0), (x0 + sw, y0), (x0 + sw, H - f), (x0 + sw - f, H), (x0 + f, H), (x0, H - f)])


def _schieber(name: str, M) -> Part:
    W, hb = M["W"], M["hb"]
    r = hb / 2 + 5.0
    xe = W + 2.0
    pts = [(-3.0, 0.0), (xe, 0.0), (xe, hb / 2 - r)]
    cx = xe + 6.0
    for k in range(25):
        a = -math.pi / 2 + math.pi * k / 24
        pts.append((cx + r * math.cos(a), hb / 2 + r * math.sin(a)))
    pts += [(xe, hb / 2 + r), (xe, hb), (-3.0, hb)]
    return Part(name, pts)


def _fuss(name: str, M) -> Part:
    from models import _deko as dk
    T, sp, tw = M["T"], M["sp"], M["tw"]
    wf = sp + 22.0
    lf = max(70.0, 0.3 * M["H"])
    p = Part(name, dk.rounded_rect(-wf / 2, -lf / 2, wf / 2, lf / 2, 6.0))
    gx, gy = tw + 0.3, 4 * T + 0.3
    p.add_hole(rect(-gx / 2, -gy / 2, gx, gy))
    return p


def build(cfg, name: str = "vierreihe", scheibe: float = 30.0, motiv_a: str = "ring", motiv_b: str = "stern",
          rand: str = "linie", zahlen: bool = True, beschriftung: str = ""):
    from models import _deko as dk
    dk.check_choice("Scheiben Spieler 1", motiv_a, S.MOTIVE)
    dk.check_choice("Scheiben Spieler 2", motiv_b, S.MOTIVE)
    dk.check_choice("Zierrand", rand, S.RAENDER)
    d = cfg.s(scheibe)
    if not 24 <= d <= 34:
        raise ValueError("Vier in einer Reihe: Scheiben-Ø muss zwischen 24 und 34 mm liegen")
    M = masse(cfg, d, zahlen, bool(beschriftung.strip()))
    W, H, T = M["W"], M["H"], M["T"]
    S.platte_passt(cfg, W, H + T, "Vier in einer Reihe")
    S.platte_passt(cfg, W + 2 + 6 + M["hb"] / 2 + 5, M["hb"] + 10, "Vier in einer Reihe (Schieber)")
    hd = 0.78 * d

    vorne = Part(f"{name}_vorne", _wand_umriss(M))
    hinten = Part(f"{name}_hinten", _wand_umriss(M))
    for p in (vorne, hinten):
        for x in M["xs"]:
            for y in M["ys"]:
                p.add_hole(dk.circle(x, y, hd / 2, 0.04, ccw=False))

    # Vorderwand gestalten
    cv = dk.Canvas(vorne, margin=1.2, hole_margin=1.0)
    for x in M["xs"]:
        for y in M["ys"]:
            cv.draw(dk.circle(x, y, hd / 2 + 1.5, 0.04), True)
    ins = 3.5
    S.zierrand(cv, dk.rounded_rect(ins, M["yl"] + ins, W - ins, H - ins, 3.0), rand, 3.0)
    y_oben = M["ys"][-1] + hd / 2 + 1.5
    if zahlen:
        for i, x in enumerate(M["xs"]):
            S.text(cv, str(i + 1), x, y_oben + 4.6, 10, 4.6, 4.6)
        y_oben += 8.0
    if beschriftung.strip():
        S.text(cv, beschriftung, W / 2, (y_oben + H - ins - 3) / 2 + 0.5, W - 2 * ins - 16, H - ins - 3 - y_oben - 2,
               10.0)

    # Rückwand: Leimmarkierungen für die Stege (gravierte Seite zeigt nach innen)
    cvh = dk.Canvas(hinten, margin=0.6, hole_margin=0.6)
    y0 = M["yl"] + M["kanal"]
    for i in range(1, 7):
        x0 = M["sp"] + i * (M["cw"] + M["sw"]) - M["sw"]
        cvh.draw([(x0, y0), (x0 + M["sw"], y0), (x0 + M["sw"], H), (x0, H)], True)
    for x0 in (0.0, W - M["sp"]):
        cvh.draw([(x0 + M["sp"] * (x0 == 0), y0), (x0 + M["sp"] * (x0 == 0), H)])
        cvh.draw([(x0 + M["sp"] * (x0 == 0), 0.6), (x0 + M["sp"] * (x0 == 0), M["yl"])])
    cvh.draw([(0.6, y0), (M["sp"], y0)])
    cvh.draw([(W - M["sp"], y0), (W - 0.6, y0)])

    asm = Assembly(name, params=dict(scheibe=d, breite=W, hoehe=H + T, spalte=M["cw"]))
    asm.parts += [vorne, hinten]
    for lage in (1, 2):
        asm.parts += [_pfosten(f"{name}_pfosten_links_unten_{lage}", M, 0.0, True),
                      _pfosten(f"{name}_pfosten_links_oben_{lage}", M, 0.0, False),
                      _pfosten(f"{name}_pfosten_rechts_unten_{lage}", M, W - M["sp"], True),
                      _pfosten(f"{name}_pfosten_rechts_oben_{lage}", M, W - M["sp"], False)]
        for i in range(1, 7):
            x0 = M["sp"] + i * (M["cw"] + M["sw"]) - M["sw"]
            asm.parts.append(_steg(f"{name}_steg{i}_{lage}", M, x0))
    asm.parts += [_schieber(f"{name}_schieber_{k}", M) for k in (1, 2)]
    asm.parts += [_fuss(f"{name}_fuss_{k}", M) for k in (1, 2)]
    for i in range(21):
        asm.parts.append(S.stein(f"{name}_scheibe_a{i + 1}", d, motiv_a))
    for i in range(21):
        asm.parts.append(S.stein(f"{name}_scheibe_b{i + 1}", d, motiv_b))
    asm.notes += [
        "Die Rückwand mit der gravierten Seite nach innen legen und die Stege beider Mittellagen auf die "
        "Markierungen leimen, die obere Lage deckungsgleich darauf. Den Kanal unten frei von Leim halten.",
        "Vorderwand aufleimen, mit Zwingen pressen. Die beiden Schieberstreifen aufeinanderleimen.",
        "Die Steckfüße unten in die Fußplatten stecken (bei Bedarf ein Tropfen Leim). Den Schieber von rechts "
        "einschieben, bis der Griff anliegt.",
        "Zum Leeren den Schieber nach rechts herausziehen – alle Scheiben fallen unten heraus.",
    ]
    return asm
