# Offene Punkte

Stand 26.10.2026. Was noch ansteht oder auf deine Entscheidung wartet.

## Entscheidungen für dich

- **Repo-Sichtbarkeit:** Das Repo `chr-braun/steckwerk` ist derzeit öffentlich. Ob es so bleibt, entscheidest du.
- **Steckwerk 2.10.0 nach `main` bringen und veröffentlichen:** Der Pull Request mit 2.10.0 (Branch
  `claude/implement-swift-app-spec-a43ysx` nach `main`) wartet auf dich. Nach dem Merge unter Actions → Release →
  „Run workflow“ auf `main` starten; dann kommen Mac-App, Steckwerk Desktop, Halloween 1.4.0 und Weihnachten 2.0.1
  in den Update-Kanal.
- **Wichtel neu gezeichnet, noch nicht veröffentlicht:** Der eingebaute Wichtel (Zubehör) ist überarbeitet und
  kommt mit der nächsten Programmversion. Die Figuren im Paket „Wichtel“ (Schichtwichtel, Möbel-Ausschnitte)
  waren schon in Ordnung.
- **Mac-Zip im Download-Ordner** ist noch 2.6.0. Die neue Desktop-App gibt es als Artefakt aus dem CI.
- **Steckwerk Desktop von Hand ersetzen, falls du noch die DMG 2.8.0 aus dem CI hast:** Die kennt das
  Selbst-Update noch nicht. Die Desktop-App 2.9.0 aus `main` aktualisiert sich dagegen von selbst auf 2.10.0.

## Zum Ausprobieren bei dir

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

- **Repo-Sichtbarkeit:** siehe oben. Das Repo ist derzeit öffentlich, der Update-Kanal braucht damit keinen Lese-Schlüssel.
- **Releases:** Der Tag-Push für automatische GitHub-Releases hat aus der Cloud nicht geklappt. Wenn du
  Releases auf GitHub haben willst, kannst du einen Tag `v2.6.0` selbst setzen.
- **Markenrecherche:** Eine Prüfung in TMview (Klassen 9 und 42) für „Steckwerk“ stand noch aus.
- **Wiki:** Diese Seiten liegen im Repo unter `docs/wiki/`. Wenn du das GitHub-Wiki einschaltest, lassen
  sie sich dorthin übernehmen.

## Bekannte Grenzen

- Große Ebenenbilder (Mehrlagig, ca. 300 mm) brauchen etwa eine Minute zum Rechnen.
- Der Engel (Mehrlagig) wirkt in kleinen Größen schwächer.
- Große Modelle (Schwibbogen ab ca. 280 mm, Spukschloss, Kürbis) brauchen ein Blatt größer als 400 × 300 mm.
- Die Mac-App ist nicht von Apple signiert, daher die einmalige Freigabe unter Datenschutz & Sicherheit.
- Keine Windows-App, dort läuft Steckwerk über Python.
