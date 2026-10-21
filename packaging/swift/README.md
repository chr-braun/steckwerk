# Steckwerk Desktop (SwiftUI)

Native macOS-Oberfläche für Steckwerk – ohne Browser. Die App startet die bestehende Python-Engine
(`webui.py`) als Kindprozess und bedient sie über die lokale HTTP-API auf `127.0.0.1`. Geometrie,
Validator, Pakete, Updates und KI bleiben in Python; in Swift steckt keine Projektlogik.

## Starten

1. `Steckwerk-Desktop-<version>-macOS.zip` entpacken (aus dem CI-Artefakt „Steckwerk-Desktop-macOS“).
2. **„Steckwerk Desktop.app“ nach /Applications ziehen** und von dort öffnen (aus „Downloads“ heraus
   verschiebt macOS die App in einen Zufallsordner).
3. Die App ist nicht notarisiert: beim ersten Start unter *Systemeinstellungen → Datenschutz & Sicherheit*
   „Trotzdem öffnen“ wählen – genau wie bei der bisherigen Mac-App.

**Voraussetzungen:** macOS 14 (Sonoma) oder neuer, Python 3.8+ (Homebrew, python.org oder Apples
Command Line Tools). Die Suche nach Python ist dieselbe wie bei der Browser-App; mit der Umgebungsvariable
`STECKWERK_PYTHON` lässt sich ein bestimmtes Python vorgeben.

Läuft schon eine Steckwerk-Engine auf Port 8765 (z. B. die Browser-App), benutzt die native App diese mit.
Sonst startet sie eine eigene auf einem freien Port und beendet sie beim Schließen wieder – auch nach einem
Absturz (die Engine überwacht die App).

## Bedienung

- **Seitenleiste:** Modelle nach Gruppen mit Suche, darunter Pakete, KI, Material, Updates.
- **Mitte:** Blattvorschau (Schnitt schwarz, Gravur blau), Zoom mit Pinch oder den Knöpfen, Ziehen verschiebt,
  Doppelklick passt ein. Statuspille öffnet den Prüfbericht.
- **Rechts:** Werte des Modells; jede Änderung baut und prüft nach einer halben Sekunde neu.
- **⌘B** bauen & prüfen · **⌘E** exportieren (nur bei „0 FEHLER“; schreibt SVGs + `pruefbericht.txt`)
  · **⌘O** Ausgabeordner · **⌘,** Einstellungen (Material, KI-Anbieter, Updates).

## Schlüssel für KI

Schlüssel für OpenRouter und ChatGPT (OpenAI) trägst du unter *KI* bzw. *Einstellungen → KI-Anbieter* ein.
Sie gehen an die Engine, die sie wie bisher im macOS-Schlüsselbund ablegt; die App selbst speichert keine.

## Entwickeln

```
cd packaging/swift
swift build          # nur auf macOS (SwiftUI)
swift test           # Schema-, Bridge- und SVG-Tests (ohne laufende Engine)
swift run            # startet die App mit der Engine aus diesem Repo
./build_app.sh       # baut ../dist/Steckwerk Desktop.app und das ZIP
```

`SteckwerkCore` enthält alles ohne Oberfläche (Schema, HTTP-Bridge, SVG-Pfade, Engine-Start) und wird von
den Tests abgedeckt; `SteckwerkDesktop` sind die SwiftUI-Ansichten. CI: `.github/workflows/macos-desktop.yml`.

Die Test-Fixtures in `Tests/SteckwerkDesktopTests/Fixtures/` stammen direkt aus der Engine
(`service.schema()` gekürzt, `service.generate({"model": "wichtelhaus"})`).

## Grenzen (Version 0.1)

- Programm-Updates installiert die native App nicht selbst; sie zeigt neue Versionen und verlinkt die Seite.
  Pakete aus dem Kanal installiert sie wie gewohnt.
- Kein Platzierungs-Editor für Motive (Werte x/y/Größe/Drehung stehen im Formular).
- Der Assistent (Werte aus einer Beschreibung) läuft weiter nur über Ollama. ChatGPT ist als dritter Anbieter
  nur für „Motiv zeichnen“ eingebaut (`bildgen.py`, Modell `gpt-image-1` oder `gpt-image-1-mini`): ein
  OpenAI-Chat-Weg hätte den Assistenten um eine zweite, kostenpflichtige Schnittstelle erweitert, ohne dass
  die Werte besser würden.
- Oberfläche nur auf Deutsch.
