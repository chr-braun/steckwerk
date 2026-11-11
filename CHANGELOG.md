# Changelog

Alle nennenswerten Änderungen an Steckwerk. Versionen folgen dem Schema Haupt.Neben.Fix.

## Neu, noch ohne Versionsnummer

- **Eigene Gravur auf jedem Modell:** Fotos, Logos, Motive und Muster lassen sich auf jedes Teil gravieren (größtes Teil, alle Teile oder ein bestimmtes), in der Browser-App, in Steckwerk Desktop und auf der Kommandozeile (`--gravur`, `--bild-import`). Gravuren laufen nie über Schnitte, Durchbrüche oder Steckverbindungen.
- **Fotos und Logos als Bild-Gravur:** JPG, PNG und HEIC importieren; Fotogravur (fein gerastert), Graustufen für XCS, Schwarzweiß-Logo oder Skizze; Bildform Rechteck, abgerundet, Oval, Kreis, Herz oder weicher Rand; Helligkeit, Kontrast, Gamma, Umkehren, Auflösung bis 12,7 Punkte je mm. Die Bilder kommen als eigene Ebene „Bild“ ins SVG und zusätzlich als PNG-Datei daneben. Fertige Bilder werden zwischengespeichert, damit es auch auf älteren Rechnern flott bleibt.
- **Motive als gestochen scharfe Bild-Gravur:** flächige Logos ohne Schraffurlinien.
- **18 neue Flächenmuster:** Rautengitter, Karo, Waben, Schuppen, Fischgrät, Wellen, Holzmaserung, Streifen, Punkte, Blume des Lebens, Mandala, Strahlen, Spitze, Ranken, Sternenhimmel, Schneeflocken, Herzen, Tannenwald – mit einstellbarem Rapport, auf Wunsch nur in einem Bereich; Zierrahmen und vorhandene Gravuren bleiben frei.
- Motive lassen sich jetzt auch aus JPG und HEIC importieren.
- Steckwerk Desktop zeigt Bild-Gravuren in der Vorschau.

## 2.11.0 – 2026-11-11

- Neues Themenpaket **Spiele** 1.0.0 (braucht Grundlagen 2.0.0): Mühle mit Steinablage und Spielernamen, rundes Tic-Tac-Toe mit ausgesägten Figuren (zum Beispiel Tanne gegen Stern), Vier in einer Reihe mit Auslöse-Schieber, Kugellabyrinth mit Fallen (jede Nummer ein neuer Irrgarten) und Solitär mit Kugelrinne. Alle Bretter haben zwei Lagen mit Mulden, und alles rechnet in Sekundenbruchteilen.
- Der Release-Workflow nimmt jetzt auch ganz neue Pakete in den Update-Kanal auf, nicht nur neue Versionen bekannter Pakete.
- Wichtel 1.1.0: edles Wichtelzubehör, alles im Wichtel-Maßstab und in jeder Größe prüfbar schnittfertig:
  - **Wichtelkamin** in zwei Lagen: Korpus zum Stecken (Rückwand mit Mauerwerk, Sockel mit gefliester Herdplatte, Sims mit Zierkante) und filigrane Zierblende mit Fries, kannelierten Pilastern und Schlussstein. Dazu Feuer mit Holzscheiten, Funkengitter mit Rosette, dreiarmige Kerzenleuchter, Kaminuhr, Girlande und Strümpfe mit Namen.
  - **Standuhr** mit Pendelfenster, Pendel und Gewichten, Zierblende mit Rosette, Uhrenkopf mit Zifferblatt und Krone (Bogen, Giebel oder Schwanenhals), auf Wunsch mit Inschrift.
  - **Schaukelstuhl** mit geschwungenen Kufen, Sprossen, schräger Sprossenlehne (Neigung einstellbar) und Armlehnen-Schnecken, dazu Sitzkissen und Strickkorb.
  - **Christbaum** aus zwei gekreuzten Hälften mit Etagen, Schmuck-Ausschnitten, Lichterkette und Stern, dazu Geschenke mit Schleife und Namen.
  - **Schneemann** über Kreuz gesteckt: Gesicht und Zweigarme vorn, Möhrennase und wehender Schal im Profil, Zylinder oder Wollmütze, Besen oder Laterne.
  - **Wichtelgarten**: Wiesenplatte mit Trittsteinen und Beet, dazu Schubkarre, Gießkanne, Vogelhaus, Blumen, Fliegenpilze und Kürbisse zum Einstecken.
