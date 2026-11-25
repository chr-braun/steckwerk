"""
_szenen.py – kleine Winter- und Adventsszenen für die Namensanhänger.

Jede Szene steht auf einem Schneehügel. Gezeichnet wird in einem Feld der Breite W (Mitte x = 0) ab der
Hügeloberkante yg nach oben, höchstens H hoch. Rückgabe: Figur (Material, Durchbrüche) und Gravurlinien.
"""
from __future__ import annotations

import math
from typing import List, Tuple

from pakete import bibliothek

K = bibliothek("verzierungen").K
F = bibliothek("verzierungen").F
Figur = K.Figur
Poly = List[Tuple[float, float]]

WINTER = [("winterdorf", "Winterdorf mit Kirche"), ("winterwald", "Winterwald mit Hirsch"),
          ("schneemann", "Schneemann mit Laterne"), ("schlitten", "Schlittenfahrt")]
ADVENT = [("adventskranz", "Adventskranz mit vier Kerzen"), ("christbaum", "Christbaum mit Geschenken"),
          ("plaetzchen", "Plätzchen backen"), ("geschenke", "Geschenke packen")]
SZENEN = WINTER + ADVENT + [("ohne", "keine Szene (Schild mit Jahreszahl)")]


def huegel(x0: float, x1: float, y: float, amp: float, tief: float, phase: float = 0.7) -> Poly:
    pts = [(x0, y - tief)]
    n = 36
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts.append((x, y + amp * (0.6 * math.sin(phase + 5.0 * i / n) + 0.4 * math.sin(2 * phase + 11.0 * i / n))))
    pts.append((x1, y - tief))
    return pts


def _tannen(f: Figur, xs, y: float, hs, seed: int) -> None:
    for i, (x, h) in enumerate(zip(xs, hs)):
        f.merge(F.fichte(h, seed + i, breite=0.55, schnee=True).place(x, y - 0.03 * h, 1.0))


def _kerze(f: Figur, g: List[Tuple[Poly, bool]], x: float, y: float, w: float, h: float, wb: float) -> None:
    f.add(K.rect(x - w / 2, y, w, h))
    # Wachstropfen am Rand
    f.add(K.ellipse(x - w * 0.32, y + h - w * 0.35, w * 0.16, w * 0.38, 0.0, 16))
    # Docht und Flamme (Flamme hängt am Docht, damit sie nicht herausfällt)
    fl = w * 1.15
    f.add(K.stroke([(x, y + h - 0.2), (x, y + h + fl * 0.35)], wb * 0.9, wb * 0.9, "flach"))
    flamme = K.spline([(x, y + h + fl * 0.25), (x + fl * 0.32, y + h + fl * 0.62), (x, y + h + fl * 1.45),
                       (x - fl * 0.32, y + h + fl * 0.62)], closed=True, n=8)
    f.add(flamme)
    g.append((K.spline([(x, y + h + fl * 0.45), (x + fl * 0.14, y + h + fl * 0.68), (x, y + h + fl * 1.05),
                        (x - fl * 0.14, y + h + fl * 0.68)], closed=True, n=6), True))


def _schleife(f: Figur, cx: float, cy: float, b: float, wmin: float) -> None:
    for s in (-1, 1):
        f.add(K.spline([(cx, cy), (cx + s * b * 0.25, cy + b * 0.32), (cx + s * b * 0.52, cy + b * 0.28),
                        (cx + s * b * 0.50, cy - b * 0.02), (cx + s * b * 0.2, cy - b * 0.08)], closed=True, n=8))
        f.add(K.stroke([(cx, cy), (cx + s * b * 0.22, cy - b * 0.30), (cx + s * b * 0.30, cy - b * 0.46)],
                       max(wmin, b * 0.12), max(wmin, b * 0.16), "flach"))
        if b > 9 * wmin:
            f.cut(K.ellipse(cx + s * b * 0.30, cy + b * 0.12, b * 0.11, b * 0.06, s * 0.35, 16))
    f.add(K.ellipse(cx, cy, b * 0.11, b * 0.13, 0.0, 18))


