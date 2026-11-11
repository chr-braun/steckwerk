"""
montage.py – Teilenummern und Montageanleitung.

* nummerieren(asm)   graviert jedem Teil eine kleine Nummer ein (an der Stelle mit dem meisten Platz)
* teileliste(asm)    [(nummer, teilname)] in derselben Reihenfolge
* anleitung_pdf()    Montageanleitung als PDF: je Modell die Blätter mit Nummern, Teileliste und
                     Montage-Hinweise. Reines Python, keine Zusatzpakete.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

from steckwerk import Assembly, Config, Part, Sheet, Stroke, bbox, dist_to_boundary, point_in_polygon, \
    __version__
from models import _font

Point = Tuple[float, float]

NUMMER_HOEHE = 3.0      # Versalhöhe der Teilenummer in mm
NUMMER_MIN = 1.6        # kleiner wird nicht graviert (sonst nicht lesbar)


# ---------------------------------------------------------------------------
# Teilenummern
# ---------------------------------------------------------------------------

def _seg_dist(p: Point, a: Point, b: Point) -> float:
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def _platz(part: Part, p: Point) -> float:
    """Abstand von p zur nächsten Kante, zum nächsten Loch und zur nächsten Gravur (≤ 0 = kein Platz)."""
    if not point_in_polygon(p, part.outline):
        return -1.0
    d = dist_to_boundary(p, part.outline)
    for h in part.holes:
        if point_in_polygon(p, h):
            return -1.0
        d = min(d, dist_to_boundary(p, h))
    for s in part.engrave:
        pts = s.points
        n = len(pts)
        for i in range(n - 1 + (1 if s.closed else 0)):
            d = min(d, _seg_dist(p, pts[i], pts[(i + 1) % n]))
            if d <= 0:
                return d
    return d


def bester_platz(part: Part, raster: int = 14) -> Tuple[Optional[Point], float]:
    """Punkt im Teil mit dem größten Freiraum (grobes Raster, dann verfeinert)."""
    x0, y0, x1, y1 = bbox(part.outline)
    best, bd = None, 0.0
    for i in range(raster):
        for j in range(raster):
            p = (x0 + (i + 0.5) * (x1 - x0) / raster, y0 + (j + 0.5) * (y1 - y0) / raster)
            d = _platz(part, p)
            if d > bd:
                best, bd = p, d
    if best is None:
        return None, 0.0
    step = max(x1 - x0, y1 - y0) / raster / 2
    for _ in range(4):                       # verfeinern
        improved = True
        while improved:
            improved = False
            for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
                q = (best[0] + dx, best[1] + dy)
                d = _platz(part, q)
                if d > bd:
                    best, bd, improved = q, d, True
        step /= 2
    return best, bd


def _nummer_striche(text: str, cx: float, cy: float, frei: float, cfg: Config) -> List[List[Point]]:
    # Text muss mit Abstand (min_web) in den Freiraum-Kreis passen
    rand = max(0.6, cfg.min_web)
    raw = _font.text_strokes(text)
    xs = [p[0] for s in raw for p in s]
    ys = [p[1] for s in raw for p in s]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    # Halbdiagonale des Texts (in mm) ≤ frei - rand
    for cap in (NUMMER_HOEHE, 2.5, 2.0, NUMMER_MIN):
        k = cap / _font.CAP
        if math.hypot(w * k, h * k) / 2 <= frei - rand:
            mx, my = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
            return [[(cx + (x - mx) * k, cy + (y - my) * k) for x, y in s] for s in raw]
    return []


def nummerieren(asm: Assembly, cfg: Config) -> Assembly:
    """Kopie der Baugruppe, in der jedes Teil seine Nummer (1, 2, …) eingraviert hat.
    Wo kein Platz ist (sehr schmale Teile), bleibt das Teil ohne Nummer – die Teileliste
    nennt es trotzdem."""
    neu: List[Part] = []
    for i, p in enumerate(asm.parts, 1):
        q = Part(p.name, list(p.outline), [list(h) for h in p.holes],
                 [Stroke(list(s.points), s.closed) for s in p.engrave], p.features, p.note)
        pt, frei = bester_platz(q)
        if pt is not None:
            for s in _nummer_striche(str(i), pt[0], pt[1], frei, cfg):
                if len(s) >= 2:
                    q.engrave.append(Stroke(s, False))
        neu.append(q)
    return Assembly(asm.name, neu, list(asm.connections), list(asm.notes), dict(asm.params))


def teileliste(asm: Assembly) -> List[Tuple[int, str]]:
    return [(i, p.name) for i, p in enumerate(asm.parts, 1)]


# ---------------------------------------------------------------------------
# Kleines PDF (A4, Vektorlinien, Helvetica)
# ---------------------------------------------------------------------------
A4 = (595.28, 841.89)          # pt
MM = 72 / 25.4


def _pdf_text(s: str) -> str:
    for a, b_ in (("≈", "~"), ("→", "->"), ("≤", "<="), ("≥", ">="), ("√", "v"), ("·", "·")):
        s = s.replace(a, b_)
    b = s.encode("cp1252", "replace").decode("latin-1")
    return b.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class _Seite:
    def __init__(self):
        self.ops: List[str] = []

    def text(self, x: float, y: float, s: str, size: float = 10, bold: bool = False) -> None:
        self.ops.append(f"0 0 0 rg BT /{'F2' if bold else 'F1'} {size:g} Tf {x:.2f} {y:.2f} Td ({_pdf_text(s)}) Tj ET")

    def linie(self, pts: Sequence[Point], closed: bool, rgb=(0, 0, 0), w: float = 0.5, fill=None) -> None:
        if len(pts) < 2:
            return
        cmd = [f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} RG {w:.2f} w"]
        if fill:
            cmd.append(f"{fill[0]:.3f} {fill[1]:.3f} {fill[2]:.3f} rg")
        cmd.append(f"{pts[0][0]:.2f} {pts[0][1]:.2f} m")
        cmd += [f"{x:.2f} {y:.2f} l" for x, y in pts[1:]]
        cmd.append(("b" if fill else "s") if closed else "S")
        self.ops.append(" ".join(cmd))


def _pdf(seiten: List[_Seite]) -> bytes:
    objs: List[bytes] = []

    def add(b: str | bytes) -> int:
        objs.append(b.encode("latin-1") if isinstance(b, str) else b)
        return len(objs)

    add("<< /Type /Catalog /Pages 2 0 R >>")
    add("")                                                   # Platzhalter Pages
    f1 = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    f2 = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    kids = []
    for s in seiten:
        body = "\n".join(s.ops).encode("latin-1")
        c = add(b"<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream")
        kids.append(add(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {A4[0]} {A4[1]}] "
                        f"/Resources << /Font << /F1 {f1} 0 R /F2 {f2} 0 R >> >> /Contents {c} 0 R >>"))
    objs[1] = (f"<< /Type /Pages /Count {len(kids)} /Kids [" + " ".join(f"{k} 0 R" for k in kids) + "] >>"
               ).encode("latin-1")
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offs).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def _umbruch(text: str, n: int = 95) -> List[str]:
    out, zeile = [], ""
    for w in text.split():
        if len(zeile) + len(w) + 1 > n:
            out.append(zeile)
            zeile = w
        else:
            zeile = (zeile + " " + w).strip()
    if zeile:
        out.append(zeile)
    return out or [""]


def anleitung_pdf(eintraege: Sequence[Tuple[Assembly, Sequence[Sheet], Optional[Dict]]], cfg: Config) -> bytes:
    """eintraege: (Baugruppe, Blätter, Schätzung oder None). Je Modell: Übersicht der Blätter mit
    Teilenummern, dann Teileliste und Montage-Schritte."""
    seiten: List[_Seite] = []
    L, R, OBEN = 40.0, A4[0] - 40.0, A4[1] - 50.0
    for asm, sheets, sch in eintraege:
        nummer = {name: i for i, name in teileliste(asm)}
        s = _Seite()
        seiten.append(s)
        y = OBEN
        s.text(L, y, f"Montageanleitung – {asm.name}", 16, True)
        y -= 18
        info = f"Steckwerk {__version__} · {cfg.thickness:g} mm Material · Kerf {cfg.kerf:g} mm · " \
               f"{len(asm.parts)} Teile · {len(sheets)} Blatt"
        if sch:
            info += f" · Laserzeit ca. {sch['zeit']}"
        s.text(L, y, info, 9)
        y -= 14
        # Blätter zeichnen
        for sh in sheets:
            bw = R - L
            k = min(bw / sh.width, 300 / sh.height)
            h = sh.height * k
            if y - h < 60:
                s = _Seite()
                seiten.append(s)
                y = OBEN
            top = y

            def tr(p, top=top, k=k):
                return (L + p[0] * k, top - p[1] * k)
            s.linie([tr((0, 0)), tr((sh.width, 0)), tr((sh.width, sh.height)), tr((0, sh.height))], True,
                    (0.7, 0.7, 0.7), 0.4)
            s.text(L, top + 3, f"Blatt {sh.index}", 8, True)
            for p in sh.parts:
                s.linie([tr(q) for q in p.outline], True, (0, 0, 0), 0.5, fill=(0.96, 0.9, 0.8))
                for hpoly in p.holes:
                    s.linie([tr(q) for q in hpoly], True, (0, 0, 0), 0.4, fill=(1, 1, 1))
                for st in p.engrave:
                    s.linie([tr(q) for q in st.points], st.closed, (0.1, 0.3, 0.9), 0.3)
                n = nummer.get(p.name)
                if n is not None:
                    x0, y0, x1, y1 = bbox(p.outline)
                    cx, cy = tr(((x0 + x1) / 2, (y0 + y1) / 2))
                    r = 6.5
                    s.linie([(cx + r * math.cos(a / 8 * math.pi), cy + r * math.sin(a / 8 * math.pi))
                             for a in range(16)], True, (0.75, 0.2, 0.1), 0.6, fill=(1, 1, 1))
                    s.text(cx - (2.6 if n < 10 else 5), cy - 3, str(n), 8.5, True)
            y = top - h - 22
        # Teileliste
        if y < 140:
            s = _Seite()
            seiten.append(s)
            y = OBEN
        s.text(L, y, "Teile", 12, True)
        y -= 15
        spalten = 3
        liste = teileliste(asm)
        breite = (R - L) / spalten
        zeilen = math.ceil(len(liste) / spalten)
        for idx, (n, name) in enumerate(liste):
            col, row = divmod(idx, zeilen)
            yy = y - row * 12
            if yy < 50:
                continue
            s.text(L + col * breite, yy, f"{n:>3}  {name[:32]}", 8.5)
        y -= zeilen * 12 + 14
        # Montage
        if asm.notes:
            if y < 100:
                s = _Seite()
                seiten.append(s)
                y = OBEN
            s.text(L, y, "Zusammenbau", 12, True)
            y -= 15
            for i, note in enumerate(asm.notes, 1):
                for j, zeile in enumerate(_umbruch(note)):
                    if y < 50:
                        s = _Seite()
                        seiten.append(s)
                        y = OBEN
                    s.text(L, y, (f"{i}. " if j == 0 else "    ") + zeile, 9)
                    y -= 12
                y -= 3
    if not seiten:
        seiten.append(_Seite())
    return _pdf(seiten)