- Weihnachten 2.1.0: neues Modell **Edler Namensanhänger**: Namen in echter Schreibschrift (elegant, schwungvoll, rund und kräftig), ein Anhänger je Name.
  - Schriftzug im Kugelring mit Szene auf dem Schneehügel: Winterdorf, Winterwald mit Hirsch, Schneemann mit Laterne, Schlittenfahrt, Adventskranz, Christbaum mit Geschenken, Plätzchen backen, Geschenke packen. Die Jahreszahl steht im Schnee.
  - Zweilagiges Medaillon (Grundplatte mit gefüllt graviertem Namen, Spitzenrahmen obendrauf) und einlagige Spitze.
  - Haarstriche werden laserfest verstärkt, i-Punkte, Umlaute und Namen mit Leerzeichen bleiben ein Stück.
  - Die Schriften sind als Umrisse im Paket (SIL Open Font License), Steckwerk braucht keine Schriftdateien.
- **Direkt für den xTool M2:** Beim Export legt Steckwerk auf Wunsch neben jede SVG ein `.xcs`-Projekt für xTool Creative Space (Ebenen „Schneiden“ rot und „Ritzen“ blau, Gerät M2) und ein `.xs`-Projekt für xTool Studio ab 1.7, in dem Leistung, Tempo und Durchgänge aus dem Materialprofil schon eingetragen sind. Die Formate sind nicht offen dokumentiert und nach öffentlichen Beispielen geschrieben – beim ersten Mal in XCS kurz prüfen.
- **„In XCS öffnen“:** speichert die Platte als `.xcs` und öffnet sie gleich in xTool Creative Space (oder xTool Studio). Browser-Oberfläche, Mac-App und Steckwerk Desktop.
- **Schnittzeit und Material:** Für jedes Modell schätzt Steckwerk Laserzeit, Schnitt- und Ritzlänge, Plattenbedarf und Ausnutzung; mit einem Preis je Platte (Einstellungen → Material) auch die Materialkosten. Zu sehen im Inspektor, im Export-Fenster und in Steckwerk Desktop neben dem Prüfstatus.
- **Teilenummern und Montageanleitung:** „Teilenummern gravieren“ (Material) schreibt jedem Teil eine kleine, geprüfte Nummer an die Stelle mit dem meisten Platz. „Montageanleitung (PDF)“ legt die Anleitung mit Blattübersicht, Teileliste und Zusammenbau-Schritten dazu.
- **Projekte:** Modell, Werte und Material unter einem Namen merken und mit einem Klick wieder öffnen (Knopf „Projekte“, gespeichert in `~/.steckwerk/projekte.json`).
- **Enger verschachteln:** Braucht ein Modell mehrere Platten, versucht Steckwerk eine dichtere Anordnung mit gedrehten Teilen und nimmt sie, wenn sie eine Platte spart. Passt alles auf eine Platte, bleibt die Datei genau wie bisher.
- **Schneller auf älteren Macs (Grundlagen 2.0.1):** Mehrlagige Bilder merken sich die Durchbrüche unveränderter Ebenen. Ändert man Text, Rückwand, Abstand oder Rahmen, ist ein Ebenenbild statt in rund 4 in gut 1 Sekunde neu gerechnet.
- Kommandozeile: `--xcs`, `--xs`, `--montage` und `--laser w10|w20`.
- README: Anleitung für xTool Creative Space statt LightBurn.

## 2.10.1 – 2026-11-10

- Steckwerk rechnet deutlich schneller und läuft damit auch auf älteren Macs flüssig. Die Schnittdateien bleiben dabei bitgenau gleich, nur der Weg dorthin ist kürzer:
  - Die Prüfung (Kerf-Versatz, Selbstüberschneidung, Stege, Gravur in der Kontur) vergleicht nicht mehr jede Kante mit jeder, sondern nur noch Kanten in der Nähe. Große Motive prüft Steckwerk dadurch 3- bis 20-mal schneller.
  - Konturen aufräumen und Schleifen beim Nach-innen-Versetzen entfernen geht auf großen Konturen viel schneller.
  - Ein großes Ebenenbild (300 × 360 mm, 6 Ebenen) braucht statt rund 90 Sekunden nur noch etwa 9. Über alle Modelle zusammen sinkt die Rechenzeit auf weniger als die Hälfte.
