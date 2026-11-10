"""Paket „Spiele“: Mühle, Tic-Tac-Toe, Vier in einer Reihe, Kugellabyrinth, Solitär – schnittfertig und spielbar."""
import math
import os
import time

import pytest

import pakete
from steckwerk import Config, point_in_polygon
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")


@pytest.fixture(scope="module")
def mods(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("spiele")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "spiele"))
    yield m
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.mark.parametrize("T,kerf", [(3.0, 0.2), (4.0, 0.15), (2.0, 0.1)])
def test_standardwerte_cut_ready(mods, T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    for name, mod in mods.items():
        params = {p["key"]: p["default"] for p in mod.INFO["params"]}
        t = time.perf_counter()
        asm = mod.build(cfg, **params)
        assert time.perf_counter() - t < 2.0, f"{name} rechnet zu lange"
        assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("groesse,ablage", [(150, "seiten"), (205, "seiten"), (240, "schmal"), (260, "keine")])
def test_muehle(mods, groesse, ablage):
    cfg = Config(thickness=3.0)
    namen = dict(name_a="Ida", name_b="Opa") if ablage != "keine" else {}
    asm = mods["muehle"].build(cfg, groesse=groesse, ablage=ablage, motiv_b="schraffiert", **namen)
    assert_cut_ready(asm, cfg)
    brett = asm.part("muehle_brett")
    assert len(brett.holes) == (24 if ablage == "keine" else 42)
    steine = [p for p in asm.parts if "_stein_" in p.name]
    assert len(steine) == 18
    # Stein passt mit Luft in die Mulde
    assert asm.params["mulde"] - asm.params["stein"] >= 1.0


def test_muehle_zu_breit(mods):
    with pytest.raises(ValueError, match="schmale Ablage"):
        mods["muehle"].build(Config(), groesse=250, ablage="seiten")


@pytest.mark.parametrize("figuren", ["tanne_stern", "x_o", "herz_stern", "glocke_tanne", "herz_o"])
def test_tictactoe(mods, figuren):
    cfg = Config(thickness=3.0)
    asm = mods["tictactoe"].build(cfg, figuren=figuren, durchmesser=150, beschriftung="Familie Sonne")
    assert_cut_ready(asm, cfg)
    assert len(asm.part("tictactoe_brett").holes) == 19
    figs = [p for p in asm.parts if p.name not in ("tictactoe_brett", "tictactoe_boden")]
    assert len(figs) == 10
    r = asm.params["mulde"] / 2
    for p in figs:                                  # jede Figur liegt ganz in ihrer Mulde
        assert max(math.hypot(x, y) for x, y in p.outline) < r - 0.5


@pytest.mark.parametrize("scheibe", [24, 30, 34])
def test_vierreihe(mods, scheibe):
    cfg = Config(thickness=3.0)
    asm = mods["vierreihe"].build(cfg, scheibe=scheibe, beschriftung="Spieleabend")
    assert_cut_ready(asm, cfg)
    assert len([p for p in asm.parts if "_scheibe_" in p.name]) == 42
    assert len(asm.part("vierreihe_vorne").holes) == 42
    # Spalte breiter als die Scheibe, Sichtloch kleiner (Scheibe fällt nicht heraus)
    assert asm.params["spalte"] > scheibe + 1.0
    lo = asm.part("vierreihe_vorne").holes[0]
    d_loch = max(p[0] for p in lo) - min(p[0] for p in lo)
    assert d_loch < 0.85 * scheibe


@pytest.mark.parametrize("kugel", ["6", "8", "12", "16"])
@pytest.mark.parametrize("nummer", [1, 42])
def test_labyrinth(mods, kugel, nummer):
    L = mods["labyrinth"]
    cfg = Config(thickness=3.0)
    asm = L.build(cfg, kugel=kugel, nummer=nummer, fallen=6, beschriftung="Für Ida")
    assert_cut_ready(asm, cfg)
    nx, ny = asm.params["zellen"]
    # perfektes Labyrinth: Baum über alle Zellen
    offen = L.irrgarten(nx, ny, nummer)
    assert len(offen) == nx * ny - 1
    weg = L.loesung(offen, nx, ny, (0, ny - 1), (nx - 1, 0))
    assert weg[0] == (0, ny - 1) and weg[-1] == (nx - 1, 0)
    # jede Wandlage hat genau einen Durchbruch: die zusammenhängende Wegfläche
    waende = [p for p in asm.parts if "_wand_" in p.name]
    assert len(waende) == asm.params["wandlagen"] >= 1
    assert all(len(p.holes) == 1 for p in waende)
    assert len(asm.part("labyrinth_boden").holes) == 1 + asm.params["fallen"]
    # Wand hoch genug für die Kugel
    assert asm.params["wandlagen"] * cfg.T >= 0.6 * float(kugel) - 1e-9


def test_labyrinth_nummern_verschieden(mods):
    L = mods["labyrinth"]
    assert L.irrgarten(12, 12, 1) != L.irrgarten(12, 12, 2)
    assert L.irrgarten(12, 12, 5) == L.irrgarten(12, 12, 5)


def test_labyrinth_fallen_nicht_auf_dem_weg(mods):
    L = mods["labyrinth"]
    cfg = Config(thickness=3.0)
    asm = L.build(cfg, nummer=3, fallen=20)
    nx, ny = asm.params["zellen"]
    offen = L.irrgarten(nx, ny, 3)
    weg = L.loesung(offen, nx, ny, (0, ny - 1), (nx - 1, 0))
    boden = asm.part("labyrinth_boden")
    pw, w, f = asm.params["wegbreite"], asm.params["wand"], 13.0
    for h in boden.holes[1:]:
        cx = sum(p[0] for p in h) / len(h)
        cy = sum(p[1] for p in h) / len(h)
        zelle = (round((cx - f - pw / 2) / (pw + w)), round((cy - f - pw / 2) / (pw + w)))
        assert zelle not in weg


@pytest.mark.parametrize("form,kugel,rinne", [("englisch", "16", True), ("franzoesisch", "14", True),
                                               ("englisch", "25", False), ("franzoesisch", "20", True)])
def test_solitaer(mods, form, kugel, rinne):
    cfg = Config(thickness=3.0)
    asm = mods["solitaer"].build(cfg, form=form, kugel=kugel, rinne=rinne)
    assert_cut_ready(asm, cfg)
    assert len(asm.part("solitaer_brett").holes) == (33 if form == "englisch" else 37)
    assert ("solitaer_ring" in [p.name for p in asm.parts]) == rinne
    # Kugel liegt auf dem Lochrand und berührt den Boden nicht
    r = float(kugel) / 2
    h = asm.params["loch"] / 2
    assert r - math.sqrt(r * r - h * h) < cfg.T


def test_solitaer_zu_gross(mods):
    with pytest.raises(ValueError, match="passt nicht"):
        mods["solitaer"].build(Config(), kugel="25", rinne=True)


def test_englisch_vollstaendig(mods):
    """Alle Modelle haben englische Texte für Beschriftungen und Auswahl."""
    for name, mod in mods.items():
        en = mod.UEBERSETZUNG["en"]
        assert mod.INFO["label"] in en and mod.INFO["desc"] in en, name
        for p in mod.INFO["params"]:
            assert p["label"] in en, (name, p["label"])
            for o in p.get("options", []):
                assert o["label"] in en, (name, o["label"])
