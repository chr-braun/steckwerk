"""
Modell-Registry von Steckwerk.

Im Kern stecken nur die Häuser (Wichtelhaus, Serie) und die Werkzeuge (eigene Motive, Gravur).
Alle Dekos – Christbaumschmuck, Schwibbogen, Zubehör, Fahrzeuge … – kommen als Pakete (Plugins).
Jedes Modell-Modul bietet build(cfg, **parameter) -> Assembly (Serie: Liste von Assemblies).
"""
from __future__ import annotations

from models import serie, wichtelhaus

MODELS = {
    "wichtelhaus": wichtelhaus,
}

__all__ = ["MODELS", "serie"] + list(MODELS)
