"""Seitenleiste und Galerie: Bereiche/Themen aus themen.json, Vorschaubilder und /api/vorschau."""
import json
import os
import re
import urllib.error
import urllib.request

import pytest

import service
import vorschau
import webui

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Nutzt Modelle, die seit 2.18 als Pakete kommen (Christbaumschmuck, Zubehör, Fahrzeuge …)
pytestmark = pytest.mark.usefixtures("mit_paketen")

def test_themen_json_is_wellformed():
    with open(os.path.join(ROOT, "themen.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    ids = [b["id"] for b in data["bereiche"]]
    assert len(ids) == len(set(ids))
    for b in data["bereiche"]:
        assert b["name"] and b["name_en"]
        for t in b["themen"]:
            assert t["name"] and t["name_en"] and t["gruppen"]


def test_schema_bereiche_cover_every_model_once():
    s = json.loads(json.dumps(service.schema()))
    gruppen = [g for b in s["bereiche"] for t in b["themen"] for g in t["gruppen"]]
    assert len(gruppen) == len(set(gruppen)), "eine Gruppe steht in mehreren Themen"
    for m in s["models"].values():
        assert m["group"] in gruppen, f"Gruppe {m['group']} fehlt in den Bereichen"


def test_kompakt_keeps_layers_and_shrinks():
    pfad = "M0 0 " + " ".join(f"L{i} {(i % 3) * 0.001:.3f}" for i in range(1, 400)) + " L400 10 L0 10 Z"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="400mm" height="300mm" viewBox="0 0 400 300">'
           f'<g id="layer-schnitt"><path d="{pfad}" stroke="#000000"/></g>'
           f'<g id="layer-gravur"><path d="M5 5 L20 5 L20 9 Z" stroke="#0000FF"/></g></svg>')
    klein = vorschau.kompakt(svg)
    assert 'id="layer-gravur"' in klein and 'id="layer-schnitt"' in klein
    assert len(klein) < len(svg)


def test_svg_rejects_unknown_and_malformed_ids():
    assert vorschau.svg("../etc/passwd") is None
    assert vorschau.svg("gibt_es_nicht", berechnen_erlaubt=False) is None


def test_svg_computes_and_caches(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_HOME", str(tmp_path))
    monkeypatch.setattr(vorschau, "MITGELIEFERT", str(tmp_path / "leer"))
    text = vorschau.svg("schneeflocke")
    assert text and text.lstrip().startswith("<svg")
    assert os.path.isfile(os.path.join(vorschau.zwischenspeicher(), "schneeflocke.svg"))
    assert vorschau.svg("schneeflocke", berechnen_erlaubt=False) == text


def test_shipped_thumbnails_are_small_valid_svgs():
    ordner = os.path.join(ROOT, "vorschau")
    dateien = [n for n in os.listdir(ordner) if n.endswith(".svg")]
    assert dateien
    for name in dateien:
        text = open(os.path.join(ordner, name), encoding="utf-8").read()
        assert text.startswith("<svg") and len(text) < 100_000, name


@pytest.fixture
def server(tmp_path):
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True)
    import threading
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_api_vorschau(server, tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_HOME", str(tmp_path))
    with urllib.request.urlopen(server + "/api/vorschau?id=schneeflocke") as r:
        assert r.headers["Content-Type"].startswith("image/svg+xml")
        assert b"<svg" in r.read()
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(server + "/api/vorschau?id=gibt_es_nicht")
    assert e.value.code == 404


def test_every_model_ships_a_thumbnail():
    """Jede Vorlage aus Kern und paketquellen/ bringt ihr Vorschaubild mit.

    Fehlt eines, rechnet die Engine es beim ersten Öffnen der Galerie – direkt nach dem Start. Bei großen
    Modellen (Papierstern ~20 s) hält das ältere Rechner minutenlang beschäftigt. Abhilfe:
    python3 packaging/vorschaubilder.py <modell …>"""
    ordner = os.path.join(ROOT, "vorschau")
    vorhanden = {n[:-4] for n in os.listdir(ordner) if n.endswith(".svg")}
    fehlen = [k for k, info in service.MODEL_INFO.items() if not info.get("paket") and k not in vorhanden]
    quellen = os.path.join(ROOT, "paketquellen")
    for pid in sorted(os.listdir(quellen)):
        manifest = os.path.join(quellen, pid, "paket.json")
        if not os.path.isfile(manifest):
            continue
        with open(manifest, encoding="utf-8") as fh:
            m = json.load(fh)
        for name in m.get("modelle", []):
            if name not in vorhanden and f"{m['id']}_{name}" not in vorhanden:
                fehlen.append(f"{m['id']}/{name}")
    assert not fehlen, "Vorschaubild fehlt (packaging/vorschaubilder.py laufen lassen): " + ", ".join(fehlen)
