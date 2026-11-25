"""Paket „Papier“ 1.0.0: Steck-Tannenbaum aus Karton."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")
KARTON = dict(thickness=0.5, kerf=0.1, min_web=0.6)


@pytest.fixture(scope="module")
def M(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("papier")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "papier"))
    yield m
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_tannenbaum_standard(M):
    cfg = Config(**KARTON)
    asm = M["steck_tannenbaum"].build(cfg)
    assert_cut_ready(asm, cfg)
    namen = [p.name for p in asm.parts]
    assert namen[:2] == ["baum_a", "baum_b"] and "stern_spitze" in namen
    assert len(namen) == 2 + 18 + 1
    a, b = asm.parts[:2]
    assert len(a.holes) >= 6 and a.engrave
    ya = [y for _, y in a.outline]
    assert max(ya) - min(ya) == pytest.approx(220, abs=6)


@pytest.mark.parametrize("kw", [dict(groesse=140, anhaenger=4, formen="herz"),
                                dict(groesse=300, anhaenger=0, fenster=False, ausmalen=False)])
def test_tannenbaum_varianten(M, kw):
    cfg = Config(**KARTON)
    asm = M["steck_tannenbaum"].build(cfg, **kw)
    assert_cut_ready(asm, cfg)
    assert len(asm.parts) == 3 + kw["anhaenger"]
    if not kw.get("ausmalen", True):
        assert not asm.parts[0].engrave and not asm.parts[0].holes


def test_tannenbaum_dickes_material_hinweis(M):
    asm = M["steck_tannenbaum"].build(Config(thickness=3.0), anhaenger=2)
    assert any("300 g" in n for n in asm.notes)


def test_tannenbaum_falsche_form(M):
    with pytest.raises(ValueError):
        M["steck_tannenbaum"].build(Config(**KARTON), formen="mond")


@pytest.mark.parametrize("kw", [dict(), dict(breite=50, tiefe=50, hoehe=50, fenster="rund", verzierung=False),
                                dict(breite=110, tiefe=90, hoehe=90, fenster="herz"),
                                dict(breite=140, tiefe=140, hoehe=140, fenster="stern", zuckerguss=False)])
def test_laternenhaus(M, kw):
    cfg = Config(**KARTON)
    asm = M["laternenhaus"].build(cfg, **kw)
    assert_cut_ready(asm, cfg)
    namen = [p.name for p in asm.parts]
    assert namen[-1] == "dach"
    gross = kw.get("breite", 80) + kw.get("tiefe", 70) > 185
    assert namen[:-1] == (["haus_vorne", "haus_hinten"] if gross else ["haus"])
    assert all(p.holes for p in asm.parts[:-1])
    assert all(p.engrave for p in asm.parts)          # Falzlinien
    assert any("LED" in n for n in asm.notes)


@pytest.mark.parametrize("tier,teile", [("rentier", ["koerper", "beine_vorne", "beine_hinten"]),
                                        ("eisbaer", ["koerper", "beine_vorne", "beine_hinten"]),
                                        ("pinguin", ["pinguin_vorne", "pinguin_seite"])])
def test_steck_tiere(M, tier, teile):
    cfg = Config(**KARTON)
    asm = M["steck_tiere"].build(cfg, tier=tier)
    assert_cut_ready(asm, cfg)
    assert [p.name for p in asm.parts] == teile
    assert all(p.engrave for p in asm.parts)


def test_steck_tiere_gross_ohne_gravur(M):
    cfg = Config(**KARTON)
    asm = M["steck_tiere"].build(cfg, tier="rentier", groesse=200, schal=False, details=False)
    assert_cut_ready(asm, cfg)
    with pytest.raises(ValueError):
        M["steck_tiere"].build(cfg, tier="einhorn")


def test_adventskalender(M):
    cfg = Config(**KARTON)
    asm = M["adventskalender"].build(cfg)
    assert_cut_ready(asm, cfg)
    assert [p.name for p in asm.parts] == [f"tag_{n}" for n in range(1, 25)]
    assert len(asm.parts[0].engrave) > 12                       # Falze, Rahmen, Zahl, Motiv
    assert asm.parts[0].engrave != asm.parts[1].engrave


def test_adventskalender_teilbereich(M):
    cfg = Config(**KARTON)
    asm = M["adventskalender"].build(cfg, groesse=70, von=20, bis=24, motive=False)
    assert_cut_ready(asm, cfg)
    assert len(asm.parts) == 5
    with pytest.raises(ValueError):
        M["adventskalender"].build(cfg, von=10, bis=5)
