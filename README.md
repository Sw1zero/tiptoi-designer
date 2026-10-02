# Tiptoi Zonen-Designer

Browser-Tool zum Platzieren von interaktiven Zonen auf einem Bild für eigene
Tiptoi-Lernspiele. Läuft komplett lokal im Browser, kein Server nötig.

## Nutzung

1. `index.html` öffnen (lokal per Doppelklick, oder gehostet z.B. über GitHub Pages)
2. Bild laden (Drag & Drop oder Dateiauswahl) — wird automatisch in die A4-Seite
   eingepasst (contain-fit, Seitenverhältnis bleibt erhalten, kein Verzerren)
3. **"+ Feld hinzufügen"** klicken — legt ein neues Feld an und aktiviert es
   automatisch zum Platzieren
4. Erklärtext fürs Feld eintragen (wird später per Sprachausgabe abgespielt)
5. Auf dem Raster die Stellen anklicken, die zu diesem Feld gehören sollen —
   beliebig viele, alle bekommen denselben Code und lösen denselben Text aus
   (z.B. mehrere gleichwertige Teile eines Diagramms). Nochmal auf eine
   bereits gesetzte Stelle klicken entfernt sie wieder. Eine Stelle, die
   schon zu einem anderen Feld gehört, lässt sich nicht überschreiben
6. "Fertig" klicken, nächstes Feld hinzufügen, wiederholen
7. "Layout als JSON herunterladen"

Jedes Feld bekommt automatisch eine Nummer (Feld 1, Feld 2, …) basierend auf
seiner Position in der Liste — kein manuelles Benennen nötig, und nach dem
Löschen eines Felds rücken die folgenden Nummern einfach nach.

Die Seite ist immer A4 bei 600dpi (Community-Erfahrung: 300dpi druckt die
Punktmuster zu grob/unzuverlässig, siehe "Druck-Tipps" unten), unten fest
eine Fussleiste mit
**Start / Wiederholen / Stopp** (plus ein reservierter, noch ungenutzter
vierter Platz für einen künftigen Modus-Button, siehe unten). Die JSON-Datei
enthält die exakten Pixelkoordinaten jeder Position auf dieser Seite — kein
Schätzen, keine manuelle Koordinatensuche, unabhängig von der Pixelgrösse
des hochgeladenen Fotos.

### Geplant, noch nicht gebaut: Modus-Button

Ein vierter Button in der Fussleiste ist im Layout reserviert (sichtbar als
gestrichelter Platzhalter "MODUS (folgt)"), aber ohne Funktion. Die Idee:
pro Feld mehrere Inhalte (z.B. Erklärung / Wissens-Fakt / Spiel) hinterlegen
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
  Auflösung unter ca. 210dpi fällt. `build_project.py` prüft das vorher
- `build_project.py` liest die dpi aus `layout.json` (Feld `pageDpi`) und
  wählt automatisch die grösstmögliche sichere Punktdicke dafür (`pixel-size`,
  Community-Erfahrung: dicker = zuverlässiger beim Drucken). Alte Exporte mit
  niedrigerer dpi bleiben dadurch gültig

### Druck-Tipps (Community-Erfahrung aus der tttool-Mailingliste)

- **Laserdrucker sind deutlich zuverlässiger als Tintenstrahler** — wenn
  verfügbar, bevorzugen
- Beim Drucken unbedingt **100%/Originalgrösse**, nie "An Seite anpassen"
  oder automatische Bildverbesserung des Druckertreibers
- Funktioniert ein Ausdruck nicht zuverlässig: zuerst einen Testdruck mit dem
  Stift prüfen, bevor eine ganze Auflage gedruckt wird
- Bei hartnäckigen Problemen: manche berichten von einem zweistufigen Druck
  (erst die Illustration, dann in einem zweiten Durchgang nur die Codes mit
  einem separaten Schwarzweiss-Laserdrucker) — für die meisten Fälle aber
  nicht nötig

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
  anpassen", sonst werden die Codes mitskaliert und unlesbar. Die Codes
  liegen unauffällig direkt auf dem Bild (echte Transparenz, kein weisser
  Kasten drumherum) — genau wie bei echten Tiptoi-Büchern
- `druckvorlage.png` — gleiches Bild, falls du es weiterbearbeiten willst
- `kontrolle-mit-markierungen.png` — **nur zur Kontrolle vor dem Drucken**,
  zeigt dieselben Stellen mit roten Kästen + "Feld N"-Beschriftung. Nicht
  drucken, nur zum Prüfen ob alles an der richtigen Stelle sitzt

## Hinweise

- Produkt-ID im Designer-Formular: für Schule/privat 9000–9999 verwenden,
  nicht mit einem echten Tiptoi-Produkt kollidieren
- Testdruck machen und mit dem Stift probetippen, bevor eine ganze Auflage
  gedruckt wird — manche Drucker rastern die feinen Punktmuster schlecht
