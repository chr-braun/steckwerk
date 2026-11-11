"""
laser.py – alles rund um den xTool M2: Materialprofile, Schnittzeit-Schätzung und Projektdateien
für xTool Creative Space / xTool Studio.

Nur Python-Standardbibliothek.

* PROFILE        eingebaute Materialprofile mit Startwerten (Leistung %, Tempo mm/s, Durchgänge)
* schaetzung()   Schnittlänge, Laufzeit und Materialbedarf eines Ergebnisses
* xcs_bytes()    ein Blatt als .xcs-Projekt (JSON; Ebenen „Schneiden“ rot, „Ritzen“ blau)
* xs_bytes()     dasselbe als .xs-Projekt (ZIP, xTool Studio ab 1.7) – mit Leistung/Tempo je Ebene

Die Dateiformate von xTool sind nicht offen dokumentiert. Der Aufbau folgt öffentlich
beschriebenen Projektdateien (u. a. der MIT-Bibliothek „unofficial-xcs-writer“). Darum gilt:
vor dem ersten Schnitt in XCS kurz prüfen, ob Ebenen und Werte stimmen.
"""
from __future__ import annotations

import io
import os
import json
import math
import time
import uuid
import zipfile
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from steckwerk import Config, Sheet, __version__

Point = Tuple[float, float]

# ---------------------------------------------------------------------------
# Materialprofile (xTool M2, 10 W und 20 W)
# ---------------------------------------------------------------------------
# Werte je Laser: cut = Schneiden (rote Linien), score = Ritzen/Gravur (blaue Linien),
# jeweils [Leistung %, Geschwindigkeit mm/s, Durchgänge]. Vorsichtige Startwerte –
# lieber ein Durchgang mehr als angekokelte Kanten.
PROFILE: List[Dict[str, Any]] = [
    dict(id="pappel15", name="Pappel-Sperrholz 1,5 mm (Filigran)", t=1.5, kerf=0.12,
         w10=dict(cut=[100, 16, 1], score=[15, 120, 1]), w20=dict(cut=[100, 25, 1], score=[10, 150, 1])),
    dict(id="pappel2", name="Pappel-Sperrholz 2 mm (Filigran)", t=2, kerf=0.12,
         w10=dict(cut=[100, 11, 1], score=[18, 110, 1]), w20=dict(cut=[100, 18, 1], score=[10, 140, 1])),
    dict(id="pappel3", name="Pappel-Sperrholz 3 mm", t=3, kerf=0.15,
         w10=dict(cut=[100, 6, 2], score=[20, 100, 1]), w20=dict(cut=[100, 8, 1], score=[12, 120, 1])),
    dict(id="linde3", name="Linde-Sperrholz 3 mm", t=3, kerf=0.15,
         w10=dict(cut=[100, 7, 2], score=[20, 100, 1]), w20=dict(cut=[100, 10, 1], score=[12, 120, 1])),
    dict(id="birke3", name="Birke-Sperrholz 3 mm", t=3, kerf=0.15,
         w10=dict(cut=[100, 4, 3], score=[22, 100, 1]), w20=dict(cut=[100, 6, 2], score=[14, 120, 1])),
    dict(id="pappel4", name="Pappel-Sperrholz 4 mm", t=4, kerf=0.18,
         w10=dict(cut=[100, 4, 3], score=[20, 100, 1]), w20=dict(cut=[100, 6, 2], score=[12, 120, 1])),
    dict(id="mdf3", name="MDF 3 mm", t=3, kerf=0.18,
         w10=dict(cut=[100, 3, 3], score=[25, 100, 1]), w20=dict(cut=[100, 5, 2], score=[15, 120, 1])),
    dict(id="pappe2", name="Graupappe 2 mm", t=2, kerf=0.15,
         w10=dict(cut=[100, 10, 1], score=[15, 150, 1]), w20=dict(cut=[100, 15, 1], score=[10, 200, 1])),
    dict(id="acryl3", name="Acryl schwarz 3 mm", t=3, kerf=0.12,
         w10=dict(cut=[100, 3, 3], score=[35, 100, 1]), w20=dict(cut=[100, 4, 2], score=[25, 120, 1])),
]
LASER = {"w10": "xTool M2 · 10 W", "w20": "xTool M2 · 20 W"}
XCS_CUT = "#FF0000"
XCS_SCORE = "#0000FF"

