"""Erweiterungspakete: anlegen, prüfen, packen, installieren, laden, entfernen."""
import base64
import json
import os
import zipfile

import pytest

import pakete
import service
from cli import run
from steckwerk import Config
from conftest import assert_cut_ready

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def paketordner(tmp_path, monkeypatch):
    inst = tmp_path / "inst"
    monkeypatch.setenv("STECKWERK_PAKETE", str(inst))
    yield tmp_path
    monkeypatch.delenv("STECKWERK_PAKETE")
    service.reload_pakete()


def test_create_pack_install_use_remove(paketordner):
    folder = pakete.create("testschild", str(paketordner), name="Testschild")
    path, lines = pakete.pack(folder, str(paketordner))
    assert path.endswith("testschild-1.0.0.swpaket") and "cut-ready" in lines[0]
    m, _ = pakete.install(path)
    assert m["id"] == "testschild"
    service.reload_pakete()
    assert service.MODEL_INFO["testschild"]["paket"]["version"] == "1.0.0"
    cfg = Config()
    asms = service.build_assemblies("testschild", {"text": "Anna", "rahmen": "oval"}, cfg)
    assert_cut_ready(asms[0], cfg)
    assert any(p["id"] == "testschild" for p in service.schema()["pakete"])
    pakete.remove("testschild")
    service.reload_pakete()
    assert "testschild" not in service.MODEL_INFO


def test_example_package_installs(paketordner):
    m, _ = pakete.install(os.path.join(HERE, "beispiel-pakete", "tuerschild-1.1.0.swpaket"))
    assert m["name"] == "Türschild"


def test_cli_commands(paketordner, capsys):
    out = str(paketordner)
    assert run(["--paket-neu", "cli_schild", "--out", out]) == 0
    assert run(["--paket-packen", os.path.join(out, "cli_schild"), "--out", out]) == 0
    assert run(["--paket-installieren", os.path.join(out, "cli_schild-1.0.0.swpaket")]) == 0
    assert run(["--pakete"]) == 0
    assert "cli_schild" in capsys.readouterr().out
    assert run(["--paket-entfernen", "cli_schild"]) == 0
    assert run(["--paket-entfernen", "cli_schild"]) == 2


def _zip(files):
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for n, t in files.items():
            zf.writestr(n, t)
    return buf.getvalue()


@pytest.mark.parametrize("files,msg", [
    ({"x/readme.txt": "?"}, "paket.json"),
    ({"x/paket.json": "{kaputt"}, "JSON"),
    ({"x/paket.json": json.dumps(dict(id="Bad Id", name="a", version="1.0.0", modelle=["a"]))}, "Paket-id"),
    ({"x/paket.json": json.dumps(dict(id="ok", name="a", version="1.0.0", modelle=["fehlt"]))}, "fehlt"),
    ({"x/paket.json": json.dumps(dict(id="ok", name="a", version="1.0.0", modelle=["mm"], steckwerk="99.0.0"))},
     "braucht"),
    ({"x/paket.json": json.dumps(dict(id="ok", name="a", version="1.0.0", modelle=["mm"])), "x/mm.py": "x = 1"},
     "build"),
    ({"x/paket.json": json.dumps(dict(id="ok", name="a", version="1.0.0", modelle=["mm"])),
      "x/mm.py": "INFO = dict(params=[])\ndef build(cfg):\n    raise ValueError('kaputt')"}, "Standardwerten"),
    ({"../boese/paket.json": "{}"}, "Unzulässiger"),
])
def test_bad_packages_are_rejected(paketordner, files, msg):
    with pytest.raises(pakete.PaketFehler, match=msg):
        pakete.install(data=_zip(files))
    assert not os.path.exists(os.path.join(str(paketordner), "inst", "ok"))


def test_webui_install(paketordner):
    import threading
    import urllib.request
    import webui
    srv = webui.make_server("127.0.0.1", 0, str(paketordner / "out"), quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        with open(os.path.join(HERE, "beispiel-pakete", "tuerschild-1.1.0.swpaket"), "rb") as fh:
            body = json.dumps({"data": base64.b64encode(fh.read()).decode()}).encode()
        req = urllib.request.Request(url + "/api/paket-installieren", body,
                                     {"Content-Type": "application/json", "X-Steckwerk": "1"})
        d = json.loads(urllib.request.urlopen(req).read())
        assert d["ok"] and "tuerschild" in d["schema"]["models"]
    finally:
        srv.shutdown()
        srv.server_close()


def test_update_greift_ohne_neustart(paketordner):
    """Ein Paket-Update wirkt sofort – auch in Hilfsmodulen und Bibliotheken, die das Paket selbst zwischenspeichert."""
    inst = paketordner / "inst"
    bib, pkg = inst / "bibtest", inst / "nutzer"
    for d in (bib, pkg):
        d.mkdir(parents=True)
    (bib / "paket.json").write_text(json.dumps(dict(standard=1, id="bibtest", name="Bib", version="1.0.0",
                                                    steckwerk="2.4.0", modelle=[], bibliothek="bibliothek")))
    (pkg / "paket.json").write_text(json.dumps(dict(standard=1, id="nutzer", name="Nutzer", version="1.0.0",
                                                    steckwerk="2.4.0", modelle=["nutzer"],
                                                    benoetigt={"bibtest": "1.0.0"})))
    hilfe = (
        "import os, sys, importlib.util\n"
        "def _sub(name):\n"
        "    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name + '.py')\n"
        "    key = 'swpaket_nutzer_' + name\n"
        "    mod = sys.modules.get(key)\n"
        "    if mod is None or getattr(mod, '__file__', None) != path:\n"
        "        spec = importlib.util.spec_from_file_location(key, path)\n"
        "        mod = importlib.util.module_from_spec(spec)\n"
        "        sys.modules[key] = mod\n"
        "        spec.loader.exec_module(mod)\n"
        "    return mod\n"
        "from pakete import bibliothek\n"
        "INFO = dict(label='Nutzer', params=[], wert=(_sub('_hilfe').WERT, bibliothek('bibtest').WERT))\n"
        "def build(cfg, name='nutzer'):\n"
        "    raise ValueError('nur zum Laden')\n")
    (pkg / "nutzer.py").write_text(hilfe)

    def stand(n):
        (pkg / "_hilfe.py").write_text(f"WERT = {n}\n")
        (bib / "bibliothek.py").write_text(f"WERT = {n}\n")
        service.reload_pakete()
        return service.MODEL_INFO["nutzer"]["wert"]

    assert stand(1) == (1, 1)
    assert stand(22) == (22, 22), "nach dem Update muss der neue Code greifen, ohne Neustart"