- Live-Vorschau: Tippst du schneller, als der Rechner rechnet, verwirft Steckwerk überholte Vorschauen, statt sie parallel weiterzurechnen. Auf langsamen Rechnern wartet die Vorschau etwas länger, bis du mit dem Tippen fertig bist.
- Speichern und ZIP direkt nach der Vorschau rechnen nicht noch einmal alles, sondern nehmen das gerade geprüfte Ergebnis.

## 2.10.0 – 2026-10-26

- Steckwerk Desktop überarbeitet: Die Vorschau baut sich beim Ändern jedes Werts von selbst neu, Motive sind in der Auswahl größer zu sehen, und beim Start sucht die App von selbst nach Updates (abschaltbar, die Anzahl steht neben „Updates“). Vor dem Ersetzen prüft das Update jetzt auch, dass wirklich eine Steckwerk-Desktop-App im Paket steckt.
- Alle 19 eingebauten Motive sind neu und deutlich detaillierter gezeichnet, mit feinen Innenformen und Gravurlinien.
- Silhouetten aus Motiven gravieren die Motivlinien mit.
- Halloween 1.4.0: Die Anhänger nehmen ihre Figuren aus der Motiv-Bibliothek und haben Platz für den Namen.
- Weihnachten 2.0.1: Die Zuckerstange trägt keine Stechpalme mehr, nur noch die Schleife.
- Der Start geht auf dem Mac schneller (keine Namensauflösung mehr beim Serverstart).
- Steckwerk Desktop: Modelle in der Seitenleiste lassen sich wieder durchsuchen.

## 2.9.0 – 2026-10-21

- Neue native Mac-App **Steckwerk Desktop** (SwiftUI, macOS 14+, gleiche Versionsnummer wie Steckwerk) unter `packaging/swift`: dieselbe Engine, aber ohne Browser – Modellliste, Formular, Blattvorschau, Prüfbericht, Export, Pakete, KI, Material und Updates als echtes Mac-Fenster. Sie aktualisiert sich selbst aus dem Update-Kanal („Updates → Installieren und neu starten“). Die bisherige App bleibt.
- „Motiv zeichnen“ kann jetzt auch **ChatGPT** (OpenAI, `gpt-image-1` oder `gpt-image-1-mini`) mit eigenem OpenAI-Schlüssel. Die Kosten zählen zum selben Monatslimit wie OpenRouter.

## 2.8.0 – 2026-10-17

- Neues Themenpaket **Verkauf** 1.0.0 mit dem Flaschenschild: Preisschild zum Aufhängen am Flaschenhals oder an einer Kordel, mit deinem Logo (aus „Motive importieren“) oder einer Kopfzeile, Preis inkl. MwSt. und Grundpreis je Liter, den Steckwerk selbst ausrechnet. Über eine Preisliste entstehen alle Schilder auf einmal.
- Die Schrift kennt jetzt auch €, % und den Mittelpunkt ·.
- Textfelder in Paketen können mehrzeilig sein.

## 2.7.0 – 2026-10-16

- Neues Themenpaket **Formen** 1.0.0 mit mathematischen Steckskulpturen: Steckkörper (Kugel, Ei, Linse, Zwiebelturm, Kreisel, Tanne oder Kuppel aus gekreuzten Rippen), Wellenfläche (Eierkarton-Welle, Sattel, Hügel, Ringwellen, Dünen, zwei Gipfel, Kissen) und Stapelvase (gedrehte Vase oder Windlicht aus gestapelten Lagen, mit Glaseinsatz oder Rundstab).
- Alte Einzelpakete (Filigran, Umrandungen, Werkstatt und die fünf Wichtel-Pakete) lädt Steckwerk nicht mehr. Unter Einstellungen → Pakete steht bei jedem, in welchem Themenpaket es jetzt steckt, mit Knopf zum Installieren. Danach verschwindet das alte Paket von selbst, oder du entfernst es direkt.

## 2.6.0 – 2026-10-16

