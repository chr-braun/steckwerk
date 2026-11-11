"""XCS-/XS-Projekte, Schnittzeit-Schätzung, Teilenummern, Montageanleitung, Projekte, dichteres Packing."""
import io
import json
import urllib.request
import zipfile

import pytest

import laser
import montage
import projekte
import service
import steckwerk
from steckwerk import Config, layout


@pytest.fixture(scope="module")
def auto():
    req = {"model": "fahrzeug", "config": {"thickness": 3, "kerf": 0.15}}
    results, cfg = service.run_request(req, preview_on_error=False)
    assert results[0].ok
    return results, cfg


def test_xcs_ebenen_und_linien(auto):
    results, cfg = auto
    res = results[0]
    sh = res.sheets[0]
    d = laser.lies_xcs(laser.xcs_bytes(sh, cfg, "auto"))
    assert d["geraet"] == laser.M2_ID
    assert d["ebenen"] == {laser.XCS_SCORE: "Ritzen", laser.XCS_CUT: "Schneiden"}
    cut, score = laser.wege(sh)
    assert d["linien"][laser.XCS_CUT] == len(cut)
    assert d["linien"][laser.XCS_SCORE] == len(score)
    # Koordinaten in mm, alles auf dem Blatt
    for disp in d["displays"]:
        assert 0 <= disp["x"] <= sh.width and 0 <= disp["y"] <= sh.height
        assert disp["dPath"].startswith("M")
    # Schnitte geschlossen, innen vor außen bleibt erhalten (letzte Linie = Außenkontur des letzten Teils)
    assert all(x["isClosePath"] for x in d["displays"] if x["layerColor"] == laser.XCS_CUT)


def test_xs_mit_laserwerten(auto):
    results, cfg = auto
    werte = {"cut": [100, 8, 1], "score": [12, 120, 1]}
    data = laser.xs_bytes(results[0].sheets[0], cfg, "auto", werte, 20)
    assert data[:2] == b"PK"
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.read(".format") == b"v2"
        dev = json.loads(z.read(f"devices/device-{laser.M2_ID}.json"))
    assert dev["power"] == [20]
    d = laser.lies_xcs(data)
    assert d["werte"]["VECTOR_CUTTING"] == {"power": 100, "speed": 8.0, "repeat": 1}
    assert d["werte"]["VECTOR_ENGRAVING"]["power"] == 12


def test_xcs_ist_reproduzierbar(auto):
    results, cfg = auto
    sh = results[0].sheets[0]
    a = json.loads(laser.xcs_bytes(sh, cfg, "auto"))
    b = json.loads(laser.xcs_bytes(sh, cfg, "auto"))
    for x in (a, b):
        x.pop("created"), x.pop("modify")
    assert a == b


def test_laserwerte_aus_profil_und_grenzen():
    cfg = Config(thickness=3, kerf=0.15)
    assert laser.laserwerte(None, cfg, "w10") == {"cut": [100, 6, 2], "score": [20, 100, 1]}
    w = laser.laserwerte({"cut": [150, 0, 99], "score": ["x"]}, cfg, "w20")
    assert w["cut"] == [100.0, 0.5, 20.0]
    assert w["score"] == [12, 120, 1]                 # ungültig → Profil


def test_schaetzung(auto):
    results, cfg = auto
    sch = laser.schaetzung(results[0].sheets, {"cut": [100, 6, 2], "score": [20, 100, 1]}, preis_platte=5)
    assert sch["blaetter"] == 1 and 0 < sch["platten"] <= 1
    assert sch["schnitt_m"] > 1 and sch["sekunden"] > sch["schnitt_m"] * 1000 / 6 * 2 * 0.99
    assert abs(sch["kosten"] - sch["platten"] * 5) < 0.05
    schneller = laser.schaetzung(results[0].sheets, {"cut": [100, 12, 1], "score": [20, 100, 1]})
    assert schneller["sekunden"] < sch["sekunden"] and "kosten" not in schneller
    assert laser.dauer_text(42) == "42 s" and laser.dauer_text(3725) == "1 h 02 min"


def test_generate_liefert_schaetzung():
    d = service.generate({"model": "tannenbaum", "leistung": "w20", "preis_platte": 3})
    sch = d["assemblies"][0]["schaetzung"]
    assert sch["werte"]["cut"][1] > 0 and "kosten" in sch


def test_teilenummern_werden_geprueft_und_graviert():
    req = {"model": "fahrzeug", "config": {"part_numbers": True}}
    results, cfg = service.run_request(req, preview_on_error=False)
    res = results[0]
    assert res.ok, res.report.text()
    ohne, _ = service.run_request({"model": "fahrzeug"}, preview_on_error=False)
    mehr = sum(len(p.engrave) for p in res.asm.parts) - sum(len(p.engrave) for p in ohne[0].asm.parts)
    assert mehr >= len(res.asm.parts)                   # jede Ziffer mindestens ein Strich