# Fahrweg ohne Laser und Anlauf je Kontur – grobe Werte für einen Diodenlaser dieser Klasse.
FAHRT_MM_S = 300.0
ANLAUF_S = 0.25


def profil(pid: str) -> Optional[Dict[str, Any]]:
    return next((p for p in PROFILE if p["id"] == pid), None)


def passendes_profil(cfg: Config) -> Optional[Dict[str, Any]]:
    """Das eingebaute Profil, dessen Stärke und Kerf zur Config passen (sonst None)."""
    for p in PROFILE:
        if abs(p["t"] - cfg.thickness) < 1e-6 and abs(p["kerf"] - cfg.kerf) < 1e-6:
            return p
    return None


def laserwerte(laser: Any, cfg: Config, leistung: str = "w10") -> Dict[str, List[float]]:
    """Laserwerte aus der Anfrage prüfen: {cut: [%, mm/s, n], score: [...]}.
    Fehlen sie, gilt das passende eingebaute Profil, sonst Pappel 3 mm."""
    base = (passendes_profil(cfg) or PROFILE[2])["w20" if leistung == "w20" else "w10"]
    out: Dict[str, List[float]] = {}
    for op in ("cut", "score"):
        v = (laser or {}).get(op) if isinstance(laser, dict) else None
        try:
            p, s, n = (float(x) for x in v)                        # type: ignore[union-attr]
        except (TypeError, ValueError):
            p, s, n = base[op]
        out[op] = [min(100.0, max(1.0, p)), min(600.0, max(0.5, s)), float(min(20, max(1, int(round(n)))))]
    return out


# ---------------------------------------------------------------------------
# Wege auf einem Blatt
# ---------------------------------------------------------------------------

def _laenge(pts: Sequence[Point], closed: bool) -> float:
    n = len(pts)
    if n < 2:
        return 0.0
    s = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(n - 1))
    if closed:
        s += math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
    return s


def wege(sheet: Sheet) -> Tuple[List[Tuple[List[Point], bool]], List[Tuple[List[Point], bool]]]:
    """(Schnittwege, Ritzwege) eines Blatts in Laser-Reihenfolge: je Teil erst innen, dann außen."""
    cut: List[Tuple[List[Point], bool]] = []
    score: List[Tuple[List[Point], bool]] = []
    for p in sheet.parts:
        for s in p.engrave:
            score.append((list(s.points), s.closed))
        for poly in p.cut_paths():
            cut.append((list(poly), True))
    return cut, score


def _fahrweg(paths: Iterable[Tuple[List[Point], bool]], start: Point = (0.0, 0.0)) -> float:
    pos, s = start, 0.0
    for pts, closed in paths:
        if not pts:
            continue
        s += math.hypot(pts[0][0] - pos[0], pts[0][1] - pos[1])
        pos = pts[0] if closed else pts[-1]
    return s


def blatt_schaetzung(sheet: Sheet, werte: Dict[str, List[float]]) -> Dict[str, float]:
    cut, score = wege(sheet)
    lc = sum(_laenge(p, c) for p, c in cut)
    ls = sum(_laenge(p, c) for p, c in score)
    pc, vc, nc = werte["cut"]
    ps, vs, ns = werte["score"]
    fahrt = _fahrweg(score) + _fahrweg(cut)
    sek = (lc / vc) * nc + (ls / vs) * ns + (len(cut) * nc + len(score) * ns) * ANLAUF_S \
        + fahrt / FAHRT_MM_S * (1 + (nc - 1) * 0.5)
    # genutzte Fläche: Hüllrechteck aller Teile (so viel Platte ist „weg“)
    xs = [x for p in sheet.parts for x, _ in p.outline]
    ys = [y for p in sheet.parts for _, y in p.outline]
    flaeche = (max(xs) - min(xs)) * (max(ys) - min(ys)) if xs else 0.0
    return dict(schnitt_mm=lc, ritz_mm=ls, konturen=len(cut), linien=len(score), sekunden=sek,
                genutzt_mm2=flaeche, platte_mm2=sheet.width * sheet.height)


