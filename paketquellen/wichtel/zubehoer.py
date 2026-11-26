"""
Zubehör-Set – Paket „Wichtel“.

Wichtel, Zaun, Laterne und Briefkasten in Standardgröße; ist das Paket „Weihnachten“ installiert, kommen
Tannenbaum und Schneemann dazu. Jedes Stück ist eine eigene Baugruppe (eigene Datei beim Export).
"""
import importlib.util
import os

import pakete

_spec = importlib.util.spec_from_file_location("swpaket_wichtel__lade_zubehoer",
                                               os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lade.py"))
_lade = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_lade)

INFO = dict(label="Zubehör-Set", group="Zubehör",
            desc="Tannenbaum, Schneemann, Zaun, Laterne, Briefkasten und Wichtel in Standardgröße "
                 "(Tannenbaum und Schneemann mit dem Paket „Weihnachten“).",
            params=[])

UEBERSETZUNG = {"en": {
    "Zubehör-Set": "Accessory set",
    "Tannenbaum, Schneemann, Zaun, Laterne, Briefkasten und Wichtel in Standardgröße "
    "(Tannenbaum und Schneemann mit dem Paket „Weihnachten“).":
        "Fir tree, snowman, fence, lantern, mailbox and elf in standard size "
        "(fir tree and snowman with the “Christmas” package).",
}}


def build(cfg, name: str = "zubehoer"):
    out = []
    for stueck in ("tannenbaum", "schneemann"):
        try:
            out.append(pakete.bibliothek("weihnacht", stueck).build(cfg))
        except pakete.PaketFehler:
            pass                                          # ohne Weihnachten: nur die Wichtel-Stücke
    for stueck in ("zaun", "laterne", "briefkasten", "wichtel"):
        out.append(_lade.modul(stueck).build(cfg))
    return out
