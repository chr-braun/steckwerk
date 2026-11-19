# Paket „Jahreszeiten“ – Arbeitsstand (Übergabe, 2026-11-19)

Wunsch von Christian: fünf sehr feine, filigrane, hochwertige Gravurmodelle passend zu den Jahreszeiten,
nur als Paket (kein Kerncode). Schwerpunkt Winter/Weihnachten.

## Fertig
- `_jz.py`: gemeinsame Werkzeuge (noch ungetestet): Polar-/Drehhelfer, Spitzenbogen-Rand, Tropfen, Öse,
  Materialstege, Leinwand → laserfestes Teil (über Grundlagen-Bibliothek `verzierungen`), `gravieren()`
  (Gravur nur auf sicherem Holz), `verdecken()` (überlappende Blätter), Text, Eiskristall, Zierstern,
  Tannenzweig mit Nadeln, Beere, Blattadern.

## Fehlt
- `paket.json` (id `jahreszeiten`, benoetigt `{"verzierungen": "2.0.0"}`, Gruppe „Jahreszeiten“), `LIES MICH.md`.
- Die fünf Modelle (geplant, je INFO + build, Pipeline wie spitzenschmuck.py im Paket weihnacht):
  1. `winterkranz` – runde Medaille: Spitzenbogenrand mit Tropfen-Durchbrüchen, gravierter Tannenkranz mit
     Beeren/Stechpalme, Bogenfries-Fenster, Mitte Eiskristall | Zierstern | Text, Öse.
  2. `eisblumen` – Fensterbild (Rundbogen/Spitzbogen/Rechteck): gravierter Rahmen, Eisblumen-Wedel als
     verzweigte Stege (Startwert), Rest ausgeschnitten.
  3. `bluetenmandala` (Frühling) – Blütenblätter-Ring und Kranz aus Blättern+Blüten | Tulpen | Kirschzweigen,
     Mitte Blüte | Schmetterling | Text, Adern graviert.
  4. `sommersonne` – Flammenstrahlen, Lorbeerkranz als Spitze, Mitte Guilloche | Sonnenblume (Phyllotaxis) | Text.
  5. `herbstkranz` – Ahorn- und Eichenblätter, Eicheln, Beeren überlappend (Adern graviert, verdeckt),
     Kranz offen oder Medaille mit Text.
- Einträge: `paketquellen/bereiche.json` (Bereich „feste“), `themen.json`, `packaging/webseite.py`,
  `tests/test_pakete_abhaengig.py` (ALLE), `docs/wiki/Pakete.md`, Vorschaubilder (`packaging/vorschaubilder.py`).
- Tests `tests/test_jahreszeiten.py` (Muster: tests/test_christbaumschmuck.py, assert_cut_ready, 2/3/4 mm).

## Recherche (kleines Modell, nur Inspiration)
Mandala/Mehrlagig und runde Medaillen mit Kranz dominieren; Winter: Tannenkranz-Medaille mit Flocke,
Spitzen-Untersetzer, Sternenkarte; Frühling: botanische Blüten mit feinen Linien, Schmetterling;
Sommer: Sonne mit Strahlen und Blattranke, Blatt-Mandala; Herbst: Ahornblatt mit Adern, Blätterkranz, Eicheln.
