"""Engine-Start für die native App (packaging/swift/bridge_start.py)."""
import json
import os
import subprocess
import sys
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