- Pakete aufgeräumt, jetzt gibt es ein Paket je Thema: Grundlagen, Wohnen, Weihnachten, Halloween, Mehrlagig und Wichtel. Die alten Einzelpakete räumt Steckwerk beim Installieren selbst weg.
- Grundlagen 2.0.0 (früher Verzierungen) enthält jetzt auch den Passungstest aus Werkstatt. Wohnen 1.0.0 bündelt Bilderrahmen, Zierrahmen und Türschild. Weihnachten 2.0.0 bringt Weihnachtsdeko und Filigran zusammen.
- Einstellungen → Pakete ist jetzt ein Katalog: Jedes Paket steht mit Beschreibung und seinen Modellen da, und alles aus dem Update-Kanal, was noch fehlt, lässt sich direkt mit „Installieren“ einbauen.

## 2.5.1 – 2026-10-16

- Fehler behoben: Modelle aus Paketen (z. B. „Spitzenschmuck“) ließen sich manchmal nicht laden, mit der Meldung „Bibliothek von verzierungen lässt sich nicht laden … has no attribute Figur“. Ursache war, dass die Oberfläche Pakete gleichzeitig aus mehreren Anfragen lädt. Jetzt wartet jede Anfrage, bis ein Paket fertig geladen ist.
- Wichtel 1.0.1 lädt seine Hilfsmodule ebenfalls geschützt.

## 2.5.0 – 2026-10-16

- Ein Paket je Thema: Alles rund um Wichtel steckt jetzt im Paket **Wichtel** 1.0.0. Die fünf einzelnen
  Pakete Wichtelmöbel, Wichteltür, Wichtelzubehör, Wichtelwelt und Wichtelfiguren räumt Steckwerk beim
  Installieren selbst weg. Dafür gibt es in der `paket.json` die neue Angabe `ersetzt` (siehe PAKETE.md).
- Neu im Paket Wichtel: **Lebkuchenstand** mit gestreifter Markise, Namensschild, Herzgirlande, Theke und
  Pflaster-Grundplatte, dazu Lebkuchenherzen, Lebkuchenmänner und Zuckerstangen.
- Neu: **Kreidetafel** zum Aufstellen und **Backstube** mit Blech, Backbrett, Teigrolle, Ausstechern und
  Plätzchen.
- Neu: **Wichtel-Briefkasten** mit Fähnchen und Briefen, **Gartenzaun** in zwei Lagen, **Werkbank** mit
  Schraubstock und Werkzeug und eine **Wegelaterne**, die über Kreuz gesteckt wird. Alles passt im
  Wichtel-Maßstab zusammen.
- **Verzierungen** 1.3.0 passt die Hinweise zum Wichtel-Maßstab an das neue Paket an.

## Paket-Updates – 2026-10-16

- **Wichtelfiguren** 1.0.0 – der **Schicht-Wichtel**: ein skandinavischer Wichtel aus vier Lagen zum Bemalen
  und Aufeinanderleimen. Tief sitzende Mütze (umgeknickt, spitz oder mit Bommel) mit graviertem Muster
  (Sterne, Herzen, Streifen, Norweger-Zacken), Fellkrempe, dicke Nase, wallender Bart mit gravierten
  Strähnen (lang, rund, lockig oder mit zwei Zipfeln), Fäustlinge, Stiefel und ein dunkler Schattenrand.
  Dazu Laterne, Herz, Stern am Stab, Tannenbaum oder Geschenk, und eine Standplatte mit Namen oder eine Öse
  zum Aufhängen. 60 bis 300 mm hoch.
- **Wichtelwelt** 1.1.0 nimmt im Wichtelzimmer jetzt den Schicht-Wichtel als Figur (ab 60 mm; die einfache
  Steckfigur gibt es weiter unter „Figur“).
- **Werkstatt** 1.0.0 – Passungstest: ein Kamm mit Schlitzen in leicht verschiedenen Breiten und ein Probestück.
  Unter jedem Schlitz steht der Kerf, mit dem genau dieser Schlitz zur Standardbreite wird. Der Wert unter dem
  Schlitz, in dem das Probestück satt sitzt, kommt ins Materialprofil.
- **Wichtel-Maßstab**: Wichtelmöbel, Wichteltür und Wichtelzubehör 1.1.0 richten ihre Maße auf Wunsch nach der
  Größe deiner Wichtelfigur (Standard 70 mm). Dann passen Tür, Fenster, Bank, Tisch, Bett, Leiter, Wegweiser
  und Wäscheleine zusammen. Unter „Maßstab: eigene Maße“ stellst du wie bisher alles selbst ein.
