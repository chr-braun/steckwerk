"""
Halloween-Anhänger – filigrane Hänger für Zweige, Fenster und Geschenke.

Fledermaus, Gespenst, Totenkopf, Katze, Hexenhut, Kürbis und Spinnennetz – fein gezeichnet mit
Durchbrüchen (Flügelknochen, Zahnreihen, Schnurrhaare, Sterne und Mond, Blattadern, Netzfäden) und
Gravuren (Schädelnähte, Brauen, Fell, Flicken mit Stichen) und einer Aufhängeöse. Mit „alle“ entsteht das ganze Set auf einmal. Ein Name kann eingraviert werden.
"""
import importlib.util
import math
import os
import sys

from steckwerk import Assembly
from models import _deko as dk
from models._font import STYLES, fit_text, unsupported
from pakete import bibliothek, num, sel, txt


def _lib():
    return bibliothek("verzierungen").G


g = _lib()

MOTIFS = [("fledermaus", "Fledermaus"), ("geist", "Gespenst"), ("totenkopf", "Totenkopf"), ("katze", "Katze"),
          ("hexenhut", "Hexenhut"), ("kuerbis", "Kürbis"), ("spinnennetz", "Spinnennetz")]

UEBERSETZUNG = {"en": g.EN}

INFO = dict(
    label="Halloween-Anhänger",
    group="Halloween",
    desc="Fledermaus, Gespenst, Totenkopf, Katze, Hexenhut, Kürbis, Spinnennetz – filigran, mit Öse.",
    params=[
        sel("motiv", "Motiv", MOTIFS + [("alle", "alle sieben (Set)")], "alle"),
        num("size", "Größe", 80, 45, 160, help="größte Abmessung in mm"),
        txt("text", "Name (Gespenst, Kürbis, Hut)", "", "leer = ohne", section="Schrift und Beschriftung"),
        sel("schrift", "Schrift", [(s, s) for s in STYLES], "normal", section="Schrift und Beschriftung"),
    ],
)


_here = os.path.dirname(os.path.abspath(__file__))


