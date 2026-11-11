"""
bilder.py – eigene Fotos und Logos als Bild-Gravur (Rastergravur) für den Laser.

Ablauf
  1. Import    PNG direkt; JPG, HEIC, GIF, TIFF, WebP über Pillow (falls installiert) oder unter macOS
               über das eingebaute „sips“. Browser-Oberfläche und Steckwerk Desktop wandeln Fotos schon
               vor dem Hochladen in PNG um – dort geht also jedes Format, das der Rechner anzeigen kann.
               Gespeichert wird ein Graustufenbild (längere Seite höchstens MAX_SEITE Pixel) als Rohdaten:
               so muss beim Rechnen kein PNG mehr entpackt werden (wichtig auf alten Rechnern).
  2. Aufbereiten  Ausschnitt, Größe in mm, Auflösung (Pixel je mm), Helligkeit, Kontrast, Gamma,
               Umkehren und Rastermodus (Graustufen, Fehlerstreuung, Schwarzweiß, Skizze). Pixel außerhalb
               der Maske (Bauteilform, Durchbrüche, Bildform) bleiben weiß und durchsichtig.
               Das Ergebnis wird zwischengespeichert (Arbeitsspeicher und Ordner „Zwischenspeicher“),
               ein zweites Rechnen mit denselben Werten kostet nichts.

Bibliothek: macOS ~/Library/Application Support/Steckwerk/Bilder, sonst ~/.steckwerk/bilder,
oder erster Ordner aus $STECKWERK_BILDER.

Nur Python-Standardbibliothek (Pillow/sips nur optional für weitere Dateiformate).
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import zlib
from collections import OrderedDict
from typing import List, Optional, Sequence, Tuple

import motive as mt

Point = Tuple[float, float]

MAX_BYTES = 25 * 1024 * 1024         # Fotos vom Telefon sind schnell 10 MB groß
MAX_SEITE = 1600                     # gespeicherte Auflösung: reicht für 160 mm bei 10 Pixel/mm
VORSCHAU_SEITE = 240
MODI = [("graustufen", "Graustufen (XCS rastert)"), ("fehlerstreuung", "Fotogravur (Punkte, fein)"),
        ("schwarzweiss", "Schwarzweiß (Logo)"), ("skizze", "Skizze (Konturen)")]
MODUS_KEYS = [k for k, _ in MODI]
FORMEN = [("rechteck", "Rechteck"), ("abgerundet", "abgerundet"), ("oval", "Oval"), ("kreis", "Kreis"),
          ("herz", "Herz"), ("weich", "weicher Rand")]
FORM_KEYS = [k for k, _ in FORMEN]
AUFLOESUNGEN = (5.0, 8.0, 10.0, 12.7)  # Pixel je mm (127, 203, 254, 323 dpi)
STANDARD_AUFLOESUNG = 10.0


class BildFehler(ValueError):
    pass


# ==================================================================================================
# Lesen
# ==================================================================================================

def _from_pillow(data: bytes) -> Optional[Tuple[int, int, bytes, Optional[bytes]]]:
    try:
        from PIL import Image, ImageOps                        # type: ignore
    except Exception:                                          # pragma: no cover - je nach Rechner
        return None
    import io
    try:
        im = Image.open(io.BytesIO(data))
        im = ImageOps.exif_transpose(im)                       # Handyfotos richtig herum
    except Exception:
        return None
    alpha = None
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        a = im.convert("RGBA").getchannel("A")
        if a.getextrema()[0] < 250:
            alpha = a.tobytes()
    g = im.convert("L")
    return g.width, g.height, g.tobytes(), alpha


def _via_sips(data: bytes) -> Optional[bytes]:
    """macOS: beliebiges Bildformat mit dem eingebauten sips in PNG umwandeln."""
    if sys.platform != "darwin" or not shutil.which("sips"):
        return None
    d = tempfile.mkdtemp(prefix="steckwerk-bild-")
    try:
        src, dst = os.path.join(d, "in"), os.path.join(d, "out.png")
        with open(src, "wb") as fh:
            fh.write(data)
        subprocess.run(["sips", "-s", "format", "png", src, "--out", dst], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        with open(dst, "rb") as fh:
            return fh.read()
    except Exception:
        return None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _art(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftyphevc"):
        return "heic"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if b"<svg" in data[:4096].lower():
        return "svg"
    return "?"


def decode(data: bytes) -> Tuple[int, int, bytes, Optional[bytes]]:
    """Bilddatei → (Breite, Höhe, Graustufen-Bytes zeilenweise, Alpha-Bytes oder None)."""
    if not data:
        raise BildFehler("Leere Datei")
    if len(data) > MAX_BYTES:
        raise BildFehler("Datei zu groß (höchstens 25 MB)")
    art = _art(data)
    if art == "svg":
        raise BildFehler("SVG ist eine Vektorgrafik – bitte unter „Motive“ importieren (wird gestochen scharf)")
    if art == "png":
        try:
            return _png_rows(data)
        except mt.MotivFehler as e:
            hit = _from_pillow(data)                            # z. B. interlaced oder sehr groß
            if hit:
                return hit
            raise BildFehler(str(e))
    hit = _from_pillow(data)
    if hit:
        return hit
    png = _via_sips(data)
    if png:
        return _png_rows(png)
    namen = {"jpg": "JPG", "gif": "GIF", "heic": "HEIC", "webp": "WebP", "tiff": "TIFF"}
    if art in namen:
        raise BildFehler(f"{namen[art]} kann dieser Rechner ohne Hilfe nicht lesen – in der Steckwerk-Oberfläche "
                         f"importieren (wandelt automatisch um) oder als PNG speichern")
    raise BildFehler("Unbekanntes Bildformat – PNG, JPG oder HEIC verwenden")


def _png_rows(data: bytes) -> Tuple[int, int, bytes, Optional[bytes]]:
    w, h, gray, alpha = _read_png_big(data)
    return w, h, b"".join(bytes(r) for r in gray), (b"".join(bytes(r) for r in alpha) if alpha else None)


def _read_png_big(data: bytes):
    """mt.read_png erlaubt höchstens 3000×3000 – für Fotos großzügiger (wird ohnehin verkleinert)."""
    old = mt.MAX_PIXELS
    mt.MAX_PIXELS = max(old, 6000 * 6000)
    try:
        return mt.read_png(data)
    finally:
        mt.MAX_PIXELS = old


# ==================================================================================================
# Schreiben (PNG, nur zlib)
# ==================================================================================================

def png_bytes(w: int, h: int, gray: bytes, alpha: Optional[bytes] = None, ppmm: float = 0.0) -> bytes:
    """Graustufen-PNG (mit Alpha, falls angegeben). ppmm setzt die physikalische Auflösung (pHYs),
    damit Programme wie xTool Creative Space die Größe in mm kennen."""
    if alpha is not None:
        raw = bytearray()
        for y in range(h):
            raw.append(0)
            row = bytearray(2 * w)
            row[0::2] = gray[y * w:(y + 1) * w]
            row[1::2] = alpha[y * w:(y + 1) * w]
            raw += row
        ctype = 4
    else:
        raw = bytearray()
        for y in range(h):
            raw.append(0)
            raw += gray[y * w:(y + 1) * w]
        ctype = 0

    def chunk(t: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + t + body + struct.pack(">I", zlib.crc32(t + body) & 0xFFFFFFFF)
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
    if ppmm > 0:
        ppm = int(round(ppmm * 1000))
        out += chunk(b"pHYs", struct.pack(">IIB", ppm, ppm, 1))
    return out + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")


def data_uri(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


# ==================================================================================================
# Skalieren
# ==================================================================================================

def resize(w: int, h: int, px: bytes, W: int, H: int) -> bytes:
    """Flächenmittel beim Verkleinern (keine Treppen, kein Flimmern), bilinear beim Vergrößern.
    Zweistufig (erst Zeilen, dann Spalten) – das hält die Laufzeit auch in reinem Python klein."""
    if (W, H) == (w, h):
        return bytes(px)
    tmp = _resize_axis(px, w, h, W, horizontal=True)
    return _resize_axis(tmp, W, h, H, horizontal=False)


def _weights(n: int, N: int) -> List[List[Tuple[int, float]]]:
    out = []
    if N <= n:                                    # verkleinern: Flächenmittel
        k = n / N
        for i in range(N):
            a, b = i * k, (i + 1) * k
            ws = []
            j = int(a)
            while j < b and j < n:
                lo, hi = max(a, j), min(b, j + 1)
                if hi > lo:
                    ws.append((j, (hi - lo) / k))
                j += 1
            out.append(ws)
    else:                                         # vergrößern: bilinear
        k = n / N
        for i in range(N):
            x = (i + 0.5) * k - 0.5
            j = int(math.floor(x))
            t = x - j
            j0, j1 = min(max(j, 0), n - 1), min(max(j + 1, 0), n - 1)
            out.append([(j0, 1 - t), (j1, t)])
    return out


def _resize_axis(px: bytes, w: int, h: int, N: int, horizontal: bool) -> bytes:
    if horizontal:
        if N == w:
            return bytes(px)
        ws = _weights(w, N)
        out = bytearray(N * h)
        for y in range(h):
            row = px[y * w:(y + 1) * w]
            o = y * N
            for i, wl in enumerate(ws):
                s = 0.0
                for j, f in wl:
                    s += row[j] * f
                out[o + i] = int(s + 0.5) if s < 254.5 else 255
        return bytes(out)
    if N == h:
        return bytes(px)
    ws = _weights(h, N)
    out = bytearray(w * N)
    rows = [px[y * w:(y + 1) * w] for y in range(h)]
    for i, wl in enumerate(ws):
        if len(wl) == 1:
            out[i * w:(i + 1) * w] = rows[wl[0][0]]
            continue
        acc = [0.0] * w
        for j, f in wl:
            r = rows[j]
            for x in range(w):
                acc[x] += r[x] * f
        out[i * w:(i + 1) * w] = bytes(min(255, int(v + 0.5)) for v in acc)
    return bytes(out)


# ==================================================================================================
# Bibliothek
# ==================================================================================================

def user_dir() -> str:
    env = [d for d in os.environ.get("STECKWERK_BILDER", "").split(os.pathsep) if d]
    if env:
        return os.path.abspath(os.path.expanduser(env[0]))
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Steckwerk/Bilder")
    return os.path.expanduser("~/.steckwerk/bilder")


def cache_dir() -> str:
    return os.path.join(user_dir(), "Zwischenspeicher")


_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
_GELADEN: "OrderedDict[str, Tuple[float, dict]]" = OrderedDict()
_LOCK = threading.Lock()


def _meta_path(bid: str) -> Optional[str]:
    if not _ID.match(bid or ""):
        return None
    p = os.path.join(user_dir(), bid + ".json")
    return p if os.path.isfile(p) else None


def exists(bid: str) -> bool:
    return _meta_path(bid) is not None


def load(bid: str) -> dict:
    """Bild mit Pixeln: {id, name, w, h, grau: bytes, alpha: bytes|None}. Hält die letzten zwei im Speicher."""
    p = _meta_path(bid)
    if not p:
        raise BildFehler(f"Bild {bid!r} gibt es nicht (mehr) – in der Bild-Bibliothek neu wählen")
    mtime = os.path.getmtime(p)
    with _LOCK:
        hit = _GELADEN.get(bid)
        if hit and hit[0] == mtime:
            _GELADEN.move_to_end(bid)
            return hit[1]
    with open(p, encoding="utf-8") as fh:
        meta = json.load(fh)
    base = os.path.join(user_dir(), bid)
    with open(base + ".grau", "rb") as fh:
        grau = fh.read()
    alpha = None
    if os.path.isfile(base + ".alpha"):
        with open(base + ".alpha", "rb") as fh:
            alpha = fh.read()
    w, h = int(meta["w"]), int(meta["h"])
    if len(grau) != w * h or (alpha is not None and len(alpha) != w * h):
        raise BildFehler(f"Bild {bid!r} ist beschädigt – bitte neu importieren")
    b = dict(meta, id=bid, grau=grau, alpha=alpha)
    with _LOCK:
        _GELADEN[bid] = (mtime, b)
        while len(_GELADEN) > 2:
            _GELADEN.popitem(last=False)
    return b


def summary(meta: dict) -> dict:
    return dict(id=meta["id"], name=meta.get("name", meta["id"]), w=meta["w"], h=meta["h"],
                seiten=round(meta["w"] / max(1, meta["h"]), 4), alpha=bool(meta.get("alpha")),
                vorschau=meta.get("vorschau", ""))


def library() -> List[dict]:
    d = user_dir()
    out = []
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json") or not _ID.match(fn[:-5]):
                continue
            try:
                with open(os.path.join(d, fn), encoding="utf-8") as fh:
                    meta = json.load(fh)
                meta["id"] = fn[:-5]
                out.append(summary(meta))
            except (OSError, ValueError, KeyError):
                continue
    out.sort(key=lambda m: m["name"].lower())
    return out


def import_bytes(data: bytes, filename: str = "", name: str = "") -> dict:
    """Foto/Logo einlesen, verkleinern und in der Bibliothek speichern. Liefert die Kurzinfo."""
    w, h, grau, alpha = decode(data)
    if w < 8 or h < 8:
        raise BildFehler("Bild zu klein (mindestens 8 × 8 Pixel)")
    if max(w, h) > MAX_SEITE:
        k = MAX_SEITE / max(w, h)
        W, H = max(1, round(w * k)), max(1, round(h * k))
        grau = resize(w, h, grau, W, H)
        if alpha is not None:
            alpha = resize(w, h, alpha, W, H)
        w, h = W, H
    if alpha is not None and min(alpha) >= 250:
        alpha = None
    name = (name or os.path.splitext(os.path.basename(filename or ""))[0] or "Bild").strip()[:40]
    bid = f"{mt.slug(name)[:24]}-{hashlib.sha1(data).hexdigest()[:6]}"
    k = VORSCHAU_SEITE / max(w, h)
    tw, th = max(1, round(w * k)), max(1, round(h * k))
    thumb = png_bytes(tw, th, resize(w, h, grau, tw, th), resize(w, h, alpha, tw, th) if alpha else None)
    meta = dict(name=name, w=w, h=h, alpha=alpha is not None, quelle=_art(data),
                vorschau=data_uri(thumb))
    d = user_dir()
    os.makedirs(d, exist_ok=True)
    base = os.path.join(d, bid)
    for ext, body in ((".grau", grau), (".alpha", alpha)):
        if body is None:
            if os.path.exists(base + ext):
                os.remove(base + ext)
            continue
        with open(base + ext + ".tmp", "wb") as fh:
            fh.write(body)
        os.replace(base + ext + ".tmp", base + ext)
    with open(base + ".json.tmp", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False)
    os.replace(base + ".json.tmp", base + ".json")
    meta["id"] = bid
    return summary(meta)


def import_file(path: str, name: str = "") -> dict:
    with open(path, "rb") as fh:
        data = fh.read(MAX_BYTES + 1)
    return import_bytes(data, os.path.basename(path), name)


def remove(bid: str) -> None:
    if not exists(bid):
        raise BildFehler(f"Bild {bid!r} gibt es nicht")
    base = os.path.join(user_dir(), bid)
    for ext in (".json", ".grau", ".alpha"):
        if os.path.exists(base + ext):
            os.remove(base + ext)
    with _LOCK:
        _GELADEN.pop(bid, None)


# ==================================================================================================
# Aufbereiten für die Gravur
# ==================================================================================================

def _lut(helligkeit: float, kontrast: float, gamma: float, invert: bool) -> bytes:
    """Tonwertkurve als Tabelle: Helligkeit/Kontrast −100…100, Gamma 0,3…3."""
    c = max(-99.0, min(100.0, kontrast)) / 100.0
    f = (1 + c) / (1 - c) if c >= 0 else 1 + c
    b = helligkeit / 100.0 * 255
    g = max(0.3, min(3.0, gamma or 1.0))
    out = bytearray(256)
    for v in range(256):
        x = (v - 128) * f + 128 + b
        x = min(255.0, max(0.0, x))
        x = 255.0 * (x / 255.0) ** (1.0 / g)
        if invert:
            x = 255 - x
        out[v] = int(x + 0.5)
    return bytes(out)


def _auto_tonwert(px: bytes, mask: Optional[bytearray]) -> bytes:
    """Histogramm auf 1 %…99 % strecken (flaue Handyfotos werden kräftiger)."""
    hist = [0] * 256
    if mask is None:
        for v in px:
            hist[v] += 1
    else:
        for v, m in zip(px, mask):
            if m:
                hist[v] += 1
    n = sum(hist)
    if n < 16:
        return bytes(range(256))
    lo_n, hi_n = n * 0.01, n * 0.99
    acc, lo, hi = 0, 0, 255
    for i, c in enumerate(hist):
        acc += c
        if acc >= lo_n:
            lo = i
            break
    acc = 0
    for i, c in enumerate(hist):
        acc += c
        if acc >= hi_n:
            hi = i
            break
    if hi - lo < 16:
        return bytes(range(256))
    return bytes(min(255, max(0, int((v - lo) * 255 / (hi - lo) + 0.5))) for v in range(256))


def _floyd(px: bytearray, w: int, h: int, mask: Optional[bytearray]) -> bytearray:
    """Fehlerstreuung (Floyd–Steinberg, Serpentine). Ergebnis 0/255."""
    out = bytearray(w * h)
    cur = [float(v) for v in px[0:w]]
    for y in range(h):
        nxt = [float(v) for v in px[(y + 1) * w:(y + 2) * w]] if y + 1 < h else [0.0] * w
        o = y * w
        if y % 2 == 0:
            rng, d = range(w), 1
        else:
            rng, d = range(w - 1, -1, -1), -1
        for x in rng:
            if mask is not None and not mask[o + x]:
                out[o + x] = 255
                continue
            old = cur[x]
            new = 255 if old >= 128 else 0
            out[o + x] = new
            e = old - new
            if e == 0:
                continue
            x1 = x + d
            if 0 <= x1 < w:
                cur[x1] += e * 0.4375
                nxt[x1] += e * 0.0625
            x0 = x - d
            if 0 <= x0 < w:
                nxt[x0] += e * 0.1875
            nxt[x] += e * 0.3125
        cur = nxt
    return out


def _sobel(px: bytes, w: int, h: int) -> bytearray:
    """Kantenstärke → dunkle Linien auf weißem Grund (Bleistiftskizze)."""
    out = bytearray(b"\xff" * (w * h))
    for y in range(1, h - 1):
        a, b, c = (y - 1) * w, y * w, (y + 1) * w
        for x in range(1, w - 1):
            gx = (px[a + x + 1] + 2 * px[b + x + 1] + px[c + x + 1]) - (px[a + x - 1] + 2 * px[b + x - 1] + px[c + x - 1])
            gy = (px[c + x - 1] + 2 * px[c + x] + px[c + x + 1]) - (px[a + x - 1] + 2 * px[a + x] + px[a + x + 1])
            g = abs(gx) + abs(gy)
            if g > 0:
                out[b + x] = max(0, 255 - min(255, g >> 1))
    return out


def _form_poly(form: str, w: float, h: float) -> Optional[List[Point]]:
    """Bildform in Pixeln (y nach unten), None = ganzes Rechteck."""
    cx, cy = w / 2, h / 2
    if form == "oval":
        return [(cx + cx * math.cos(t * math.pi / 90), cy + cy * math.sin(t * math.pi / 90)) for t in range(180)]
    if form == "kreis":
        r = min(cx, cy)
        return [(cx + r * math.cos(t * math.pi / 90), cy + r * math.sin(t * math.pi / 90)) for t in range(180)]
    if form == "abgerundet":
        r = min(w, h) * 0.12
        pts = []
        for (ox, oy, a0) in ((w - r, h - r, 0), (r, h - r, 90), (r, r, 180), (w - r, r, 270)):
            for k in range(13):
                a = math.radians(a0 + k * 7.5)
                pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
        return pts
    if form == "herz":
        pts = []
        for k in range(200):
            t = 2 * math.pi * k / 200
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((cx + x / 17.0 * cx, cy - (y + 2.5) / 16.5 * cy))
        return pts
    return None


def _fill_mask(w: int, h: int, polys: Sequence[Sequence[Point]]) -> bytearray:
    r = mt.Raster(w, h).fill(polys, "evenodd")
    out = bytearray(w * h)
    for y, row in enumerate(r.rows):
        if not row:
            continue
        o = y * w
        x = 0
        while row:
            if row & 1:
                out[o + x] = 1
            row >>= 1
            x += 1
    return out


_ERGEBNIS: "OrderedDict[str, Tuple[int, int, bytes]]" = OrderedDict()


def aufbereiten(bid: str, breite: float, hoehe: float, ppmm: float = STANDARD_AUFLOESUNG,
                modus: str = "fehlerstreuung", helligkeit: float = 0.0, kontrast: float = 0.0, gamma: float = 1.0,
                invertieren: bool = False, form: str = "rechteck", ausschnitt: Optional[Tuple[float, float, float, float]] = None,
                maske: Optional[Sequence[Sequence[Point]]] = None, auto: bool = True) -> Tuple[int, int, bytes]:
    """Fertiges Gravurbild (W, H, PNG-Bytes mit Alpha) für eine Fläche breite × hoehe mm.

    ausschnitt  (x0, y0, x1, y1) als Anteil 0…1 des Quellbilds (Standard: ganz)
    maske       Polygone in Bild-mm (Ursprung oben links, y nach unten); gerade/ungerade-Regel.
                Nur Pixel innerhalb werden graviert (Bauteilfläche ohne Durchbrüche).
    """
    if modus not in MODUS_KEYS:
        raise BildFehler(f"Rastermodus {modus!r} unbekannt – erlaubt: {', '.join(MODUS_KEYS)}")
    if form not in FORM_KEYS:
        raise BildFehler(f"Bildform {form!r} unbekannt – erlaubt: {', '.join(FORM_KEYS)}")
    if breite <= 0 or hoehe <= 0:
        raise BildFehler("Bildgröße muss größer als 0 sein")
    b = load(bid)
    ppmm = max(2.0, min(20.0, float(ppmm)))
    W, H = max(1, int(round(breite * ppmm))), max(1, int(round(hoehe * ppmm)))
    if W * H > 4_000_000:
        raise BildFehler(f"Bild-Gravur zu groß ({breite:.0f} × {hoehe:.0f} mm bei {ppmm:g} Pixel/mm) – "
                         f"kleiner machen oder eine geringere Auflösung wählen")
    key_src = json.dumps([bid, b.get("w"), b.get("h"), len(b["grau"]), round(breite, 3), round(hoehe, 3), ppmm,
                          modus, helligkeit, kontrast, gamma, bool(invertieren), form, ausschnitt, auto,
                          [[(round(x, 3), round(y, 3)) for x, y in p] for p in (maske or [])]],
                         separators=(",", ":"))
    key = hashlib.sha1(key_src.encode()).hexdigest()
    with _LOCK:
        hit = _ERGEBNIS.get(key)
        if hit:
            _ERGEBNIS.move_to_end(key)
            return hit
    path = os.path.join(cache_dir(), key + ".png")
    if os.path.isfile(path):
        try:
            with open(path, "rb") as fh:
                png = fh.read()
            res = (W, H, png)
            _merken(key, res)
            return res
        except OSError:
            pass
    res = (W, H, _rechnen(b, W, H, ppmm, modus, helligkeit, kontrast, gamma, invertieren, form, ausschnitt,
                          maske, auto))
    _merken(key, res)
    try:
        os.makedirs(cache_dir(), exist_ok=True)
        with open(path + ".tmp", "wb") as fh:
            fh.write(res[2])
        os.replace(path + ".tmp", path)
        _aufraeumen()
    except OSError:
        pass
    return res


def _merken(key: str, res) -> None:
    with _LOCK:
        _ERGEBNIS[key] = res
        while len(_ERGEBNIS) > 8:
            _ERGEBNIS.popitem(last=False)


def _aufraeumen(max_dateien: int = 200) -> None:
    """Zwischenspeicher klein halten: älteste Dateien löschen."""
    d = cache_dir()
    try:
        files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".png")]
    except OSError:
        return
    if len(files) <= max_dateien:
        return
    files.sort(key=lambda p: os.path.getmtime(p))
    for p in files[:len(files) - max_dateien]:
        try:
            os.remove(p)
        except OSError:
            pass


def _rechnen(b: dict, W: int, H: int, ppmm: float, modus: str, helligkeit: float, kontrast: float, gamma: float,
             invertieren: bool, form: str, ausschnitt, maske, auto: bool) -> bytes:
    w, h, grau, alpha = int(b["w"]), int(b["h"]), b["grau"], b["alpha"]
    if ausschnitt:
        x0, y0, x1, y1 = ausschnitt
        X0, Y0 = max(0, int(x0 * w)), max(0, int(y0 * h))
        X1, Y1 = min(w, max(X0 + 1, int(round(x1 * w)))), min(h, max(Y0 + 1, int(round(y1 * h))))
        if (X0, Y0, X1, Y1) != (0, 0, w, h):
            grau = b"".join(grau[y * w + X0:y * w + X1] for y in range(Y0, Y1))
            if alpha is not None:
                alpha = b"".join(alpha[y * w + X0:y * w + X1] for y in range(Y0, Y1))
            w, h = X1 - X0, Y1 - Y0
    px = bytearray(resize(w, h, grau, W, H))
    al = resize(w, h, alpha, W, H) if alpha is not None else None
    if al is not None:                                     # freigestellt: durchsichtig = weiß
        for i, a in enumerate(al):
            if a < 255:
                px[i] = 255 - ((255 - px[i]) * a) // 255
    # Maske: Bauteilfläche × Bildform × deckende Pixel
    mask: Optional[bytearray] = None
    polys = [[(x * ppmm, y * ppmm) for x, y in p] for p in (maske or []) if len(p) >= 3]
    if polys:
        mask = _fill_mask(W, H, polys)
    fp = _form_poly(form, W, H)
    if fp:
        fm = _fill_mask(W, H, [fp])
        mask = fm if mask is None else bytearray(a & c for a, c in zip(mask, fm))
    weich = None
    if form == "weich":                                    # Vignette: Rand weich ausblenden
        weich = bytearray(W * H)
        rx, ry = W / 2, H / 2
        for y in range(H):
            dy = (y + 0.5 - ry) / ry
            for x in range(W):
                dx = (x + 0.5 - rx) / rx
                r = math.sqrt(dx * dx + dy * dy)
                weich[y * W + x] = 255 if r < 0.7 else (0 if r > 1.0 else int(255 * (1.0 - (r - 0.7) / 0.3)))
    if auto and modus != "schwarzweiss":
        lut = _auto_tonwert(bytes(px), mask)
        px = bytearray(px.translate(lut))
    px = bytearray(px.translate(_lut(helligkeit, kontrast, gamma, invertieren)))
    if weich is not None:
        for i, f in enumerate(weich):
            if f < 255:
                px[i] = 255 - ((255 - px[i]) * f) // 255
    if modus == "skizze":
        px = _sobel(bytes(px), W, H)
        px = bytearray(px.translate(bytes(0 if v < 170 else 255 for v in range(256))))
    elif modus == "schwarzweiss":
        px = bytearray(px.translate(bytes(0 if v < 128 else 255 for v in range(256))))
    elif modus == "fehlerstreuung":
        px = _floyd(px, W, H, mask)
    a_out = bytearray(b"\xff" * (W * H))
    if mask is not None:
        for i, m in enumerate(mask):
            if not m:
                px[i] = 255
                a_out[i] = 0
    if al is not None:
        for i, a in enumerate(al):
            if a < 128:
                px[i] = 255
                a_out[i] = 0
    if weich is not None:
        for i, f in enumerate(weich):
            if f == 0:
                px[i] = 255
                a_out[i] = 0
    return png_bytes(W, H, bytes(px), bytes(a_out), ppmm)


def motiv_raster(polys: Sequence[Sequence[Point]], breite: float, hoehe: float,
                 ppmm: float = STANDARD_AUFLOESUNG, maske: Optional[Sequence[Sequence[Point]]] = None) -> Tuple[int, int, bytes]:
    """Vektor-Motiv (Polygone in Bild-mm, y nach unten, gerade/ungerade) als gestochen scharfes
    Schwarzweiß-Gravurbild – für flächige Logos die sauberste Gravur (keine Schraffurlinien)."""
    ppmm = max(2.0, min(20.0, float(ppmm)))
    W, H = max(1, int(round(breite * ppmm))), max(1, int(round(hoehe * ppmm)))
    if W * H > 4_000_000:
        raise BildFehler("Logo-Gravur zu groß – kleiner machen oder eine geringere Auflösung wählen")
    key = hashlib.sha1(json.dumps(["m", W, H, ppmm, [[(round(x, 3), round(y, 3)) for x, y in p] for p in polys],
                                   [[(round(x, 3), round(y, 3)) for x, y in p] for p in (maske or [])]],
                                  separators=(",", ":")).encode()).hexdigest()
    with _LOCK:
        hit = _ERGEBNIS.get(key)
        if hit:
            return hit
    on = _fill_mask(W, H, [[(x * ppmm, y * ppmm) for x, y in p] for p in polys])
    if maske:
        mk = _fill_mask(W, H, [[(x * ppmm, y * ppmm) for x, y in p] for p in maske if len(p) >= 3])
        on = bytearray(a & c for a, c in zip(on, mk))
    px = bytes(0 if v else 255 for v in on)
    al = bytes(255 if v else 0 for v in on)
    res = (W, H, png_bytes(W, H, px, al, ppmm))
    _merken(key, res)
    return res