- **Wichtelwelt** 1.0.0 – Wichtelzimmer auf Knopfdruck: Wichtelfigur, Tür, Fenster und Möbel (auf Wunsch auch
  Leiter, Wegweiser und Wäscheleine) im selben Maßstab, mit deinem Namen auf Türschild, Bett und Figur.
- **Verzierungen** 1.2.0 bringt den gemeinsamen Wichtel-Maßstab mit. Ist der Wichtel für die Materialstärke zu
  klein, sagt Steckwerk jetzt, ab welcher Größe es passt.

## Paket-Updates – 2026-10-15

- **Verzierungen** 1.1.0 – die Bibliothek bringt jetzt auch die Motiv-Figuren und die Halloween-Formen mit,
  die bisher in mehreren Paketen doppelt steckten.
- **Mehrlagig** 1.2.0, **Halloween** 1.3.0 und **Weihnachtsdeko** 1.1.0 nutzen diese Bibliothek statt eigener
  Kopien. Die Teile bleiben gleich, die Pakete werden kleiner, und Verbesserungen an Ornamenten kommen
  überall gleichzeitig an. Die Quellen liegen jetzt im Repo unter `paketquellen/`.
- **Halloween** 1.3.0 behebt zwei seltene Prüffehler: Beim Spukschloss mit Spinne und beim Kürbis mit Blatt
  konnten bei manchen Größen spitze Zwickel den Kerf-Ausgleich stören.
- **Filigran** 1.1.0 – Muster-Rezepte beim Spitzenschmuck: Unter „Rezept“ stellst du dir aus Bausteinen
  (Blüten, Bögen, Speichen, Zickzack, Perlen, Ranken, Sterne, Tropfen, Herzen) von innen nach außen dein
  eigenes Muster zusammen. „Zufall“ würfelt mit jedem Startwert ein neues Muster und schreibt das Rezept dazu.
  Der Assistent kann Rezepte aus einer Beschreibung vorschlagen.

## 2.4.0 – 2026-10-15

- Pakete können jetzt andere Pakete benutzen: `benoetigt` in der `paket.json` nennt sie mit Mindestversion,
  `bibliothek` bietet eigene Formen und Werkzeuge allen anderen Paketen an. Über **Updates** kommen
  benötigte Pakete automatisch mit, und ein Paket, das andere noch brauchen, lässt sich nicht entfernen.
  Details in PAKETE.md.
- **Verzierungen** 1.0.0 – die gemeinsame Ornament-Bibliothek für alle Pakete (Rosetten, Eckornamente,
  Bordüren, Kanten, Durchbrüche, Ausschnittmotive, Rahmenformen) plus die Modelle Zierstück und Zierleiste.
- **Umrandungen** 1.0.0 – Bilderrahmen (9 × 13 bis 15 × 20 cm oder eigenes Maß, mit Sockel oder
  Schlüsselloch) und Zierrahmen mit Schild und graviertem Text.
- **Wichtelmöbel** 1.0.0 – Bank mit Lehne, Tisch mit Hockern und Bett mit graviertem Kissen und Decke,
  alles gesteckt.
- **Wichteltür** 1.0.0 – Tür mit Steinbogen oder Holzrahmen, Stufe und Namensschild, dazu ein Fenster
  mit Sprossen, Gardinen, Fensterläden und Blumenkasten.
- **Wichtelzubehör** 1.0.0 – Steckleiter, Wegweiser mit eigenen Ortsnamen und Wäscheleine mit Mini-Wäsche.

## 2.3.0 – 2026-10-11

- Aufgeräumte Seitenleiste: ein Suchfeld oben (⌘K oder ⌘F), darunter die zuletzt benutzten Modelle.
  Die Gruppen sind nach „Vorlagen“ und „Aus Paketen“ getrennt, zeigen ihre Anzahl und bleiben
  eingeklappt, bis du sie öffnest. Die Gruppe des gewählten Modells ist immer offen.
- Assistent im Inspektor: Ein kleines Sprachmodell auf deinem Rechner (Ollama, z. B. qwen2.5:3b) macht aus
  einer kurzen Beschreibung passende Werte. Steckwerk grenzt jede Zahl ein und verwirft Unpassendes.
  „Rückgängig“ stellt die alten Werte wieder her. Einschalten unter Einstellungen → Assistent.
- Neu: **Motiv zeichnen …** in der Seitenleiste. Ein Bildmodell zeichnet dein Motiv nach Beschreibung. Mit
  einem Schieberegler stellst du die Schwelle ein, dann landet es als eigenes Motiv in der Bibliothek und
  sofort in der Vorlage.
