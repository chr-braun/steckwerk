# Entwicklung

## Wie Steckwerk entstanden ist

Steckwerk wurde komplett in der Cloud gebaut (mit Claude) und liegt im Repo `chr-braun/laserforge`
(inzwischen umbenannt in `chr-braun/steckwerk`). Eine Arbeitskopie mit allen Mac-Zips und Paketen liegt
im Projektordner. Der Code muss mit Python 3.8/3.9 laufen, weil das Python von Apples Command Line Tools
3.9 ist, und nutzt nur die Standardbibliothek.

## Aufbau

```
steckwerk.py      Engine: Config, Geometrie, Kerf-Offset, Bauteile, Zinken/Tabs, Layout, SVG
laserforge.py     Kompatibilitäts-Alias für alte Pakete (from laserforge import …)
validator.py      Geometrie-, Verbindungs-, Blatt- und SVG-Prüfung
service.py        gemeinsame Schicht für CLI, Konfigurator und Web (MODEL_INFO = Formulare)
cli.py            Kommandozeile und --konfigurator
webui.py          lokaler Webserver; web/index.html ist die ganze Oberfläche (ohne Build-Schritt)
steckwerk_app.py  App-Betrieb: eine Instanz, Browserfenster, Selbst-Beenden, Mac-Installation
i18n.py           Deutsch/Englisch (deutsche Texte sind die Schlüssel)
motive.py         SVG-Parser, PNG-Nachzeichner, Motiv-Bibliothek
pakete.py         Paket-Standard: laden, prüfen, packen
updater.py        Update-Kanal lesen, Prüfsummen, Installieren
assistent.py      Ollama-Assistent (nur localhost/eigenes Netz)
bildgen.py        Motiv zeichnen: Ollama und OpenRouter, Kostenschätzung, Monatslimit
models/           alle Modelle; _deko.py = Gestaltungs-Baukasten, _font.py = Einlinien-Schrift
packaging/        build_macos.py, make_icon.py, update_kanal.py, motive_bauen.py (eingebaute Motive zeichnen)
packaging/swift/  Steckwerk Desktop: SteckwerkCore (Client, Modelle, Formularlogik, Vorschau),
                  SteckwerkDesktop (SwiftUI), bridge_start.py (Engine für die App), build_app.sh, make_dmg.sh
tests/            pytest
```

## Eigenes Modell ergänzen

1. In `models/` ein Modul mit `build(cfg, **parameter) -> Assembly` anlegen (mm, y nach oben, Außenkontur
   gegen den Uhrzeigersinn).
2. Für jede Steckverbindung an beiden Teilen ein `JointFeature` anlegen und mit
   `asm.connect("teilA:feature", "teilB:feature")` verbinden – der Validator prüft sie dann automatisch.
3. In `models/__init__.py` unter `MODELS` und in `service.py` unter `MODEL_INFO` eintragen. Optionen mit
   `section` landen in aufklappbaren Gruppen, `when` blendet sie bedingt ein.
4. Neue Gravuren immer über `_deko.Canvas`, dann kommen sie nie auf Schnitte.
5. Neue deutsche Oberflächentexte brauchen einen englischen Eintrag (`EN_UI`/`EN_RX` in
   `web/index.html` bzw. `i18n.py`).
6. Neue Python-Datei auf oberster Ebene? Dann in `packaging/build_macos.py` unter `CODE_FILES` eintragen
   (ein Test passt darauf auf).

## Tests

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

Stand 26.10.2026: 1321 Python-Tests, dazu 59 Swift-Tests. Die Swift-Tests laufen in CI auf macOS,
inklusive Integrationstest gegen die echte Engine. Auf GitHub laufen sie bei jedem Push (Python 3.9 und
3.12, Linux und macOS). Abgedeckt sind jede Gestaltungsoption, Engine, Validator (positiv und negativ),
jedes Modell, CLI, Weboberfläche, App-Betrieb, Pakete, Motive, Updater und der Assistent (mit
nachgebautem Ollama/OpenRouter-Server).

Oberfläche testen: `python3 webui.py --port 8799 --no-browser` und Screenshots mit Playwright.

## Steckwerk Desktop bauen

```bash
cd packaging/swift
swift build && swift test            # Tests mit STECKWERK_ROOT=<Repo> für den Integrationstest
./build_app.sh ../dist               # App-Bundle mit eingebauter Engine (nur macOS)
./make_dmg.sh                        # DMG mit Programme-Verknüpfung
```

Unter Linux bauen und testen nur der Kern `SteckwerkCore`; die Oberfläche entsteht auf macOS.

## Neue Version veröffentlichen

1. Version in `steckwerk.py` und `CHANGELOG.md` / `CHANGELOG.en.md` pflegen, Tests grün, auf `main` mergen.
2. Unter Actions → **Release** → „Run workflow“ auf `main` starten. Der Workflow setzt das Tag aus `steckwerk.py`,
   legt das GitHub-Release mit Mac-App an, baut Steckwerk Desktop auf einem Mac-Runner, packt alle Pakete, deren
   Version im Kanal fehlt, und frischt den [Update-Kanal](Updates.md) auf.
3. Zum Schluss läuft **Aufräumen** (`.github/workflows/aufraeumen.yml`): Auf der Releases-Seite bleiben nur die
   zwei neuesten Releases stehen, die Git-Tags bleiben. Der Update-Kanal hängt nicht an den Releases, ältere Apps
   finden ihre Updates weiter.
4. Danach baut der Workflow **Webseite** die Seite neu.

„Aufräumen“ lässt sich auch von Hand starten (Actions → Aufräumen); dort kann man zusätzlich alte Branches zum
Löschen angeben. `main`, `updates` und `gh-pages` sind geschützt.

## Webseite

Die Webseite liegt unter <https://chr-braun.github.io/steckwerk/>. Quelle ist der Ordner `webseite/`: die Startseite
`index.html`, die Seite `pakete-bauen.html` (wie Steckwerk Teile errechnet und wie man ein Paket baut), das gemeinsame
`stil.css` und Screenshots, ohne Build-Werkzeuge. `python3 packaging/webseite.py --out _site` baut sie:
Es installiert alle Paketquellen in einen Wegwerf-Ordner, rechnet daraus die Modellbilder (so, wie Steckwerk die
Teile schneidet) und setzt die Pakete nach Bereichen in die Seite ein. Welches Modell eine Paketkarte zeigt und
welche Teile die Leiste mit dem Millimeterlineal zeigt, steht oben in `packaging/webseite.py`. Programmversion und
Download-Link holt die Seite beim Öffnen aus dem Update-Kanal, sie stimmen also immer mit dem letzten Release.

Der Workflow `.github/workflows/pages.yml` baut und veröffentlicht die Seite bei Änderungen an `webseite/`,
`paketquellen/` oder dem Bauskript und nach jedem Release. Einmalig nötig: Settings → Pages → Source
**GitHub Actions**.

Gestaltung: ruhig und materialnah. Schnitt = Tinte, Gravur = Blau, wie in jeder Steckwerk-Datei; Systemschriften,
keine externen Schriften oder Tracker.

## Ideen und Fehler melden

Im Repo gibt es Vorlagen für Issues („Fehler“ und „Idee“) und eine PR-Vorlage, dazu `CONTRIBUTING.md`.
