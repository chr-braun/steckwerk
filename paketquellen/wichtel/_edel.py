"""
_edel.py – Bausteine für das edle Wichtelzubehör im Paket „Wichtel“ (ab 1.1.0): Kamin-Zierblende, Feuer,
Funkengitter, Kerzenleuchter, Kaminuhr, Girlande, Strümpfe, Zifferblatt, Gravuren (Ziegel, Fliesen, Kassetten)
und kleine Geschenke.

Alle Teile entstehen als Figur und werden über die Bibliothek „Verzierungen“ laserfest gemacht
(Stege, Kerf und Inseln geprüft). Steckzapfen sitzen immer an einer exakt geraden Unterkante.
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from pakete import bibliothek

Z = bibliothek("verzierungen")
K = Z.K
Point = Tuple[float, float]


# --------------------------------------------------------------------------------------------------
# Gravuren
# --------------------------------------------------------------------------------------------------

def ziegel(part, W: float, H: float, h: float, rand: float = 0.8):
    """Ziegelmauer (versetzte Fugen) auf dem Rechteck 0 … W × 0 … H."""
    lin = []
    n = max(2, int(H / h))
    h = H / n
    b = h * 2.1
    for r in range(n):
        y0, y1 = r * h, (r + 1) * h
        if r:
            lin.append(([(0, y0), (W, y0)], False))
        x = (b / 2) if r % 2 else 0.0
        x += b
        while x < W - 0.5:
            lin.append(([(x, y0), (x, y1)], False))
            x += b
    Z.gravur(part, lin, rand=rand)


def kassette(part, x0: float, y0: float, x1: float, y1: float, inset: float):
    """Gravierte Füllung (abgerundetes Rechteck mit zweiter Linie) – wirkt wie ein Rahmen-Paneel."""
    lin = []
    for d in (inset, inset + max(0.9, inset * 0.45)):
        if x1 - x0 > 2 * d + 2 and y1 - y0 > 2 * d + 2:
            lin.append((Z.abrunden(K.rect(x0 + d, y0 + d, x1 - x0 - 2 * d, y1 - y0 - 2 * d), min(2.0, d), 3), True))
    Z.gravur(part, lin, rand=0.5)


def fliesen(part, x0: float, y0: float, x1: float, y1: float, s: float):
    """Fliesenspiegel: Raster mit einer kleinen Raute in jeder Fliese."""
    lin = []
    nx = max(1, int(round((x1 - x0) / s)))
    ny = max(1, int(round((y1 - y0) / s)))
    sx, sy = (x1 - x0) / nx, (y1 - y0) / ny
    lin.append((K.rect(x0, y0, x1 - x0, y1 - y0), True))
    for i in range(1, nx):
        lin.append(([(x0 + i * sx, y0), (x0 + i * sx, y1)], False))
    for j in range(1, ny):
        lin.append(([(x0, y0 + j * sy), (x1, y0 + j * sy)], False))
    if min(sx, sy) > 3.2:
        for i in range(nx):
            for j in range(ny):
                cx, cy = x0 + (i + 0.5) * sx, y0 + (j + 0.5) * sy
                d = min(sx, sy) * 0.22
                lin.append(([(cx - d, cy), (cx, cy + d), (cx + d, cy), (cx, cy - d)], True))
    Z.gravur(part, lin, rand=0.5)


def zifferblatt(cx: float, cy: float, r: float, roemisch: bool = False):
    """Zifferblatt als Gravurlinien: Ring, Stundenstriche (vier lange), Zeiger auf 10 nach 10."""
    out = [(K.circle(cx, cy, r, 48), True)]
    if r > 3.5:
        out.append((K.circle(cx, cy, r * 0.84, 40), True))
    for k in range(12):
        a = math.pi / 2 - k * math.pi / 6
        lang = k % 3 == 0
        r0 = r * (0.58 if lang else 0.68) if r > 3.5 else r * 0.6
        r1 = r * (0.8 if r > 3.5 else 0.9)
        out.append(([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))],
                    False))
    for a, L in ((math.pi / 2 + math.pi / 3, 0.42), (math.pi / 2 - math.pi / 3, 0.6)):     # 10 und 2 (10 nach 10)
        out.append(([(cx, cy), (cx + r * L * math.cos(a), cy + r * L * math.sin(a))], False))
    return out


# --------------------------------------------------------------------------------------------------
# Kamin
# --------------------------------------------------------------------------------------------------

def _bogen_oeffnung(Wo: float, Ho: float, unten: float = -5.0):
    r = Wo / 2
    hs = Ho - r
    return [(-Wo / 2, unten), (Wo / 2, unten), (Wo / 2, hs)] + \
        [(r * math.cos(a), hs + r * math.sin(a)) for a in (math.pi * i / 40 for i in range(1, 40))] + [(-Wo / 2, hs)]


def kaminblende(cfg, Wb: float, Hb: float, Wo: float, Ho: float, fries: str, notes: List[str]):
    """Filigrane Zierblende für die Kaminfront: Fries mit Durchbruch-Ornament, kannelierte Pilaster,
    Bogenprofil und Schlussstein. Wird vorn auf die Front geleimt (gleicher Umriss)."""
    w = Z.wmin(cfg)
    f = Z.Figur().add(K.rect(-Wb / 2, 0, Wb, Hb))
    f.cut(_bogen_oeffnung(Wo, Ho))
    m = max(1.8, w * 1.3)
    beine = (Wb - Wo) / 2
    # Fries oben: Fenster ausschneiden, Bordüre hineinsetzen
    luft = Hb - Ho
    hf = min(luft * 0.48, Hb * 0.22)
    y0 = Hb - m - hf
    if hf >= 4 * w and Wb - 2 * m > 6 * hf * 0.5:
        L = Wb - 2 * m
        f.cut(K.rect(-L / 2, y0, L, hf))
        f.merge(Z.bordure(L, hf, fries, w).map(lambda p: (p[0] - L / 2, p[1] + y0)))
    # Kanneluren der Pilaster (durchbrochen: das Holz der Front schimmert durch)
    fb = max(1.0, w * 0.75)
    n = 3 if beine > 9 * fb + 4 * m else 2
    yk0, yk1 = max(m * 1.6, Hb * 0.1), min(Ho - 2 * m, y0 - 2 * m)
    if yk1 - yk0 > 4 * fb and beine > n * fb * 2.6 + 2 * m:
        for sg in (-1, 1):
            xc = sg * (Wo / 2 + beine / 2)
            for i in range(n):
                x = xc + (i - (n - 1) / 2) * fb * 2.6
                f.cut(K.stroke([(x, yk0 + fb / 2), (x, yk1 - fb / 2)], fb))
    part = Z.figur_teil(cfg, "zierblende", f, notes, unten_flach=True)
    # Gravuren: Bogenprofil, Schlussstein, Kapitelle und Sockel der Pilaster
    lin = []
    r = Wo / 2
    hs = Ho - r
    for d in (1.4, 2.6):
        rr = r + d
        lin.append(([(-Wo / 2 - d, 0.6)] + [(rr * math.cos(a), hs + rr * math.sin(a))
                                           for a in (math.pi * (1 - i / 40) for i in range(41))] +
                    [(Wo / 2 + d, 0.6)], False))
    ks = min(luft - hf - m, Wo * 0.2)
    if ks > 3.5:
        lin.append(([(-ks * 0.32, Ho + 0.6), (-ks * 0.48, Ho + ks), (ks * 0.48, Ho + ks), (ks * 0.32, Ho + 0.6)],
                    False))
    for sg in (-1, 1):
        x0, x1 = sorted((sg * (Wo / 2 + 2.6 + 0.8), sg * (Wb / 2 - 0.8)))
        for y in (yk1 + m * 0.6, yk1 + m * 1.2, yk0 - m * 0.6):
            lin.append(([(x0, y), (x1, y)], False))
    Z.gravur(part, lin, rand=0.6)
    return part


def flamme(cx: float, y0: float, b: float, h: float, lean: float = 0.0):
    links = K.bez3((cx - b / 2, y0), (cx - b * 0.75, y0 + h * 0.45), (cx + lean - b * 0.15, y0 + h * 0.72),
                   (cx + lean, y0 + h), 16)
    rechts = K.bez3((cx + lean, y0 + h), (cx + b * 0.4 + lean * 0.4, y0 + h * 0.6), (cx + b * 0.75, y0 + h * 0.3),
                    (cx + b / 2, y0), 16)
    return links + rechts[1:-1]


def feuer(cfg, name: str, Wf: float, Hf: float, tf: float, pos: float, notes: List[str]):
    """Lodernde Flammen über zwei Holzscheiten, mit Zapfen unten."""
    T = cfg.T
    w = Z.wmin(cfg)
    hl = max(2.4 * w, Hf * 0.2)
    f = Z.Figur()
    f.add(Z.abrunden(K.rect(-Wf / 2, 0, Wf, hl), hl * 0.45, 4))                       # unteres Scheit
    f.add(K.stroke([(-Wf * 0.38, hl * 0.55), (Wf * 0.36, hl * 1.45)], hl * 0.85))      # schräges Scheit
    yf = hl * 0.6
    hf = Hf - yf
    zungen = ((0.0, Wf * 0.36, hf, Wf * 0.03), (-Wf * 0.27, Wf * 0.28, hf * 0.74, -Wf * 0.05),
              (Wf * 0.28, Wf * 0.28, hf * 0.8, Wf * 0.06), (-Wf * 0.13, Wf * 0.16, hf * 0.55, -Wf * 0.02),
              (Wf * 0.14, Wf * 0.16, hf * 0.6, Wf * 0.02))
    for cx, b, h, lean in zungen:
        f.add(flamme(cx, yf, b, h, lean))
    for cx, b, h, lean in zungen[:3]:
        bi = b * 0.5
        if bi > 2.4 * w:
            f.cut(flamme(cx + lean * 0.2, yf + h * 0.16, bi, h * 0.5, lean * 0.5))
    part = Z.figur_teil(cfg, name, f, notes, unten_flach=True)
    Z.zapfen_unten(part, 0.0, tf, T, "fuss", pos)
    lin = []
    for x in (-Wf / 2 + hl * 0.5, Wf / 2 - hl * 0.5):                                   # Jahresringe
        for rr in (hl * 0.18, hl * 0.32):
            lin.append((K.circle(x, hl / 2, rr, 16), True))
    lin.append(([(-Wf * 0.2, hl * 0.35), (Wf * 0.15, hl * 0.35)], False))
    Z.gravur(part, lin, rand=0.4)
    return part


def gitter(cfg, name: str, Wg: float, Hg: float, fuesse: Sequence[Tuple[float, str, float]], tg: float,
           notes: List[str]):
    """Funkengitter: Rahmen mit Bogen oben, senkrechte Stäbe, Medaillon mit Rosette in der Mitte, Füße."""
    T = cfg.T
    w = Z.wmin(cfg)
    hs = Hg * 0.72
    oben = K.bez3((Wg / 2, hs), (Wg * 0.3, Hg * 1.05), (-Wg * 0.3, Hg * 1.05), (-Wg / 2, hs), 30)
    umr = [(-Wg / 2, 0), (Wg / 2, 0)] + oben
    f = Z.Figur().add(umr)
    m = max(1.6, w * 1.15)
    fh = max(m * 2.2, Hg * 0.16)
    inner = [(-Wg / 2 + m, fh), (Wg / 2 - m, fh)] + [(x * (Wg / 2 - m) / (Wg / 2), fh + (y - fh) * (Hg - m - fh) / (Hg - fh))
                                                      for x, y in oben[1:-1]]
    f.cut(inner)
    def top_y(x):                                   # Oberkante des Fensters bei x
        pts = inner[2:]
        best = min(pts, key=lambda p: abs(p[0] - x))
        return best[1]
    # Bogen zwischen den Füßen
    fx = min(abs(x) for x, _, _ in fuesse) - tg / 2 - 2.2
    if fx > 2 * w:
        f.cut(K.ellipse(0, 0, fx, fh - max(m, w * 1.2), 0, 40))
    # Stäbe
    st = max(w, 1.0)
    n = max(3, int((Wg - 2 * m) / max(2.8, st * 2.6)))
    for i in range(1, n):
        x = -Wg / 2 + m + (Wg - 2 * m) * i / n
        f.add(K.rect(x - st / 2, fh - 0.3, st, top_y(x) - fh + 0.8))
    f.add(K.rect(-Wg / 2 + 0.5, fh + (Hg - fh) * 0.36, Wg - 1.0, st))                                # Querstab
    # Medaillon
    rm = min(Wg * 0.2, (Hg - fh) * 0.4)
    cy = fh + (Hg - fh) * 0.45
    if rm > 3 * w:
        f.add(K.circle(0, cy, rm, 48))
        f.cut(K.circle(0, cy, rm - st * 1.1, 48))
        f.merge(Z.rosette(rm - st * 1.1 + 0.3, "bluete", 6, w).map(lambda p: (p[0], p[1] + cy)))
    part = Z.figur_teil(cfg, name, f, notes, unten_flach=True)
    for x, fid, pos in fuesse:
        Z.zapfen_unten(part, x, tg, T, fid, pos)
    return part


def kerzenleuchter(cfg, name: str, g: float, t: float, pos: float, notes: List[str]):
    """Dreiarmiger Kerzenleuchter (bei kleiner Größe einarmig) mit Kerzen und Flammen, Zapfen unten."""
    T = cfg.T
    w = Z.wmin(cfg)
    f = Z.Figur()
    fb = max(t + 4.6, g * 0.42)
    f.add(Z.abrunden(K.rect(-fb / 2, 0, fb, max(1.6, w * 1.1)), 0.5, 2))
    f.add([(-fb * 0.45, 0.5), (fb * 0.45, 0.5), (fb * 0.16, g * 0.13), (-fb * 0.16, g * 0.13)])
    sw = max(w, g * 0.06)
    kb = max(w * 1.1, g * 0.1)                       # Kerzenbreite
    kh = g * 0.26
    drei = g >= 16.0
    ya = g * 0.48                                       # Höhe der Tropfschalen der Außenkerzen
    ym = g * 0.56 if drei else g * 0.5
    f.add(K.rect(-sw / 2, g * 0.05, sw, ym))
    for y in (g * 0.16, g * 0.3):                       # Knäufe
        f.add(K.ellipse(0, y, sw * 1.15, sw * 0.75, 0, 20))
    kerzen = [(0.0, ym)]
    if drei:
        ax = g * 0.27
        for sg in (-1, 1):
            arm = K.bez3((0, g * 0.3), (sg * ax * 0.2, g * 0.22), (sg * ax, g * 0.26), (sg * ax, ya), 16)
            f.add(K.stroke(arm, sw))
            kerzen.append((sg * ax, ya))
    for x, y in kerzen:
        f.add(K.ellipse(x, y, kb * 0.95, sw * 0.6, 0, 20))                                # Tropfschale
        f.add(K.rect(x - kb / 2, y, kb, kh))
        yk = y + kh
        f.add(K.rect(x - w * 0.5, yk - 0.3, w, g * 0.05 + 0.3))                           # Docht
        rf = max(w * 1.0, kb * 0.62)
        yc = yk + g * 0.04 + rf
        f.add(K.circle(x, yc, rf, 20))
        f.add([(x - rf * 0.92, yc + rf * 0.38), (x + rf * 0.92, yc + rf * 0.38), (x, yc + rf * 2.6)])
    part = Z.figur_teil(cfg, name, f, notes, unten_flach=True)
    Z.zapfen_unten(part, 0.0, t, T, "fuss", pos)
    return part


def kaminuhr(cfg, name: str, g: float, t: float, pos: float, notes: List[str]):
    """Kaminuhr mit geschwungenem Gehäuse, Sockel, Füßchen und Zierkugel; Zifferblatt graviert."""
    T = cfg.T
    w = Z.wmin(cfg)
    b = g * 0.72
    f = Z.Figur()
    hs = g * 0.12
    f.add(Z.abrunden(K.rect(-b / 2, 0, b, hs), 0.6, 2))                                  # Sockel
    bk = b * 0.8
    hk = g * 0.5
    rechts = K.bez3((bk / 2, hs + hk), (bk * 0.5, hs + hk * 1.25), (bk * 0.22, hs + hk * 1.25), (0, hs + hk * 1.32), 16)
    gehaeuse = [(-bk / 2, hs - 0.3), (bk / 2, hs - 0.3)] + rechts + [(-x, y) for x, y in reversed(rechts[:-1])]
    f.add(gehaeuse)
    for sg in (-1, 1):                                                                    # Voluten an den Seiten
        cx, cy = sg * (bk / 2), hs + hk * 0.45
        f.add(K.ellipse(cx, cy, max(w, g * 0.05), hk * 0.42, 0, 24))
    ytop = hs + hk * 1.32
    rk = max(w * 1.1, g * 0.05)
    f.add(K.rect(-w / 2, ytop - 0.4, w, rk * 1.4 + 0.4))
    f.add(K.circle(0, ytop + rk * 2.0, rk, 20))
    part = Z.figur_teil(cfg, name, f, notes, unten_flach=True)
    Z.zapfen_unten(part, 0.0, t, T, "fuss", pos)
    r = min(bk * 0.32, hk * 0.42)
    cy = hs + hk * 0.62
    lin = zifferblatt(0.0, cy, r)
    lin.append(([(-b / 2 + 1.0, hs * 0.55), (b / 2 - 1.0, hs * 0.55)], False))
    Z.gravur(part, lin, rand=0.5)
    return part


def girlande(cfg, name: str, L: float, h: float, notes: List[str]):
    """Girlande in Bögen: Blattranke mit Beeren, Kugeln unten in jedem Bogen, Schleifen an den Aufhängungen."""
    w = Z.wmin(cfg)
    n = max(2, int(round(L / (h * 3.4))))
    bw = max(w * 1.3, h * 0.17)
    f = Z.Figur()
    tief = h * 0.55
    xs = [-L / 2 + L * k / n for k in range(n + 1)]
    for k in range(n):
        x0, x1 = xs[k], xs[k + 1]
        pfad = [(x0 + (x1 - x0) * t, h - tief * math.sin(math.pi * t)) for t in (i / 24 for i in range(25))]
        f.add(K.stroke(pfad, bw))
        # Blätter abwechselnd über/unter der Ranke
        bl = max(2.2 * w, h * 0.34)
        pts = K.resample(pfad, bl * 0.55)
        for i in range(1, len(pts) - 1):
            (ax, ay), (bx, by) = pts[i - 1], pts[i + 1]
            ang = math.atan2(by - ay, bx - ax) + (0.9 if i % 2 else -0.9)
            f.add(Z.blatt(pts[i], ang, bl, max(w * 1.05, bl * 0.36)))
        xm = (x0 + x1) / 2
        rk = max(1.6 * w, h * 0.17)
        f.add(K.circle(xm, h - tief - rk * 0.9, rk, 24))
        f.add(K.rect(xm - w * 0.6, h - tief - rk * 0.15, w * 1.2, rk * 0.5))
    sb = max(5 * w, h * 0.7)
    for x in xs:
        f.merge(Z.schleife(sb, w).map(lambda p, x=x: (p[0] + x, p[1] + h)))
    part = Z.figur_teil(cfg, name, f, notes)
    return part


STRUMPF_MUSTER = ("streifen", "punkte", "herz")


def strumpf(cfg, name: str, hs: float, text: str, k: int, notes: List[str]):
    """Weihnachtsstrumpf mit Fellbund, Aufhängeschlaufe und Namen auf dem Bund."""
    w = Z.wmin(cfg)
    b = hs * 0.52
    f = Z.Figur()
    hb = hs * 0.24                                                                       # Fellbund
    f.add(Z.abrunden(K.rect(-b / 2, hs - hb, b, hb), hb * 0.3, 4))
    f.add(K.rect(-b * 0.4, hs * 0.3, b * 0.8, hs * 0.75 - hs * 0.3))                     # Schaft
    f.add(K.ellipse(b * 0.12, hs * 0.2, b * 0.78, hs * 0.2, 0, 48))                     # Fuß
    f.add(K.circle(-b * 0.2, hs * 0.26, hs * 0.2, 36))                                   # Ferse
    rs = max(hs * 0.08, w * 1.6)                                                         # Schlaufe
    f.add(K.circle(-b / 2 + rs * 0.3, hs + rs * 0.6, rs, 24))
    loch = rs - w
    if loch > 0.6:
        f.cut(K.circle(-b / 2 + rs * 0.3, hs + rs * 0.6, loch, 20))
    muster = STRUMPF_MUSTER[k % 3]
    if muster == "herz" and hs * 0.2 > 3.5 * w:
        f.cut(Z.herz(0.0, hs * 0.5, hs * 0.2))
    part = Z.figur_teil(cfg, name, f, notes)
    lin = []
    if muster == "streifen":
        for y in (hs * 0.42, hs * 0.52, hs * 0.62):
            lin.append(([(-b * 0.4, y), (b * 0.4, y)], False))
    elif muster == "punkte":
        for x, y in ((-b * 0.15, hs * 0.45), (b * 0.15, hs * 0.55), (-b * 0.12, hs * 0.66), (b * 0.2, hs * 0.38)):
            lin.append((K.circle(x, y, max(0.5, hs * 0.025), 10), True))
    lin.append((K.arc(b * 0.62, hs * 0.2, hs * 0.16, -math.pi * 0.45, math.pi * 0.45, 12), False))   # Spitze
    lin.append((K.arc(-b * 0.2, hs * 0.26, hs * 0.12, math.pi * 0.7, math.pi * 1.35, 12), False))    # Ferse
    Z.gravur(part, lin, rand=0.5)
    if text.strip():
        for t in (text.strip(), text.strip()[0]):
            try:
                st, _ = Z.text_in_box(t, 0.0, hs - hb / 2, b * 0.86, hb * 0.72, hb * 0.6, 1.4, 0.08)
                Z.gravur(part, [(s, False) for s in st], rand=0.3)
                if t != text.strip():
                    notes.append(f"„{text.strip()}“ ist für den Strumpf zu lang – graviert wird nur der Anfangsbuchstabe.")
                break
            except ValueError:
                continue
    return part


# --------------------------------------------------------------------------------------------------
# Über Kreuz gesteckte Paare (freistehend, von allen Seiten gleich)
# --------------------------------------------------------------------------------------------------

def kreuzpaar(cfg, name: str, fig_a, fig_b, notes: List[str], y_mid: float, gravur=None, px=None):
    """Zwei Figuren (Mittelachse x = 0) → Teile name_a (Schlitz von oben) und name_b (Schlitz von unten),
    über Kreuz zusammengesteckt. gravur(teil, von_oben) darf danach Linien ergänzen."""
    from models._shapes import cut_axis_slot
    from steckwerk import JointFeature, Part
    T = cfg.T
    out = []
    for suf, fig, von_oben in (("a", fig_a, True), ("b", fig_b, False)):
        p = Z.figur_teil(cfg, f"{name}_{suf}", fig, notes, unten_flach=True, px=px)
        umr, slot = cut_axis_slot(p.outline, T, y_mid, von_oben)
        ys = [q[1] for q in p.outline]
        span = (y_mid, max(ys)) if von_oben else (min(ys), y_mid)
        q = Part(p.name, umr, features=[JointFeature("kreuz", "halving", span[1] - span[0], T, span=span,
                                                     points=slot)])
        for h in p.holes:
            q.add_hole(h)
        if gravur:
            gravur(q, von_oben)
        out.append(q)
    return out


def geschenk(cfg, name: str, b: float, h: float, text: str, notes: List[str]):
    """Geschenkpäckchen aus zwei gekreuzten Teilen: Band als Gravur, Schleife oben (auf Teil b), Name."""
    T = cfg.T
    w = Z.wmin(cfg)
    if b < 2 * T + 8 or h < 2 * T + 6:
        raise ValueError("Die Geschenke sind für diese Materialstärke zu klein")
    a = Z.Figur().add(Z.abrunden(K.rect(-b / 2, 0, b, h), 0.5, 2))
    bb = Z.Figur().add(Z.abrunden(K.rect(-b / 2, 0, b, h), 0.5, 2))
    sb = min(b * 0.8, h * 0.9)
    bb.merge(Z.schleife(sb, w).map(lambda p: (p[0], p[1] + h + sb * 0.12)))
    bb.add(K.rect(-sb * 0.1, h - 0.5, sb * 0.2, sb * 0.14 + 0.5))

    def grav(part, von_oben):
        d = T / 2 + max(1.0, b * 0.08)
        lin = [([(sg * d, 0.4), (sg * d, h - 0.4)], False) for sg in (-1, 1)]
        yb = h * 0.55
        for yy in (yb - d * 0.7, yb + d * 0.7):
            for sg in (-1, 1):
                lin.append(([(sg * (T / 2 + 0.8), yy), (sg * (b / 2 - 0.4), yy)], False))
        Z.gravur(part, lin, rand=0.3)
        if text.strip() and not von_oben:
            x0 = d + 0.6
            try:
                st, _ = Z.text_in_box(text, (x0 + b / 2) / 2, h * 0.25, b / 2 - x0 - 0.6, h * 0.3, h * 0.25, 1.3, 0.08)
                Z.gravur(part, [(s, False) for s in st], rand=0.2)
            except ValueError:
                notes.append(f"„{text}“ passt nicht aufs Geschenk – größere Geschenke wählen.")
    return kreuzpaar(cfg, name, a, bb, notes, h * 0.5, grav)
