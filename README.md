# Tiptoi Zonen-Designer

Browser-Tool zum Platzieren von interaktiven Zonen auf einem Bild für eigene
Tiptoi-Lernspiele. Läuft komplett lokal im Browser, kein Server nötig.

## Nutzung

1. `index.html` öffnen (lokal per Doppelklick, oder gehostet z.B. über GitHub Pages)
2. Bild laden (Drag & Drop oder Dateiauswahl) — wird automatisch in die A4-Seite
   eingepasst (contain-fit, Seitenverhältnis bleibt erhalten, kein Verzerren)
3. Auf das Bild klicken, um eine Zone zu setzen (rastet standardmässig am
   Raster ein). Marker lassen sich per Drag verschieben.
4. Pro Zone: Label (kurz, sichtbar) und Erklärtext (wird später gesprochen) eintragen
5. "Layout als JSON herunterladen"

Die Seite ist immer A4 bei 300dpi, unten fest eine Fussleiste mit
**Start / Wiederholen / Stopp** (plus ein reservierter, noch ungenutzter
vierter Platz für einen künftigen Modus-Button, siehe unten). Die JSON-Datei
enthält die exakten Pixelkoordinaten jeder Zone auf dieser Seite — kein
Schätzen, keine manuelle Koordinatensuche, unabhängig von der Pixelgrösse
des hochgeladenen Fotos.

### Geplant, noch nicht gebaut: Modus-Button

Ein vierter Button in der Fussleiste ist im Layout reserviert (sichtbar als
gestrichelter Platzhalter "MODUS (folgt)"), aber ohne Funktion. Die Idee:
pro Zone mehrere Inhalte (z.B. Erklärung / Wissens-Fakt / Spiel) hinterlegen
und per Tipp auf diesen Button umschalten — wie bei den originalen
Ravensburger-Büchern. Braucht einen grösseren Umbau des Datenmodells, kommt
als eigener Schritt, sobald klar ist, welche Modi tatsächlich gebraucht werden.

### Wie gross darf der Code sein?

Der gedruckte Punktcode ist ein kleines Motiv, das sich fein-periodisch über
die ganze gewählte Fläche wiederholt (deshalb liest der Stift auch bei einem
Tipp nicht exakt in der Mitte zuverlässig). Das heisst:

- **Jede Grösse funktioniert**, solange genug Auflösung da ist — getestet von
  5mm bis 80mm, keine festen Zwischenstufen nötig
- Für einen grösseren, grosszügigeren "Trefferbereich" einfach die Code-Grösse
  (mm) erhöhen — tttool kachelt das Motiv automatisch weiter, kein separates
  Raster-Feature nötig
- tttool verweigert die Erzeugung ("Dots too large"), wenn die effektive
  Auflösung unter ca. 210dpi fällt. `build_project.py` prüft das vorher und
  sagt dir direkt, wie viel du die Zielbreite verkleinern musst

## Weiterverarbeitung zu einer echten Tiptoi-Datei

Braucht [tttool](https://github.com/entropia/tip-toi-reveng) (liegt in
diesem Projekt bereits unter `../demo/tttool-1.11/`), sowie `espeak` und
`oggenc` für die Sprachausgabe.

```
python3 build_project.py layout.json dein-bild.jpg ausgabe-ordner/
```

Erzeugt im Ausgabe-Ordner:
- `projekt.gme` — auf den Tiptoi-Stift kopieren
- `druckvorlage.pdf` — zum Drucken verwenden, hat die korrekte physische
  Seitengrösse fest einprogrammiert. Bei 100% drucken, nicht "An Seite
  anpassen", sonst werden die Codes mitskaliert und unlesbar
- `druckvorlage.png` — gleiches Bild, falls du es weiterbearbeiten willst

## Hinweise

- Produkt-ID im Designer-Formular: für Schule/privat 9000–9999 verwenden,
  nicht mit einem echten Tiptoi-Produkt kollidieren
- Testdruck machen und mit dem Stift probetippen, bevor eine ganze Auflage
  gedruckt wird — manche Drucker rastern die feinen Punktmuster schlecht