def schaetzung(sheets: Sequence[Sheet], werte: Dict[str, List[float]],
               preis_platte: float = 0.0) -> Dict[str, Any]:
    """Schätzung für alle Blätter eines Ergebnisses: Laufzeit, Schnittlänge, Platten und Kosten."""
    blaetter = [blatt_schaetzung(sh, werte) for sh in sheets]
    sek = sum(b["sekunden"] for b in blaetter)
    lc = sum(b["schnitt_mm"] for b in blaetter)
    ls = sum(b["ritz_mm"] for b in blaetter)
    # angebrochene letzte Platte nur anteilig (Reststück bleibt nutzbar)
    platten = 0.0
    for i, b in enumerate(blaetter):
        platten += 1.0 if i < len(blaetter) - 1 else min(1.0, b["genutzt_mm2"] / max(1.0, b["platte_mm2"]))
    out: Dict[str, Any] = dict(
        sekunden=round(sek, 1), zeit=dauer_text(sek), schnitt_m=round(lc / 1000, 2), ritz_m=round(ls / 1000, 2),
        blaetter=len(blaetter), platten=round(platten, 2),
        ausnutzung=round(100 * sum(b["genutzt_mm2"] for b in blaetter)
                         / max(1.0, sum(b["platte_mm2"] for b in blaetter))),
        werte=werte)
    if preis_platte and preis_platte > 0:
        out["kosten"] = round(platten * preis_platte, 2)
    return out


def dauer_text(sek: float) -> str:
    sek = int(round(sek))
    if sek < 60:
        return f"{sek} s"
    m, s = divmod(sek, 60)
    if m < 60:
        return f"{m} min {s:02d} s" if m < 10 else f"{m} min"
    h, m = divmod(m, 60)
    return f"{h} h {m:02d} min"


# ---------------------------------------------------------------------------
# Projektdateien für xTool Creative Space (.xcs) und xTool Studio (.xs)
# ---------------------------------------------------------------------------
M2_ID = "JS002"          # Gerätekennung des xTool M2 in XCS-Projekten
M2_NAME = "M2"


def _n(v: float) -> float:
    r = round(v, 3)
    return 0.0 if r == 0 else r


def _d(pts: Sequence[Point], closed: bool) -> str:
    d = "M" + "L".join(f"{_n(x):g} {_n(y):g}" for x, y in pts)
    return d + ("Z" if closed else "")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "steckwerk:" + seed))


def _display(pts: Sequence[Point], closed: bool, color: str, did: str, z: int, name: str) -> Dict[str, Any]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0 = min(xs), min(ys)
    farbe = int(color[1:], 16)
    return {
        "id": did, "name": name, "type": "PATH",
        "x": _n(x0), "y": _n(y0), "angle": 0,
        "scale": {"x": 1, "y": 1}, "skew": {"x": 0, "y": 0}, "pivot": {"x": 0, "y": 0},
        "localSkew": {"x": 0, "y": 0}, "offsetX": _n(x0), "offsetY": _n(y0),
        "lockRatio": True, "isClosePath": bool(closed), "zOrder": z,
        "groupTags": [], "groupTag": did, "layerTag": color, "layerColor": color,
        "visible": True, "originColor": color, "enableTransform": True, "visibleState": True,
        "lockState": False, "resourceOrigin": "", "customData": {}, "rootComponentId": "",
        "minCanvasVersion": "0.0.0", "alpha": 1,
        "fill": {"paintType": "color", "visible": False, "color": 0, "alpha": 1},
        "stroke": {"paintType": "color", "visible": True, "color": farbe, "alpha": 1, "width": 1,
                   "cap": "butt", "join": "miter", "miterLimit": 4, "alignment": 0.5},
        "effects": [],
        "width": _n(max(xs) - x0), "height": _n(max(ys) - y0),
        "isFill": False, "lineColor": farbe, "fillColor": color,
        "points": [], "dPath": _d(pts, closed), "fillRule": "nonzero",
        "graphicX": 0, "graphicY": 0, "isCompoundPath": False,
    }


