"""Paket „Wichtel“ 1.1.0, edles Zubehör: Kamin, Standuhr, Schaukelstuhl, Christbaum, Schneemann, Wichtelgarten –
schnittfertig in allen Varianten und Wichtelgrößen, und schnell genug für schwache Rechner."""
import os
import time

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")
NEU = ["kamin", "standuhr", "schaukelstuhl", "christbaum", "schneemann", "wichtelgarten"]


@pytest.fixture(scope="module")
def mods(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("wichtel_edel")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "wichtel"))
    yield m
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _std(mod, **kw):
    p = {p["key"]: p["default"] for p in mod.INFO["params"]}
    p.update(kw)
    return p


def test_im_paket(mods):
    m = pakete.read_manifest(os.path.join(QUELLEN, "wichtel"))
    assert m["version"] == "1.1.0"
    for n in NEU:
        assert n in m["modelle"] and n in mods
        assert mods[n].INFO["group"] == "Wichtel"
        assert "en" in mods[n].UEBERSETZUNG


@pytest.mark.parametrize("T,kerf", [(3.0, 0.2), (4.0, 0.15), (2.0, 0.1)])
@pytest.mark.parametrize("modell", NEU)
def test_standardwerte_cut_ready(mods, modell, T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(mods[modell].build(cfg, **_std(mods[modell])), cfg)


@pytest.mark.parametrize("modell", NEU)
@pytest.mark.parametrize("groesse", [60, 110, 160])
def test_wichtelgroessen(mods, modell, groesse):
    cfg = Config(thickness=3.0)
    assert_cut_ready(mods[modell].build(cfg, **_std(mods[modell], wichtel=groesse)), cfg)


@pytest.mark.parametrize("modell", NEU)
def test_zu_klein_meldet_sich(mods, modell):
    with pytest.raises(ValueError):
        mods[modell].build(Config(thickness=6.0), **_std(mods[modell], wichtel=40))


def test_kamin_varianten(mods):
    cfg = Config(thickness=3.0)
    asm = mods["kamin"].build(cfg, **_std(mods["kamin"], namen="Ida, Paul, Mia, Lio", struempfe=4))
    assert_cut_ready(asm, cfg)
    namen = {p.name for p in asm.parts}
    assert {"front", "rueckwand", "seite_l", "seite_r", "sockel", "sims", "zierblende", "feuer", "funkengitter",
            "kerze1", "kerze2", "uhr", "girlande", "strumpf4"} <= namen
    assert asm.part("strumpf1").engrave                        # Name graviert
    nackt = mods["kamin"].build(cfg, **_std(mods["kamin"], feuer=False, gitter=False, aufsatz="keine",
                                            girlande=False, struempfe=0, fries="wellen", kante="keine"))
    assert_cut_ready(nackt, cfg)
    assert len(nackt.parts) == 7
    # langer Name: nur der Anfangsbuchstabe, mit Hinweis
    lang = mods["kamin"].build(cfg, **_std(mods["kamin"], namen="Maximiliane-Theresa", struempfe=1))
    assert any("Anfangsbuchstabe" in n for n in lang.notes)


@pytest.mark.parametrize("krone", ["bogen", "giebel", "schwan"])
def test_standuhr_kronen(mods, krone):
    cfg = Config(thickness=3.0)
    asm = mods["standuhr"].build(cfg, **_std(mods["standuhr"], krone=krone, inschrift="Anno 1890"))
    assert_cut_ready(asm, cfg)
    assert {"kopf", "pendel", "gewichte", "zierblende"} <= {p.name for p in asm.parts}


@pytest.mark.parametrize("neigung", [0, 14, 25])
def test_schaukelstuhl_neigung(mods, neigung):
    cfg = Config(thickness=3.0)
    asm = mods["schaukelstuhl"].build(cfg, **_std(mods["schaukelstuhl"], neigung=neigung, motiv="stern"))
    assert_cut_ready(asm, cfg)
    assert {"seite_l", "seite_r", "sitz", "lehne", "kissen", "strickkorb_a", "strickkorb_b"} <= \
        {p.name for p in asm.parts}


@pytest.mark.parametrize("schmuck", ["sterne", "herzen", "kugeln", "keiner"])
@pytest.mark.parametrize("etagen", [3, 6])
def test_christbaum(mods, schmuck, etagen):
    cfg = Config(thickness=3.0)
    asm = mods["christbaum"].build(cfg, **_std(mods["christbaum"], schmuck=schmuck, etagen=etagen, geschenke=5))
    assert_cut_ready(asm, cfg)
    assert len([p for p in asm.parts if p.name.startswith("geschenk")]) == 10


@pytest.mark.parametrize("hut", ["zylinder", "muetze"])
@pytest.mark.parametrize("hand", ["besen", "laterne", "keins"])
def test_schneemann(mods, hut, hand):
    cfg = Config(thickness=3.0)
    assert_cut_ready(mods["schneemann"].build(cfg, **_std(mods["schneemann"], hut=hut, hand=hand)), cfg)


def test_garten_ohne_platte_und_einzeln(mods):
    cfg = Config(thickness=3.0)
    asm = mods["wichtelgarten"].build(cfg, **_std(mods["wichtelgarten"], platte=False))
    assert_cut_ready(asm, cfg)
    assert "wiese" not in {p.name for p in asm.parts}
    nur = mods["wichtelgarten"].build(cfg, **_std(mods["wichtelgarten"], schubkarre=False, giesskanne=False,
                                                  vogelhaus=False, blumen=False, kuerbisse=False))
    assert_cut_ready(nur, cfg)
    assert {p.name for p in nur.parts} == {"fliegenpilze", "wiese"}


def test_rechenzeit(mods):
    """Auch auf schwachen Rechnern flott: alle sechs zusammen bauen hier deutlich unter drei Sekunden."""
    cfg = Config(thickness=3.0)
    t = time.perf_counter()
    for n in NEU:
        mods[n].build(cfg, **_std(mods[n]))
    assert time.perf_counter() - t < 3.0
