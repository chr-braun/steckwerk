# Steckwerk Desktop (native Mac-App)

Seit dem Stand vom 17.10.2026 gibt es zusätzlich zur Mac-App mit Browser eine **native App**, die ohne Browser
auskommt. Sie startet die bekannte Steckwerk-Engine im Hintergrund und zeigt alles in einem Fenster: Modelle
links, Formular in der Mitte, Vorschau und Prüfbericht rechts.

Die Engine ist dieselbe wie sonst. Geometrie, Prüfung, Pakete, Updates und KI bleiben in Python; die App ist
eine zweite Oberfläche darauf.

## Herunterladen

Die App wird bei jedem Push auf den Entwicklungs-Branch automatisch gebaut.

1. Auf GitHub unter **Actions → macOS Desktop** den neuesten erfolgreichen Lauf öffnen.
2. Unten unter **Artifacts** das Paket **Steckwerk-Desktop-macOS-dmg** laden. Darin liegt `Steckwerk-Desktop-macOS.dmg`.
   Das ZIP **Steckwerk-Desktop-macOS** enthält dieselbe App.
3. Du brauchst ein GitHub-Konto mit Zugriff auf das Repo. Die Downloads bleiben 14 Tage verfügbar.

## Installieren

1. DMG öffnen und `Steckwerk Desktop.app` auf die Verknüpfung **Programme** ziehen.
2. Beim ersten Start meldet macOS, der Entwickler lasse sich nicht überprüfen. Die App ist nicht von Apple
   notarisiert. Dann unter **Systemeinstellungen → Datenschutz & Sicherheit** bei „Steckwerk Desktop“ auf
   **Dennoch öffnen** klicken. Das ist nur einmal nötig.

**Voraussetzungen:** macOS 14 oder neuer, Apple Silicon oder Intel. Python ab 3.9. Die App sucht es wie die
bisherige Mac-App (Homebrew, python.org, pyenv, MacPorts, Apples Command Line Tools). Fehlt Python, zeigt die
App einen Hinweis mit dem Weg zur Installation.

## Bedienung

- **Seitenleiste:** Modelle nach Gruppen, darunter Pakete, KI, Material und Updates.
- **Formular:** Abschnitte wie in der Weboberfläche, Zahlen mit Stepper und Einheit, Auswahllisten, Schalter,
  Textfelder (mehrzeilig, wo sinnvoll) und das Motiv-Raster mit Vorschaubildern.
- **Motive vorab sehen:** Im Motiv-Raster und in der Motivliste stehen die Motive groß, bevor du sie platzierst.
- **Bauen & prüfen (⌘B):** Die Engine baut das Modell und prüft es. Oben steht zum Beispiel
  „0 FEHLER · 8 Teile · 1 Blatt · CUT-READY“.
- **Live-Vorschau:** Jede Änderung baut das Blatt nach einer kurzen Pause neu. Du siehst Schnitt und Gravur,
  bevor du etwas auslöst. Schnitt schwarz, Gravur blau, Blattrahmen. Zoomen mit der Pinch-Geste oder den Lupen,
  verschieben durch Ziehen, Doppelklick setzt zurück.
- **Prüfbericht:** Fehler stehen rot darüber. Montagehinweise und alle Prüfzeilen lassen sich aufklappen.
- **Exportieren (⌘E):** Schreibt je Baugruppe die Blatt-SVGs und `pruefbericht.txt` in einen Ordner deiner
  Wahl. Das geht nur nach bestandener Prüfung, wie überall in Steckwerk. „In den Steckwerk-Ordner speichern“
  legt die Dateien in `Dokumente/Steckwerk` ab.
- **Ordner öffnen (⌘O)**
- **Einstellungen (⌘,):** Material (Stärke T, Kerf, Maßstab, Blatt, Farben) und KI-Anbieter.

## Pakete, Updates, Material

- **Pakete:** Installierte Pakete ansehen und entfernen, den Update-Kanal laden und Pakete daraus installieren
  oder eine `.swpaket`-Datei einbauen.
- **Updates:** Zeigt neue Pakete und neue Programmversionen. Gibt es eine neue Version, lädt
  **„Installieren und neu starten“** sie aus dem Update-Kanal, prüft Prüfsumme, Kennung und Version, ersetzt die App
  an ihrem Ort und startet sie neu. Beim Start sucht die App von selbst nach Updates (abschaltbar), die Anzahl steht
  dann als Zahl neben „Updates“ in der Seitenleiste.
  Das klappt, wenn die App im Programme-Ordner liegt (nicht direkt aus dem DMG) und der Kanal für diese Version
  ein Steckwerk-Desktop-Paket hat. Sonst sagt die App, warum nicht, und du lädst das neue DMG von Hand.
- **Material:** Gilt für alle Modelle und bleibt gespeichert.

## KI und Schlüssel

- Der **Assistent** (Werte-Vorschläge) läuft über Ollama auf diesem Rechner.
- **Motiv zeichnen** nutzt Ollama (lokal), OpenRouter oder ChatGPT, siehe [KI-Funktionen](KI-Funktionen.md).
- Schlüssel trägst du unter **Einstellungen → KI-Anbieter** ein. Die App gibt sie nur an die lokale Engine weiter.
  Die Engine legt sie im macOS-Schlüsselbund ab. Die App speichert sie nirgends, zeigt sie nie wieder an und
  meldet nur, ob für einen Anbieter einer hinterlegt ist.

## Grenzen

- Nicht notarisiert; beim ersten Start einmal „Dennoch öffnen“.
- Motive platzierst du über eine Liste mit Zahlenfeldern. Der grafische Platzierungs-Editor kommt später.
- Die Oberfläche ist nur auf Deutsch.
- Die Wiki-Seiten haben noch keine Screenshots der App; die baut der macOS-Runner nicht.

## Für Entwickler

Der Quellcode liegt in `packaging/swift/`:

- `Sources/SteckwerkCore/`: HTTP-Client, Antworttypen, Formularlogik, SVG-Leser für die Vorschau, Prüfbericht
  und Export, Engine-Start. Baut und testet auch unter Linux.
- `Sources/SteckwerkDesktop/`: die SwiftUI-Oberfläche (nur macOS).
- `bridge_start.py`: startet `webui.py` für die App auf freiem Port und endet, wenn die App wegfällt.
- `build_app.sh` (App-Bundle mit eingebauter Engine), `make_dmg.sh` (DMG).
- Selbsttest ohne Fenster: `"Steckwerk Desktop.app/Contents/MacOS/SteckwerkDesktop" --self-test`.

Die CI-Datei `.github/workflows/macos-desktop.yml` baut, testet, erstellt App, ZIP und DMG und prüft das
fertige Bundle samt DMG per Selbsttest. Details: [Entwicklung](Entwicklung.md).
