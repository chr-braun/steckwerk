"""
projekte.py – gemerkte Projekte (Modell + Werte + Material) unter einem Namen.

Liegen in ~/.steckwerk/projekte.json (STECKWERK_HOME setzt einen anderen Ordner), damit
Browser-Oberfläche, Mac-App und Steckwerk Desktop dieselben Projekte sehen.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List

MAX_PROJEKTE = 200
_LOCK = threading.Lock()


class ProjektFehler(ValueError):
    pass


def datei() -> str:
    home = os.environ.get("STECKWERK_HOME") or os.path.expanduser("~/.steckwerk")
    return os.path.join(home, "projekte.json")


def _lesen() -> List[Dict[str, Any]]:
    try:
        with open(datei(), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    return [p for p in data.get("projekte", []) if isinstance(p, dict) and p.get("name")] \
        if isinstance(data, dict) else []


def _schreiben(liste: List[Dict[str, Any]]) -> None:
    path = datei()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "projekte": liste}, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def liste() -> List[Dict[str, Any]]:
    """Alle Projekte, zuletzt geänderte zuerst."""
    with _LOCK:
        return sorted(_lesen(), key=lambda p: -float(p.get("geaendert") or 0))


def speichern(name: str, projekt: Dict[str, Any]) -> Dict[str, Any]:
    name = " ".join(str(name or "").split())[:80]
    if not name:
        raise ProjektFehler("Bitte einen Namen für das Projekt angeben")
    if not isinstance(projekt, dict) or not projekt.get("model"):
        raise ProjektFehler("Projekt ohne Modell")
    eintrag = {
        "name": name,
        "model": str(projekt["model"])[:80],
        "params": projekt.get("params") if isinstance(projekt.get("params"), dict) else {},
        "config": projekt.get("config") if isinstance(projekt.get("config"), dict) else {},
        "profil": str(projekt.get("profil") or "")[:40],
        "geaendert": time.time(),
    }
    if len(json.dumps(eintrag, ensure_ascii=False)) > 200_000:
        raise ProjektFehler("Projekt zu groß")
    with _LOCK:
        alle = [p for p in _lesen() if p.get("name") != name]
        alle.insert(0, eintrag)
        _schreiben(alle[:MAX_PROJEKTE])
    return eintrag


def loeschen(name: str) -> None:
    with _LOCK:
        alle = _lesen()
        neu = [p for p in alle if p.get("name") != name]
        if len(neu) == len(alle):
            raise ProjektFehler(f"Projekt „{name}“ gibt es nicht")
        _schreiben(neu)
