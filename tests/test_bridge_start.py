"""Engine-Start für die native App (packaging/swift/bridge_start.py)."""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = os.path.join(ROOT, "packaging", "swift", "bridge_start.py")


def _post(port, path):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=b"{}", method="POST",
                                 headers={"X-Steckwerk": "1", "Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def test_freier_port_und_ende_mit_der_app(tmp_path):
    app = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    eng = subprocess.Popen([sys.executable, START, "--engine", ROOT, "--port", "0", "--out", str(tmp_path),
                            "--parent", str(app.pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        line = eng.stdout.readline().strip()
        assert line.startswith("STECKWERK_PORT="), (line, eng.stderr.read() if eng.poll() is not None else "")
        port = int(line.split("=", 1)[1])
        info = _post(port, "/api/ping")
        assert info["app"] == "steckwerk" and info["ok"]
        app.kill()
        app.wait()
        assert eng.wait(timeout=15) == 0
    finally:
        for p in (app, eng):
            if p.poll() is None:
                p.kill()


def test_fehlende_engine(tmp_path):
    r = subprocess.run([sys.executable, START, "--engine", str(tmp_path)], capture_output=True, text=True, timeout=20)
    assert r.returncode == 2 and "webui.py" in r.stderr


def test_desktop_update_endpunkte(tmp_path):
    import plistlib
    app = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    c = tmp_path / "Steckwerk Desktop.app" / "Contents"
    c.mkdir(parents=True)
    (c / "Info.plist").write_bytes(plistlib.dumps({"CFBundleShortVersionString": "2.8.0"}))
    kanal = tmp_path / "kanal"
    kanal.mkdir()
    (kanal / "feed.json").write_text(json.dumps({"standard": 1, "pakete": [], "desktop": {"version": "2.8.0"}}))
    env = dict(os.environ, STECKWERK_DATEN=str(tmp_path / "daten"), STECKWERK_UPDATE_KANAL=(kanal / "feed.json").as_uri())
    eng = subprocess.Popen([sys.executable, START, "--engine", ROOT, "--out", str(tmp_path / "out"),
                            "--parent", str(app.pid), "--bundle", str(c.parent)],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    try:
        port = int(eng.stdout.readline().strip().split("=", 1)[1])
        d = _post(port, "/api/desktop-check")
        assert d["ok"] and d["installiert"] == "2.8.0" and not d["neu"]
        assert _post(port, "/api/ping")["app"] == "steckwerk"               # Engine-Endpunkte bleiben
        try:
            _post(port, "/api/desktop-install")
            raise AssertionError("Installieren hätte scheitern müssen")
        except urllib.error.HTTPError as e:
            assert e.code == 400 and "schon aktuell" in json.loads(e.read().decode("utf-8"))["error"]
    finally:
        for p in (app, eng):
            if p.poll() is None:
                p.kill()