def _paket(f: Figur, g: List[Tuple[Poly, bool]], x: float, y: float, w: float, h: float, wmin: float,
           schleife: bool = True, muster: str = "") -> None:
    """Geschenkpaket: Schachtel mit Deckel, Band graviert, Schleife oben."""
    f.add(K.rect(x - w / 2, y, w, h))
    f.add(K.rect(x - w / 2 - w * 0.05, y + h * 0.78, w * 1.1, h * 0.22))
    g.append(([(x - w / 2 - w * 0.05, y + h * 0.78), (x + w / 2 + w * 0.05, y + h * 0.78)], False))
    bw = max(1.0, w * 0.13)
    for dx in (-bw / 2, bw / 2):
        g.append(([(x + dx, y + 0.4), (x + dx, y + h - 0.4)], False))
    if muster == "punkte":
        for i in range(3):
            for j in range(2):
                px = x - w * 0.32 + (w * 0.64) * (i / 2)
                py = y + h * (0.22 + 0.36 * j)
                if abs(px - x) > bw:
                    g.append((K.circle(px, py, max(0.5, w * 0.04), 10), True))
    elif muster == "sterne":
        for px, py in ((x - w * 0.28, y + h * 0.35), (x + w * 0.28, y + h * 0.55)):
            g.append((K.star(px, py, w * 0.09, w * 0.04, 5), True))
    if schleife:
        _schleife(f, x, y + h + w * 0.08, w * 0.62, wmin)


def szene(art: str, W: float, H: float, yg: float, seed: int, wmin: float, wb: float
          ) -> Tuple[Figur, List[Tuple[Poly, bool]]]:
    """Szene zeichnen; ragt sie über das Feld hinaus (Geweih, Stern …), wird sie kleiner neu gezeichnet –
    nicht nachträglich verkleinert, damit Beine und Stege ihre Mindestbreite behalten."""
    h = H
    for _ in range(3):
        f, g = _zeichnen(art, W, h, yg, seed, wmin, wb)
        x0, y0, x1, y1 = f.bbox()
        k = min(H / max(1e-6, y1 - yg), W / max(1e-6, x1 - x0))
        if k >= 0.995:
            break
        h *= k * 0.99
    return f, g


