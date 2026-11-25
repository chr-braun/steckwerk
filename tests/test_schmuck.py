"""Paket „Schmuck“ (ab 2.8.0): Ohrhänger-Paare (Christbaumschmuck hat eigene Tests)."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _laden():
    """Schmuck braucht seit 1.1.0 das Paket „verzierungen“: kurz in ein Temp-Verzeichnis installieren."""
    import tempfile
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tempfile.mkdtemp(prefix="schmuck-")
    os.environ["STECKWERK_PAKETE"] = os.path.join(d, "inst")
    os.environ["STECKWERK_DATEN"] = os.path.join(d, "daten")
    try:
        pakete.install(os.path.join(HERE, "paketquellen", "verzierungen"))
        return pakete.load_folder(os.path.join(HERE, "paketquellen", "schmuck"))[1]
    finally:
        for k, v in alt.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


MODS = _laden()
OH = MODS["ohrhaenger"]


@pytest.mark.parametrize("motiv", [m for m, _ in OH.MOTIVE])
@pytest.mark.parametrize("stil", [s for s, _ in OH.STILE])
def test_motive_cut_ready(motiv, stil):
    cfg = Config(thickness=3.0)
    asm = OH.build(cfg, motiv=motiv, stil=stil)
    assert [p.name for p in asm.parts] == ["links", "rechts"]
    assert_cut_ready(asm, cfg)
    for p in asm.parts:
        assert p.holes, "Öse fehlt"
    if stil == "graviert":
        assert all(p.engrave for p in asm.parts)


def test_paar_ist_gespiegelt():
    asm = OH.build(Config(thickness=2.0), motiv="fluegel")
    a, b = asm.parts
    xa = sorted(round(x, 3) for x, _ in a.outline)
    xb = sorted(round(-x, 3) for x, _ in b.outline)
    assert xa == xb


@pytest.mark.parametrize("zwischen", ["kreis", "stern", "tropfen", "mond"])
def test_zwischenteil(zwischen):
    cfg = Config(thickness=2.0)
    asm = OH.build(cfg, motiv="tropfen", zwischen=zwischen, paar=False)
    assert [p.name for p in asm.parts] == ["einzeln", "einzeln_oben"]
    assert len(asm.parts[1].holes) == 2
    assert_cut_ready(asm, cfg)


def test_kleine_ohrringe_bleiben_laserfest():
    cfg = Config(thickness=1.5)
    for m, _ in OH.MOTIVE:
        assert_cut_ready(OH.build(cfg, motiv=m, groesse=20, loch=1.4), cfg)


def test_rahmen_zu_breit():
    with pytest.raises(ValueError, match="Rahmen"):
        OH.build(Config(thickness=3.0), motiv="mond", groesse=20, stil="rahmen", rand=6)
