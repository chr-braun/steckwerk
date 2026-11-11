"""Spiele 1.1.0 – Puzzle: Teile passen ineinander, Bild läuft über alle Teile, schnittfertig und schnell."""
import math
import os
import time

import pytest

import pakete
from steckwerk import Config, signed_area
from conftest import MATERIALS, assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")

LOGO = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        b'<path d="M50 5 L61 38 L95 38 L67 58 L78 92 L50 71 L22 92 L33 58 L5 38 L39 38 Z" fill="black"/>'
        b'<circle cx="50" cy="52" r="10" fill="white"/></svg>')


@pytest.fixture(scope="module")
def umgebung(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN", "STECKWERK_MOTIVE")}
    d = tmp_path_factory.mktemp("puzzle")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    os.environ["STECKWERK_MOTIVE"] = str(d / "motive")
    import motive
    logo = motive.import_bytes(LOGO, "logo.svg", "Logo")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "spiele"))
    yield m["puzzle"], logo["id"]
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _teile(asm):
    return [p for p in asm.parts if "_teil_" in p.name]


@pytest.mark.parametrize("T,kerf", MATERIALS)
def test_standard_alle_materialien(umgebung, T, kerf):
    mod, _ = umgebung
    cfg = Config(thickness=T, kerf=kerf)
    t = time.perf_counter()
    asm = mod.build(cfg)
    assert time.perf_counter() - t < 2.0
    assert_cut_ready(asm, cfg)
    assert len(_teile(asm)) == 24


@pytest.mark.parametrize("bild", ["winterdorf", "christbaum", "mandala", "sternenhimmel", "waldtiere"])
@pytest.mark.parametrize("form", ["rechteck", "rund"])
def test_bilder(umgebung, bild, form):
    mod, _ = umgebung
    cfg = Config(thickness=3.0, kerf=0.15)
    t = time.perf_counter()
    asm = mod.build(cfg, bild=bild, form=form, teile=30, beschriftung="Frohe Weihnachten", zierrand="sterne")
    assert time.perf_counter() - t < 3.0, "Bild rechnet zu lange"
    assert_cut_ready(asm, cfg)
    teile = _teile(asm)
    assert sum(len(p.engrave) for p in teile) > 300, "Bild ist nicht detailreich genug"
    mit_gravur = [p for p in teile if p.engrave]
    assert len(mit_gravur) >= 0.8 * len(teile), "Das Bild muss über (fast) alle Teile laufen"


@pytest.mark.parametrize("schnitt", ["klassisch", "verspielt", "gerade"])
@pytest.mark.parametrize("nummer", [1, 7, 42])
def test_schnitte(umgebung, schnitt, nummer):
    mod, _ = umgebung
    cfg = Config(thickness=3.0, kerf=0.2)
    asm = mod.build(cfg, schnitt=schnitt, nummer=nummer, teile=48, breite=260, hoehe=190, bild="mandala")
    assert_cut_ready(asm, cfg)


def test_teile_fuellen_flaeche_mit_spiel(umgebung):
    """Ohne Spiel decken die Teile das Puzzle exakt ab; mit Spiel bleibt ringsum ein Spalt."""
    mod, _ = umgebung
    cfg = Config(thickness=3.0)
    for form, soll in (("rechteck", 200 * 150), ("rund", math.pi * 100 ** 2)):
        asm = mod.build(cfg, form=form, spiel=0.0, bild="ohne", muster="keins")
        flaeche = sum(signed_area(p.outline) for p in _teile(asm))
        assert flaeche == pytest.approx(soll, rel=2e-3)
        asm2 = mod.build(cfg, form=form, spiel=0.2, bild="ohne", muster="keins")
        assert sum(signed_area(p.outline) for p in _teile(asm2)) < flaeche


def test_nummer_aendert_schnittmuster(umgebung):
    mod, _ = umgebung
    a = mod.build(Config(), nummer=1, bild="ohne", muster="keins")
    b = mod.build(Config(), nummer=2, bild="ohne", muster="keins")
    assert [p.outline for p in _teile(a)] != [p.outline for p in _teile(b)]
    c = mod.build(Config(), nummer=1, bild="ohne", muster="keins")
    assert [p.outline for p in _teile(a)] == [p.outline for p in _teile(c)]


