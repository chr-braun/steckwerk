"""Räumliches Raster für Strecken (steckwerk._SegGrid): gleiche Ergebnisse wie der Vergleich jeder Kante mit jeder."""
import math
import random

import pytest

import steckwerk as S


def _stern(rnd, n, cx=0.0, cy=0.0, r=20.0, zacken=0.45):
    """Unregelmäßiger, sternförmiger Polygonzug mit n Punkten (viele enge Ecken)."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = r * (1 - zacken * rnd.random())
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _min_distance_einfach(p1, p2, limit):
    best = math.inf
    for a, b in S.edges(p1):
        for c, d in S.edges(p2):
            if (max(a[0], b[0]) < min(c[0], d[0]) - limit or min(a[0], b[0]) > max(c[0], d[0]) + limit
                    or max(a[1], b[1]) < min(c[1], d[1]) - limit or min(a[1], b[1]) > max(c[1], d[1]) + limit):
                continue
            best = min(best, S.seg_seg_dist(a, b, c, d))
    return best


def _polygon_ok_einfach(pts):
    if len(pts) < 3 or S.signed_area(pts) <= 1e-9:
        return False
    es = S.edges(pts)
    m = len(es)
    return not any(S.segments_cross(*es[i], *es[j]) for i in range(m) for j in range(i + 2, m)
                   if not (i == 0 and j == m - 1))


@pytest.mark.parametrize("seed", range(6))
def test_min_distance_wie_einfach(seed):
    rnd = random.Random(seed)
    a = _stern(rnd, 150)
    for dx in (30.0, 41.0, 45.0, 80.0):
        b = _stern(rnd, 120, cx=dx, cy=rnd.uniform(-5, 5))
        for limit in (0.5, 2.0, 6.0):
            assert S.min_distance(a, b, limit=limit) == pytest.approx(_min_distance_einfach(a, b, limit), abs=1e-12)


@pytest.mark.parametrize("seed", range(6))
def test_abstand_zur_kontur_wie_einfach(seed):
    rnd = random.Random(seed)
    poly = _stern(rnd, 200)
    abstand = S.BoundaryDistance(poly, hint=0.4)
    for _ in range(300):
        p = (rnd.uniform(-25, 25), rnd.uniform(-25, 25))
        assert abstand(p) == pytest.approx(S.dist_to_boundary(p, poly), abs=1e-12)


@pytest.mark.parametrize("seed", range(8))
def test_selbstueberschneidung_wie_einfach(seed):
    rnd = random.Random(seed)
    pts = _stern(rnd, 120, zacken=0.3)
    if seed % 2:                                    # zwei Punkte vertauschen → Überschneidung
        i = rnd.randrange(10, 100)
        pts[i], pts[i + 5] = pts[i + 5], pts[i]
    assert S.polygon_ok(pts) == _polygon_ok_einfach(pts)


def test_lange_strecken_werden_gefunden():
    """Eine lange Kante, die viele Zellen überspannt, muss trotzdem in jeder Abfrage auftauchen."""
    segs = [((x, 0.0), (x + 0.5, 0.0)) for x in range(100)] + [((-500.0, -500.0), (500.0, 500.0))]
    grid = S._SegGrid(segs)
    assert len(segs) - 1 in grid.near(10.0, 10.0, 10.1, 10.1)


def test_schleifen_entfernen_wie_vorher():
    """inset_polygon nutzt remove_loops; Fläche und Gültigkeit hängen nicht vom Raster ab."""
    rnd = random.Random(3)
    pts = S.oriented(_stern(rnd, 160, zacken=0.5), True)
    innen = S.inset_polygon(pts, 0.8)
    assert innen and S.signed_area(innen) < S.signed_area(pts) and S.polygon_ok(innen)
