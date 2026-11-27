"""
Schattenbox Weihnachtsnacht – fertige Vorlage der Leuchtenden Schattenbox mit eigenen Startwerten (alle Einstellungen bleiben änderbar).
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
VORGABEN = {'szene': 'weihnachtsnacht', 'form': 'spitzbogen', 'ebenen': 5, 'hintergrund': 'papier', 'ecken': 'ranke'}
INFO = B.vorlage_info('Schattenbox Weihnachtsnacht',
                      'Fertige Vorlage: Rentierschlitten über dem Dorf, Spitzbogenfenster, der ganze Himmel leuchtet durch Transparentpapier.',
                      VORGABEN)
UEBERSETZUNG = {"en": {
    'Schattenbox Weihnachtsnacht': 'Christmas night shadow box',
    'Fertige Vorlage: Rentierschlitten über dem Dorf, Spitzbogenfenster, der ganze Himmel leuchtet durch Transparentpapier.':
        'Ready-made template: reindeer sleigh above the village, pointed-arch window, the whole sky glows through tracing paper.',
}}
STYLE_KEYS = B.PARAM_KEYS                 # alle Einstellungen der Schattenbox werden durchgereicht


def build(cfg, name='schattenbox_weihnachtsnacht', **kw):
    return B.build(cfg, name=name, **{**VORGABEN, **kw})


def vorschau(cfg, **kw):
    return B.vorschau(cfg, name='schattenbox_weihnachtsnacht', **{**VORGABEN, **kw})
