# Offene Punkte

Stand 17.10.2026. Was noch ansteht oder auf deine Entscheidung wartet.

## Entscheidungen für dich

- **Repo-Sichtbarkeit:** Das Repo `chr-braun/steckwerk` ist derzeit öffentlich. Ob es so bleibt, entscheidest du.
- **Pull Request #5** (https://github.com/chr-braun/steckwerk/pull/5) bringt Steckwerk Desktop, die neuen Motive
  und den Stand 2.9.0 auf den Zielbranch `claude/project-thread-y7q7zo`. Prüfen und mergen liegt bei dir.
- **Wichtelanhänger** sind noch nicht überarbeitet. Die Weihnachtsanhänger sind in Ordnung.
- **Mac-Zip im Download-Ordner** ist noch 2.6.0. Die neue Desktop-App gibt es als Artefakt aus dem CI.
- **Steckwerk Desktop einmal von Hand ersetzen:** Die bisher installierte Desktop-App (2.8.0) kennt das
  Selbst-Update noch nicht. Einmal das DMG 2.9.0 installieren, ab dann aktualisiert sie sich selbst.

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
