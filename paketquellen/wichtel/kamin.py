"""
Wichtelkamin – Paket „Wichtel“ (edles Zubehör, ab 1.1.0).

Kamin zum Stecken in zwei Lagen: ein stabiler Korpus (Front mit Rundbogen, Rückwand mit Ziegeln, zwei
Seiten, Sockel mit gefliester Herdplatte und Kaminsims mit verzierter Kante) und davor eine filigrane
Zierblende mit Fries, Pilastern und Schlussstein. Dazu Feuer mit Holzscheiten, ein Funkengitter, Kerzen-
leuchter und Kaminuhr auf dem Sims, eine Tannengirlande und Strümpfe mit Namen.
"""
import importlib.util
import math
import os

from steckwerk import Assembly, JointFeature, Part, oriented
from pakete import flag, integer, num, sel, txt

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_kamin",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
M = _m.markt()
MO = _m.moebel()
E = _m.modul("_edel")
Z, K = M.Z, M.K

AUFSAETZE = [("keine", "nichts"), ("kerzen", "Kerzenleuchter"), ("uhr", "Kaminuhr"), ("beides", "Uhr und Kerzen")]

UEBERSETZUNG = {"en": {
    "Wichtelkamin": "Elf fireplace", "Wichtel": "Elves",
    "Kamin in zwei Lagen: Korpus zum Stecken und filigrane Zierblende, dazu Feuer, Funkengitter, Kerzen, "
    "Kaminuhr, Girlande und Strümpfe mit Namen.":
        "Two-layer fireplace: slot-together body and a filigree front, plus fire, spark screen, candles, mantel "
        "clock, garland and stockings with names.",
    "Breite": "Width", "Höhe": "Height", "Tiefe": "Depth", "Fries": "Frieze", "Simskante": "Mantel edge",
    "Feuer mit Holzscheiten": "Fire with logs", "Funkengitter": "Spark screen", "Auf dem Sims": "On the mantel",
    "nichts": "nothing", "Kerzenleuchter": "Candlesticks", "Kaminuhr": "Mantel clock",
    "Uhr und Kerzen": "Clock and candles", "Girlande": "Garland", "Strümpfe": "Stockings",
    "Namen auf den Strümpfen": "Names on the stockings", "keine": "none",
    "Mit Komma trennen, z. B. Ida, Paul": "Separate with commas, e.g. Ida, Paul",
    "Ausstattung": "Accessories",
}}

INFO = dict(
    label="Wichtelkamin", group="Wichtel",
    desc="Kamin in zwei Lagen: Korpus zum Stecken und filigrane Zierblende, dazu Feuer, Funkengitter, Kerzen, "
         "Kaminuhr, Girlande und Strümpfe mit Namen.",
    params=[
        num("breite", "Breite", 70, 45, 250),
        num("hoehe", "Höhe", 56, 36, 200),
        num("tiefe", "Tiefe", 22, 14, 100),
        sel("fries", "Fries", Z.BORDUEREN, "ranke"),
        sel("kante", "Simskante", [("keine", "keine")] + Z.KANTEN, "perlen"),
        flag("feuer", "Feuer mit Holzscheiten", True, section="Ausstattung"),
        flag("gitter", "Funkengitter", True, section="Ausstattung"),
        sel("aufsatz", "Auf dem Sims", AUFSAETZE, "beides", section="Ausstattung"),
        flag("girlande", "Girlande", True, section="Ausstattung"),
        integer("struempfe", "Strümpfe", 3, 0, 6, section="Ausstattung"),
        txt("namen", "Namen auf den Strümpfen", "Ida, Paul, Mia", help="Mit Komma trennen, z. B. Ida, Paul",
            section="Ausstattung", when={"struempfe": [1, 2, 3, 4, 5, 6]}),
    ],
)
INFO["params"] = M.mit_massstab("kamin", INFO["params"])
UEBERSETZUNG["en"].update(M.EN)