def _zeichnen(art: str, W: float, H: float, yg: float, seed: int, wmin: float, wb: float
              ) -> Tuple[Figur, List[Tuple[Poly, bool]]]:
    f = Figur()
    g: List[Tuple[Poly, bool]] = []
    if art == "winterdorf":
        f.merge(_auf_hoehe(lambda h: F.kirche(h, seed, "zwiebel"), 0.98 * H).place(0.10 * W, yg - 0.02 * H, 1.0))
        f.merge(F.haus(0.22 * W, 0.52 * H, seed, "giebel").place(-0.27 * W, yg - 0.02 * H, 1.0))
        _tannen(f, [-0.46 * W, 0.42 * W], yg, [0.62 * H, 0.70 * H], seed)
    elif art == "winterwald":
        f.merge(_auf_hoehe(lambda h: F.hirsch(h, wmin_mm=wmin), 0.95 * H).place(0.02 * W, yg - 0.03 * H, 1.0))
        _tannen(f, [-0.40 * W, -0.27 * W, 0.32 * W, 0.44 * W], yg, [0.95 * H, 0.66 * H, 0.80 * H, 0.58 * H], seed)
    elif art == "schneemann":
        f.merge(F.schneemann(0.92 * H, seed).place(-0.08 * W, yg - 0.03 * H, 1.0))
        f.merge(F.laterne(0.98 * H).place(0.26 * W, yg - 0.02 * H, 1.0))
        _tannen(f, [-0.42 * W, 0.45 * W], yg, [0.62 * H, 0.50 * H], seed)
    elif art == "schlitten":
        s = F.schlitten(wmin=max(0.05, wmin / (0.24 * W)))
        x0, y0, x1, y1 = s.bbox()
        k = min(0.62 * W / (x1 - x0), 0.80 * H / (y1 - y0))
        f.merge(s.place(-(x0 + x1) / 2 * k - 0.02 * W, yg - y0 * k - 0.04 * H, k))
        _tannen(f, [-0.42 * W, 0.40 * W, 0.47 * W], yg, [0.80 * H, 0.66 * H, 0.46 * H], seed)
    elif art == "adventskranz":
        # Kranz von der Seite auf einem Tischchen: Tannengrün mit Büscheln, vier Kerzen, Schleife vorn
        rx, ry = 0.34 * W, 0.10 * H
        cy = yg + 0.16 * H
        f.add(K.rect(-0.30 * W, yg - 0.05 * H, 0.60 * W, 0.08 * H))          # Tischplatte / Teller
        f.add(K.ellipse(0, cy, rx, ry * 1.4, 0.0, 72))
        for i in range(26):                                   # Nadelbüschel: unruhige Kante gegen den Himmel
            a2 = 2 * math.pi * i / 26
            x, y = rx * 1.02 * math.cos(a2), cy + ry * 1.45 * math.sin(a2)
            f.add(K.ellipse(x, y, 0.035 * W, 0.075 * H, a2 + 0.5, 10))
        for i in range(9):                                    # Zweigstruktur graviert
            x = -0.26 * W + 0.065 * W * i
            g.append(([(x - 0.025 * W, cy - 0.04 * H), (x, cy), (x + 0.025 * W, cy + 0.05 * H)], False))
        kw = max(0.085 * W, 2.6 * wb)
        for x, hh in zip((-0.24, -0.08, 0.08, 0.24), (0.38, 0.50, 0.50, 0.38)):
            _kerze(f, g, x * W, cy + ry * 0.6, kw, hh * H, wb)
        for x in (-0.20, -0.04, 0.12, 0.27):                  # Beeren vorn
            f.add(K.circle(x * W, cy - ry * 0.9, 0.028 * W, 14))
        _schleife(f, -0.02 * W, cy - ry * 0.3, 0.22 * W, wmin)
    elif art == "christbaum":
        h = 0.88 * H
        bw = 0.42 * W
        f.add(K.rect(-0.04 * W, yg - 0.02 * H, 0.08 * W, 0.14 * h))
        # Silhouette in vier Stufen, Einkerbungen weit offen (keine schmalen Keile, die der Laser zusetzt)
        stufen = 4
        rechts = [(0.0, yg + 0.98 * h)]
        for i in range(stufen):
            t = (i + 1) / stufen
            y_tip = yg + (0.98 - 0.86 * t) * h
            x_tip = bw / 2 * (0.35 + 0.65 * t)
            rechts.append((x_tip, y_tip))
            if i < stufen - 1:
                rechts.append((x_tip * 0.55, y_tip + 0.07 * h))
        rechts.append((0.06 * W, yg + 0.12 * h))
        f.add([(-x, y) for x, y in reversed(rechts[1:])] + rechts)
        f.add(K.star(0.0, yg + 0.97 * h, 0.075 * H + 1.0, 0.032 * H + 0.5, 5))
        rk = max(0.022 * H, 0.7 * wmin)
        for x, y in ((-0.05, 0.26), (0.06, 0.40), (-0.02, 0.56)):
            f.cut(K.circle(x * W, yg + y * h, rk, 14))
        for i in range(3):                                    # Lichterkette graviert
            y = yg + (0.28 + 0.2 * i) * h
            w2 = bw / 2 * (0.75 - 0.2 * i)
            g.append((K.bez((-w2, y + 0.04 * h), (0, y - 0.03 * h), (w2, y + 0.06 * h), 12), False))
        for x, w, hh, m in ((-0.33, 0.17, 0.24, "punkte"), (0.32, 0.15, 0.30, "sterne")):
            _paket(f, g, x * W, yg - 0.02 * H, w * W, hh * H, wmin, True, m)
    elif art == "plaetzchen":
        # Lebkuchenmann in der Mitte, daneben ein Stapel Plätzchen, Stern und Herz, vorn das Nudelholz
        f.merge(_lebkuchenmann(0.95 * H, g, wmin, (0.0, yg - 0.02 * H)))
        for i in range(3):                                    # Plätzchenstapel links
            f.add(K.ellipse(-0.30 * W, yg + 0.05 * H + i * 0.11 * H, 0.10 * W, 0.06 * H, 0.0, 30))
            g.append((K.arc(-0.30 * W, yg + 0.05 * H + i * 0.11 * H, 0.075 * W, math.radians(200),
                            math.radians(340), 10), False))
        f.add(K.star(-0.30 * W, yg + 0.42 * H, 0.09 * W, 0.04 * W, 5))
        f.add(K.stroke([(-0.30 * W, yg + 0.30 * H), (-0.30 * W, yg + 0.40 * H)], wb, wb, "flach"))
        f.add(_herz(0.30 * W, yg + 0.06 * H, 0.22 * W))
        g.append((_herz(0.30 * W, yg + 0.08 * H, 0.15 * W), True))
        f.add(K.star(0.40 * W, yg + 0.26 * H, 0.08 * W, 0.036 * W, 6, 0.0))
        f.add(K.stroke([(0.37 * W, yg + 0.12 * H), (0.40 * W, yg + 0.24 * H)], wb, wb, "flach"))
        g.append((K.star(0.40 * W, yg + 0.26 * H, 0.045 * W, 0.02 * W, 6, 0.0), True))
    elif art == "geschenke":
        _paket(f, g, -0.20 * W, yg - 0.02 * H, 0.32 * W, 0.42 * H, wmin, False, "sterne")
        _paket(f, g, 0.18 * W, yg - 0.02 * H, 0.26 * W, 0.30 * H, wmin, True, "punkte")
        _paket(f, g, -0.21 * W, yg - 0.02 * H + 0.42 * H, 0.22 * W, 0.22 * H, wmin, True, "")
        # Geschenkband-Rolle und Schere
        f.add(K.circle(0.40 * W, yg + 0.10 * H, 0.08 * W, 30))
        f.cut(K.circle(0.40 * W, yg + 0.10 * H, max(0.03 * W, 1.6 * wmin), 20))
        band = [(0.40 * W + 0.08 * W, yg + 0.10 * H)]
        for i in range(1, 9):
            band.append((0.48 * W - i * 0.02 * W, yg + 0.10 * H + 0.20 * H * math.sin(i / 8 * math.pi) * 0.6
                         + i * 0.02 * H))
        f.add(K.stroke(band, max(wmin, 0.022 * W), max(wmin, 0.022 * W), "rund"))
        # Tannenzweig auf dem Stapel
        f.merge(F.fichte(0.30 * H, seed, breite=0.5).place(0.20 * W, yg + 0.27 * H, 1.0))
    else:
        raise ValueError(f"Unbekannte Szene {art!r}")
    return f, g


