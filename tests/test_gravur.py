"""Eigene Gravuren: Fotos/Logos (Bild-Ebene), Motive und Flächenmuster auf jedem Modell."""
import json
import struct
import zlib

import pytest

import bilder
import gravur
import service
from models import _muster as mu
from steckwerk import Part, rect


def _png(w, h, fn, alpha=False):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            v = fn(x, y)
            raw.append(v)
            if alpha:
                raw.append(0 if v > 250 else 255)
    ctype = 4 if alpha else 0

    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b""))


@pytest.fixture()
def bildordner(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_BILDER", str(tmp_path / "bilder"))
    bilder._GELADEN.clear()
    bilder._ERGEBNIS.clear()
    service.clear_cache()
    return tmp_path


@pytest.fixture()
def foto(bildordner):
    data = _png(120, 90, lambda x, y: min(255, (x * 2 + y) % 256))
    return bilder.import_bytes(data, "verlauf.png", "Verlauf")


def test_import_und_bibliothek(foto):
    assert foto["id"].startswith("verlauf-") and foto["w"] == 120 and foto["h"] == 90
    assert foto["vorschau"].startswith("data:image/png;base64,")
    assert [b["id"] for b in bilder.library()] == [foto["id"]]
    b = bilder.load(foto["id"])
    assert len(b["grau"]) == 120 * 90 and b["alpha"] is None
    bilder.remove(foto["id"])
    assert bilder.library() == [] and not bilder.exists(foto["id"])


def test_grosses_bild_wird_verkleinert(bildordner):
    b = bilder.import_bytes(_png(2000, 500, lambda x, y: (x // 7) % 256), "breit.png")
    assert (b["w"], b["h"]) == (1600, 400)


def test_ungueltige_dateien(bildordner):
    with pytest.raises(bilder.BildFehler, match="Vektorgrafik"):
        bilder.import_bytes(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", "x.svg")
    with pytest.raises(bilder.BildFehler):
        bilder.import_bytes(b"", "leer.png")
    with pytest.raises(bilder.BildFehler):
        bilder.import_bytes(b"\x00\x01kein bild" * 10, "x.bin")


def test_jpg_import(bildordner):
    PIL = pytest.importorskip("PIL.Image")
    import io
    buf = io.BytesIO()
    PIL.new("RGB", (64, 48), (200, 100, 50)).save(buf, "JPEG")
    b = bilder.import_bytes(buf.getvalue(), "foto.jpg")
    assert (b["w"], b["h"]) == (64, 48)


@pytest.mark.parametrize("modus", bilder.MODUS_KEYS)
@pytest.mark.parametrize("form", ["rechteck", "oval", "herz", "weich"])
def test_aufbereiten_modi(foto, modus, form):
    W, H, png = bilder.aufbereiten(foto["id"], 30, 20, ppmm=5, modus=modus, form=form)
    assert (W, H) == (150, 100)
    w, h, gray, alpha = bilder.mt.read_png(png)
    assert (w, h) == (150, 100) and alpha
    if modus in ("fehlerstreuung", "schwarzweiss"):
        assert {v for row in gray for v in row} <= {0, 255}
    if form != "rechteck":                                  # Ecken liegen außerhalb der Bildform
        assert alpha[0][0] == 0 and gray[0][0] == 255


def test_aufbereiten_zwischenspeicher(foto):
    a = bilder.aufbereiten(foto["id"], 25, 25, ppmm=4)
    bilder._ERGEBNIS.clear()                                 # Arbeitsspeicher leer → Datei im Ordner
    b = bilder.aufbereiten(foto["id"], 25, 25, ppmm=4)
    assert a == b
    import os
    assert any(f.endswith(".png") for f in os.listdir(bilder.cache_dir()))


def test_png_mit_aufloesung():
    png = bilder.png_bytes(2, 2, b"\x00\xff\xff\x00", ppmm=10)
    assert b"pHYs" in png and struct.pack(">II", 10000, 10000) in png


@pytest.mark.parametrize("art", mu.MUSTER_KEYS)
def test_muster_bleiben_im_teil(art):
    from models import _deko as dk
    from validator import check_part
    from steckwerk import Config
    p = Part("platte", rect(0, 0, 60, 40))
    p.add_hole(rect(25, 15, 10, 10))
    cv = dk.Canvas(p, margin=1.5)
    n = mu.muster(cv, art, (0, 0, 60, 40), 5)
    assert n > 0
    assert check_part(p, Config()) == []


def test_pruefen_meldet_fehler(bildordner):
    assert gravur.pruefen(None) == []
    g = gravur.pruefen('{"quelle": "muster"}')[0]
    assert g["muster"] == "mandala" and g["teil"] == "auto" and g["abstand"] == 6
    with pytest.raises(ValueError, match="Gravur 1: Bild"):
        gravur.pruefen([{"quelle": "bild", "bild": "gibtsnicht"}])
    with pytest.raises(ValueError, match="Gravur 1: muster"):
        gravur.pruefen([{"quelle": "muster", "muster": "quatsch"}])
    with pytest.raises(ValueError, match="Höchstens"):
        gravur.pruefen([{"quelle": "muster"}] * 9)


def _gen(model, gravuren, params=None):
    return service.generate(dict(model=model, params=params or {}, gravuren=gravuren))


def test_foto_auf_anhaenger(foto):
    d = _gen("motiv_anhaenger", [dict(quelle="bild", bild=foto["id"], form="oval")], dict(motive=[]))
    assert d["ok"], d.get("error") or d["assemblies"][0]["errors"]
    svg = d["assemblies"][0]["sheets"][0]["svg"]
    assert 'id="layer-bild"' in svg and "data:image/png;base64," in svg
    assert any("Bild-Gravur" in n for n in d["assemblies"][0]["notes"])
    assert d["assemblies"][0]["teile"][0]["name"] == "anhaenger"


def test_foto_ragt_ueber_das_teil(foto):
    d = _gen("motiv_anhaenger", [dict(quelle="bild", bild=foto["id"], groesse=40, x=30)], dict(motive=[]))
    assert not d["ok"] and "ragt über das Teil" in " ".join(d["assemblies"][0]["errors"])


def test_motiv_und_muster_auf_haus(bildordner):
    d = _gen("wichtelhaus", [dict(quelle="muster", muster="ranken", teil="alle", abstand=6),
                             dict(quelle="motiv", motiv="stern", art="raster", teil="wichtelhaus_boden", groesse=30),
                             dict(quelle="motiv", motiv="herz", art="flaeche", teil="wichtelhaus_hinten", groesse=25)])
    assert d["ok"], d.get("error") or d["assemblies"][0]["errors"]
    notes = " ".join(d["assemblies"][0]["notes"])
    assert "Muster „Ranken“" in notes and "Motiv-Gravur „Stern“" in notes


def test_unbekanntes_teil(bildordner):
    d = _gen("wichtelhaus", [dict(quelle="muster", teil="gibtsnicht")])
    assert not d["ok"] and "gibt es in diesem Modell nicht" in d["error"] and "wichtelhaus_vorne" in d["error"]


def test_bild_wird_layout_gedreht_mitgenommen(foto):
    # Großes Schild auf schmaler Platte: das Layout dreht das Teil, das Bild muss mit
    d = service.generate(dict(model="motiv_schild", params=dict(width=200, height=120, motive=[]),
                              config=dict(sheet_width=150, sheet_height=260),
                              gravuren=[dict(quelle="bild", bild=foto["id"])]))
    assert d["ok"], d.get("error") or d["assemblies"][0]["errors"]
    svg = d["assemblies"][0]["sheets"][0]["svg"]
    m = svg.split('transform="matrix(')[1].split(")")[0].split()
    assert abs(float(m[0])) < 1e-3 and abs(abs(float(m[1])) - 1) < 1e-3      # 90° gedreht


def test_cache_unterscheidet_gravuren(bildordner):
    a = _gen("motiv_anhaenger", [], dict(motive=[]))
    b = _gen("motiv_anhaenger", [dict(quelle="muster", muster="sterne")], dict(motive=[]))
    assert a["assemblies"][0]["sheets"][0]["svg"] != b["assemblies"][0]["sheets"][0]["svg"]


def test_zip_enthaelt_bilddatei(foto):
    import io
    import zipfile
    results, cfg = service.run_request(dict(model="motiv_anhaenger", params=dict(motive=[]),
                                            gravuren=[dict(quelle="bild", bild=foto["id"])]), preview_on_error=False)
    names = zipfile.ZipFile(io.BytesIO(service.zip_results(results, cfg))).namelist()
    assert any(n.endswith(".png") and "_bild1_" in n for n in names)


def test_schema_hat_gravur_optionen(foto):
    s = service.schema()
    assert s["gravur"]["muster"][0]["value"] == "rauten" and s["bilder"][0]["id"] == foto["id"]
    json.dumps(s)


def test_cli_gravur(foto, tmp_path, capsys):
    import cli
    rc = cli.run(["--model", "motiv_anhaenger", "-O", "motive=[]", "--gravur",
                  json.dumps({"quelle": "bild", "bild": foto["id"], "modus": "skizze"}),
                  "--out", str(tmp_path / "out"), "-q"])
    assert rc == 0
    assert list((tmp_path / "out" / "anhaenger").glob("*_bild1_*.png"))


def test_teilenummern_behalten_bild(foto):
    d = service.generate(dict(model="motiv_anhaenger", params=dict(motive=[]), config=dict(part_numbers=True),
                              gravuren=[dict(quelle="bild", bild=foto["id"], groesse=25)]))
    assert d["ok"], d.get("error") or d["assemblies"][0]["errors"]
    assert 'id="layer-bild"' in d["assemblies"][0]["sheets"][0]["svg"]
