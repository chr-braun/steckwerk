#!/usr/bin/env python3
"""
webseite.py – die Steckwerk-Webseite (GitHub Pages) bauen.

  python3 packaging/webseite.py [--out _site] [--ohne-bilder]

Kopiert webseite/ nach --out, rechnet die Modellbilder frisch aus den Paketquellen (so, wie Steckwerk
die Teile schneidet: Holzfläche mit Schnittkante, Gravurlinien) und schreibt die Paketübersicht nach
Bereichen (paketquellen/bereiche.json) direkt in die Seite. Versionen und Download-Link holt die Seite
beim Öffnen live aus dem Update-Kanal.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLEN = os.path.join(ROOT, "paketquellen")

# Bild je Paket: Modell, Teile (ids aus der SVG) und Bildunterschrift. Kurztexte für die Karten.
KARTEN: Dict[str, Dict[str, Any]] = {
    "weihnacht": dict(modell="namensanhaenger", teile=["emma"], masse="Namensanhänger", masse_en="Name ornament",
                      text="Edler Christbaumschmuck, Namensanhänger in echter Schreibschrift, Steckkrippe, Zierschlitten, "
                           "Spitzenschmuck und Kristall-Schneeflocken.",
                      text_en="Fine tree ornaments, name ornaments in real script, nativity set, sleigh, lace ornaments "
                              "and crystal snowflakes."),
    "wichtel": dict(modell="schaukelstuhl", teile=["seite_l", "strickkorb_a"], masse="Schaukelstuhl", masse_en="Rocking chair",
                    groesse="Wichtel-Maßstab", groesse_en="elf scale",
                    text="Wichteltür, Möbel, Wichtelzimmer, Wichtelmarkt und edles Zubehör wie Kamin, Standuhr und "
                         "Christbaum. Alles im selben Maßstab.",
                    text_en="Elf door, furniture, elf room, elf market and fine accessories like fireplace, clock and "
                            "tree. All at the same scale."),
    "halloween": dict(modell="spinnennetz", teile=["spinnennetz_rund"], masse="Spinnennetz", masse_en="Spider web",
                      text="Spukschloss im gotischen Bogen, Kürbislaterne, Grabstein, filigranes Spinnennetz, "
                           "Skelett-Hampelmann und Süßigkeitenschale.",
                      text_en="Haunted castle in a gothic arch, pumpkin lantern, gravestone, filigree spider web, "
                              "skeleton jumping jack and candy bowl."),
    "wohnen": dict(modell="zierrahmen", teile=["rahmen"], masse="Zierrahmen", masse_en="Ornamental frame",
                   text="Bilderrahmen zum Hinstellen oder Aufhängen, Zierrahmen für Schilder, Uhren und Spiegel und "
                        "ein Türschild mit Namen.",
                   text_en="Picture frames to stand or hang, ornamental frames for signs, clocks and mirrors, and a "
                           "door sign with your name."),
    "schmuck": dict(modell="ohrhaenger", teile=["links", "rechts"], masse="Ohrhänger Lotus", masse_en="Lotus earrings",
                    paar=True,
                    text="Ohrhänger als Paar in zehn Formen, durchbrochen, als Rahmen oder graviert.",
                    text_en="Earring pairs in ten shapes, pierced, as a frame or engraved."),
    "ebenen": dict(modell="ebenenmotiv", teile=["ebenenmotiv_grund", "ebenenmotiv_motiv", "ebenenmotiv_auflage"],
                   masse="Ebenenmotiv", masse_en="Layered motif", groesse="drei Lagen", groesse_en="three layers",
                   text="Schneidebilder mit vier Szenen, Motive aus drei Lagen mit Steckstiften und feine "
                        "Aufsteck-Verzierungen.",
                   text_en="Cut pictures with four scenes, three-layer motifs held by pegs and fine clip-on decorations."),
    "spiele": dict(modell="labyrinth", teile=["labyrinth_wand_1"], masse="Kugellabyrinth", masse_en="Marble maze",
                   text="Mühle, Tic-Tac-Toe, Vier in einer Reihe, Kugellabyrinth, Solitär und Bilderpuzzle, auch mit "
                        "deinem eigenen Foto.",
                   text_en="Nine men’s morris, tic-tac-toe, four in a row, marble maze, peg solitaire and jigsaw "
                           "puzzles, also with your own photo."),
    "bewegung": dict(modell="hampelmann", teile=["hampelmann_koerper"], masse="Hampelmann", masse_en="Jumping jack",
                     text="Hampelmann als Wichtel, Rentier oder Skelett, Kurbeltier, Turner-Affe, Kreisel und "
                          "Balancier-Vogel.",
                     text_en="Jumping jack as elf, reindeer or skeleton, crank animal, acrobat monkey, spinning top and "
                             "balancing bird."),
    "formen": dict(bild="formen.webp", masse="Stapelvase", masse_en="Stacked vase", groesse="gedrehte Lagen",
                   groesse_en="twisted layers",
                   text="Kugel, Ei oder Zwiebelturm aus gekreuzten Rippen, Wellenflächen als Gitter und gedrehte "
                        "Stapelvasen.",
                   text_en="Sphere, egg or onion dome from crossed ribs, wave surfaces as a grid and twisted stacked vases."),
    "verkauf": dict(modell="flaschenschild", teile=None, masse="Flaschenschild", masse_en="Bottle tag",
                    text="Preisschilder für die Flasche mit Logo, Preis und Grundpreis je Liter, auch als ganze "
                         "Preisliste auf einmal.",
                    text_en="Bottle price tags with logo, price and unit price per litre, also a whole price list at once."),
    "verzierungen": dict(modell="zierstueck", teile=None, masse="Rosette", masse_en="Rosette",
                         text="Ornamente als Zierstücke und Zierleisten und der Passungstest, mit dem du in einem "
                              "Schnitt den richtigen Kerf für dein Holz findest.",
                         text_en="Ornaments as appliqués and border strips, plus the fit test that finds the right kerf "
                                 "for your wood in one cut."),
}

# Werkstück-Leiste unter dem Einstieg: Teile im echten Größenverhältnis
LEISTE: List[Tuple[str, Optional[List[str]], str, str]] = [
    ("christbaumschmuck", ["engel"], "Engel", "Angel"),
    ("namensanhaenger", ["emma"], "Namensanhänger", "Name ornament"),
    ("schaukelstuhl", ["seite_l", "strickkorb_a"], "Schaukelstuhl", "Rocking chair"),
    ("spitzenschmuck", None, "Spitzenschmuck", "Lace bauble"),
    ("zierstueck", None, "Rosette", "Rosette"),
    ("ohrhaenger", ["links", "rechts"], "Ohrhänger", "Earrings"),
    ("flaschenschild", None, "Flaschenschild", "Bottle tag"),
    ("kamin", ["zierblende", "kerze1", "uhr"], "Wichtelkamin", "Elf fireplace"),
]

STIL = ("<style>.cut{fill:#e6cba0;stroke:#8a6238;stroke-width:.28;stroke-linejoin:round}"
        ".eng{fill:none;stroke:#8a6238;stroke-width:.2;stroke-linecap:round}</style>")
ZAHL = re.compile(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")


def teile(svg: str) -> Dict[str, Dict[str, List[str]]]:
    """Pfade je Teil aus einer Steckwerk-SVG (Gruppen schnitt-<teil> und gravur-<teil>)."""
    s = open(svg, encoding="utf-8").read()
    out: Dict[str, Dict[str, List[str]]] = {}
    for ebene in ("schnitt", "gravur"):
        for m in re.finditer(r'<g id="%s-([^"]+)">(.*?)</g>' % ebene, s, re.S):
            out.setdefault(m.group(1), {}).setdefault(ebene, []).extend(re.findall(r'd="([^"]+)"', m.group(2)))
    return out


def zeichne(svg: str, ids: Optional[List[str]], ziel: str, titel: str, abstand: float = 6) -> Tuple[float, float, float]:
    """Gewählte Teile nebeneinander (unten bündig) als eigene SVG; gibt Breite, Höhe und Breite des ersten Teils in mm."""
    alle = teile(svg)
    ids = ids or [next(iter(k for k in alle if alle[k].get("schnitt")))]
    boxen = []
    for i in ids:
        pts = [(float(x), float(y)) for d in alle[i]["schnitt"] for x, y in ZAHL.findall(d)]
        xs, ys = zip(*pts)
        boxen.append((i, min(xs), min(ys), max(xs), max(ys)))
    hoehe = max(y1 - y0 for _, _, y0, _, y1 in boxen)
    x, koerper = 0.0, []
    for i, x0, y0, x1, y1 in boxen:
        dx, dy = x - x0, hoehe - y1

        def schiebe(d: str) -> str:
            return ZAHL.sub(lambda m: "%.2f,%.2f" % (float(m.group(1)) + dx, float(m.group(2)) + dy), d)
        koerper.append('<path class="cut" fill-rule="evenodd" d="%s"/>' % " ".join(map(schiebe, alle[i]["schnitt"])))
        if alle[i].get("gravur"):
            koerper.append('<path class="eng" d="%s"/>' % " ".join(map(schiebe, alle[i]["gravur"])))
        x += x1 - x0 + abstand
    breite = x - abstand
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 %.1f %.1f" role="img" aria-label="%s">%s%s</svg>'
                 % (breite + 4, hoehe + 4, titel, STIL, "".join(koerper)))
    return breite, hoehe, boxen[0][3] - boxen[0][1]


class Rechner:
    """Modelle mit allen Paketquellen rechnen (in einem eigenen Datenordner)."""

    def __init__(self, tmp: str):
        self.tmp = tmp
        self.env = dict(os.environ, STECKWERK_PAKETE=os.path.join(tmp, "inst"), STECKWERK_DATEN=os.path.join(tmp, "daten"),
                        STECKWERK_SPRACHE="de")
        cli = [sys.executable, os.path.join(ROOT, "cli.py")]
        quellen = [os.path.join(QUELLEN, "verzierungen")] + sorted(
            d for d in glob.glob(os.path.join(QUELLEN, "*")) if os.path.isfile(os.path.join(d, "paket.json")))
        for q in quellen:
            subprocess.run(cli + ["--paket-installieren", q], env=self.env, check=True, stdout=subprocess.DEVNULL)
        self.cli, self.fertig = cli, {}

    def svg(self, modell: str) -> str:
        if modell not in self.fertig:
            out = os.path.join(self.tmp, "out", modell)
            subprocess.run(self.cli + ["-m", modell, "--out", out, "-q"], env=self.env, check=True, stdout=subprocess.DEVNULL)
            self.fertig[modell] = glob.glob(os.path.join(out, "*", "*.svg"))[0]
        return self.fertig[modell]


def manifeste() -> Dict[str, Dict[str, Any]]:
    out = {}
    for f in glob.glob(os.path.join(QUELLEN, "*", "paket.json")):
        with open(f, encoding="utf-8") as fh:
            m = json.load(fh)
        out[m["id"]] = m
    return out


def bauen(ziel: str, bilder: bool = True) -> Dict[str, Any]:
    quelle = os.path.join(ROOT, "webseite")
    if os.path.isdir(ziel):
        shutil.rmtree(ziel)
    shutil.copytree(quelle, ziel)
    with open(os.path.join(QUELLEN, "bereiche.json"), encoding="utf-8") as fh:
        bereiche = json.load(fh)["bereiche"]
    mf = manifeste()
    daten: Dict[str, Any] = {"bereiche": [], "pakete": {}, "leiste": []}
    for b in bereiche:
        eintrag = {k: b.get(k, "") for k in ("id", "name", "name_en", "text", "text_en")}
        eintrag["pakete"] = [p for p in b["pakete"] if p in mf]
        daten["bereiche"].append(eintrag)
    with tempfile.TemporaryDirectory() as tmp:
        r = Rechner(tmp) if bilder else None
        for pid, m in mf.items():
            k = KARTEN.get(pid, {})
            eintrag = dict(name=m.get("name", pid), name_en=m.get("name_en", ""), version=m["version"],
                           modelle=len(m.get("modelle") or []), text=k.get("text") or m.get("beschreibung", ""),
                           text_en=k.get("text_en") or m.get("beschreibung_en", ""),
                           masse=k.get("masse", ""), masse_en=k.get("masse_en", ""), bild=k.get("bild", ""))
            if r and k.get("modell"):
                eintrag["bild"] = f"pakete/{pid}.svg"
                w, h, w1 = zeichne(r.svg(k["modell"]), k.get("teile"), os.path.join(ziel, "bilder", eintrag["bild"]),
                                   eintrag["masse"])
                if "groesse" not in k:
                    w = w1 if k.get("paar") else w
                    eintrag["groesse"] = eintrag["groesse_en"] = "%d × %d mm" % (round(w), round(h))
            for f in ("groesse", "groesse_en"):
                if k.get(f):
                    eintrag[f] = k[f]
            daten["pakete"][pid] = eintrag
        if r:
            for modell, ids, de, en in LEISTE:
                datei = f"leiste/{modell}.svg"
                w, _, _ = zeichne(r.svg(modell), ids, os.path.join(ziel, "bilder", datei), de)
                daten["leiste"].append(dict(bild=datei, mm=round(w, 1), name=de, name_en=en))
    seite = os.path.join(ziel, "index.html")
    with open(seite, encoding="utf-8") as fh:
        html = fh.read()
    sys.path.insert(0, ROOT)
    from steckwerk import __version__
    html = html.replace("/*DATEN*/null", json.dumps(daten, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("{{VERSION}}", __version__)
    with open(seite, "w", encoding="utf-8") as fh:
        fh.write(html)
    return daten


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Steckwerk-Webseite bauen")
    ap.add_argument("--out", default=os.path.join(ROOT, "_site"))
    ap.add_argument("--ohne-bilder", action="store_true", help="Modellbilder nicht neu rechnen (schneller, für Tests)")
    a = ap.parse_args(argv)
    os.makedirs(os.path.join(a.out), exist_ok=True)
    d = bauen(a.out, not a.ohne_bilder)
    print(f"Webseite in {a.out}: {len(d['pakete'])} Pakete in {len(d['bereiche'])} Bereichen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
