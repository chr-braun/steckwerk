"""Pakete, die andere Pakete brauchen (benoetigt/bibliothek, ab 2.4.0) und die mitgelieferten Paketquellen."""
import json
import os
import sys

import pytest

import pakete
import service
import updater
from steckwerk import Config
from conftest import assert_cut_ready

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "packaging"))
import update_kanal  # noqa: E402
QUELLEN = os.path.join(HERE, "paketquellen")
NEUE = ["verzierungen", "umrandungen", "wichtelmoebel", "wichteltuer", "wichtelzubehoer"]
WELT = ["wichtelwelt"]                                                  # braucht Verzierungen 1.1.0
UMGESTELLT = ["ebenen", "filigran", "halloween", "weihnacht"]           # nutzen seit 2026-10-15 die Bibliothek


@pytest.fixture
def inst(tmp_path, monkeypatch):
    monkeypatch.setenv("STECKWERK_PAKETE", str(tmp_path / "inst"))
    monkeypatch.setenv("STECKWERK_DATEN", str(tmp_path / "daten"))
    yield tmp_path
    monkeypatch.delenv("STECKWERK_PAKETE")
    service.reload_pakete()


def test_manifeste():
    for pid in NEUE:
        m = pakete.read_manifest(os.path.join(QUELLEN, pid))
        assert m["id"] == pid and m["name_en"] and m["beschreibung_en"]
        if pid != "verzierungen":
            assert m["benoetigt"] == {"verzierungen": "1.0.0"}
    for pid in UMGESTELLT:
        m = pakete.read_manifest(os.path.join(QUELLEN, pid))
        assert m["benoetigt"] == {"verzierungen": "1.1.0"}
        assert not [f for f in os.listdir(os.path.join(QUELLEN, pid)) if f in ("_kit.py", "_ebenen.py", "_figuren.py")]
    for pid in WELT:
        m = pakete.read_manifest(os.path.join(QUELLEN, pid))
        assert m["name_en"] and m["beschreibung_en"] and m["benoetigt"] == {"verzierungen": "1.1.0"}
    assert pakete.read_manifest(os.path.join(QUELLEN, "verzierungen"))["bibliothek"] == "bibliothek"


def test_abhaengigkeit_fehlt_und_entfernen(inst):
    with pytest.raises(pakete.PaketFehler, match="braucht zuerst das Paket"):
        pakete.install(os.path.join(QUELLEN, "umrandungen"))
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    m, _ = pakete.install(os.path.join(QUELLEN, "umrandungen"))
    assert m["id"] == "umrandungen"
    with pytest.raises(pakete.PaketFehler, match="noch gebraucht von: Umrandungen"):
        pakete.remove("verzierungen")
    pakete.remove("umrandungen")
    pakete.remove("verzierungen")


def test_bibliothek_laden(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    Z = pakete.bibliothek("verzierungen")
    assert Z.VERSION == "1.1.0" and Z.F and Z.G and pakete.bibliothek("verzierungen") is Z
    cfg = Config()
    fig = Z.Figur().add(Z.kartusche(80, 50, "oval"))
    fig.merge(Z.ausschnitt("herz", 0, 25, 16))
    notes = []
    teil = Z.figur_teil(cfg, "probe", fig, notes)
    assert teil.holes and not notes
    b = Z.brett("brett", 40, 20, cfg.T, links=[(10, 6, "l", 1)], rechts=[(10, 6, "r", 2)])
    assert {f.id for f in b.features} == {"l", "r"}
    with pytest.raises(pakete.PaketFehler):
        pakete.bibliothek("gibtsnicht")


def test_updater_installiert_abhaengigkeit_mit(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))          # zum Prüfen beim Packen
    paths = [pakete.pack(os.path.join(QUELLEN, pid), str(inst / "pk"))[0] for pid in ("verzierungen", "wichtelmoebel")]
    pakete.remove("verzierungen")
    kanal = inst / "kanal"
    update_kanal.build(str(kanal), None, paths, today="2026-10-15")
    feed = json.loads((kanal / "feed.json").read_text())
    assert {p["id"]: p.get("benoetigt") for p in feed["pakete"]}["wichtelmoebel"] == {"verzierungen": "1.0.0"}
    os.environ["STECKWERK_UPDATE_KANAL"] = (kanal / "feed.json").as_uri()
    try:
        m = updater.install_paket("wichtelmoebel")
        assert m["id"] == "wichtelmoebel"
        assert set(updater.installed_pakete()) >= {"verzierungen", "wichtelmoebel"}
    finally:
        del os.environ["STECKWERK_UPDATE_KANAL"]


@pytest.mark.parametrize("pid", NEUE + UMGESTELLT + WELT)
def test_modelle_cut_ready(inst, pid):
    if pid != "verzierungen":
        pakete.install(os.path.join(QUELLEN, "verzierungen"))
    m, mods = pakete.load_folder(os.path.join(QUELLEN, pid))
    for cfg in (Config(), Config(thickness=4.0, kerf=0.15)):
        for name, mod in mods.items():
            params = {p["key"]: p["default"] for p in mod.INFO["params"]}
            asm = mod.build(cfg, **params)
            for a in asm if isinstance(asm, list) else [asm]:
                assert_cut_ready(a, cfg)


