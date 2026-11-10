"""Weihnachten 2.1.0: Edler Namensanhänger mit echter Schreibschrift und Winter-/Adventsszenen."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")
SCHRIFTEN = ["elegant", "schwungvoll", "rund"]
SZENEN = ["winterdorf", "winterwald", "schneemann", "schlitten", "adventskranz", "christbaum", "plaetzchen",
          "geschenke", "ohne"]
RAHMEN = ["bluetenkranz", "spitze", "ranken", "sterne", "herzen", "perlen"]


@pytest.fixture(scope="module")
def NA(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("namensanhaenger")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "weihnacht"))
    yield m["namensanhaenger"]
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_listen_aktuell(NA):
    assert [k for k, _ in NA.SS.SCHRIFTEN] == SCHRIFTEN
    assert [k for k, _ in NA.SZ.SZENEN] == SZENEN
    assert [k for k, _ in NA.RAHMEN] == RAHMEN


@pytest.mark.parametrize("schrift", SCHRIFTEN)
def test_schriften_vollstaendig(NA, schrift):
    SS = NA.SS
    assert SS.fehlende("Äpfel Öse Über ß Zoë José 2026 & Co.", schrift) == []
    s = SS.Satz("Anna", schrift)
    assert s.breite > s.hoehe > 0


@pytest.mark.parametrize("szene", SZENEN)
def test_szenen_cut_ready(NA, szene):
    cfg = Config(thickness=3.0)
    asm = NA.build(cfg, namen="Emma", szene=szene)
    assert len(asm.parts) == 1
    assert_cut_ready(asm, cfg)
    assert asm.parts[0].holes and asm.parts[0].engrave


@pytest.mark.parametrize("schrift", SCHRIFTEN)
@pytest.mark.parametrize("name", ["Jörg", "Anna Lena", "Maximilian"])
def test_schriftzug_haelt_zusammen(NA, schrift, name):
    """i-Punkte, Umlaute und Wörter hängen am Schriftzug – nichts fällt beim Lasern heraus."""
    cfg = Config(thickness=3.0)
    asm = NA.build(cfg, namen=name, schrift=schrift, szene="winterwald", zier="flocke")
    assert_cut_ready(asm, cfg)
    assert not [n for n in asm.notes if "weggelassen" in n], asm.notes


@pytest.mark.parametrize("ausfuehrung", ["medaillon", "spitze"])
@pytest.mark.parametrize("rahmen", RAHMEN)
def test_flaechige_ausfuehrungen(NA, ausfuehrung, rahmen):
    cfg = Config(thickness=2.0)
    asm = NA.build(cfg, namen="Clara", ausfuehrung=ausfuehrung, rahmen=rahmen, zeile="Frohe Weihnachten")
    assert len(asm.parts) == (2 if ausfuehrung == "medaillon" else 1)
    assert_cut_ready(asm, cfg)
    assert asm.parts[0].engrave


def test_medaillon_lagen_deckungsgleich(NA):
    asm = NA.build(Config(thickness=2.0), namen="Ida", ausfuehrung="medaillon")
    grund, rahmen = asm.parts
    assert [p.name for p in asm.parts] == ["ida_grundplatte", "ida_spitzenrahmen"]
    gb, rb = grund.bbox(), rahmen.bbox()
    assert all(abs(a - b) < 0.6 for a, b in zip(gb, rb))
    assert len(rahmen.holes) > 10                       # Fenster plus Spitze


@pytest.mark.parametrize("ausfuehrung", ["schriftzug", "medaillon"])
def test_herz(NA, ausfuehrung):
    cfg = Config(thickness=3.0)
    assert_cut_ready(NA.build(cfg, namen="Lea", form="herz", ausfuehrung=ausfuehrung, szene="adventskranz"), cfg)


def test_ein_anhaenger_je_name(NA):
    asm = NA.build(Config(thickness=3.0), namen="Anna|Ben|Anna", szene="ohne")
    assert [p.name for p in asm.parts] == ["anna", "ben", "anna_2"]


def test_fehler_verstaendlich(NA):
    cfg = Config(thickness=3.0)
    with pytest.raises(ValueError, match="Namen"):
        NA.build(cfg, namen=" | ")
    with pytest.raises(ValueError, match="Zeichen"):
        NA.build(cfg, namen="Ωmega")
    with pytest.raises(ValueError, match="zu lang"):
        NA.build(cfg, namen="Maximiliane-Friederike", groesse=60)


@pytest.mark.parametrize("dicke,kerf", [(3.0, 0.2), (4.0, 0.15), (2.0, 0.1)])
def test_materialien(NA, dicke, kerf):
    cfg = Config(thickness=dicke, kerf=kerf)
    assert_cut_ready(NA.build(cfg, namen="Paul", szene="schlitten"), cfg)
