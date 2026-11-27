"""
Schattenbox Winterdorf – fertige Vorlage der Leuchtenden Schattenbox mit eigenen Startwerten (alle Einstellungen bleiben änderbar).
"""
from __future__ import annotations

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name: str):
    import importlib.util
    path = os.path.join(_here, name + ".py")
    key = "swpaket_schattenbox_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


B = _sub("schattenbox")
VORGABEN = {'szene': 'winterdorf', 'form': 'bogen', 'ebenen': 5, 'hintergrund': 'sterne', 'ecken': 'blatt'}
INFO = B.vorlage_info('Schattenbox Winterdorf',
                      'Fertige Vorlage: Winterdorf mit Kirche, Mond und Sternen im Rundbogenfenster, LED-Teelicht dahinter.',
                      VORGABEN)
UEBERSETZUNG = {"en": {
    'Schattenbox Winterdorf': 'Winter village shadow box',
    'Fertige Vorlage: Winterdorf mit Kirche, Mond und Sternen im Rundbogenfenster, LED-Teelicht dahinter.':
        'Ready-made template: winter village with church, moon and stars in a round-arch window, LED tea light behind.',
}}
STYLE_KEYS = B.PARAM_KEYS                 # alle Einstellungen der Schattenbox werden durchgereicht


def build(cfg, name='schattenbox_winterdorf', **kw):
    return B.build(cfg, name=name, **{**VORGABEN, **kw})


def vorschau(cfg, **kw):
    return B.vorschau(cfg, name='schattenbox_winterdorf', **{**VORGABEN, **kw})
