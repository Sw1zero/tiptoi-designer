# Tiptoi Zonen-Designer

Browser-Tool zum Platzieren von interaktiven Zonen auf einem Bild für eigene
Tiptoi-Lernspiele. Läuft komplett lokal im Browser, kein Server nötig.

## Nutzung

1. `index.html` öffnen (lokal per Doppelklick, oder gehostet z.B. über GitHub Pages)
2. Bild laden (Drag & Drop oder Dateiauswahl)
3. Auf das Bild klicken, um eine Zone zu setzen. Marker lassen sich per Drag verschieben.
4. Pro Zone: Label (kurz, sichtbar) und Erklärtext (wird später gesprochen) eintragen
5. "Layout als JSON herunterladen"

Die JSON-Datei enthält die exakten Pixelkoordinaten jeder Zone im
Originalbild — kein Schätzen, keine manuelle Koordinatensuche.

## Weiterverarbeitung zu einer echten Tiptoi-Datei

Braucht [tttool](https://github.com/entropia/tip-toi-reveng) (liegt in
diesem Projekt bereits unter `../demo/tttool-1.11/`), sowie `espeak` und
`oggenc` für die Sprachausgabe.

```
python3 build_project.py layout.json dein-bild.jpg ausgabe-ordner/
```

Erzeugt im Ausgabe-Ordner:
- `projekt.gme` — auf den Tiptoi-Stift kopieren
- `druckvorlage.png` — ausdrucken, mit den echten Punktcodes an den
  gesetzten Positionen

## Hinweise

- Produkt-ID im Designer-Formular: für Schule/privat 9000–9999 verwenden,
  nicht mit einem echten Tiptoi-Produkt kollidieren
- Testdruck machen und mit dem Stift probetippen, bevor eine ganze Auflage
  gedruckt wird — manche Drucker rastern die feinen Punktmuster schlecht