def test_config_bool_aus_text():
    assert Config.from_dict({"part_numbers": "true"}).part_numbers is True
    assert Config.from_dict({"part_numbers": "nein"}).part_numbers is False


def test_montage_pdf(auto):
    results, cfg = auto
    res = results[0]
    pdf = montage.anleitung_pdf([(res.asm, res.sheets, {"zeit": "15 min"})], cfg)
    assert pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF")
    assert b"Montageanleitung" in pdf and b"Zusammenbau" in pdf
    # xref zeigt auf echte Objekte
    xref = int(pdf.rsplit(b"startxref", 1)[1].split()[0])
    assert pdf[xref:xref + 4] == b"xref"


def test_zip_mit_allen_formaten():
    req = {"model": "tannenbaum", "formate": ["xcs", "xs", "pdf", "exe"]}
    results, cfg = service.run_request(req, preview_on_error=False)
    names = zipfile.ZipFile(io.BytesIO(service.zip_results(results, cfg, req))).namelist()
    assert any(n.endswith(".xcs") for n in names) and any(n.endswith(".xs") for n in names)
    assert any(n.endswith("_montage.pdf") for n in names)
    assert not any(n.endswith(".exe") for n in names)
    plain = zipfile.ZipFile(io.BytesIO(service.zip_results(results, cfg))).namelist()
    assert not any(n.endswith((".xcs", ".xs", ".pdf")) for n in plain)


def test_dichtes_packing_spart_platten():
    cfg = Config(sheet_width=250, sheet_height=180)
    results, _ = service.run_request({"model": "fahrzeug", "config": {"sheet_width": 250, "sheet_height": 180}},
                                     preview_on_error=False)
    parts = [p.compensated(cfg.kerf_offset) for p in results[0].asm.parts]
    orig = steckwerk._layout_dicht
    try:
        steckwerk._layout_dicht = lambda *a: None
        regal = layout(parts, cfg)
    finally:
        steckwerk._layout_dicht = orig
    dicht = layout(parts, cfg)
    assert len(regal) == 2 and len(dicht) == 1
    assert results[0].ok and len(results[0].sheets) == 1


def test_packing_unveraendert_wenn_nichts_gespart(cfg):
    results, _ = service.run_request({"model": "wichtelhaus"}, preview_on_error=False)
    parts = [p.compensated(cfg.kerf_offset) for p in results[0].asm.parts]
    assert len(layout(parts, cfg)) == 1


def test_projekte(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_HOME", str(tmp_path))
    assert projekte.liste() == []
    projekte.speichern("  Oma  Haus ", {"model": "wichtelhaus", "params": {"W": 90}, "config": {"thickness": 4}})
    projekte.speichern("Zweites", {"model": "tannenbaum"})
    namen = [p["name"] for p in projekte.liste()]
    assert namen == ["Zweites", "Oma Haus"]
    projekte.speichern("Oma Haus", {"model": "wichtelhaus", "params": {"W": 100}})
    assert len(projekte.liste()) == 2 and projekte.liste()[0]["params"] == {"W": 100}
    projekte.loeschen("Zweites")
    with pytest.raises(projekte.ProjektFehler):
        projekte.loeschen("Zweites")
    with pytest.raises(projekte.ProjektFehler):
        projekte.speichern("", {"model": "x"})


def test_xcs_oeffnen_mac(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("sys.platform", "darwin")
    assert laser.oeffnen_in_xcs("a.xcs", runner=lambda c: calls.append(c) or (0 if "xTool Studio" in c else 1)) \
        == "xTool Studio"
    assert calls[0][:3] == ["open", "-a", "xTool Creative Space"]
    with pytest.raises(OSError):
        laser.oeffnen_in_xcs("a.xcs", runner=lambda c: 1)


def _post(port, path, body):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "X-Steckwerk": "1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


def test_api_projekte_und_xcs_oeffnen(tmp_path, monkeypatch):
    import threading
    import webui
    monkeypatch.setenv("STECKWERK_HOME", str(tmp_path / "home"))
    geoeffnet = []
    monkeypatch.setattr(laser, "oeffnen_in_xcs", lambda p: geoeffnet.append(p) or "xTool Creative Space")
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    try:
        d = _post(port, "/api/projekte", {"aktion": "speichern", "name": "A",
                                          "projekt": {"model": "tannenbaum", "params": {}}})
        assert d["ok"] and d["projekte"][0]["name"] == "A"
        assert not _post(port, "/api/projekte", {"aktion": "speichern", "name": ""})["ok"]
        d = _post(port, "/api/xcs-oeffnen", {"model": "tannenbaum"})
        assert d["ok"], d
        assert geoeffnet and geoeffnet[0].endswith(".xcs")
        assert laser.lies_xcs(open(geoeffnet[0], "rb").read())["geraet"] == laser.M2_ID
    finally:
        srv.shutdown()