def _sub(name):
    path = os.path.join(_here, name + ".py")
    key = "swpaket_halloween_" + name
    mod = sys.modules.get(key)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(key, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return mod


SP = _sub("_spuk")
K = SP.K


def _netz_scheibe(S, cfg):
    """Runder Anhänger: Rand, Netz mit durchhängenden Fäden und Tautropfen, Kreuzspinne in der Mitte."""
    w = SP.wmin(cfg)
    R = S / 2
    rand = max(1.4 * w, 0.035 * S)
    f = SP.Figur()
    f.add(K.circle(0.0, 0.0, R, 96))
    f.cut(K.circle(0.0, 0.0, R - rand, 96))
    ringe = max(3, min(6, int((R - rand) / (2.2 * w + 2.4))))
    speichen = max(8, min(14, int(S / 8)))
    netz, _, _, _, radii = SP.netz(0.0, 0.0, R - rand * 0.3, math.pi / 2, math.pi / 2 + SP.TAU, ringe, speichen, w,
                                   cfg.seed, False, True, voll=True)
    f.merge(netz)
    a = math.radians(-40)
    r0 = radii[max(0, ringe // 2 - 1)]
    sp_ = (0.40 * S, cfg, r0 * math.cos(a), r0 * math.sin(a), a - math.pi / 2 + 0.35)
    f.merge(SP.spinne_frei(*sp_))
    f.merge(SP.spinne(*sp_))
    f.gravur = netz.gravur
    return f


def figur(motiv, S, cfg):
    """Figur des Motivs (Größe S) und das Feld für den Namen ((x, y), Breite, Höhe) oder None."""
    if motiv == "fledermaus":
        f, _ = SP.fledermaus(S, "segeln", cfg)
        return SP.eingepasst(f, S), None
    if motiv == "geist":
        f, _ = SP.gespenst(S, cfg)
        f = SP.eingepasst(f, S)
        return f, ((0.0, -0.06 * S), 0.34 * S, 0.09 * S)
    if motiv == "totenkopf":
        return SP.eingepasst(SP.totenkopf(S, cfg), S), None
    if motiv == "katze":
        return SP.eingepasst(SP.katze(S, cfg), S), None
    if motiv == "hexenhut":
        f = SP.eingepasst(SP.hexenhut(S, cfg), S)
        return f, ((0.0, -0.25 * S), 0.62 * S, 0.055 * S)
    if motiv == "kuerbis":
        f, _ = SP.kuerbis(S, cfg, "klassisch", cfg.seed)
        return SP.eingepasst(f, S), ((0.0, 0.0), 0.0, 0.0)
    if motiv == "spinnennetz":
        return _netz_scheibe(S, cfg), None
    raise ValueError(motiv)


def build_one(cfg, name, motiv, S, text, schrift, notes):
    f, feld = figur(motiv, S, cfg)
    gr = list(getattr(f, "gravur", []))
    # Öse oben an der höchsten Stelle nahe der Mitte (Hexenhut: an der Spitze, Katze: am Ohr)
    x0, y0, x1, y1 = f.bbox()
    d = max(2.5, min(5.0, 0.05 * S))
    if motiv == "hexenhut":
        xs = [q for s_, p in f.ops if s_ == "+" for q in p]
        tip = max(xs, key=lambda q: q[1] + 0.25 * q[0])
        ort, eins0 = (tip[0], tip[1]), 0.7
    elif motiv == "katze":
        xe = -0.13 * (x1 - x0) + (x0 + x1) / 2
        ort, eins0 = (xe, SP.oberkante(f, xe, 0.02 * S)), 0.6
    else:
        xm = (x0 + x1) / 2
        ort, eins0 = (xm, SP.oberkante(f, xm, 0.06 * S)), 0.45
    part = None
    for eins in (eins0, eins0 - 0.2, eins0 - 0.4, eins0 - 0.6):
        g_ = SP.Figur(list(f.ops))
        loch = SP.oese(g_, ort[0], ort[1], d, cfg, einsatz=eins)
        try:
            part = SP.teil(name, g_, cfg, notes, [loch])
            break
        except ValueError:
            continue
    if part is None:
        raise ValueError(f"{name}: Öse passt nicht – Anhänger größer wählen")
    if motiv == "katze" and getattr(f, "gloeckchen", None):
        gx, gy, gr_ = f.gloeckchen
        gr.append((K.circle(gx, gy, max(gr_, 1.2), 20), True))
    SP.gravur(part, gr, cfg.seed)
    if text and feld:
        cv = dk.Canvas(part, margin=0.9, hole_margin=0.9, seed=cfg.seed)
        (tx, ty), bw_, bh_ = feld
        if motiv == "kuerbis":
            (tx, ty), bw_, bh_ = (0.0, -0.33 * S), 0.40 * S, 0.07 * S
        try:
            strokes, _ = fit_text(text, tx, ty, bw_, bh_, min_h=2.2, max_cap=bh_, style=schrift)
            for st in strokes:
                cv.draw(st)
        except ValueError:
            notes.append(f"{name}: Name passt nicht – kürzer oder Anhänger größer wählen.")
    return part


def build(cfg, name="halloween_anhaenger", motiv="alle", size=80.0, text="", schrift="normal"):
    S = cfg.s(size)
    if not 45 <= S <= 160:
        raise ValueError("Anhänger: Größe muss zwischen 45 und 160 mm liegen")
    if motiv != "alle":
        dk.check_choice("Motiv", motiv, MOTIFS)
    bad = unsupported(text or "")
    if bad:
        raise ValueError(f"Zeichen {''.join(bad)!r} gibt es in der Gravurschrift nicht")
    notes = []
    motifs = [m for m, _ in MOTIFS] if motiv == "alle" else [motiv]
    asm = Assembly(name, params=dict(motiv=motiv, size=S, **({"text": text} if text else {})))
    for m in motifs:
        asm.parts.append(build_one(cfg, f"{name}_{m}", m, S, text, schrift, notes))
    asm.notes.extend(dict.fromkeys(notes))
    asm.notes.append("Anhänger an einem Faden durch die Öse aufhängen. Tipp: schwarz lasiert vor einem "
                     "hellen Fenster wirken sie wie Scherenschnitte.")
    return asm
