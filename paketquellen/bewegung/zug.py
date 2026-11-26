"""
Zug-Set – Lok, Tender und Wagen in passender Größe, mit Kupplungslöchern zum Verbinden.

Baut die Fahrzeuge aus dem Modell „Steckfahrzeug“ (fahrzeug.py im selben Paket), alle im Maßstab der Lok.
"""
from __future__ import annotations

import os
import sys
from typing import List, Optional

from steckwerk import Assembly, Config
from models import _deko as dk
from pakete import integer, num, sel, txt

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    """Nachbarmodul aus demselben Paket laden (gleicher Name wie beim Paket-Lader)."""
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_bewegung_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


F = _sub("fahrzeug")
SYM, SCHRIFT = F.SYM, F.SCHRIFT

INFO = dict(
    label="Zug-Set", group="Fahrzeuge",
    desc="Lok, Tender und Wagen in passender Größe – mit Kupplungslöchern zum Verbinden.",
    params=[num("length", "Länge der Lok", 150, 100, 300, help="Tender und Wagen wachsen mit"),
            num("width", "Breite", 60, 30, 250),
            integer("wagen", "Anzahl Wagen", 2, 0, 6),
            sel("wagentyp", "Wagen", [("gemischt", "abwechselnd"), ("personenwagen", "Personenwagen"),
                                      ("gueterwagen", "Güterwagen")], "gemischt"),
            txt("text", "Aufschriften", "", "mit Komma je Fahrzeug: Lok, Tender, Wagen … – " + SYM, 80,
                symbols=True),
            sel("textrahmen", "Textrahmen", dk.SIGNS, "ohne", section=SCHRIFT)]
           + F._schrift() + [
            sel("zierlinie", "Zierlinie", dk.TRIMS, "keine", section="Zierlinien")])


def build(cfg: Config, name: str = "zug", length: Optional[float] = None, width: Optional[float] = None,
          wagen: int = 2, wagentyp: str = "gemischt", text: str = "", schrift: str = "normal",
          schreibweise: str = "gross", textrahmen: str = "ohne", zierlinie: str = "keine") -> List[Assembly]:
    """Lok + Tender + Wagen, alle im Maßstab der Lok, mit Kupplungslöchern."""
    k = (length or 150.0) / 150.0
    W = width or 60.0
    kinds = ["lok", "tender"] + [("personenwagen", "gueterwagen")[i % 2] if wagentyp == "gemischt" else wagentyp
                                 for i in range(int(wagen))]
    names = [t.strip() for t in text.split(",")] if text else []
    out = []
    for i, v in enumerate(kinds):
        L = F.DEFAULTS[v]["length"] * k
        out.append(F.build(cfg, name=f"zug_{i + 1:02d}_{v}", vehicle=v, length=L, width=min(W, 0.8 * L),
                           text=names[i] if i < len(names) else "", kupplung=True, schrift=schrift,
                           schreibweise=schreibweise, textrahmen=textrahmen, zierlinie=zierlinie))
    return out
