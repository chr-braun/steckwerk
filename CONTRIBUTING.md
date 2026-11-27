# Mitmachen

Steckwerk ist reines Python (≥ 3.8, nur Standardbibliothek) – die Mac-App bringt Python 3.9 mit,
deshalb keine neueren Sprachmittel und keine externen Pakete im Programmcode.

## Einrichten

```
git clone https://github.com/chr-braun/steckwerk.git
cd steckwerk
python3 -m pip install -r requirements-dev.txt     # nur für Tests und Vorschaubilder
python3 -m pytest -q tests
python3 webui.py                                   # Werkbank im Browser
```

## Regeln

- **Cut-ready oder gar nicht:** Jedes Modell muss für alle Werte im erlaubten Bereich vom Validator
  ohne FEHLER durchkommen. Was nicht passt, meldet `build()` mit einem verständlichen `ValueError`.
- **Gravuren über `models/_deko.py`** (Canvas), damit sie nie Schnitte berühren.
- **Neue Optionen** gehören in `service.MODEL_INFO` (mit `section`, wenn es Gestaltung ist), in einen
  Test und ins README.
- **Tests:** jede neue Form oder Option bekommt einen Test in `tests/`; für Geometrie lohnt ein
  Zufallslauf über Materialstärken 1.5–6 mm und Kerf 0–0.3 mm.
- **Schneller Start auf alten Rechnern:** Beim Start darf nichts Schweres rechnen. Jede Vorlage (Kern und
  `paketquellen/`) bringt ihr Vorschaubild in `vorschau/` mit: `python3 packaging/vorschaubilder.py <modell …>`.
  Der Test `test_every_model_ships_a_thumbnail` erzwingt das.
- **Update in der App:** Jedes Release muss sich in Steckwerk Desktop selbst installieren lassen (App und
  Pakete). Der Release-Workflow prüft am Ende, dass Programm, Desktop und alle Pakete in der neuen Version im
  Kanal stehen.
- Neue Modelle, die nicht jeder braucht, lieber als **Erweiterungspaket** bauen – siehe PAKETE.md.

## Neue Version

1. `__version__` in `steckwerk.py` erhöhen und `CHANGELOG.md` ergänzen.
2. Commit auf `main`, dann `git tag v1.6.0 && git push origin v1.6.0`.
3. GitHub Actions testet, packt die Mac-App und das Beispielpaket und legt das Release an.
