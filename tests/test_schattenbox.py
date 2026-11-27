"""Paket Schattenbox 1.0.0: Leuchtende Schattenbox – Zinkenkasten mit Szenen-Ebenen, Lichtkammer und Wechselsatz."""
import os

import pytest

import pakete
from steckwerk import Config, bbox
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")
SZENEN = ["winterwald", "winterdorf", "spukschloss", "weihnachtsnacht"]
KLEIN = dict(width=150, height=170)          # schneller, aber mit allen Teilen


@pytest.fixture(scope="module")
def PAKET(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("schattenbox")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    pakete.install(os.path.join(QUELLEN, "ebenen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "schattenbox"))
    yield m
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture(scope="module")
def SB(PAKET):
    return PAKET["schattenbox"]


def _namen(asm):
    return [p.name for p in asm.parts]


def test_standard_teile_und_hinweise(SB):
    cfg = Config(thickness=3.0)
    asm = SB.build(cfg)
    assert_cut_ready(asm, cfg)
    assert _namen(asm) == ["schattenbox_" + s for s in
                           ("vorne", "hinten", "links", "rechts", "boden", "deckel",
                            "ebene1", "ebene2", "ebene3", "ebene4", "himmel")]
    text = " ".join(asm.notes)
    assert "keine echte Kerze" in text and "Szene wechseln" in text
    vorne = asm.part("schattenbox_vorne")
    assert len(vorne.holes) == 1, "genau ein Bildfenster"
    assert len(vorne.engrave) >= 100, "feine Gravur auf dem Frontrahmen erwartet"
    for k in range(1, 5):
        assert asm.part(f"schattenbox_ebene{k}").holes, "jede Ebene trägt einen Teil der Szene"


@pytest.mark.parametrize("T,kerf", [(3.0, 0.2), (4.0, 0.15)])
@pytest.mark.parametrize("szene", SZENEN)
def test_alle_szenen_beide_staerken(SB, szene, T, kerf):
    cfg = Config(thickness=T, kerf=kerf)
    for licht in ("teelicht", "lichterkette"):
        asm = SB.build(cfg, szene=szene, licht=licht, **KLEIN)
        assert_cut_ready(asm, cfg)


@pytest.mark.parametrize("ebenen", [3, 4, 5, 6])
def test_anzahl_ebenen(SB, ebenen):
    cfg = Config(thickness=3.0)
    asm = SB.build(cfg, ebenen=ebenen, **KLEIN)
    assert_cut_ready(asm, cfg)
    assert sum(n.startswith("schattenbox_ebene") for n in _namen(asm)) == ebenen
    # je Ebene plus Hintergrund zwei Schlitze im Boden zusätzlich zu den Wandschlitzen
    boden = asm.part("schattenbox_boden")
    assert sum(f.id.startswith("e") for f in boden.features) == 2 * (ebenen + 1)


@pytest.mark.parametrize("form", ["bogen", "spitzbogen", "rechteck", "abgerundet"])
def test_fensterformen(SB, form):
    cfg = Config(thickness=3.0)
    assert_cut_ready(SB.build(cfg, form=form, **KLEIN), cfg)


def test_wechselsatz(SB):
    cfg = Config(thickness=3.0)
    ohne = SB.build(cfg, **KLEIN)
    asm = SB.build(cfg, wechselsatz=True, szene2="spukschloss", **KLEIN)
    assert_cut_ready(asm, cfg)
    b = [p for p in asm.parts if p.name.endswith("_b")]
    assert [p.name for p in b] == ["schattenbox_ebene1_b", "schattenbox_ebene2_b", "schattenbox_ebene3_b",
                                   "schattenbox_ebene4_b", "schattenbox_himmel_b"]
    for p in b:
        a = asm.part(p.name[:-2])
        assert p.outline == a.outline, "Wechselsatz muss exakt dieselben Zapfen haben"
        assert not p.features, "Wechselsatz ist nicht fest verbunden"
    assert any(p.holes != asm.part(p.name[:-2]).holes for p in b), "andere Szene erwartet"
    assert len(asm.parts) == len(ohne.parts) + 5
    assert any("Wechselsatz" in n for n in asm.notes)


def test_wechselsatz_mit_gleicher_szene_entfaellt(SB):
    cfg = Config(thickness=3.0)
    asm = SB.build(cfg, wechselsatz=True, szene2="winterwald", **KLEIN)
    assert not any(n.endswith("_b") for n in _namen(asm))


def test_papierrahmen(SB):
    cfg = Config(thickness=3.0)
    asm = SB.build(cfg, hintergrund="papier", wechselsatz=True, **KLEIN)
    assert_cut_ready(asm, cfg)
    assert len(asm.part("schattenbox_himmel").holes) == 1, "Rahmen mit einem großen Fenster"
    assert "schattenbox_himmel_b" not in _namen(asm), "Papierrahmen ist für beide Sätze gleich"
    assert any("Transparentpapier" in n for n in asm.notes)


def _lichtkammer(asm, cfg):
    """Tiefe zwischen Hintergrund und Rückwand, aus Seitenwand und Bodenschlitzen abgelesen."""
    T = cfg.T
    seite = asm.part("schattenbox_links")
    x0, _, x1, _ = seite.bbox()
    D = x1 - x0                                # Seitenwand D − 2T plus Zinken je T
    assert abs(D - asm.params["depth"]) < 1e-6
    m = max(2 * T, 5.0)
    boden = asm.part("schattenbox_boden")
    hinterste = max(bbox(f.points)[3] for f in boden.features if f.id.startswith("e")) - m
    return (D - T) - hinterste


@pytest.mark.parametrize("T", [3.0, 4.0])
def test_lichtkammer_tiefe(SB, T):
    cfg = Config(thickness=T)
    tee = SB.build(cfg, licht="teelicht", **KLEIN)
    kette = SB.build(cfg, licht="lichterkette", **KLEIN)
    assert _lichtkammer(tee, cfg) >= 45.0
    assert 15.0 <= _lichtkammer(kette, cfg) < _lichtkammer(tee, cfg)
    # Teelicht-Markierung auf dem Boden
    assert len(tee.part("schattenbox_boden").engrave) > len(kette.part("schattenbox_boden").engrave)


def test_kabelloch_in_der_rueckwand(SB):
    cfg = Config(thickness=3.0)
    hinten = SB.build(cfg, licht="lichterkette", **KLEIN).part("schattenbox_hinten")
    assert len(hinten.holes) == 1
    x0, y0, x1, y1 = bbox(hinten.holes[0])
    assert abs((x1 - x0) - 8.0) < 0.6 and abs((y1 - y0) - 8.0) < 0.6
    assert y0 >= 2 * cfg.T + cfg.min_web - 1e-6, "Abstand zu den Bodentabs"


def test_ebenen_passen_in_den_kasten(SB):
    cfg = Config(thickness=4.0)
    asm = SB.build(cfg, **KLEIN)
    W, H = asm.params["width"], asm.params["height"]
    for p in asm.parts:
        if "_ebene" in p.name or "_himmel" in p.name:
            x0, y0, x1, y1 = p.bbox()
            assert x1 - x0 <= W - 2 * cfg.T - 0.9, "Spiel zu den Seitenwänden"
            assert y1 <= H - 2.0, "Luft unter dem Deckel"
            assert abs(y0 + cfg.T) < 1e-6, "Zapfen so tief wie der Boden dick"


def test_text_und_ornamente(SB):
    cfg = Config(thickness=3.0)
    ohne = SB.build(cfg, ecken="keine", **KLEIN).part("schattenbox_vorne")
    mit = SB.build(cfg, ecken="ranke", text="Frohe Weihnachten", **KLEIN)
    assert_cut_ready(mit, cfg)
    assert len(mit.part("schattenbox_vorne").engrave) > len(ohne.engrave) + 20


def test_ungueltige_eingaben(SB):
    cfg = Config(thickness=3.0)
    with pytest.raises(ValueError):
        SB.build(cfg, width=140, height=140, rand=40)
    with pytest.raises(ValueError):
        SB.build(cfg, ebenen=2)
    with pytest.raises(ValueError):
        SB.build(cfg, szene="mond")
    with pytest.raises(ValueError):
        SB.build(cfg, licht="kerze")
    with pytest.raises(ValueError):
        SB.build(cfg, width=150, height=170, text="Ein viel zu langer Text für so einen kleinen Rahmen")


def test_reproduzierbar(SB):
    cfg = Config(thickness=3.0, seed=7)
    a = SB.build(cfg, **KLEIN)
    b = SB.build(cfg, **KLEIN)
    assert [p.holes for p in a.parts] == [p.holes for p in b.parts]


def test_galerie_vorschau_zeigt_die_szene(SB):
    linien = SB.vorschau(Config(thickness=3.0))
    schnitt = [l for l in linien if l[2] == "schnitt"]
    gravur = [l for l in linien if l[2] == "gravur"]
    assert len(gravur) >= 100, "Frontrahmen mit Gravur"
    assert len(schnitt) >= 30, "Szene durch das Fenster sichtbar, nicht nur der leere Rahmen"
    import vorschau
    svg = vorschau.kompakt(vorschau._linien_svg(linien))
    assert 'id="layer-schnitt"' in svg and 'id="layer-gravur"' in svg


VORLAGEN = {"schattenbox_winterdorf": "winterdorf", "schattenbox_spukschloss": "spukschloss",
            "schattenbox_weihnachtsnacht": "weihnachtsnacht"}


@pytest.mark.parametrize("mid", sorted(VORLAGEN))
def test_fertige_vorlagen(PAKET, mid):
    mod = PAKET[mid]
    defaults = {p["key"]: p["default"] for p in mod.INFO["params"]}
    assert defaults["szene"] == VORLAGEN[mid]
    assert [p["key"] for p in mod.INFO["params"]] == list(mod.B.PARAM_KEYS)
    cfg = Config(thickness=3.0)
    import service
    asm = service.call_build(mod, cfg, width=150, height=170, ebenen=3)   # Parameter kommen über STYLE_KEYS an
    assert_cut_ready(asm, cfg)
    assert asm.name == mid and asm.params["szene"] == VORLAGEN[mid] and asm.params["ebenen"] == 3
    assert len(mod.vorschau(cfg, width=150, height=170, ebenen=3)) > 50


def test_jede_vorlage_hat_ein_galeriebild(PAKET):
    root = os.path.dirname(QUELLEN)
    for mid in ["schattenbox"] + sorted(VORLAGEN):
        assert os.path.isfile(os.path.join(root, "vorschau", mid + ".svg")), mid
