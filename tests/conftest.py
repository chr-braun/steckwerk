"""Gemeinsame Test-Helfer: Projektordner in den Importpfad, Validierungs-Assert."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from steckwerk import Config, layout  # noqa: E402
from validator import validate_assembly, validate_sheets  # noqa: E402


def check(asm, cfg):
    """Validiert Baugruppe + Blattlayout und gibt den Report zurück."""
    rep = validate_assembly(asm, cfg)
    sheets = layout([p.compensated(cfg.kerf_offset) for p in asm.parts], cfg)
    validate_sheets(sheets, cfg, rep)
    return rep


def assert_cut_ready(asm, cfg):
    rep = check(asm, cfg)
    assert rep.passed, "\n" + "\n".join(e.line() for e in rep.errors)
    return rep


@pytest.fixture
def cfg():
    return Config()


# Materialstärken/Kerfs, mit denen jedes Modell funktionieren muss
MATERIALS = [(3.0, 0.2), (2.0, 0.1), (4.0, 0.15), (6.0, 0.3), (3.0, 0.0)]


@pytest.fixture(autouse=True)
def _deutsche_dialoge(monkeypatch):
    """Mac-Dialoge in Tests immer deutsch, ohne die Systemsprache abzufragen."""
    monkeypatch.setenv("STECKWERK_SPRACHE", "de")
    import steckwerk_app
    monkeypatch.setattr(steckwerk_app, "_LANG", None)


# --- Modelle, die seit 2.18 als Pakete kommen (Weihnachten, Wichtel, Bewegung) -----------------------------
QUELLEN = os.path.join(ROOT, "paketquellen")
KERN_PAKETE = ("verzierungen", "weihnacht", "wichtel", "bewegung")


_GELADEN = {}


def lade(pid, name):
    """Modellmodul direkt aus den Paketquellen laden (ohne Installation), z. B. lade("weihnacht", "ornament")."""
    import pakete
    if (pid, name) not in _GELADEN:
        _GELADEN[pid, name] = pakete._import(os.path.join(QUELLEN, pid), pid, name)
    return _GELADEN[pid, name]


@pytest.fixture(scope="session")
def _kern_pakete_ordner(tmp_path_factory):
    d = tmp_path_factory.mktemp("kernpakete")
    for pid in KERN_PAKETE:
        os.symlink(os.path.join(QUELLEN, pid), str(d / pid))
    return str(d)


@pytest.fixture
def mit_paketen(_kern_pakete_ordner, tmp_path, monkeypatch):
    """service kennt die früheren Kernmodelle (Christbaumschmuck, Zubehör, Fahrzeuge …) aus den Paketquellen."""
    import service
    monkeypatch.setenv("STECKWERK_PAKETE", _kern_pakete_ordner)
    monkeypatch.setenv("STECKWERK_DATEN", str(tmp_path / "daten"))
    service.reload_pakete()
    yield service
    monkeypatch.undo()
    service.reload_pakete()


@pytest.fixture(scope="module")
def mit_paketen_modul(_kern_pakete_ordner, tmp_path_factory):
    """Wie mit_paketen, aber für modulweite Fixtures."""
    import service
    mp = pytest.MonkeyPatch()
    mp.setenv("STECKWERK_PAKETE", _kern_pakete_ordner)
    mp.setenv("STECKWERK_DATEN", str(tmp_path_factory.mktemp("daten")))
    service.reload_pakete()
    yield service
    mp.undo()
    service.reload_pakete()