@pytest.mark.parametrize("art,muster", [("flaeche", "flocken"), ("umriss", "rauten"), ("flaeche", "keins")])
def test_eigenes_motiv(umgebung, art, muster):
    mod, logo = umgebung
    cfg = Config(thickness=3.0)
    asm = mod.build(cfg, bild="eigenes", motiv=logo, motiv_art=art, muster=muster, teile=20)
    assert_cut_ready(asm, cfg)
    assert sum(len(p.engrave) for p in _teile(asm)) > 50


def test_rahmen(umgebung):
    mod, _ = umgebung
    cfg = Config(thickness=3.0, kerf=0.2)
    for form in ("rechteck", "rund"):
        asm = mod.build(cfg, form=form, rahmen="rahmen", beschriftung="Frohe Weihnachten", zierrand="punkte",
                        breite=180, hoehe=130, teile=12, schnitt="gerade")
        assert_cut_ready(asm, cfg)
        rahmen = asm.part("puzzle_rahmen")
        assert len(rahmen.holes) == 1
        asm.part("puzzle_boden")
        # alle Teile liegen in der Rahmenöffnung
        from steckwerk import point_in_polygon
        for p in _teile(asm):
            assert all(point_in_polygon(q, rahmen.holes[0]) for q in p.outline[::5])


def test_viele_teile_schnell(umgebung):
    mod, _ = umgebung
    cfg = Config(thickness=3.0, kerf=0.2)
    t = time.perf_counter()
    asm = mod.build(cfg, breite=380, hoehe=280, teile=200, bild="winterdorf")
    assert time.perf_counter() - t < 3.0
    assert len(_teile(asm)) >= 180
    assert_cut_ready(asm, cfg)


def test_zu_kleine_teile(umgebung):
    mod, _ = umgebung
    with pytest.raises(ValueError, match="weniger Teile"):
        mod.build(Config(thickness=3.0), breite=80, hoehe=60, teile=150)


def test_schnittstelle_fuer_andere_pakete(umgebung):
    mod, _ = umgebung
    cfg = Config(thickness=3.0)
    bild = [([(-40.0, -30.0), (40.0, 30.0)], False), ([(-40.0, 30.0), (40.0, -30.0)], False)]
    teile = mod.puzzle_aus_bild(cfg, "test", "rechteck", 120, 90, 12, "klassisch", 5, bild)
    assert len(teile) == 12
    assert sum(len(p.engrave) for p in teile) >= 6


def _testfoto():
    """Kleines Graustufen-Testbild (Verlauf mit Kreis) als PNG."""
    import bilder
    w, h = 120, 80
    px = bytearray()
    for y in range(h):
        for x in range(w):
            v = int(255 * x / w)
            if (x - 60) ** 2 + (y - 40) ** 2 < 25 ** 2:
                v = 255 - v
            px.append(v)
    return bilder.png_bytes(w, h, bytes(px))


@pytest.mark.parametrize("form,teil", [("rechteck", "auto"), ("rund", "alle")])
def test_fotopuzzle_ueber_alle_teile(umgebung, tmp_path, monkeypatch, form, teil):
    """Ein Foto aus „Eigene Gravur“ läuft einmal über alle Puzzleteile (nicht je Teil ein ganzes Foto)."""
    import bilder
    import gravur
    monkeypatch.setenv("STECKWERK_BILDER", str(tmp_path / "bilder"))
    monkeypatch.setattr(bilder, "user_dir", lambda: str(tmp_path / "bilder"))
    monkeypatch.setattr(bilder, "cache_dir", lambda: str(tmp_path / "cache"))
    meta = bilder.import_bytes(_testfoto(), "foto.png", "Testfoto")
    mod, _ = umgebung
    cfg = Config(thickness=3.0, kerf=0.2)
    asm = mod.build(cfg, bild="foto", form=form, teile=12, breite=160, hoehe=110, rahmen="rahmen")
    gravur.anwenden([asm], [{"quelle": "bild", "bild": meta["id"], "teil": teil, "aufloesung": 5}])
    assert_cut_ready(asm, cfg)
    teile = _teile(asm)
    assert all(len(p.images) == 1 for p in teile), "jedes Teil bekommt seinen Ausschnitt"
    assert not asm.part("puzzle_rahmen").images
    # die Ausschnitte zusammen sind etwa so groß wie das Puzzle, nicht 12 ganze Fotos
    flaeche = sum(abs((im.corners[1][0] - im.corners[0][0]) * (im.corners[0][1] - im.corners[2][1]))
                  for p in teile for im in p.images)
    soll = 160 * 110 if form == "rechteck" else math.pi * 80 ** 2
    assert flaeche < 2.2 * soll
    assert any("läuft über alle" in n for n in asm.notes)
