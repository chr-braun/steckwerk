# Bedienung

## Oberfläche (Mac-Stil, überarbeitet in Oberfläche 3)

![Steckwerk hell](medien/oberflaeche-hell.png)


![Steckwerk dunkel](medien/oberflaeche-dunkel.png)


Die Weboberfläche sieht aus wie eine Mac-App, hell oder dunkel wie dein System, und lädt nichts aus dem
Internet.

- **Seitenleiste links (Steckwerk Desktop):** oben ein Suchfeld, darunter **Alle Vorlagen**, **Zuletzt** mit
  deinen Projekten und die sechs **Bereiche** mit Anzahl. Ein Klick zeigt rechts die **Galerie**: jede Vorlage
  als Kachel mit Vorschaubild der Platte, nach Themen gegliedert (bei einem Bereich mit mehreren Themen oben
  filterbar); ein Klick auf die Kachel öffnet sie. In der **Bibliothek** liegen *Motive und Fotos* und
  *Pakete*. Unten steht **Einstellungen** mit Material und Updates (und der Zahl neuer Updates).
- **Werkzeugleiste oben:** Projekt- oder Vorlagenname, das **Material-Menü** und der Hauptknopf
  **An xTool senden** (im reinen Browser *Exportieren …*).
- **Mitte:** maßstäbliche Vorschau je Platte mit mm-Lineal. Holz = Restplatte, hell = Teile, blau = Gravur.
  Bei mehreren Platten wählst du oben im Umschalter.
- **Statusleiste unten:** grün *Schnittfertig* oder rot *Fehler* (Klick öffnet den Prüfbericht), Teile und
  Platten mit Ausnutzung, die geschätzte Laserzeit (mit Preis je Platte auch die Materialkosten) und die Datei.
- **Inspektor rechts:** die Werte der Vorlage in *Größe*, *Ausstattung*, *Motive* und *Gestaltung*.
  *Zurücksetzen* stellt alles auf Standard, *Überrasch mich* würfelt die Gestaltung. Bei Texten fügen die
  Knöpfe ♥ ★ ❄ 🎄 Symbole ein, `|` macht eine neue Zeile. Hier sitzt auch der [Assistent](KI-Funktionen.md).
- **Einstellungen (⌘,):** Material, Pakete, Motive, Updates, Assistent und Allgemein (Sprache,
  hell/dunkel, Live-Vorschau).

## An xTool senden (⌘E)

Das Ausgeben-Blatt bietet zwei Wege:

- **In xTool Creative Space öffnen** (empfohlen): speichert die Platte als `.xcs` mit den Ebenen
  *Schneiden* (rot) und *Ritzen* (blau) für den xTool M2 und öffnet sie direkt in XCS.
- **Dateien sichern:** alles als ZIP, nur die gezeigte Platte als SVG oder in den Steckwerk-Ordner.
  Auf Wunsch kommen ein **XCS-Projekt (.xcs)** und ein **xTool-Studio-Projekt (.xs)** ab Version 1.7
  dazu (Leistung, Tempo und Durchgänge sind dort schon eingetragen).

Für beide Wege gibt es die Schalter **Teilenummern klein eingravieren** und **Montageanleitung als PDF**
(Blattübersicht, nummerierte Teile, Teileliste, Zusammenbau). Darunter stehen Laserzeit, Schnitt- und
Ritzlänge, Platten und Ausnutzung, mit Preis je Platte (Einstellungen → Material) auch die Materialkosten.
Ist ein Materialprofil aktiv, zeigt *Laserwerte für dieses Material* die Startwerte für XCS.

> Die xTool-Formate sind nicht offen dokumentiert. Beim ersten Mal kurz prüfen, ob Ebenen und Werte in XCS stimmen.

## Prüfbericht

Ein Klick auf den Status unten öffnet den Prüfbericht: ein Satz zum Ergebnis, die **Teiletabelle** mit
Nummer (dieselbe wie bei den gravierten Teilenummern), Name, Größe und Prüfergebnis, dann der
**Zusammenbau** Schritt für Schritt. Die einzelnen Prüfzeilen des Validators stehen eingeklappt unter
*Technische Details* und gehen bei Fehlern von selbst auf.

## Projekte

Ein Projekt merkt sich Vorlage, alle Werte und das Material unter einem Namen, z. B. „Wichtelhaus Oma“.
**⌘S** sichert (beim ersten Mal mit Namen), die letzten Projekte stehen oben in der Seitenleiste unter
*Zuletzt* und öffnen sich mit einem Klick. *Verwalten* bzw. *Alle* zeigt die ganze Liste mit Löschen.
Ändert man danach etwas, steht unter dem Titel *geändert*. Die Projekte liegen in `~/.steckwerk/projekte.json`
und gelten für Browser-Oberfläche, Mac-App und Steckwerk Desktop gemeinsam.

## Teilenummern

**Teilenummern klein eingravieren** (im Ausgeben-Blatt oder unter Einstellungen → Material) schreibt jedem
Teil eine kleine Nummer auf, an die Stelle mit dem meisten Platz. Die Nummern passen zu Prüfbericht und
Montageanleitung und werden wie alles andere geprüft. Sehr schmale Teile bleiben ohne Nummer, stehen aber
in der Teileliste.

## Tastenkürzel

![Prüfbericht](medien/pruefbericht.png)



| Kürzel | Wirkung |
|---|---|
| ⌘, | Einstellungen |
| ⌘E | An xTool senden / Exportieren |
| ⌘S | Projekt sichern (⇧⌘S: als neues Projekt) |
| ⌘↩ | Vorschau berechnen (wenn Live-Vorschau aus ist) |
| ⌘K / ⌘F | Modell suchen |
| Esc | Fenster schließen |

## Sprache

Deutsch und Englisch (seit 2.0.0), umschaltbar unter Einstellungen → Allgemein. Formular, Prüfbericht,
Montagehinweise, Fehlermeldungen und Update-Hinweise wechseln mit. Die Mac-Dialoge folgen der
Systemsprache, die Kommandozeile bleibt deutsch.

## Weboberfläche starten

```bash
python3 webui.py                 # http://127.0.0.1:8765
python3 webui.py --port 9000     # anderer Port
python3 webui.py --lan           # im Heimnetz, z. B. vom Tablet am Laser (ohne Passwort!)
python3 webui.py --out ~/laser   # Ordner für „In Ordner speichern“
```

## Konfigurator im Terminal

`python3 cli.py --konfigurator` fragt Modell, Maße, Optionen, Material und Ausgabeordner ab und zeigt am
Ende den passenden Kommandozeilen-Befehl.

## Kommandozeile

```bash
python3 cli.py --model wichtelhaus --out out
python3 cli.py --model serie --count 5 --seed 42        # Serie, reproduzierbar über den Seed
python3 cli.py --model ornament --options               # alle Gestaltungsoptionen eines Modells
python3 cli.py --model schwibbogen -O szene=kirche -O kerzen=9 -O "text=Glück auf!"
python3 cli.py --model zug -O wagen=3 -O "text=Polar,,Post,Nordpol"
python3 cli.py --model wichtelhaus --validate          # nur prüfen, nichts schreiben
python3 cli.py --check-svg datei.svg                    # fertige SVG prüfen
```

Jede Gestaltungsoption setzt du mit `-O NAME=WERT`. Die vollständige Liste steht im README unter
„Alle Optionen“.
