"""Weihnachten 2.2.0: Edler Christbaumschmuck – zwölf detailreiche Anhänger."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")
MOTIVE = ["engel", "stern", "kugel", "glocke", "zapfen", "tannenbaum", "schneemann", "herz", "mond", "kerze",
          "geschenk", "stiefel"]


@pytest.fixture(scope="module")
def CS(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("christbaumschmuck")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "weihnacht"))
    yield m["christbaumschmuck"]
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_liste_aktuell(CS):
    assert [k for k, _ in CS.MOTIVE] == MOTIVE
    assert set(CS.ZEICHNER) == set(MOTIVE)


@pytest.mark.parametrize("motiv", MOTIVE)
def test_motiv_cut_ready_und_detailreich(CS, motiv):
    cfg = Config(thickness=3.0)
    asm = CS.build(cfg, motiv=motiv)
    assert len(asm.parts) == 1
    assert_cut_ready(asm, cfg)
    p = asm.parts[0]
    assert len(p.holes) >= 4, "Öse plus ausgeschnittene Fenster erwartet"
    assert len(p.engrave) >= 20, "feine Gravur erwartet"
    assert not any("weggelassen" in n for n in asm.notes)


@pytest.mark.parametrize("motiv", sorted({"stern", "kugel", "glocke", "herz", "schneemann", "geschenk", "stiefel",
                                           "engel"}))
def test_mit_namen(CS, motiv):
    cfg = Config(thickness=3.0)
    ohne = CS.build(cfg, motiv=motiv).parts[0]
    asm = CS.build(cfg, motiv=motiv, text="Emma")
    assert_cut_ready(asm, cfg)
    assert len(asm.parts[0].engrave) > len(ohne.engrave)


@pytest.mark.parametrize("T,kerf", [(2.0, 0.1), (4.0, 0.15)])
@pytest.mark.parametrize("motiv", ["engel", "herz", "tannenbaum", "kugel"])
def test_andere_staerken(CS, motiv, T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(CS.build(cfg, motiv=motiv, groesse=80), cfg)


def test_groesse_und_set(CS):
    cfg = Config(thickness=3.0)
    gross = CS.build(cfg, motiv="stern", groesse=150)
    assert_cut_ready(gross, cfg)
    x0, y0, x1, y1 = gross.parts[0].bbox()
    assert 150 <= y1 - y0 <= 165
    asm = CS.build(cfg, motiv="alle", anzahl=1)
    assert [p.name for p in asm.parts] == MOTIVE


def test_fehler_klar(CS):
    cfg = Config(thickness=3.0)
    with pytest.raises(ValueError):
        CS.build(cfg, motiv="rakete")
    with pytest.raises(ValueError):
        CS.build(cfg, motiv="stern", groesse=40)
    with pytest.raises(ValueError):
        CS.build(cfg, motiv="stern", text="Emma☃")
    asm = CS.build(cfg, motiv="mond", text="Emma")
    assert any("keinen Platz" in n for n in asm.notes)