def _projekt(sheet: Sheet, titel: str) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Gemeinsamer Teil: Leinwand mit Ebenen und Linien. Gibt (Projekt, Schnitt-IDs, Ritz-IDs) zurück."""
    cut, score = wege(sheet)
    canvas_id = _uid(f"{titel}:canvas")
    displays: List[Dict[str, Any]] = []
    cut_ids: List[str] = []
    score_ids: List[str] = []
    z = 1
    # Ritzen zuerst (wie im SVG), dann Schneiden – innen vor außen
    for i, (pts, closed) in enumerate(score):
        if len(pts) < 2:
            continue
        did = _uid(f"{titel}:r{i}")
        displays.append(_display(pts, closed, XCS_SCORE, did, z, "Ritzen"))
        score_ids.append(did)
        z += 1
    for i, (pts, closed) in enumerate(cut):
        if len(pts) < 3:
            continue
        did = _uid(f"{titel}:s{i}")
        displays.append(_display(pts, closed, XCS_CUT, did, z, "Schneiden"))
        cut_ids.append(did)
        z += 1
    layer = {}
    if score_ids:
        layer[XCS_SCORE] = {"name": "Ritzen", "order": 1, "visible": True}
    layer[XCS_CUT] = {"name": "Schneiden", "order": 2, "visible": True}
    now = int(time.time() * 1000)
    proj = {
        "canvasId": canvas_id,
        "canvas": [{
            "id": canvas_id, "title": titel[:60] or "Steckwerk",
            "layerData": layer, "groupData": {}, "displays": displays,
            "extendInfo": {"version": "2.15.17", "minCanvasVersion": "0.0.0", "displayProcessConfigMap": {},
                           "rulerPluginData": {"rulerGuide": []},
                           "gridOptions": {"color": "normal", "isShow": True}},
        }],
        "extId": M2_ID, "extName": M2_NAME,
        "device": {"id": M2_ID, "power": [10], "data": {"dataType": "Map", "value": []},
                   "materialList": [], "materialTypeList": [], "customProjectData": {}},
        "version": "1.1.10", "created": now, "modify": now, "ua": f"Steckwerk {__version__}",
        "meta": [], "cover": "", "minRequiredVersion": "2.6.0",
        "appMinRequiredVersion": "", "webMinRequiredVersion": "",
        "projectTraceID": _uid(f"{titel}:trace"),
    }
    return proj, cut_ids, score_ids


def xcs_bytes(sheet: Sheet, cfg: Config, titel: str, leistung_w: int = 10) -> bytes:
    """Ein Blatt als .xcs-Projekt für xTool Creative Space. Ebenen und Farben sind gesetzt;
    Leistung und Tempo trägt man in XCS je Ebene ein (das .xcs-Format speichert sie anders
    als .xs und ist dafür nicht verlässlich beschrieben)."""
    proj, _, _ = _projekt(sheet, titel)
    proj["device"]["power"] = [leistung_w]
    return json.dumps(proj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def xs_bytes(sheet: Sheet, cfg: Config, titel: str, werte: Dict[str, List[float]], leistung_w: int = 10) -> bytes:
    """Ein Blatt als .xs-Projekt (xTool Studio ab 1.7) – mit Leistung, Tempo und Durchgängen je Ebene."""
    proj, cut_ids, score_ids = _projekt(sheet, titel)
    canvas = proj["canvas"][0]
    cid = canvas["id"]
    profiles: Dict[str, Any] = {}
    refs: List[str] = []
    bindings: List[Dict[str, Any]] = []
    for op, typ, ids in (("score", "VECTOR_ENGRAVING", score_ids), ("cut", "VECTOR_CUTTING", cut_ids)):
        if not ids:
            continue
        p, s, n = werte[op]
        pid = "profile:" + _uid(f"{titel}:{op}:profile")
        profiles[pid] = {"id": pid, "processingType": typ,
                         "values": {"power": int(round(p)), "speed": float(s), "repeat": int(n)}}
        refs.append(pid)
        bindings.append({"bindingId": "binding:" + _uid(f"{titel}:{op}:binding"), "canvasId": cid,
                         "mode": "LASER_PLANE", "baseProfileId": pid, "displayIds": ids})

    def js(v: Any) -> bytes:
        return json.dumps(v, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(".format", "v2")
        z.writestr("meta/persistence-meta.json", js({"schemaVersion": "2.0.0", "protocol": "xcs-workspace-v2"}))
        z.writestr("project.json", js({
            "__v2__": True, "version": "2.0.0", "schemaMeta": {"schemaVersion": "2.1.0", "format": "directory"},
            "projectId": proj["projectTraceID"], "projectTraceID": proj["projectTraceID"],
            "projectName": titel[:60] or "Steckwerk", "activeCanvasId": cid, "activeDeviceId": M2_ID,
            "versionInfo": {"source": "web", "appVersion": "", "savedAt": proj["modify"], "ua": proj["ua"],
                            "minRequiredVersion": proj["minRequiredVersion"], "appMinRequiredVersion": "",
                            "webMinRequiredVersion": ""},
            "created": proj["created"], "modify": proj["modify"],
            "modules": {"canvases": [cid], "devices": [M2_ID]},
            "customProjectData": {"projectTraceID": proj["projectTraceID"]}}))
        z.writestr("profiles.json", js({"profiles": profiles}))
        z.writestr(f"canvases/{cid}.json", js({
            "id": cid, "title": canvas["title"], "hidden": False, "layerData": canvas["layerData"],
            "groupData": {}, "extendInfo": {"version": canvas["extendInfo"]["version"], "minCanvasVersion": "0.0.0",
                                            "displayProcessConfigMap": {}, "rulerPluginData": {"rulerGuide": []},
                                            "type": "2d"},
            "chunkLayout": {"displayCount": len(canvas["displays"]), "chunkCount": 1, "chunkIndexes": [0]}}))
        z.writestr(f"canvases/{cid}/displays-0.json", js({"canvasId": cid, "chunkIndex": 0,
                                                          "displays": canvas["displays"]}))
        z.writestr(f"devices/device-{M2_ID}.json", js({
            "id": M2_ID, "deviceCode": M2_ID, "extId": M2_ID, "extName": M2_NAME, "power": [leistung_w],
            "processing": {cid: {"id": cid, "activeMode": "LASER_PLANE", "modes": {"LASER_PLANE": {
                "ignoredDisplayIds": [],
                "data": {"material": 0, "thickness": cfg.thickness, "perimeter": None, "diameter": None,
                         "isProcessByLayer": True, "pathPlanning": "custom", "fillPlanning": "separate",
                         "scanDirection": "topToBottom", "enableOddEvenKerf": True,
                         "focalLen": None, "focalLength": None},
                "profileRefs": refs, "patches": {}, "bindings": bindings}}}}}))
    return buf.getvalue()


def lies_xcs(data: bytes) -> Dict[str, Any]:
    """Kleine Prüfung für Tests und Support: .xcs (JSON) oder .xs (ZIP) lesen →
    {ebenen: {farbe: name}, linien: {farbe: anzahl}, geraet: id, werte: {typ: values}}."""
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()
            proj = json.loads(z.read("project.json"))
            cid = proj["activeCanvasId"]
            canvas = json.loads(z.read(f"canvases/{cid}.json"))
            displays = json.loads(z.read(f"canvases/{cid}/displays-0.json"))["displays"]
            profiles = json.loads(z.read("profiles.json"))["profiles"]
            dev = json.loads(z.read(next(n for n in names if n.startswith("devices/"))))
            werte = {p["processingType"]: p["values"] for p in profiles.values()}
            geraet = dev["id"]
            layer = canvas["layerData"]
    else:
        proj = json.loads(data.decode("utf-8"))
        canvas = proj["canvas"][0]
        displays = canvas["displays"]
        layer = canvas["layerData"]
        geraet = proj["device"]["id"]
        werte = {}
    linien: Dict[str, int] = {}
    for d in displays:
        linien[d["layerColor"]] = linien.get(d["layerColor"], 0) + 1
    return dict(ebenen={k: v["name"] for k, v in layer.items()}, linien=linien, geraet=geraet, werte=werte,
                displays=displays)


# ---------------------------------------------------------------------------
# Direkt in xTool Creative Space öffnen
# ---------------------------------------------------------------------------
XCS_APPS = ("xTool Creative Space", "xTool Studio", "XCS")


def oeffnen_in_xcs(path: str, runner=None) -> str:
    """Projektdatei an XCS übergeben. Liefert den Namen des Programms, das sie geöffnet hat.
    macOS: erst die bekannten App-Namen, sonst das Standardprogramm für .xcs-Dateien."""
    import subprocess
    import sys
    run = runner or (lambda cmd: subprocess.run(cmd, capture_output=True, timeout=20).returncode)
    if sys.platform == "darwin":
        for app in XCS_APPS:
            if run(["open", "-a", app, path]) == 0:
                return app
        if run(["open", path]) == 0:
            return "Standardprogramm"
        raise OSError("xTool Creative Space wurde nicht gefunden – bitte XCS installieren "
                      "oder die gespeicherte .xcs-Datei von Hand öffnen")
    if sys.platform.startswith("win"):
        os.startfile(path)                                   # type: ignore[attr-defined]
        return "Standardprogramm"
    if run(["xdg-open", path]) == 0:
        return "Standardprogramm"
    raise OSError("Kein Programm für .xcs-Dateien gefunden")
