# Offene Punkte

Stand 11.11.2026, abends. Was noch ansteht oder auf deine Entscheidung wartet.

## Entscheidungen für dich

- **Bild-Gravur in XCS testen:** Fotos stecken als eingebettetes PNG in der SVG-Ebene „Bild“. Bitte einmal in xTool Creative Space importieren und prüfen, ob Lage und Größe stimmen. Falls XCS das Bild nicht übernimmt, liegt jedes Bild zusätzlich als PNG mit Maß im Dateinamen daneben. Der direkte .xcs/.xs-Export nimmt Bilder noch nicht mit.
- **Repo-Sichtbarkeit:** Das Repo `chr-braun/steckwerk` ist derzeit öffentlich. Ob es so bleibt, entscheidest du.
- **Wichtelanhänger** sind noch nicht überarbeitet. Die Weihnachtsanhänger sind in Ordnung.
- **Steckwerk Desktop von Hand ersetzen, falls du noch die DMG 2.8.0 aus dem CI hast:** Die kennt das
  Selbst-Update noch nicht. Die Desktop-App 2.9.0 aus `main` aktualisiert sich dagegen von selbst auf 2.10.0.

## Zum Ausprobieren bei dir

- **XCS-Projekte testen:** Ein kleines Modell mit „XCS-Projekt (.xcs)“ und „xTool Studio (.xs)“ exportieren
  bzw. „In XCS öffnen“ drücken und in XCS prüfen: Liegen die Teile richtig, heißen die Ebenen
  *Schneiden*/*Ritzen*, ist der M2 gewählt? Beim `.xs`: stehen Leistung, Tempo und Durchgänge? Wenn etwas nicht
  passt, kurz Bescheid geben (am besten mit der Datei, die XCS selbst speichert) – dann passen wir das Format an.

- **Filigran-Rezepte ausprobieren (Paket Weihnachten):** Beim Spitzenschmuck „Muster: eigenes Rezept“ oder „Zufall“ wählen
  und ein paar Startwerte durchklicken. Gefällt dir ein Muster, steht sein Rezept bei den Hinweisen zum Modell.
- **Passungstest schneiden (Paket Grundlagen):** Einmal mit deinem Holz schneiden und den Kerf aus dem
  Schlitz, in dem das Probestück satt sitzt, ins Materialprofil übernehmen. Danach Wichtel (Möbel, Tür, Lebkuchenstand,
  Werkbank, Wegelaterne) und die Rahmen aus Wohnen probeschneiden – die sind geprüft, aber noch nicht auf dem xTool gelasert.

- **KI-Funktionen echt testen:** Assistent und „Motiv zeichnen“ sind nur gegen nachgebaute Server
  getestet. Erster echter Lauf mit Ollama, OpenRouter und ChatGPT am Mac.
- **Steckwerk Desktop:** Screenshots für die Wiki-Seiten fehlen, der CI-Runner kann keine machen.
  Die App ist nicht notarisiert; „Dennoch öffnen“ bleibt nötig.
- **Materialprofile kalibrieren:** Die XCS-Startwerte sind vorsichtige Schätzungen. Wenn du für ein
  Material bessere Werte findest, als eigenes Profil sichern – oder Bescheid geben, dann passen wir die
  eingebauten an.

## Auf GitHub

- **Webseite:** Pages ist eingeschaltet (Quelle „GitHub Actions“), der Workflow „Webseite“ läuft durch. Die Seite liegt unter <https://chr-braun.github.io/steckwerk/>. Bitte einmal im Browser prüfen, ob Startseite und „Pakete bauen“ laden.
- **Repo-Beschreibung und Topics:** eingetragen (Stand 11.11., von Christian bestätigt).
- **Paketkanal:** Der Update-Kanal steht auf Steckwerk 2.12.0 mit den Paket-Bereichen. Alte Releases 2.9.0 bis 2.10.1 sind entfernt, die Tags bleiben.
- **Repo-Sichtbarkeit:** Das Repo ist derzeit öffentlich, der Update-Kanal braucht damit keinen Lese-Schlüssel. Ob es so bleibt, entscheidest du.
- **Markenrecherche:** Eine Prüfung in TMview (Klassen 9 und 42) für „Steckwerk“ stand noch aus.
- **Wiki:** Diese Seiten liegen im Repo unter `docs/wiki/`. Wenn du das GitHub-Wiki einschaltest, lassen
  sie sich dorthin übernehmen.

## Bekannte Grenzen

- Große Ebenenbilder (Mehrlagig, ca. 300 mm) brauchen seit 2.10.1 nur noch rund 10 Sekunden (vorher etwa eine Minute); auf einem älteren Mac entsprechend länger.
- Der Engel (Mehrlagig) wirkt in kleinen Größen schwächer.
- Große Modelle (Schwibbogen ab ca. 280 mm, Spukschloss, Kürbis) brauchen ein Blatt größer als 400 × 300 mm.
- Die Mac-App ist nicht von Apple signiert, daher die einmalige Freigabe unter Datenschutz & Sicherheit.
- Keine Windows-App, dort läuft Steckwerk über Python.
