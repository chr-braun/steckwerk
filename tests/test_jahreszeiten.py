"""Paket „Jahreszeiten“: fünf feine Gravurmodelle – Winterkranz, Eisblumen, Blütenmandala, Sommersonne, Herbstkranz."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")
MODELLE = ["winterkranz", "eisblumen", "bluetenmandala", "sommersonne", "herbstkranz"]

# Hauptvarianten je Modell (alle Auswahlwerte kommen mindestens einmal vor)
VARIANTEN = {
    "winterkranz": [dict(), dict(mitte="stern", kranz="stechpalme", boegen="16"),
                    dict(mitte="text", kranz="zapfen", boegen="32")],
    "eisblumen": [dict(), dict(form="spitzbogen", dichte="dicht", startwert=4),
                  dict(form="rechteck", sprossen=False, dichte="licht")],
    "bluetenmandala": [dict(), dict(kranz="tulpen", mitte="schmetterling", zaehlig="8"),
                       dict(kranz="kirsch", mitte="text", zaehlig="16")],
    "sommersonne": [dict(), dict(mitte="sonnenblume", ring="perlen", strahlen="8"),
                    dict(mitte="text", strahlen="16")],
    "herbstkranz": [dict(), dict(laub="ahorn", startwert=2),
                    dict(form="medaille", laub="eiche", startwert=3)],
}
FAELLE = [(m, v) for m in MODELLE for v in VARIANTEN[m]]


@pytest.fixture(scope="module")
def mods(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("jahreszeiten")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "jahreszeiten"))
    yield m
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_alle_modelle_geladen(mods):
    assert sorted(mods) == sorted(MODELLE)
    for m in MODELLE:
        assert mods[m].INFO["group"] == "Jahreszeiten"


@pytest.mark.parametrize("modell,werte", FAELLE, ids=[f"{m}-{i}" for m in MODELLE for i in range(3)])
def test_cut_ready_und_fein(mods, modell, werte):
    cfg = Config(thickness=3.0)
    asm = mods[modell].build(cfg, **werte)
    assert len(asm.parts) == 1
    assert_cut_ready(asm, cfg)
    p = asm.parts[0]
    assert len(p.holes) >= 2, "Durchbrüche erwartet"
    assert len(p.engrave) >= 30, "feine Gravur erwartet"
    assert not any("weggelassen" in n for n in asm.notes), asm.notes


@pytest.mark.parametrize("T,kerf,feinheit", [(2.0, 0.1, "fein"), (4.0, 0.15, "kraeftig")])
@pytest.mark.parametrize("modell", MODELLE)
def test_andere_staerken(mods, modell, T, kerf, feinheit):
    cfg = Config(thickness=T, kerf=kerf)
    asm = mods[modell].build(cfg, feinheit=feinheit)
    assert_cut_ready(asm, cfg)
    assert len(asm.parts[0].engrave) >= 30


@pytest.mark.parametrize("modell", MODELLE)
def test_klein_und_ohne_oese(mods, modell):
    cfg = Config(thickness=3.0)
    lo = min(p["min"] for p in mods[modell].INFO["params"] if p["key"] == "groesse")
    asm = mods[modell].build(cfg, groesse=lo, oese=False)
    assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("modell", MODELLE)
def test_anzahl(mods, modell):
    asm = mods[modell].build(Config(thickness=3.0), anzahl=2)
    assert len(asm.parts) == 2


@pytest.mark.parametrize("modell", MODELLE)
def test_ungueltige_auswahl(mods, modell):
    with pytest.raises(ValueError):
        mods[modell].build(Config(thickness=3.0), feinheit="riesig")


def test_englisch_vollstaendig(mods):
    """Alle Modelle haben englische Texte für Beschriftungen und Auswahl."""
    for name, mod in mods.items():
        en = mod.UEBERSETZUNG["en"]
        assert mod.INFO["label"] in en and mod.INFO["desc"] in en, name
        for p in mod.INFO["params"]:
            assert p["label"] in en, (name, p["label"])
            for o in p.get("options", []):
                assert o["label"] in en, (name, o["label"])
