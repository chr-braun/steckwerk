"""Die schnellen Prüf-Helfer müssen dasselbe liefern wie die einfachen Varianten „jede Kante mit jeder“."""
import math
import random
import threading
import time

import pytest

import service
import steckwerk as K
import validator
from steckwerk import Config, PolygonIndex, SegmentGrid


def _blob(rng, n, cx=0.0, cy=0.0, r=20.0):
    """Zufällige, sternförmige (also einfache) Kontur mit n Punkten."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (0.55 + 0.45 * rng.random())
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _brute_min_distance(p1, p2, limit):
    e2 = [(a, b, min(a[0], b[0]) - limit, max(a[0], b[0]) + limit,
           min(a[1], b[1]) - limit, max(a[1], b[1]) + limit) for a, b in K.edges(p2)]
    best = math.inf
    for a, b in K.edges(p1):
        x0, x1 = min(a[0], b[0]), max(a[0], b[0])
        y0, y1 = min(a[1], b[1]), max(a[1], b[1])
        for c, d, ex0, ex1, ey0, ey1 in e2:
            if x1 < ex0 or x0 > ex1 or y1 < ey0 or y0 > ey1:
                continue
            best = min(best, K.seg_seg_dist(a, b, c, d))
    return best


def test_segment_grid_gleich_wie_alle_kanten():
    rng = random.Random(3)
    for _ in range(20):
        poly = _blob(rng, rng.randint(5, 400))
        grid = SegmentGrid(poly)
        for _ in range(60):
            p = (rng.uniform(-25, 25), rng.uniform(-25, 25))
            r = rng.choice([0.0002, 0.1, 1.0, 5.0, 100.0])
            exact = K.dist_to_boundary(p, poly)
            got = grid.near_dist(p, r)
            if exact <= r:
                assert got == pytest.approx(exact, abs=1e-12)
            else:
                assert got == math.inf


def test_polygon_index_gleich_wie_point_in_polygon():
    rng = random.Random(5)
    for _ in range(20):
        poly = _blob(rng, rng.randint(3, 500))
        ix = PolygonIndex(poly)
        pts = [(rng.uniform(-25, 25), rng.uniform(-25, 25)) for _ in range(200)] + list(poly)
        for p in pts:
            assert ix.contains(p) == K.point_in_polygon(p, poly)


def test_min_distance_mit_raster_gleich():
    rng = random.Random(7)
    for _ in range(30):
        a = _blob(rng, rng.randint(40, 300), 0, 0, 10)
        b = _blob(rng, rng.randint(40, 300), rng.uniform(14, 30), rng.uniform(-5, 5), 10)
        for lim in (0.5, 2.0, 8.0):
            assert K.min_distance(a, b, limit=lim) == _brute_min_distance(a, b, lim)


def test_remove_loops_findet_schleife_wie_vorher():
    # Stern mit tiefer Kerbe: beim Nach-innen-Versetzen entstehen Schleifen, die verschwinden müssen
    star = []
    for i in range(10):
        r = 20 if i % 2 == 0 else 6
        a = math.pi / 2 + math.pi * i / 5
        star.append((r * math.cos(a), r * math.sin(a)))
    inner = K.inset_polygon(star, 1.5)
    assert len(inner) >= 3
    assert not K._crossing_pairs(inner)


def test_check_path_meldet_selbstueberschneidung():
    acht = [(0, 0), (10, 10), (10, 0), (0, 10)]
    errs = validator.check_path(acht, True, Config())
    assert any("Selbstüberschneidung" in e for e in errs)


def test_ergebnis_wird_fuer_speichern_wiederverwendet():
    service.clear_cache()
    req = {"model": "briefkasten", "params": {}, "config": {}}
    r1, _ = service.run_request(req)
    r2, _ = service.run_request(req)
    assert r1 is r2                                        # zweiter Aufruf aus dem Speicher
    service.clear_cache()
    r3, _ = service.run_request(req)
    assert r3 is not r1


def test_ueberholte_vorschau_wird_abgebrochen(monkeypatch):
    import webui
    started = threading.Event()
    release = threading.Event()
    calls = []

    def langsam(req, stop=None):
        calls.append(req["n"])
        if req["n"] == 1:
            started.set()
            release.wait(5)
        return {"ok": True, "n": req["n"], "stale": bool(stop and stop())}

    monkeypatch.setattr(service, "generate", langsam)
    out = {}

    def run(n):
        out[n] = webui._generate_latest({"n": n}, "fenster")

    t1 = threading.Thread(target=run, args=(1,))
    t1.start()
    started.wait(5)
    t2 = threading.Thread(target=run, args=(2,))
    t3 = threading.Thread(target=run, args=(3,))
    t2.start()
    time.sleep(0.05)
    t3.start()
    time.sleep(0.05)
    release.set()
    for t in (t1, t2, t3):
        t.join(5)
    assert out[1]["stale"] is True                         # die laufende merkt, dass sie überholt ist
    assert out[2].get("cancelled") is True                 # die wartende entfällt ganz
    assert out[3]["ok"] and out[3]["n"] == 3
    assert calls == [1, 3]


def test_durchbrueche_zwischenspeicher_liefert_dasselbe():
    """Mehrlagig: unveränderte Ebenen holen ihre Durchbrüche aus dem Zwischenspeicher – mit gleichem Ergebnis."""
    import importlib.util
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "paketquellen", "verzierungen", "_ebenen.py")
    spec = importlib.util.spec_from_file_location("test_ebenen_cache", path)
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    lw = E.Leinwand((0, 0, 60, 40), 0.1)
    bereich = lw.flaechen([K.rect(4, 4, 52, 32)])
    material = lw.flaechen([K.circle(20, 20, 6), K.rect(34, 10, 4, 22)])
    E._DURCH_CACHE.clear()
    n1, n2 = [], []
    a = E.durchbrueche(lw, bereich, material, 1.0, 0.15, n1, "Ebene 1")
    assert len(E._DURCH_CACHE) == 1
    a[0].append((999.0, 999.0))                     # Rückgabe verändern darf den Speicher nicht berühren
    b = E.durchbrueche(lw, bereich, material, 1.0, 0.15, n2, "Ebene 1")
    assert len(E._DURCH_CACHE) == 1 and n1 == n2
    assert (999.0, 999.0) not in b[0]
    frisch = E._durchbrueche(lw, bereich, material, 1.0, 0.15, [], "Ebene 1")
    assert b == frisch
    E.durchbrueche(lw, bereich, material, 1.0, 0.2, [], "Ebene 1")   # anderer Kerf → neu rechnen
    assert len(E._DURCH_CACHE) == 2
