# Steckwerk-Wiki

Willkommen! Hier steht alles, was wir bisher für **Steckwerk** gebaut haben – vom ersten Wichtelhaus bis zum
KI-Assistenten. Steckwerk hieß bis Version 1.7.0 **Laserforge**; im Repo und in alten Dateinamen taucht der
alte Name deshalb noch auf.

## Was ist Steckwerk?

![Übersicht der Modelle](medien/uebersicht.png)


Steckwerk erzeugt **parametrische, geprüfte Lasercut-SVGs** für Steckmodelle aus Holz, Pappe oder Acryl:
Wichtelhäuser und ganze Serien, Weihnachtszubehör, Christbaumschmuck, Schneeflocken, Schwibbögen und
Steckfahrzeuge mit drehenden Rädern. Über Pakete kommen weitere Modelle dazu (Halloween, Weihnachten,
Mehrlagig, Wichtel, Wohnen …).

Das Besondere: Jede Datei wird **vor dem Schreiben geprüft**. Kerf, Steckverbindungen, Mindeststege und das
fertige SVG werden kontrolliert. Gibt es auch nur einen Fehler, wird nichts geschrieben.

- Reines Python (ab 3.8), nur Standardbibliothek, läuft komplett lokal.
- Bedienung als Mac-App, im Browser, als Konfigurator im Terminal oder per Kommandozeile.
- Deutsch und Englisch.
- Abgestimmt auf deinen **xTool M2** mit **xTool Creative Space** (Rot = Schneiden, Blau = Ritzen).

## Aktueller Stand

| | |
|---|---|
| Programm | Steckwerk **2.10.0** (26.10.2026) mit Steckwerk Desktop 2.10.0 · im Update-Kanal noch 2.9.0, bis das Release 2.10.0 läuft · Mac-App-Zip im Download-Ordner noch 2.6.0 |
| Pakete im Update-Kanal | Grundlagen 2.0.0 · Wohnen 1.0.0 · Weihnachten 2.0.1 · Halloween 1.4.0 · Mehrlagig 1.2.0 · Wichtel 1.0.1 |
| Tests | PYTESTS Python-Tests grün · 59 Swift-Tests (Desktop-App) grün |
| Repo | `chr-braun/laserforge` (umbenannt in `chr-braun/steckwerk`), Lizenz MIT |

## Seiten

**Erste Schritte**

- [Downloads](Downloads.md) – Mac-App, Desktop-App und alle Pakete zum Herunterladen
- [Steckwerk Desktop](Steckwerk-Desktop.md) – die native Mac-App ohne Browser, mit Live-Vorschau
- [Installation](Installation.md) – Mac-App, Weboberfläche, Python
- [Bedienung](Bedienung.md) – Oberfläche, Export, Tastenkürzel, Kommandozeile

**Gestalten**

- [Modelle](Modelle.md) – alle eingebauten Vorlagen
- [Material und Laser](Material-und-Laser.md) – xTool M2, Materialprofile, Kerf, Montage
- [Gestaltung und Beschriftung](Gestaltung-und-Beschriftung.md) – Fenster, Gravuren, Schriften
- [Eigene Motive](Eigene-Motive.md) – eingebaute und eigene Motive, importieren und platzieren
- [Pakete](Pakete.md) – Erweiterungspakete, alle bisherigen Pakete, eigene bauen
- [KI-Funktionen](KI-Funktionen.md) – Assistent, „Motiv zeichnen“ mit Ollama, OpenRouter oder ChatGPT

**Betrieb**

- [Updates](Updates.md) – Updater und Update-Kanal
- [Offene Punkte](Offene-Punkte.md) – was ansteht und was auf deine Entscheidung wartet

**Entwicklung**

- [Entwicklung](Entwicklung.md) – Aufbau des Codes, Tests, Veröffentlichen
- [Versionsverlauf](Versionsverlauf.md) – was wann dazukam