- Bildquellen: Ollama auf dem Mac (kostenlos, z. B. x/z-image-turbo) oder OpenRouter mit eigenem
  Schlüssel. Für OpenRouter gibt es eine Empfehlungsliste für Lasermotive mit den geschätzten Kosten
  je Bild und den Kosten dieses Monats. Ein Monatslimit lässt sich setzen.
- Der OpenRouter-Schlüssel liegt im Schlüsselbund. An OpenRouter geht nur die Beschreibung.
- Englische Oberfläche: Platzhaltertexte in Eingabefeldern werden jetzt auch übersetzt.

## 2.2.1 – 2026-10-11

- Zwei neue Materialprofile für feine Arbeiten: Pappel-Sperrholz 1,5 mm und 2 mm (Filigran), passend
  zu den Paketen Filigran und Mehrlagig.

## 2.2.0 – 2026-10-11

- Materialprofile für den xTool M2 (10 W und 20 W): Pappel, Linde und Birke 3 mm, Pappel 4 mm, MDF 3 mm,
  Graupappe 2 mm und Acryl schwarz 3 mm. Ein Profil stellt Materialstärke und Kerf ein und färbt die SVG
  für xTool Creative Space: Rot = Schneiden, Blau = Ritzen.
- Zu jedem Profil zeigt Steckwerk Startwerte für XCS (Leistung, Tempo, Durchgänge), auch im Export-Fenster.
- Eigene Profile: aktuelle Werte unter einem Namen sichern und die Laserwerte selbst eintragen.
- Das Material-Menü oben wechselt direkt zwischen den Profilen.

## 2.1.0 – 2026-10-10

- Neue Oberfläche im Mac-Stil, übersichtlicher und aufgeräumt: links eine Seitenleiste mit allen
  Modellen nach Gruppen, oben eine Werkzeugleiste mit Status, Material-Menü, Würfel und **Exportieren…**,
  in der Mitte nur die Platte und rechts der Inspektor mit den Werten des gewählten Modells
  (Größe, Ausstattung mit Schaltern, Motive, Gestaltung zum Aufklappen).
- Prüfbericht und Zusammenbau öffnen sich per Klick auf den Status, der Export als eigenes Fenster
  (ZIP, einzelne Platte als SVG oder in den Steckwerk-Ordner).
- Material, Pakete, Motive, Updates, Sprache, hell/dunkel und Live-Vorschau liegen jetzt im
  Einstellungsfenster (⌘,).
- Tastatur: ⌘, Einstellungen, ⌘E Exportieren, ⌘↩ Vorschau, Esc schließt.
- Systemschrift statt Webschriften – die Oberfläche lädt nichts mehr aus dem Internet.

## 2.0.0 – 2026-10-10

- Neuer Name: Aus Laserforge wird **Steckwerk**. Beim ersten Start übernimmt Steckwerk Pakete, Motive,
  Einstellungen und den Update-Schlüssel automatisch, die alte App im Programme-Ordner wird ersetzt.
- Pakete heißen jetzt `.swpaket`; ältere `.lfpaket`-Dateien und Pakete mit `from laserforge import …`
  funktionieren weiter.
- Deutsch und Englisch: oben rechts die Sprache wählen. Formular, Prüfbericht, Montagehinweise,
  Fehlermeldungen und Update-Hinweise erscheinen dann auf Englisch, die Mac-Dialoge folgen der
  Systemsprache. Eine englische Beschreibung liegt in README.en.md.
- Pakete können englische Texte mitbringen (`UEBERSETZUNG`, siehe PAKETE.md); das Halloween-Paket 1.1.0
  ist komplett zweisprachig.

> Bis Version 1.7.0 hieß das Programm Laserforge.

## 1.7.0 – 2026-10-10

- Updates direkt in Steckwerk: Der neue Bereich „Updates“ zeigt neue Programmversionen und Pakete
  aus dem Update-Kanal. Pakete installierst oder aktualisierst du mit einem Klick, die Mac-App ersetzt
  sich selbst durch die neue Version und startet neu.
