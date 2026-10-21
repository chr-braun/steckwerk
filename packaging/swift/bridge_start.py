#!/usr/bin/env python3
"""
bridge_start.py – startet die Steckwerk-Engine für die native App „Steckwerk Desktop“.

  python3 bridge_start.py --engine <Ordner mit webui.py> [--port 0] [--out ~/Steckwerk] [--parent PID]
                          [--bundle "/Applications/Steckwerk Desktop.app"]

Nutzt webui.make_server unverändert und ergänzt nur zwei Endpunkte für die native App:
  POST /api/desktop-check     → gibt es eine neuere Steckwerk Desktop.app im Update-Kanal?
  POST /api/desktop-install   → laden, Prüfsumme und Version prüfen, die App in ihrem Ordner ersetzen
 Mit --port 0 sucht sich das System einen freien Port; der
gewählte Port steht als erste Zeile „STECKWERK_PORT=12345“ auf stdout. Mit --parent beendet sich
die Engine selbst, sobald die App nicht mehr läuft (kein Waisenprozess nach einem Absturz).
Nur Standardbibliothek, Python 3.8+.
"""
from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
import time


def parent_alive(pid: int) -> bool:
    if pid <= 0:
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return os.getppid() != 1


def watch_parent(pid: int, srv, interval: float = 2.0) -> None:
    while parent_alive(pid):
        time.sleep(interval)
    threading.Thread(target=srv.shutdown, daemon=True).start()
    time.sleep(3)
    os._exit(0)


def desktop_handler(base, bundle):
    """Handler der Engine plus die Update-Endpunkte für Steckwerk Desktop."""

    class DesktopHandler(base):
        def do_POST(self):
            path = self.path.split("?", 1)[0]
            if path not in ("/api/desktop-check", "/api/desktop-install"):
                return base.do_POST(self)
            if not self._host_ok() or not self.headers.get("X-Steckwerk"):
                return self._json({"ok": False, "error": "Zugriff verweigert"}, 403)
            import updater
            try:
                self._body()
                self._touch()
                if path == "/api/desktop-check":
                    return self._json(updater.desktop_check(bundle))
                target, version = updater.install_desktop(bundle or "")
                self._json({"ok": True, "version": version, "ziel": target,
                            "message": f"Steckwerk Desktop {version} ist installiert und startet gleich neu"})
            except (updater.UpdateFehler, ValueError, OSError) as e:
                self._json({"ok": False, "error": str(e)}, 400)

    return DesktopHandler


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bridge_start", description="Engine für Steckwerk Desktop")
    ap.add_argument("--engine", default=os.environ.get("STECKWERK_ENGINE", ""), help="Ordner mit webui.py")
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--out", default=os.path.join("~", "Steckwerk"), help="Ordner für „In Ordner speichern“")
    ap.add_argument("--parent", type=int, default=0, help="PID der App; Engine endet mit ihr")
    ap.add_argument("--bundle", default="", help="Pfad der laufenden Steckwerk Desktop.app (für Updates)")
    a = ap.parse_args(argv)

    engine = os.path.abspath(os.path.expanduser(a.engine or os.path.dirname(os.path.abspath(__file__))))
    if not os.path.exists(os.path.join(engine, "webui.py")):
        print(f"webui.py nicht gefunden in {engine}", file=sys.stderr)
        return 2
    sys.path.insert(0, engine)
    os.chdir(engine)
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

    import webui
    from steckwerk import migrate_legacy
    migrate_legacy()
    try:
        srv = webui.make_server("127.0.0.1", a.port, os.path.expanduser(a.out), quiet=True)
    except OSError as e:
        print(f"Port {a.port} ist belegt ({e})", file=sys.stderr)
        return 1
    srv.RequestHandlerClass = desktop_handler(srv.RequestHandlerClass, a.bundle or None)
    port = srv.server_address[1]
    print(f"STECKWERK_PORT={port}", flush=True)

    def stop(*_):
        threading.Thread(target=srv.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    if a.parent:
        threading.Thread(target=watch_parent, args=(a.parent, srv), daemon=True).start()
    try:
        srv.serve_forever()
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