def _auf_hoehe(bauer, H: float) -> Figur:
    """Figur so groß zeichnen, dass sie samt Geweih, Kreuz o. ä. genau H hoch wird."""
    probe = bauer(H)
    x0, y0, x1, y1 = probe.bbox()
    k = H / max(1e-6, y1 - min(0.0, y0))
    return bauer(H * k) if abs(k - 1) > 0.02 else probe


def _lebkuchenmann(h: float, g: List[Tuple[Poly, bool]], wmin: float, ort=(0.0, 0.0)) -> Figur:
    f = Figur()
    g0 = len(g)
    u = h
    f.add(K.circle(0, 0.81 * u, 0.15 * u, 40))
    body = K.spline([(-0.15 * u, 0.67 * u), (-0.36 * u, 0.62 * u), (-0.38 * u, 0.53 * u), (-0.17 * u, 0.52 * u),
                     (-0.20 * u, 0.30 * u), (-0.30 * u, 0.04 * u), (-0.22 * u, 0.0), (-0.10 * u, 0.0),
                     (0.0, 0.22 * u), (0.10 * u, 0.0), (0.22 * u, 0.0), (0.30 * u, 0.04 * u), (0.20 * u, 0.30 * u),
                     (0.17 * u, 0.52 * u), (0.38 * u, 0.53 * u), (0.36 * u, 0.62 * u), (0.15 * u, 0.67 * u)],
                    closed=True, n=6)
    f.add(body)
    r_auge = max(0.022 * u, 0.55 * wmin)
    for x in (-0.055, 0.055):
        f.cut(K.circle(x * u, 0.84 * u, r_auge, 12))
    g.append((K.arc(0, 0.80 * u, 0.07 * u, math.radians(205), math.radians(335), 10), False))
    for y in (0.50, 0.40, 0.30):
        g.append((K.circle(0, y * u, 0.025 * u, 12), True))
    for sx in (-1, 1):                                        # Zuckerguss-Zickzack an Armen und Beinen
        g.append(([(sx * (0.27 + 0.025 * (i % 2)) * u, (0.535 + 0.06 * (i / 4)) * u) for i in range(5)], False))
        g.append(([(sx * (0.15 + 0.03 * i) * u, (0.10 - 0.02 * (i % 2)) * u) for i in range(4)], False))
    ox, oy = ort
    g[g0:] = [([(x + ox, y + oy) for x, y in pts], c) for pts, c in g[g0:]]
    return f.place(ox, oy, 1.0)


def _herz(cx: float, cy: float, g: float) -> Poly:
    pts = []
    for i in range(40):
        t = 2 * math.pi * i / 40
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x / 32 * g, cy + (y + 2.5) / 32 * g))
    return pts


def _mond(cx: float, cy: float, r: float) -> Poly:
    a = K.arc(cx, cy, r, math.radians(-120), math.radians(120), 24)
    b = K.arc(cx + r * 0.45, cy, r * 0.78, math.radians(110), math.radians(-110), 20)
    return a + b