def test_filigran_rezepte(inst):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "filigran"))
    FG = mods["spitzenschmuck"].FG
    assert list(FG.rezept_lesen("Blüten, perlen,BÖGEN")) == ["blueten", "perlen", "boegen"]
    with pytest.raises(ValueError, match="kenne"):
        FG.rezept_lesen("blüten, wolken")
    assert FG.rezept_zufall(7) == FG.rezept_zufall(7)
    cfg = Config()
    mod = mods["spitzenschmuck"]
    asm = mod.build(cfg, muster="rezept", rezept="ranken, herzen, zickzack", form="herz")
    assert_cut_ready(asm, cfg)
    asm = mod.build(cfg, muster="zufall", startwert=3, anzahl=2)
    assert len(asm.parts) == 2 and sum("Startwert" in n for n in asm.notes) == 2
    assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("kerf", [0.1, 0.2])
def test_halloween_spitze_zwickel(inst, kerf):
    """Spukschloss mit Spinne und Kürbis mit Blatt: spitze Zwickel überstehen den Kerf-Versatz."""
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, mods = pakete.load_folder(os.path.join(QUELLEN, "halloween"))
    cfg = Config(thickness=3.0, kerf=kerf)
    assert_cut_ready(mods["spukschloss"].build(
        cfg, width=176.49808971447334, szene="friedhof", himmel="nichts", fledermaeuse=1, kuerbisse=1, spinne=True,
        variante=55, rahmen_deko="keine", text="Happy Halloween", schrift="breit", schreibweise="gross"), cfg)
    cfg = Config(thickness=5.0, kerf=kerf)
    assert_cut_ready(mods["kuerbis"].build(cfg, width=119.59090487445758, gesicht="froehlich", rippen=True, blatt=True,
                                           text="BOO!", schrift="normal", schreibweise="gross"), cfg)


def _welt(inst, pid="wichtelwelt"):
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    return pakete.load_folder(os.path.join(QUELLEN, pid))[1]


def test_wichtelfigur_familie_und_varianten(inst):
    mod = _welt(inst)["wichtelfigur"]
    cfg = Config()
    fam = mod.build(cfg, familie=3, sockeltext="Fridolin|Frieda|Fritz")
    assert isinstance(fam, list) and len(fam) == 3
    assert fam[0].params["hoehe"] > fam[1].params["hoehe"] > fam[2].params["hoehe"]
    assert len({a.params["muster"] for a in fam}) == 3
    for a in fam:
        assert {"grundform", "bart", "schnurrbart", "muetze", "nase", "sockel"} <= {p.name for p in a.parts}
        assert_cut_ready(a, cfg)
    for haelt in ("keins", "stern", "herz", "geschenk"):
        for muster in ("sterne", "zacken", "glatt"):
            a = mod.build(cfg, hoehe=90, haelt=haelt, muster=muster, bart="zottelig", spitze="links", sockeltext="")
            assert_cut_ready(a, cfg)
    with pytest.raises(ValueError, match="zu klein"):
        mod.build(cfg, hoehe=40)


def test_wichtelmuetze_muster_bleibt_innen(inst):
    """Das Mützenmuster schneidet nie in den Rand der Mütze."""
    mod = _welt(inst)["wichtelfigur"]
    cfg = Config()
    for muster in ("streifen", "zacken", "punkte"):
        a = mod.build(cfg, muster=muster)
        m = a.part("muetze")
        assert m.holes
        from steckwerk import dist_to_boundary
        for h in m.holes:
            assert min(dist_to_boundary(q, m.outline) for q in h) > cfg.min_web


@pytest.mark.parametrize("T,kerf", [(3.0, 0.2), (2.0, 0.1), (4.0, 0.15)])
def test_wichtelwelt_bauten(inst, T, kerf):
    mods = _welt(inst)
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(mods["lebkuchenstand"].build(cfg, markise="zacken", krone="ranke", schild="", theke="",
                                                  maenner=4, herzen=0), cfg)
    assert_cut_ready(mods["werkbank"].build(cfg, laenge=120, lochwand=True, wandtext="", kistenmotiv="tanne"), cfg)
    for kopf in ("klassisch", "rund", "spitz"):
        a = mods["strassenlaterne"].build(cfg, kopf=kopf, deko="beides")
        assert [c.a for c in a.connections] == ["laterne_a:kreuz"]
        assert_cut_ready(a, cfg)
    assert_cut_ready(mods["lattenzaun"].build(cfg, spitze="gotisch", kappe="herz", tor=True, schnee=False), cfg)
    assert_cut_ready(mods["lattenzaun"].build(cfg, laenge=120, spitze="rund", kappe="stern", tor=False), cfg)


def test_parkbank(inst):
    mod = _welt(inst, "wichtelmoebel")["parkbank"]
    cfg = Config()
    a = mod.build(cfg, text="Wichtelpause", sitzlatten=5, lehnenlatten=2, stil="herz")
    names = [p.name for p in a.parts]
    assert names.count("seite_links") == 1 and sum(n.startswith("sitzlatte") for n in names) == 5
    assert a.part("lehnenlatte2").engrave
    assert_cut_ready(a, cfg)
    for T, kerf in ((2.0, 0.1), (4.0, 0.15), (6.0, 0.3)):
        c = Config(thickness=T, kerf=kerf)
        assert_cut_ready(mod.build(c, laenge=120, sitzhoehe=45, stil="schlicht"), c)
