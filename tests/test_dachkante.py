"""Geschnittene Dachkante (Traufe) an Wichtelhaus, Anbau, Serie und Briefkasten."""
import pytest

from conftest import MATERIALS, assert_cut_ready
from steckwerk import Config, signed_area
from models import _deko as dk
from models import briefkasten, serie, wichtelhaus

KANTEN = [v for v, _ in dk.EAVES if v != "gerade"]


@pytest.mark.parametrize("kante", KANTEN)
def test_kante_ist_schnittfertig(cfg, kante):
    asm = wichtelhaus.build(cfg, dachkante=kante, wand="ziegel")
    assert_cut_ready(asm, cfg)
    assert asm.params["dachkante"] == kante


@pytest.mark.parametrize("kante", KANTEN)
def test_kante_haengt_unter_der_traufe(cfg, kante):
    """Die Zierkante ist Teil der Schnittkontur und hängt unter dem Dachüberstand."""
    glatt = wichtelhaus.build(cfg).part("wichtelhaus_dach_links")
    roof = wichtelhaus.build(cfg, dachkante=kante).part("wichtelhaus_dach_links")
    gx0, gy0, gx1, gy1 = glatt.bbox()
    x0, y0, x1, y1 = roof.bbox()
    assert (x0, x1, y1) == pytest.approx((gx0, gx1, gy1))
    tief = wichtelhaus.eave_depth(65.0)
    assert -tief * 1.7 <= y0 < -0.5 * tief
    assert len(roof.outline) > 20                        # echte Kontur statt Rechteck
    assert signed_area(roof.outline) > signed_area(glatt.outline)
    # Slots für Giebel und Kamin bleiben, wo sie waren
    assert sorted(map(sorted, glatt.holes[:5])) == sorted(map(sorted, [h for h in roof.holes
                                                                         if len(h) == 4]))


def test_gravur_bleibt_auf_der_dachflaeche(cfg):
    roof = wichtelhaus.build(cfg, dachkante="bogen", dach="schindel").part("wichtelhaus_dach_links")
    ys = [y for s in roof.engrave for _, y in s.points]
    assert ys and min(ys) >= 1.0


def test_spitzenkante_hat_lochung(cfg):
    roof = wichtelhaus.build(cfg, dachkante="spitze").part("wichtelhaus_dach_links")
    unter = [h for h in roof.holes if max(y for _, y in h) < 0]
    assert len(unter) >= 4


def test_gerade_bleibt_unveraendert(cfg):
    a = wichtelhaus.build(cfg).part("wichtelhaus_dach_links")
    b = wichtelhaus.build(cfg, dachkante="gerade").part("wichtelhaus_dach_links")
    assert a.outline == b.outline and len(a.outline) == 4


def test_unbekannte_kante(cfg):
    with pytest.raises(ValueError, match="Dachkante"):
        wichtelhaus.build(cfg, dachkante="spitzen")


@pytest.mark.parametrize("T,kerf", MATERIALS)
@pytest.mark.parametrize("kante", ["bogen", "spitze", "zuckerguss", "eiszapfen"])
def test_jedes_material(T, kerf, kante):
    cfg = Config(thickness=T, kerf=kerf)
    assert_cut_ready(wichtelhaus.build(cfg, dachkante=kante), cfg)


@pytest.mark.parametrize("kw", [dict(annex=True), dict(width=50, depth=45, height=40, pitch=30),
                                dict(width=150, depth=120, height=130, pitch=60), dict(chimney=False)])
@pytest.mark.parametrize("kante", KANTEN)
def test_groessen_und_anbau(cfg, kw, kante):
    assert_cut_ready(wichtelhaus.build(cfg, dachkante=kante, **kw), cfg)


def test_anbau_bekommt_dieselbe_kante(cfg):
    asm = wichtelhaus.build(cfg, dachkante="wellen", annex=True)
    for name in ("wichtelhaus_anbau_dach_links", "wichtelhaus_anbau_dach_rechts"):
        assert asm.part(name).bbox()[1] < 0


@pytest.mark.parametrize("kante", KANTEN)
def test_briefkasten(cfg, kante):
    asm = briefkasten.build(cfg, dachkante=kante)
    assert_cut_ready(asm, cfg)
    assert asm.part("briefkasten_dach_links").bbox()[1] < 0
    assert asm.params["dachkante"] == kante


def test_serie_wuerfelt_kante_ohne_alte_merkmale_zu_aendern(cfg):
    neu = serie.styles(8, 7, {k: serie.RANDOM for k in serie.RANDOM_KEYS})
    alt = serie.styles(8, 7, {k: serie.RANDOM for k in serie.RANDOM_KEYS if k != "dachkante"})
    for a, b in zip(alt, neu):
        assert {k: v for k, v in b.items() if k != "dachkante"} == a
    assert len({s["dachkante"] for s in neu}) >= 2


def test_serie_mit_fester_kante(cfg):
    for asm in serie.build(cfg, n=3, dachkante="zuckerguss"):
        assert_cut_ready(asm, cfg)
        assert asm.params["dachkante"] == "zuckerguss"


def test_formular_hat_dachkante():
    import service
    for mid in ("wichtelhaus", "serie", "briefkasten"):
        keys = {p["key"]: p for p in service.MODEL_INFO[mid]["params"]}
        assert "dachkante" in keys
        values = [o["value"] for o in keys["dachkante"]["options"]]
        assert set(KANTEN) <= set(values)
