"""
Schattenbox Spukschloss – fertige Vorlage der Leuchtenden Schattenbox mit eigenen Startwerten (alle Einstellungen bleiben änderbar).
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
VORGABEN = {'szene': 'spukschloss', 'form': 'spitzbogen', 'ebenen': 4, 'hintergrund': 'sterne', 'ecken': 'schnoerkel'}
INFO = B.vorlage_info('Schattenbox Spukschloss',
                      'Fertige Vorlage: Spukschloss mit Hexe vor dem Vollmond, Spitzbogenfenster mit Schnörkeln – für Halloween.',
                      VORGABEN)
UEBERSETZUNG = {"en": {
    'Schattenbox Spukschloss': 'Haunted castle shadow box',
    'Fertige Vorlage: Spukschloss mit Hexe vor dem Vollmond, Spitzbogenfenster mit Schnörkeln – für Halloween.':
        'Ready-made template: haunted castle with a witch in front of the full moon, pointed-arch window with flourishes – for Halloween.',
}}
STYLE_KEYS = B.PARAM_KEYS                 # alle Einstellungen der Schattenbox werden durchgereicht


def build(cfg, name='schattenbox_spukschloss', **kw):
    return B.build(cfg, name=name, **{**VORGABEN, **kw})


def vorschau(cfg, **kw):
    return B.vorschau(cfg, name='schattenbox_spukschloss', **{**VORGABEN, **kw})
