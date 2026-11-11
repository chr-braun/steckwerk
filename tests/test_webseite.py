"""Webseite: Bauskript setzt Bereiche, Pakete und Version ein; Bildauswahl passt zu den Modellen."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "packaging"))
import webseite  # noqa: E402
from steckwerk import __version__  # noqa: E402


def test_bauen_ohne_bilder(tmp_path):
    ziel = tmp_path / "site"
    daten = webseite.bauen(str(ziel), bilder=False)
    html = (ziel / "index.html").read_text(encoding="utf-8")
    assert "/*DATEN*/" not in html and "{{VERSION}}" not in html and __version__ in html
    m = re.search(r"var DATEN = (\{.*?\});\n", html)
    assert m and json.loads(m.group(1))["bereiche"][0]["id"] == "feste"
    ids = {p for b in daten["bereiche"] for p in b["pakete"]}
    assert ids == set(webseite.manifeste()), "jedes Paket steht in einem Bereich auf der Webseite"
    for pid, p in daten["pakete"].items():
        assert p["name"] and p["text"] and p["version"], pid
    assert (ziel / "pakete-bauen.html").exists() and (ziel / "stil.css").exists()
    for f in ("app.webp", "pruefbericht.webp", "ausgeben.webp", "formen.webp", "symbol.svg"):
        assert (ziel / "bilder" / f).exists(), f


def test_karten_passen_zu_den_paketen():
    mf = webseite.manifeste()
    modelle = {m for p in mf.values() for m in p.get("modelle") or []}
    for pid, k in webseite.KARTEN.items():
        assert pid in mf, f"{pid}: Paket gibt es nicht"
        if k.get("modell"):
            assert k["modell"] in modelle, f"{pid}: Modell {k['modell']} fehlt"
    for modell, *_ in webseite.LEISTE:
        assert modell in modelle, modell


def test_zeichne(tmp_path):
    svg = tmp_path / "t.svg"
    svg.write_text('<svg><g id="layer-gravur"><g id="gravur-a"><path d="M2,2 L3,3"/></g></g>'
                   '<g id="layer-schnitt"><g id="schnitt-a"><path d="M0,0 L10,0 L10,20 L0,20 Z"/></g>'
                   '<g id="schnitt-b"><path d="M50,0 L55,0 L55,5 L50,5 Z"/></g></g></svg>', encoding="utf-8")
    w, h, w1 = webseite.zeichne(str(svg), ["a", "b"], str(tmp_path / "o" / "x.svg"), "Test")
    assert (w, h, w1) == (21, 20, 10)
    out = (tmp_path / "o" / "x.svg").read_text(encoding="utf-8")
    assert out.count('class="cut"') == 2 and out.count('class="eng"') == 1
