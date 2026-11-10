"""Weihnachten 2.1.0: Edler Namensanhänger mit echter Schreibschrift und Winter-/Adventsszenen."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_, MODS = pakete.load_folder(os.path.join(HERE, "paketquellen", "weihnacht"))
NA = MODS["namensanhaenger"]
SS = NA.SS
SZ = NA.SZ


@pytest.mark.parametrize("schrift", [k for k, _ in SS.SCHRIFTEN])
def test_schriften_vollstaendig(schrift):
    assert SS.fehlende("Äpfel Öse Über ß Zoë José 2026 & Co.", schrift) == []
    s = SS.Satz("Anna", schrift)
    assert s.breite > s.hoehe > 0


@pytest.mark.parametrize("szene", [k for k, _ in SZ.SZENEN])
def test_szenen_cut_ready(szene):
    cfg = Config(thickness=3.0)
    asm = NA.build(cfg, namen="Emma", szene=szene)
    assert len(asm.parts) == 1
    assert_cut_ready(asm, cfg)
    assert asm.parts[0].holes and asm.parts[0].engrave


@pytest.mark.parametrize("schrift", [k for k, _ in SS.SCHRIFTEN])
@pytest.mark.parametrize("name", ["Jörg", "Anna Lena", "Maximilian"])
def test_schriftzug_haelt_zusammen(schrift, name):
    """i-Punkte, Umlaute und Wörter hängen am Schriftzug – nichts fällt beim Lasern heraus."""
    cfg = Config(thickness=3.0)
    asm = NA.build(cfg, namen=name, schrift=schrift, szene="winterwald", zier="flocke")
    assert_cut_ready(asm, cfg)
    assert not [n for n in asm.notes if "weggelassen" in n], asm.notes


@pytest.mark.parametrize("ausfuehrung", ["medaillon", "spitze"])
@pytest.mark.parametrize("rahmen", [k for k, _ in NA.RAHMEN])
def test_flaechige_ausfuehrungen(ausfuehrung, rahmen):
    cfg = Config(thickness=2.0)
    asm = NA.build(cfg, namen="Clara", ausfuehrung=ausfuehrung, rahmen=rahmen, zeile="Frohe Weihnachten")
    assert len(asm.parts) == (2 if ausfuehrung == "medaillon" else 1)
    assert_cut_ready(asm, cfg)
    assert asm.parts[0].engrave


def test_medaillon_lagen_deckungsgleich():
    asm = NA.build(Config(thickness=2.0), namen="Ida", ausfuehrung="medaillon")
    grund, rahmen = asm.parts
    assert [p.name for p in asm.parts] == ["ida_grundplatte", "ida_spitzenrahmen"]
    gb, rb = grund.bbox(), rahmen.bbox()
    assert all(abs(a - b) < 0.6 for a, b in zip(gb, rb))
    assert len(rahmen.holes) > 10                       # Fenster plus Spitze


@pytest.mark.parametrize("ausfuehrung", ["schriftzug", "medaillon"])
def test_herz(ausfuehrung):
    cfg = Config(thickness=3.0)
    assert_cut_ready(NA.build(cfg, namen="Lea", form="herz", ausfuehrung=ausfuehrung, szene="adventskranz"), cfg)


def test_ein_anhaenger_je_name():
    asm = NA.build(Config(thickness=3.0), namen="Anna|Ben|Anna", szene="ohne")
    assert [p.name for p in asm.parts] == ["anna", "ben", "anna_2"]


def test_fehler_verstaendlich():
    cfg = Config(thickness=3.0)
    with pytest.raises(ValueError, match="Namen"):
        NA.build(cfg, namen=" | ")
    with pytest.raises(ValueError, match="Zeichen"):
        NA.build(cfg, namen="Ωmega")
    with pytest.raises(ValueError, match="zu lang"):
        NA.build(cfg, namen="Maximiliane-Friederike", groesse=60)


@pytest.mark.parametrize("dicke,kerf", [(3.0, 0.2), (4.0, 0.15), (2.0, 0.1)])
def test_materialien(dicke, kerf):
    cfg = Config(thickness=dicke, kerf=kerf)
    assert_cut_ready(NA.build(cfg, namen="Paul", szene="schlitten"), cfg)
