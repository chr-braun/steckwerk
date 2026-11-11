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
| Programm | Steckwerk **2.12.0** (11.11.2026) mit Steckwerk Desktop 2.12.0 |
| Pakete im Update-Kanal | 11 Themenpakete in 6 Bereichen, siehe [Pakete](Pakete.md) |
| Tests | 1321 Python-Tests grün · 59 Swift-Tests (Desktop-App) grün |
| Repo | [`chr-braun/steckwerk`](https://github.com/chr-braun/steckwerk), Lizenz MIT · [Webseite](https://chr-braun.github.io/steckwerk/) |

## Seiten

**Erste Schritte**

- [Downloads](Downloads.md) – Steckwerk Desktop, Mac-App und Pakete
- [Steckwerk Desktop](Steckwerk-Desktop.md) – die native Mac-App ohne Browser, mit Live-Vorschau
- [Installation](Installation.md) – Mac-App, Weboberfläche, Python
- [Bedienung](Bedienung.md) – Oberfläche, Export, Tastenkürzel, Kommandozeile
- [Kommandozeile und Referenz](Kommandozeile.md) – alle Optionen, Validator, Montage, Aufbau (früher das README)

**Gestalten**

- [Modelle](Modelle.md) – alle eingebauten Vorlagen
- [Material und Laser](Material-und-Laser.md) – xTool M2, Materialprofile, Kerf, Montage
- [Gestaltung und Beschriftung](Gestaltung-und-Beschriftung.md) – Fenster, Gravuren, Schriften
- [Eigene Motive](Eigene-Motive.md) – eingebaute und eigene Motive, importieren und platzieren
- [Eigene Gravur](Eigene-Gravur.md) – Fotos, Logos, Motive und 18 Muster auf jedem Teil
- [Pakete](Pakete.md) – Erweiterungspakete, alle bisherigen Pakete, eigene bauen
- [KI-Funktionen](KI-Funktionen.md) – Assistent, „Motiv zeichnen“ mit Ollama, OpenRouter oder ChatGPT

**Betrieb**

- [Updates](Updates.md) – Updater und Update-Kanal
- [Offene Punkte](Offene-Punkte.md) – was ansteht und was auf deine Entscheidung wartet

**Entwicklung**

- [Entwicklung](Entwicklung.md) – Aufbau des Codes, Tests, Veröffentlichen, Webseite
- [Versionsverlauf](Versionsverlauf.md) – was wann dazukam
