"""Paket „Steckstern“ 1.0.0: Holzstern (zwei gesteckte Platten) und gefalteter Papierstern."""
import os

import pytest

import pakete
from steckwerk import Config
from conftest import assert_cut_ready

QUELLEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paketquellen")


@pytest.fixture(scope="module")
def M(tmp_path_factory):
    alt = {k: os.environ.get(k) for k in ("STECKWERK_PAKETE", "STECKWERK_DATEN")}
    d = tmp_path_factory.mktemp("steckstern")
    os.environ["STECKWERK_PAKETE"] = str(d / "inst")
    os.environ["STECKWERK_DATEN"] = str(d / "daten")
    pakete.install(os.path.join(QUELLEN, "verzierungen"))
    _, m = pakete.load_folder(os.path.join(QUELLEN, "steckstern"))
    yield m
    for k, v in alt.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


KARTON = dict(thickness=0.5, kerf=0.1, min_web=0.6)


@pytest.mark.parametrize("a,b,wechsel", [("eiskristall", "eiskristall", False), ("ranke", "perlen", False),
                                         ("sternennacht", "eiskristall", True)])
def test_holzstern_cut_ready(M, a, b, wechsel):
    cfg = Config(thickness=4.0)
    asm = M["holzstern"].build(cfg, muster_a=a, muster_b=b, wechsel=wechsel)
    assert_cut_ready(asm, cfg)
    pa, pb = asm.parts
    assert len(pa.holes) > 20 and len(pb.holes) > 20
    assert pa.engrave and pb.engrave
    # Schlitz A unten, B oben: beide zusammen ergeben die volle Höhe
    sa, sb = pa.feature("kreuz"), pb.feature("kreuz")
    assert sa.span[1] == pytest.approx(0.0) and sb.span[0] == pytest.approx(0.0)


def test_holzstern_klein_meldet(M):
    with pytest.raises(ValueError):
        M["holzstern"].build(Config(thickness=4.0), groesse=60)


@pytest.mark.parametrize("muster", ["lebensblume", "sternmosaik", "eisfeder", "schneeflocken"])
def test_papierstern_cut_ready(M, muster):
    cfg = Config(**KARTON)
    asm = M["papierstern"].build(cfg, muster=muster, teile="vorne")
    assert_cut_ready(asm, cfg)
    (vorne,) = asm.parts
    assert len(vorne.holes) > 150
    assert len(vorne.engrave) >= 10                      # Falzlinien


def test_papierstern_rueckseite_mit_lampenloch(M):
    cfg = Config(**KARTON)
    asm = M["papierstern"].build(cfg, muster="sternmosaik")
    assert_cut_ready(asm, cfg)
    vorne, hinten = asm.parts
    gross = lambda p: max(abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(h, h[1:] + h[:1]))) / 2 for h in p.holes)
    assert gross(hinten) > gross(vorne)                  # Öffnung für die Lampe
    assert any("Holz" not in n and "Karton" not in n for n in asm.notes)


def test_papierstern_hinweis_bei_holz(M):
    asm = M["papierstern"].build(Config(thickness=3.0), muster="eisfeder", teile="vorne")
    assert any("Karton" in n for n in asm.notes)


@pytest.mark.parametrize("entwurf", ["eisblume", "rosette", "spitze"])
def test_fensterstern(M, entwurf):
    cfg = Config(**KARTON)
    asm = M["fensterstern"].build(cfg, entwurf=entwurf)
    assert_cut_ready(asm, cfg)
    assert len(asm.parts) == 1 and len(asm.parts[0].holes) > 100


def test_fensterstern_klein_und_falsch(M):
    cfg = Config(**KARTON)
    assert_cut_ready(M["fensterstern"].build(cfg, entwurf="rosette", groesse=120), cfg)
    with pytest.raises(ValueError):
        M["fensterstern"].build(cfg, entwurf="komet")
