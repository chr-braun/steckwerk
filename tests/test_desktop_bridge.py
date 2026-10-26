"""Tests für Steckwerk Desktop: das Startskript packaging/swift/bridge_start.py."""
import json
import os
import subprocess
import sys
import time
import urllib.request

import webui

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "packaging", "swift", "bridge_start.py")


# --- bridge_start.py --------------------------------------------------------------------------------

def _env(tmp_path):
    env = dict(os.environ)
    env.update(HOME=str(tmp_path / "home"), XDG_STATE_HOME=str(tmp_path / "state"),
               STECKWERK_DATEN=str(tmp_path / "daten"), PYTHONDONTWRITEBYTECODE="1")
    os.makedirs(env["HOME"], exist_ok=True)
    return env


def _start(tmp_path, *extra):
    p = subprocess.Popen([sys.executable, "-u", BRIDGE, "--root", ROOT, "--out", str(tmp_path / "out"), *extra],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_env(tmp_path))
    line = p.stdout.readline().decode().strip()
    assert line.startswith("STECKWERK_PORT="), (line, p.stderr.read().decode() if p.poll() is not None else "")
    return p, line


def _post(port, path, body=None):
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), json.dumps(body or {}).encode(),
                                 {"Content-Type": "application/json", "X-Steckwerk": "1"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


def _wait(p, seconds):
    end = time.monotonic() + seconds
    while p.poll() is None and time.monotonic() < end:
        time.sleep(0.05)
    return p.poll()


def test_bridge_meldet_port_und_laeuft_im_app_modus(tmp_path):
    p, line = _start(tmp_path, "--no-reuse")
    try:
        port = int(line.split("=", 1)[1])
        assert _post(port, "/api/ping", {"client": "test"})["app"] == "steckwerk"
        assert _post(port, "/api/open-folder")["ok"] is not None      # nur im App-Modus vorhanden
    finally:
        p.stdin.close()
        assert _wait(p, 5) == 0, "Engine muss enden, wenn stdin schließt"


def test_bridge_endet_bei_quit(tmp_path):
    p, line = _start(tmp_path, "--no-reuse")
    port = int(line.split("=", 1)[1])
    _post(port, "/api/quit")
    assert _wait(p, 5) == 0
    p.stdin.close()


def test_bridge_nutzt_laufende_instanz_mit(tmp_path):
    first, line = _start(tmp_path, "--no-reuse")
    try:
        port = int(line.split("=", 1)[1])
        sys.path.insert(0, ROOT)
        env = _env(tmp_path)
        script = ("import json, steckwerk_app; "
                  "json.dump({'port': %d}, open(steckwerk_app.running_path(), 'w'))" % port)
        subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=env, check=True)
        second, line2 = _start(tmp_path)
        assert line2 == "STECKWERK_PORT=%d REUSED" % port
        assert _wait(second, 5) == 0
        second.stdin.close()
    finally:
        first.stdin.close()
        _wait(first, 5)


def test_server_fragt_keinen_rechnernamen_ab(monkeypatch, tmp_path):
    """Auf macOS hängt socket.getfqdn() für 127.0.0.1 teils viele Sekunden – der Start darf es nicht brauchen."""
    import socket

    def kein_dns(*a, **k):
        raise AssertionError("getfqdn darf beim Start nicht aufgerufen werden")

    monkeypatch.setattr(socket, "getfqdn", kein_dns)
    srv = webui.make_server("127.0.0.1", 0, str(tmp_path / "out"), quiet=True)
    try:
        assert srv.server_name == "127.0.0.1" and srv.server_port == srv.server_address[1] > 0
    finally:
        srv.server_close()


def test_bridge_ohne_webui(tmp_path):
    r = subprocess.run([sys.executable, BRIDGE, "--root", str(tmp_path)], capture_output=True, text=True,
                       env=_env(tmp_path), timeout=30)
    assert r.returncode == 2 and "webui.py nicht gefunden" in r.stderr
