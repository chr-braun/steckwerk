#!/usr/bin/env python3
"""
vorschaubilder.py – erzeugt die mitgelieferten Vorschaubilder der Vorlagen (Ordner vorschau/).

  python3 packaging/vorschaubilder.py            alle Vorlagen (Pakete aus paketquellen/)
  python3 packaging/vorschaubilder.py wichtelhaus kuerbis   nur diese

Fehlt ein Bild, berechnet Steckwerk es beim ersten Öffnen der Galerie selbst; die mitgelieferten Bilder sparen das
auf älteren Rechnern. Nach neuen oder stark geänderten Vorlagen einmal laufen lassen.
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("STECKWERK_PAKETE", os.path.join(ROOT, "paketquellen"))
os.environ.setdefault("STECKWERK_HOME", os.path.join(ROOT, ".vorschau-home"))
sys.path.insert(0, ROOT)

import service  # noqa: E402
import vorschau  # noqa: E402


def main(ids) -> int:
    os.makedirs(vorschau.MITGELIEFERT, exist_ok=True)
    ids = ids or sorted(service.MODEL_INFO)
    total, fehler = 0, []
    for k in ids:
        t = time.time()
        text = vorschau.berechnen(k)
        if not text:
            fehler.append(k)
            print(f"  {k}: keine Vorschau")
            continue
        with open(os.path.join(vorschau.MITGELIEFERT, k + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(text)
        total += len(text)
        print(f"  {k}: {len(text) // 1024} KB in {time.time() - t:.1f} s")
    print(f"{len(ids) - len(fehler)} Bilder, zusammen {total // 1024} KB" + (f"; ohne Bild: {', '.join(fehler)}" if fehler else ""))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