def _front_umriss(Wb, Hb, Wo, Ho):
    """Front des Korpus: Rechteck mit Rundbogen-Öffnung bis zum Boden (CCW)."""
    r = Wo / 2
    hs = Ho - r
    bogen = [(r * math.cos(a), hs + r * math.sin(a)) for a in (math.pi * (1 - i / 32) for i in range(33))]
    return [(-Wb / 2, 0.0), (-Wo / 2, 0.0)] + bogen + [(Wo / 2, 0.0), (Wb / 2, 0.0), (Wb / 2, Hb), (-Wb / 2, Hb)]


def build(cfg, name="kamin", breite=70.0, hoehe=56.0, tiefe=22.0, fries="ranke", kante="perlen", feuer=True,
          gitter=True, aufsatz="beides", girlande=True, struempfe=3, namen="Ida, Paul, Mia", massstab="wichtel",
          wichtel=70.0):
    if massstab == "wichtel":
        _mm = M.mass("kamin", wichtel, INFO["params"], cfg)
        breite, hoehe, tiefe = _mm["breite"], _mm["hoehe"], _mm["tiefe"]
    T = cfg.T
    w = Z.wmin(cfg)
    Ws, H, D = cfg.s(breite), cfg.s(hoehe), cfg.s(tiefe)
    notes = []
    asm = Assembly(name, params=dict(breite=Ws, hoehe=H, tiefe=D, fries=fries, aufsatz=aufsatz))
    ov = max(2.5, Ws * 0.05)                         # Überstand des Simses
    Wb = Ws - 2 * ov                                 # Korpusbreite
    Hb = H - 2 * T                                   # Korpushöhe zwischen Sockel und Sims
    Dk = D                                           # Korpustiefe (Front bis Rückwand, außen)
    if Hb < 6 * T + 10 or Dk < 3 * T + 6 or Wb < 8 * T + 14:
        raise ValueError("Der Kamin ist für diese Materialstärke zu klein – größer wählen oder dünneres Holz")
    Wo = Wb * 0.5                                    # Feueröffnung
    Ho = min(Hb * 0.66, Hb - 2.5 * T - 4)
    beine = (Wb - Wo) / 2
    xf = Wo / 2 + beine / 2                          # Zapfen von Front/Rückwand (Mitte der Wangen)
    tw = min(M.tabbreite(cfg, beine, 0.5), beine - 3.0)
    ts = min(M.tabbreite(cfg, Dk - 2 * T, 0.5), Dk - 2 * T - 2.0)
    if tw < cfg.min_tab_width or ts < cfg.min_tab_width:
        raise ValueError("Der Kamin ist für diese Materialstärke zu klein – größer wählen oder dünneres Holz")

    # ---------------- Korpus ----------------
    yv, yh = T / 2, Dk - T / 2                       # Mittellinien von Front und Rückwand (Tiefe, von vorn)
    xs_seite = Wb / 2 - T / 2
    zl = [(-xf, "l"), (xf, "r")]
    out, feats = Z.E.zapfen_einsetzen(_front_umriss(Wb, Hb, Wo, Ho), [x for x, _ in zl], tw, T, oben=Hb)
    front = Part("front", oriented(out, True))
    for seite, x, pts in feats:
        fid = ("u" if seite == "unten" else "o") + ("l" if x < 0 else "r")
        front.features.append(JointFeature(fid, "tab", tw, T, pos=(10 if seite == "unten" else 20) + (x > 0),
                                               points=pts))
    asm.parts.append(front)
    rueck = Z.brett("rueckwand", Wb, Hb, T,
                    unten=[(Wb / 2 + x, tw, "u" + s, 12 + k) for k, (x, s) in enumerate(zl)],
                    oben=[(Wb / 2 + x, tw, "o" + s, 22 + k) for k, (x, s) in enumerate(zl)])
    E.ziegel(rueck, Wb, Hb, max(2.4, Hb * 0.075), rand=0.9)
    asm.parts.append(rueck)
    Ls = Dk - 2 * T - 0.2
    for k, s in enumerate("lr"):
        sp = Z.brett(f"seite_{s}", Ls, Hb, T, unten=[(Ls / 2, ts, "u", 14 + k)], oben=[(Ls / 2, ts, "o", 24 + k)])
        E.kassette(sp, 0, 0, Ls, Hb, max(1.6, Ls * 0.14))
        asm.parts.append(sp)

    # Sockel mit Herdplatte (vorn verlängert) und Sims – Schlitze für alle Zapfen
    herd = max(7.0, min(Dk * 0.6, Wb * 0.25)) if gitter or feuer else max(4.0, Dk * 0.25)
    ov2 = max(ov * 0.6, max(2.0, T * 0.8) + 0.6)
    schl_s, schl_o = [], []
    for k, (x, s) in enumerate(zl):
        schl_s += [(f"f{s}", x, -yv, tw, 10 + k, 0.0), (f"r{s}", x, -yh, tw, 12 + k, 0.0)]
        schl_o += [(f"f{s}", x, -yv, tw, 20 + k, 0.0), (f"r{s}", x, -yh, tw, 22 + k, 0.0)]
    for k, s in enumerate("lr"):
        x = xs_seite * (-1 if s == "l" else 1)
        schl_s.append((f"s{s}", x, -Dk / 2, ts, 14 + k, math.pi / 2))
        schl_o.append((f"s{s}", x, -Dk / 2, ts, 24 + k, math.pi / 2))
    # Koordinaten der Platten: x quer, y = −Tiefe (vorn bei y = 0, hinten negativ) → Kante vorn oben im Bild
    ys0, ys1 = -Dk - ov2, herd
    sockel_umr = Z.abrunden([(-Wb / 2 - ov2, ys0), (Wb / 2 + ov2, ys0), (Wb / 2 + ov2, ys1), (-Wb / 2 - ov2, ys1)],
                            min(2.5, ov2), 4)
    yf = -Dk * 0.5                                   # Feuer: Mitte der Feuerstelle
    tf = min(M.tabbreite(cfg, Wo * 0.5, 0.4), Wo * 0.3)
    if feuer:
        schl_s.append(("feuer", 0.0, yf, tf, 40, 0.0))
    wg = Wo + 2 * max(3.0, T)                        # Funkengitter etwas breiter als die Öffnung
    yg = herd * 0.5
    tg = min(M.tabbreite(cfg, wg * 0.3, 0.5), wg * 0.18)
    if gitter:
        for k, x in enumerate((-wg * 0.32, wg * 0.32)):
            schl_s.append((f"gitter{k}", x, yg, tg, 50 + k, 0.0))
    sockel = MO.platte(cfg, "sockel", sockel_umr, notes, schl_s, "keine")
    E.fliesen(sockel, -Wo / 2 - beine * 0.6, 0.6, Wo / 2 + beine * 0.6, ys1 - 0.8, max(3.0, herd * 0.38))
    asm.parts.append(sockel)
    ys0 = -Dk - 1.0
    ys1 = ov
    sims_umr = Z.abrunden([(-Ws / 2, ys0), (Ws / 2, ys0), (Ws / 2, ys1), (-Ws / 2, ys1)], min(2.0, ov * 0.6), 4)
    # Aufsatz: Kerzen links/rechts, Uhr in der Mitte – stehen mit Zapfen in Schlitzen auf dem Sims
    yk = -Dk * 0.45
    deko = []
    gk = min(Hb * 0.42, Ws * 0.3)                    # Höhe der Kerzenleuchter
    gu = min(Hb * 0.44, Wb * 0.34)                   # Höhe der Uhr
    tk = M.tabbreite(cfg, gk * 0.3, 0.6)
    if aufsatz in ("kerzen", "beides"):
        if gk >= 14.0:
            for k, x in enumerate((-Wb * 0.36, Wb * 0.36)):
                deko.append((f"kerze{k + 1}", x, gk, tk, 60 + k))
        else:
            notes.append("Für Kerzenleuchter ist der Kamin zu klein – sie entfallen.")
    tu = M.tabbreite(cfg, gu * 0.4, 0.5)
    if aufsatz in ("uhr", "beides"):
        if gu * 0.62 >= tu + 3.0:
            deko.append(("uhr", 0.0, gu, tu, 65))
        else:
            notes.append("Für die Kaminuhr ist der Kamin zu klein – sie entfällt.")
    for n, x, g, t, pos in deko:
        schl_o.append((n, x, yk, t, pos, 0.0))
    kante_ok = kante != "keine"
    sims = MO.platte(cfg, "sims", sims_umr, notes, schl_o, kante if kante_ok else "keine",
                     kante_ausser=lambda p: p[1] < ys1 - 0.5)
    asm.parts.append(sims)
    for k, (x, s) in enumerate(zl):
        asm.connect(f"front:u{s}", f"sockel:f{s}")
        asm.connect(f"front:o{s}", f"sims:f{s}")
        asm.connect(f"rueckwand:u{s}", f"sockel:r{s}")
        asm.connect(f"rueckwand:o{s}", f"sims:r{s}")
    for s in "lr":
        asm.connect(f"seite_{s}:u", f"sockel:s{s}")
        asm.connect(f"seite_{s}:o", f"sims:s{s}")

    # ---------------- Zierblende ----------------
    asm.parts.append(E.kaminblende(cfg, Wb, Hb, Wo, Ho, fries, notes))

    # ---------------- Ausstattung ----------------
    if feuer:
        asm.parts.append(E.feuer(cfg, "feuer", Wo * 0.82, min(Ho * 0.72, Ho - Wo * 0.12), tf, 40, notes))
        asm.connect("feuer:fuss", "sockel:feuer")
    if gitter:
        hg = min(Ho * 0.55, Hb * 0.4)
        asm.parts.append(E.gitter(cfg, "funkengitter", wg, hg, [(-wg * 0.32, "f0", 50), (wg * 0.32, "f1", 51)], tg,
                                  notes))
        asm.connect("funkengitter:f0", "sockel:gitter0")
        asm.connect("funkengitter:f1", "sockel:gitter1")
    for n, x, g, t, pos in deko:
        teil = E.kerzenleuchter(cfg, n, g, t, pos, notes) if n.startswith("kerze") else E.kaminuhr(cfg, n, g, t, pos,
                                                                                                    notes)
        asm.parts.append(teil)
        asm.connect(f"{n}:fuss", f"sims:{n}")
    if girlande:
        asm.parts.append(E.girlande(cfg, "girlande", Ws * 0.96, max(8.0, Hb * 0.22), notes))
    liste = [n.strip() for n in str(namen or "").split(",") if n.strip()]
    anzahl = max(int(struempfe), 0)
    if anzahl:
        hs = max(11.0, Hb * 0.36)
        for k in range(anzahl):
            asm.parts.append(E.strumpf(cfg, f"strumpf{k + 1}", hs, liste[k] if k < len(liste) else "", k, notes))

    asm.notes.append("Korpus: Seiten, Front und Rückwand (Ziegel nach innen) mit den Zapfen in den Sockel stecken, "
                     "dann den Sims von oben aufsetzen. Die Zierblende passgenau vorn auf die Front leimen.")
    if feuer or gitter:
        asm.notes.append("Das Feuer hinten in die Feuerstelle stecken, das Funkengitter vorn auf die Herdplatte. "
                         "Tipp: rotes Transparentpapier hinters Feuer und ein LED-Teelicht dahinter.")
    if deko:
        asm.notes.append("Uhr und Kerzenleuchter in die Schlitze auf dem Sims stecken.")
    if girlande or anzahl:
        asm.notes.append("Girlande vorn an die Simskante leimen, die Strümpfe darunter – vorher bemalen.")
    asm.notes += list(dict.fromkeys(notes))
    return asm