- Beim Start prüft Steckwerk automatisch (abschaltbar); gibt es Neues, erscheint oben „Updates“ mit Anzahl.
- Jede Datei wird vor dem Installieren über ihre Prüfsumme kontrolliert.
- Für ein privates GitHub-Repo trägst du einmal einen Lese-Schlüssel ein; er liegt auf dem Mac im Schlüsselbund.
- Kommandozeile: `--update-pruefen`, `--update-paket ID|alle`, `--update-schluessel`, `--update-kanal`.
- Für Herausgeber: `packaging/update_kanal.py` baut den Update-Kanal (feed.json + Dateien).

## 1.6.0 – 2026-10-09

- Eigene Motive: SVG- und PNG-Dateien hochladen (PNG wird automatisch nachgezeichnet, auf Wunsch mit
  umgekehrten Farben). Die Motive landen in einer Motiv-Bibliothek, 19 Motive sind schon dabei.
- Neue Vorlagen in der Gruppe „Eigene Motive“: Aufsteller mit Sockel, Schild, Anhänger, Untersetzer
  und Silhouette (das Motiv selbst als Umriss, mit Sockel, Öse oder ohne Fuß).
- Motive in der Vorschau mit der Maus verschieben, an der Ecke skalieren, am Punkt drehen; dazu
  Felder für Größe, Drehung und Spiegeln. Je Motiv: ausschneiden, Umriss gravieren oder flächig gravieren.
- Klare Meldungen, wenn ein Motiv über den Rand ragt, zu dicht an einem anderen sitzt oder zu feine
  Stellen hat; herausfallende Inseln werden im Prüfbericht genannt.
- Kommandozeile: `--motive`, `--motiv-import DATEI`, `--motiv-entfernen ID`.
- Pakete können Motive über `motiv(...)` und `motive(...)` aus `pakete.py` nutzen.

## 1.5.1 – 2026-10-09

- Mac-App: Startet man Steckwerk direkt aus „Downloads“, zeigte das Fenster nach kurzer Zeit nur
  noch einen Fehler, weil macOS die temporäre Kopie der App entfernt hatte. Steckwerk läuft in
  diesem Fall jetzt im Vordergrund weiter und bietet die Installation erneut an.
- Eine laufende Steckwerk, die ihre Dateien nicht mehr findet, wird beim nächsten Start
  automatisch beendet und neu gestartet.

## 1.5.0 – 2026-10-09

- Neue Fahrzeuge: Tender, Personenwagen, Güterwagen, Bus und Traktor (große Hinterräder).
- Modell „Zug-Set“: Lok, Tender und bis zu 6 Wagen im Maßstab der Lok, Aufschrift je Fahrzeug.
- Kupplungslöcher in Front und Heck von Lok, Tender und Wagen (`kupplung`).
- Erweiterungspakete (`.swpaket`, Standard 1): laden in der App und per `--paket-installieren`,
  erstellen mit `--paket-neu`, `--paket-pruefen`, `--paket-packen`. Spezifikation in PAKETE.md,
  Beispielpaket „Türschild“.

## 1.4.0 – 2026-10-09

- Neues Modell Schwibbogen: Szene Dorf, Wald oder Kirche, 1–11 Kerzen, ausgeschnittene Fenster
  zum Hinterleuchten, Zierlinie auf dem Bogen, Text auf der Sockelleiste, Bodenplatte.

## 1.3.0 – 2026-10-09

- Acht neue Schmuckformen: Lebkuchenmann, Nikolausstiefel, Zuckerstange, Geschenk, Kerze, Engel,
  Tannenzapfen, Schneemann – mit gravierten Details; vier davon auch als 3D-Steckversion.

## 1.2.0 – 2026-10-09

- Gestaltung und Beschriftung: Fensterformen, Sprossen, Läden, Türschmuck, Giebel, Wand- und
  Dachgravuren, Zierleisten, Schilder mit Rahmen, sechs Schriftstile mit Kleinbuchstaben,
  Umlauten und Symbolen, automatischer Zeilenumbruch.
- Texte auf Briefkasten, Figurensockeln, Fahrzeugen und Schmuck; Zierlinien für Fahrzeuge.
- Weboberfläche mit aufklappbaren Gruppen und „Gestaltung würfeln“; Kommandozeile mit `-O`/`--options`.
- Mac-App erkennt ältere Versionen und bietet „Ersetzen“ an.

## 1.1.0 und früher

- Wichtelhaus, Serie, Zubehör, Christbaumschmuck, Schneeflocken und Steckfahrzeuge.
- Validator, Weboberfläche, Konfigurator und Mac-App.
