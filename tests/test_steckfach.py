"""Schmuck 1.1.0 (vorher Weihnachten 2.3.0): Christbaumschmuck mit Steckfach – drei Lagen, Fach für Geldschein oder Gutscheinkarte."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")
FORMEN = ["kugel", "haus", "geschenk"]


@pytest.fixture(scope="module")
def SF(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("steckfach")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "schmuck"))
    yield m["steckfach"]
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _fach_innen(outline, inn):
    """Misst im Fachrahmen die lichte Breite und Höhe des Fachs (Mitte x = 0)."""
    ys = [q[1] for q in outline]
    y = min(ys) + 0.3
    while inn(outline, (0.0, y)):
        y += 0.02
    boden = y
    yc = boden + 5.0
    x = 0.0
    while not inn(outline, (x, yc)):
        x += 0.02
    rechts = x
    x = 0.0
    while not inn(outline, (x, yc)):
        x -= 0.02
    return rechts - x, boden


def test_liste_aktuell(SF):
    assert [k for k, _ in SF.FORMEN] == FORMEN
    ids = [p["key"] for p in SF.INFO["params"]]
    assert {"form", "einlage", "spiel", "text", "gruss"} <= set(ids)


@pytest.mark.parametrize("einlage", ["schein", "karte"])
@pytest.mark.parametrize("form", FORMEN)
def test_drei_lagen_cut_ready(SF, form, einlage):
    cfg = Config(thickness=3.0)
    asm = SF.build(cfg, form=form, einlage=einlage)
    assert_cut_ready(asm, cfg)
    vorne, rahmen, hinten = asm.parts
    assert vorne.name.endswith("_vorderseite") and rahmen.name.endswith("_fachrahmen")
    assert hinten.name.endswith("_rueckseite")
    assert len(vorne.holes) >= 8, "Spitze bzw. Fenster in der Vorderseite erwartet"
    assert len(vorne.engrave) >= 150, "feine Gravur vorne erwartet"
    assert len(hinten.engrave) >= 50, "Gruß auf der Rückseite erwartet"
    assert len(hinten.holes) == 1 and not rahmen.holes, "Rückseite nur mit Öse, Rahmen ohne Löcher"
    assert not any("weggelassen" in n for n in asm.notes)


@pytest.mark.parametrize("einlage", ["schein", "karte"])
@pytest.mark.parametrize("form", FORMEN)
def test_fach_passt(SF, form, einlage):
    """Das Fach im Rahmen ist so groß wie bestellt (Einlage + Spiel), höchstens 0,15 mm knapper."""
    cfg = Config(thickness=3.0)
    asm = SF.build(cfg, form=form, einlage=einlage)
    soll = SF.EINLAGE_MASS[einlage]
    breite, _ = _fach_innen(asm.parts[1].outline, SF._innen_pkt)
    moeglich = [soll[0] + 2.0, soll[1] + 2.0]
    assert min(abs(breite - m) for m in moeglich) < 0.15, (breite, moeglich)
    # Einlage passt mit Luft: mindestens 0,8 mm je Seite
    assert any(breite - m >= 1.6 for m in soll)


def test_einlage_versteckt(SF):
    """Über dem Fach hat die Vorderseite keine Durchbrüche – die Einlage bleibt unsichtbar."""
    cfg = Config(thickness=3.0)
    for form in FORMEN:
        asm = SF.build(cfg, form=form, einlage="karte")
        vorne, rahmen, _ = asm.parts
        breite, boden = _fach_innen(rahmen.outline, SF._innen_pkt)
        a, b = asm.params["fach_b"], asm.params["fach_h"]
        hoehe = b if abs(breite - a) < abs(breite - b) else a
        for h in vorne.holes:
            for x, y in h:
                assert not (abs(x) < breite / 2 and boden < y < boden + hoehe), (form, x, y)


def test_eigenes_mass_und_spiel(SF):
    cfg = Config(thickness=3.0)
    asm = SF.build(cfg, form="haus", einlage="eigen", einlage_b=60.0, einlage_h=30.0, spiel=1.5)
    assert_cut_ready(asm, cfg)
    breite, _ = _fach_innen(asm.parts[1].outline, SF._innen_pkt)
    assert abs(breite - 63.0) < 0.15


def test_set_und_ohne_text(SF):
    cfg = Config(thickness=3.0)
    asm = SF.build(cfg, form="alle", text="", gruss="")
    assert len(asm.parts) == 9
    assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("T,kerf", [(2.0, 0.1), (4.0, 0.15)])
@pytest.mark.parametrize("form", FORMEN)
def test_andere_staerken(SF, form, T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    asm = SF.build(cfg, form=form, einlage="karte", text="Lea")
    assert_cut_ready(asm, cfg)


def test_ungueltig(SF):
    cfg = Config(thickness=3.0)
    with pytest.raises(ValueError):
        SF.build(cfg, form="stern")
    with pytest.raises(ValueError):
        SF.build(cfg, text="★")
