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
