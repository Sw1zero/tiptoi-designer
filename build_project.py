#!/usr/bin/env python3
"""Baut aus layout.json (vom Zonen-Designer) + Originalbild eine Tiptoi-GME-Datei
und eine Druckvorlage mit echten OID-Codes.

ponytail: ein Script, kein Paket. tttool macht Codes+GME, wir machen nur das Compositing.

Wichtig: Der OID-Code wird von tttool in einer festen physischen Grösse (mm) bei
PRINT_DPI erzeugt und 1:1 (ohne Resize) eingefügt. Nachträgliches Skalieren würde
den Punktabstand verzerren und den Code für den Stift unlesbar machen.

Aufruf:
  python3 build_project.py layout.json bild.jpg ausgabe-ordner/
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

TTTOOL = Path(__file__).resolve().parent.parent / "demo" / "tttool-1.11" / "tttool"
MM_PER_INCH = 25.4
MIN_DPI = 210  # gemessen: tttool verweigert Codes unterhalb von ~201dpi ("Dots too large"), mit Marge


def build_yaml(data: dict) -> str:
    lines = [
        f"product-id: {data['productId']}",
        f"comment: {json.dumps(data.get('title', 'Tiptoi-Projekt'))}",
        "language: de",
        "",
        "speak:",
    ]
    for z in data["zones"]:
        text = z["text"].strip() or z["label"] or z["id"]
        lines.append(f"  {z['id']}: {json.dumps(text)}")
    lines.append("")
    lines.append("scripts:")
    for z in data["zones"]:
        lines.append(f"  {z['id']}: P({z['id']})")
    return "\n".join(lines) + "\n"


def paste_code(base: Image.Image, draw: ImageDraw.ImageDraw, code_path: Path,
                cx: int, cy: int, shape: str, label: str | None = None):
    code_img = Image.open(code_path).convert("RGBA")  # native Grösse, kein resize()
    w, h = code_img.size
    pad = max(4, w // 10)
    if shape == "square":
        box = [cx - w // 2 - pad, cy - h // 2 - pad, cx + w // 2 + pad, cy + h // 2 + pad]
        draw.rectangle(box, fill="white", outline="black", width=2)
    else:
        # Kreis muss die Diagonale des quadratischen Codes abdecken, sonst ragen die Ecken heraus.
        r = (w / 2) * 1.414 + pad
        box = [cx - r, cy - r, cx + r, cy + r]
        draw.ellipse(box, fill="white", outline="black", width=2)
    base.paste(code_img, (cx - w // 2, cy - h // 2), code_img)
    if label:
        draw.text((cx, box[3] + 4), label, fill="black", anchor="ma")


def main():
    if len(sys.argv) != 4:
        print(f"Aufruf: {sys.argv[0]} layout.json bild.jpg ausgabe-ordner/")
        sys.exit(1)

    layout_path = Path(sys.argv[1]).resolve()
    image_path = Path(sys.argv[2]).resolve()
    out_dir = Path(sys.argv[3]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(layout_path.read_text())

    if not data["zones"]:
        sys.exit("Keine Zonen im Layout — zuerst im Designer Zonen setzen.")

    code_size_mm = data.get("codeSizeMm", 25)
    shape = data.get("markerShape", "circle")
    target_width_mm = data.get("targetWidthMm", 200)
    # dpi des gesamten Projekts: wie viele Pixel im Designer-Bild einem Zoll beim Druck
    # entsprechen. Daraus leiten sich sowohl die Code-Erzeugung als auch die PDF-Seitengrösse
    # konsistent ab -- unabhängig von der tatsächlichen Pixelzahl des Originalbilds.
    dpi = round(data["imageWidth"] / target_width_mm * MM_PER_INCH)
    if dpi < MIN_DPI:
        max_width_mm = data["imageWidth"] / MIN_DPI * MM_PER_INCH
        sys.exit(
            f"Zielbreite {target_width_mm}mm ergibt nur {dpi}dpi — zu wenig, tttool braucht mindestens "
            f"{MIN_DPI}dpi für saubere Codes.\n"
            f"Entweder im Designer die Zielbreite auf höchstens {max_width_mm:.0f}mm verkleinern "
            f"(Bild wird dann kleiner gedruckt), oder ein höher aufgelöstes Originalbild verwenden."
        )

    yaml_text = build_yaml(data)
    yaml_path = out_dir / "projekt.yaml"
    yaml_path.write_text(yaml_text)
    print(f"geschrieben: {yaml_path}")

    gme_path = out_dir / "projekt.gme"
    subprocess.run([str(TTTOOL), "assemble", str(yaml_path), str(gme_path)], check=True, cwd=out_dir)
    print(f"geschrieben: {gme_path}")

    print(f"Projekt-DPI: {dpi} (aus Zielbreite {target_width_mm}mm für {data['imageWidth']}px)")
    subprocess.run(
        [str(TTTOOL), "--code-dim", str(code_size_mm), "--dpi", str(dpi), "--pixel-size", "1",
         "-f", "PNG", "oid-codes", str(yaml_path)],
        check=True, cwd=out_dir,
    )

    base = Image.open(image_path).convert("RGB")
    if (base.width, base.height) != (data["imageWidth"], data["imageHeight"]):
        print("Warnung: Bildgrösse weicht vom Designer-Export ab, skaliere nur die Positionen (nicht die Codes).")
        sx = base.width / data["imageWidth"]
        sy = base.height / data["imageHeight"]
    else:
        sx = sy = 1.0

    draw = ImageDraw.Draw(base)
    for z in data["zones"]:
        code_file = out_dir / f"oid-{data['productId']}-{z['id']}.png"
        cx, cy = int(z["x"] * sx), int(z["y"] * sy)
        paste_code(base, draw, code_file, cx, cy, shape, z.get("label"))

    start_file = out_dir / f"oid-{data['productId']}-START.png"
    start_w, _ = Image.open(start_file).size
    sx0, sy0 = 10 + start_w // 2, 10 + start_w // 2
    paste_code(base, draw, start_file, sx0, sy0, shape, "START")

    out_png = out_dir / "druckvorlage.png"
    base.save(out_png, dpi=(dpi, dpi))
    print(f"geschrieben: {out_png} ({base.width}x{base.height}px @ {dpi} dpi"
          f" = {base.width / dpi * MM_PER_INCH:.0f}x{base.height / dpi * MM_PER_INCH:.0f}mm)")

    out_pdf = out_dir / "druckvorlage.pdf"
    # resolution in DPI an save() ergibt bei PDF die physische Seitengrösse direkt aus den Pixeln,
    # keine nachträgliche Skalierung noetig.
    base.save(out_pdf, resolution=dpi)
    print(f"geschrieben: {out_pdf}")

    print("\nFertig. GME auf den Stift kopieren.")
    print("PDF in Originalgrösse (100%) drucken, NICHT 'An Seite anpassen' — sonst werden die Codes mitskaliert und unlesbar.")


if __name__ == "__main__":
    main()
