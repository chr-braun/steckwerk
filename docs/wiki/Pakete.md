# Pakete

Mit Paketen kommen neue Modelle in Steckwerk, ohne die App neu zu installieren. Ein Paket ist eine
**`.swpaket`**-Datei (ein ZIP mit Ordner). Ältere `.lfpaket`-Dateien aus Laserforge-Zeiten funktionieren
weiter. Die vollständige Spezifikation steht in [PAKETE.md](https://github.com/chr-braun/steckwerk/blob/main/PAKETE.md) im Repo.

## Laden

- In der App: Einstellungen → **Pakete**. Dort siehst du jedes installierte Paket mit Beschreibung und
  seinen Modellen, und darunter alles, was es im Update-Kanal noch gibt – mit **Installieren**-Knopf.
  Eigene Dateien gehen über **Paket laden …**.
- Kommandozeile: `python3 cli.py --paket-installieren datei.swpaket`, `--pakete`, `--paket-entfernen ID`.

![Einstellungen → Pakete: installierte Pakete und der Update-Kanal mit Installieren-Knopf](medien/steckwerk-2.6-paketkatalog.png)

Beim Installieren wird jedes Modell mit Standardwerten gebaut und geprüft. Nur ein komplett
schnittfertiges Paket wird übernommen. „Grundlagen“ kommt automatisch mit.

> Pakete enthalten Python-Code, der mit deinen Rechten läuft. Lade nur Pakete aus Quellen, denen du
> vertraust.

## Unsere Pakete

Seit Steckwerk 2.6.0 gibt es **ein Paket je Thema**. Alte Einzelpakete räumt Steckwerk beim Installieren
selbst weg (Spalte „ersetzt“). Die Pakete sind in **Bereiche** geordnet; so stehen sie auch im Paketkatalog
der App, auf der [Webseite](https://chr-braun.github.io/steckwerk/) und im README.

| Bereich | Paket (ID) | Version | Was drin ist | ersetzt |
|---|---|---|---|---|
| Feste und Jahreszeiten | **Weihnachten** (`weihnacht`) | 2.2.0 | Edler **Christbaumschmuck** (zwölf Anhänger in Scherenschnitt-Qualität), **Namensanhänger** in echter Schreibschrift, Zierschlitten mit Schnörkelkufen, Steckkrippe (Stall und Figuren), Familien- und Weihnachtsanhänger, **Spitzenschmuck** (mit Muster-Rezepten und Zufallsmustern), **Scherenschnitt-Medaillon**, **Kristall-Schneeflocken**. Filigranes am besten mit den Profilen 1,5 / 2 mm. | Weihnachtsdeko, Filigran |
| | **Wichtel** (`wichtel`) | 1.1.0 | **Figur:** Schicht-Wichtel aus vier Lagen zum Bemalen. **Haus:** Wichteltür, Wichtelfenster. **Möbel:** Bank, Tisch mit Hockern, Bett. **Zubehör:** Leiter, Wegweiser, Wäscheleine. **Wichtelzimmer** auf Knopfdruck. **Wichtelmarkt:** Lebkuchenstand, Kreidetafel, Backstube, Briefkasten, Gartenzaun, Werkbank, Wegelaterne. **Edles Zubehör:** Kamin mit Zierblende, Feuer und Strümpfen mit Namen, Standuhr, Schaukelstuhl, Christbaum mit Geschenken, Schneemann, Wichtelgarten. Alles im selben Wichtel-Maßstab. | Wichtelmöbel, Wichteltür, Wichtelzubehör, Wichtelwelt, Wichtelfiguren |
| | **Halloween** (`halloween`) | 1.4.0 | Spukschloss im gotischen Bogen, Kürbislaterne, Grabstein mit Gespenst, Anhänger-Set aus der Motiv-Bibliothek, Spinnennetz, Skelett (Hampelmann), Fledermausgirlande, Süßigkeitenschale. | – |
| Zuhause und Geschenke | **Wohnen** (`wohnen`) | 1.0.0 | **Bilderrahmen** (9 × 13 bis 15 × 20 cm oder eigenes Maß, schlicht oder filigran, mit Sockel oder Schlüsselloch), **Zierrahmen** mit Schild und graviertem Text, **Türschild** mit Namen. | Umrandungen, Türschild |
| | **Schmuck** (`schmuck`) | 1.0.0 | **Ohrhänger** als Paar: Lotusblüte, Flügel, Tropfen, Mond, Sonne, Wolke, Raute, Waben, Regenbogen, Fächer – durchbrochen, als Rahmen oder graviert, auf Wunsch mit Zwischenteil. | – |
| | **Mehrlagig** (`ebenen`) | 1.2.0 | **Ebenenbild**: Schattenbox mit 3–6 Lagen (Winterwald, Winterdorf, Spukschloss, Weihnachtsnacht). **Ebenenmotiv**: Motiv aus drei Lagen mit Steckstiften. **Aufsteckdeko**: Motive als Kantenreiter, Zapfen, Öse oder Spieß. | – |
| Spielen und Bewegen | **Spiele** (`spiele`) | 1.1.0 | Mühle, Tic-Tac-Toe, Vier in einer Reihe, Kugellabyrinth, Solitär und das **Puzzle**: Bilderpuzzle mit Nasen, rechteckig oder rund, 4–200 Teile, mit detailreichen Szenen, eigenem Motiv/Logo oder Foto, auf Wunsch mit Rahmen. | – |
| | **Bewegung** (`bewegung`) | 1.0.0 | Hampelmann (Wichtel, Weihnachtsmann, Rentier, Schneemann, Skelett), Kurbeltier mit Nocken, Turner-Affe, Kreisel, Balancier-Vogel. | – |
| Formen und Kunst | **Formen** (`formen`) | 1.0.0 | **Steckkörper** (Kugel, Ei, Zwiebelturm, Tanne aus gekreuzten Rippen), **Wellenfläche** als Gitter, gedrehte **Stapelvase**. | – |
| Laden und Markt | **Verkauf** (`verkauf`) | 1.0.0 | **Flaschenschild**: Preisschild für den Flaschenhals mit Logo, Preis inkl. MwSt. und Grundpreis je Liter, auch als ganze Preisliste. | – |
| Basis | **Grundlagen** (`verzierungen`) | 2.0.1 | Die Basis für alle anderen Pakete. **Zierstück** und **Zierleiste** mit Rosetten, Ecken, Ranken, Bordüren, Schleifen und Zweigen; **Passungstest**: Kamm mit Schlitzen in verschiedenen Breiten, unter dem Schlitz, in dem das Probestück satt sitzt, steht dein Kerf. Dazu die Ornament-Bibliothek, die alle Pakete nutzen. Kommt automatisch mit. | Verzierungen, Werkstatt |

Die Paketdateien liegen im Update-Kanal (Branch `updates`); in der App installierst du sie mit einem Klick.
Jedes `.swpaket` enthält den kompletten Quellcode – zum Ändern einfach entpacken. Die Quellen stehen auch im
Repo unter `paketquellen/`.

### Bereiche

Welches Paket in welchem Bereich steht, regelt eine einzige Datei: `paketquellen/bereiche.json` (Bereich mit
Namen, englischem Namen, Kurztext und den Paket-ids in Reihenfolge). Der Release-Workflow schreibt die Bereiche in
den Update-Kanal; ab Steckwerk 2.13.0 gruppieren die Browser-App und Steckwerk Desktop den Paketkatalog danach,
ältere Versionen zeigen weiter die einfache Liste. Ein neues Themenpaket bekommt dort seinen Platz, sonst steht
es in der App am Ende ohne Bereich. Ein Test prüft, dass jedes Paket aus `paketquellen/` genau einem Bereich
zugeordnet ist.

## Vorschau

### Mehrlagig

![Mehrlagig 1.0](medien/mehrlagig-1.0.png)

![Mehrlagig 1.1 – neue Motive](medien/mehrlagig-1.1-neu.png)

### Weihnachten

![Weihnachten: Krippe und Schlitten](medien/weihnachtsdeko-krippe-schlitten.png)

![Weihnachten: Anhänger](medien/weihnachtsdeko-anhaenger.png)

![Weihnachten: Spitzenschmuck, Medaillon, Kristallflocke](medien/filigran-vorschau.png)

![Weihnachten: Muster-Rezepte und Zufallsmuster](medien/filigran-1.1-rezepte.png)

### Spiele: Puzzle

![Spiele 1.1 – Puzzle](medien/spiele-1.1-puzzle.png)

### Halloween

![Halloween 1.2](medien/halloween-1.2-vorschau-1.png)

![Halloween 1.2](medien/halloween-1.2-vorschau-2.png)

### Grundlagen

![Grundlagen: Zierstücke und Zierleisten](medien/verzierungen-1.0-vorschau.png)

![Grundlagen: Passungstest](medien/werkstatt-1.0-passungstest.png)

### Wohnen

![Wohnen: Bilderrahmen und Zierrahmen](medien/umrandungen-1.0-vorschau.png)

### Wichtel

![Wichtel: Möbel](medien/wichtelmoebel-1.0-vorschau.png)

![Wichtel: Tür](medien/wichteltuer-1.0-vorschau.png)

![Wichtel: Zubehör](medien/wichtelzubehoer-1.0-vorschau.png)

![Wichtel: Schicht-Wichtel bemalt, vier Varianten](medien/wichtelfiguren-1.0-bemalt.png)

![Wichtel: Schicht-Wichtel, die Teile zum Lasern](medien/wichtelfiguren-1.0-teile.png)

![Wichtel: Wichtelzimmer mit Schicht-Wichtel](medien/wichtelwelt-1.1-zimmer.png)

![Wichtelmarkt: Lebkuchenstand mit Ware](medien/wichtel-1.0-lebkuchenstand.png)

![Wichtelmarkt: Backstube](medien/wichtel-1.0-backstube.png)

![Wichtelmarkt: Werkbank mit Werkzeug](medien/wichtel-1.0-werkbank.png)

![Wichtelmarkt: Wegelaterne, Kreidetafel, Briefkasten, Gartenzaun](medien/wichtel-1.0-markt.png)

### Wichtel-Maßstab

Jedes Wichtel-Modell hat oben die Auswahl **Maßstab**. Bei „passend zur Wichtelgröße“ gibst du nur die
Höhe deiner Wichtelfigur an (Standard 70 mm, wie die Wichtelfigur in Steckwerk), und alle Maße richten sich
danach. So passen Tür, Möbel und Zubehör zusammen. Bei „eigene Maße“ stellst du alles selbst ein.
Dickeres Holz braucht größere Wichtel: Bei 4 mm ab etwa 60 mm, bei 5 mm ab etwa 75 mm. Steckwerk sagt dir
die genaue Grenze.

## Eigenes Paket bauen

Schritt für Schritt mit Beispielcode erklärt es auch die Webseite: [Pakete bauen](https://chr-braun.github.io/steckwerk/pakete-bauen.html).

```bash
python3 cli.py --paket-neu krippe --out meine-pakete        # Vorlage mit Beispielmodell
python3 cli.py --paket-pruefen meine-pakete/krippe          # bauen + prüfen
python3 cli.py --paket-packen meine-pakete/krippe --out .   # → krippe-1.0.0.swpaket
```

Ein Paket besteht aus `paket.json` (id, name, version, modelle, optional `steckwerk`-Mindestversion,
`name_en`/`beschreibung_en`) und je Modell einer Python-Datei mit `INFO` (Formular) und `build(cfg, …)`.
Englische Texte kommen über ein `UEBERSETZUNG`-Wörterbuch. Seit 2.5.0 kann ein Paket alte Pakete
ablösen: `"ersetzt": ["altes_paket"]` räumt sie beim Installieren weg. Seit 2.4.0 kann ein Paket andere Pakete
nutzen: `"benoetigt": {"verzierungen": "1.0.0"}` in der `paket.json`, dann im Code
`Z = pakete.bibliothek("verzierungen")` – so stehen alle Ornamente und Steck-Werkzeuge zur Verfügung. Bei jeder Änderung die Version erhöhen und
über den [Update-Kanal](Updates.md) veröffentlichen.

## Was wir beim Bauen gelernt haben

Die aufwendigen Pakete (Mehrlagig, Weihnachten, Halloween) zeichnen Figuren als Plus/Minus-
Formen, rastern sie und machen daraus wieder saubere, laserfeste Konturen. Stolperfallen dabei:

- Ein Schnittschlitz über die ganze Breite teilt das Teil, und das kleinere Stück verschwindet still.
- Sehr dünne Überlappungen (unter ca. 1,3 mm) werden aufgemacht.
- Große Ebenenbilder (ca. 300 mm) brauchen etwa eine Minute zum Rechnen.
- Der Engel wirkt in kleinen Größen schwächer.
