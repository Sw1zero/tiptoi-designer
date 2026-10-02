#!/usr/bin/env python3
"""Baut aus layout.json (vom Zonen-Designer) + Originalbild eine Tiptoi-GME-Datei
und eine Druckvorlage mit echten OID-Codes.

ponytail: ein Script, kein Paket. tttool macht Codes+GME, wir machen nur das Compositing.

Aufruf:
  python3 build_project.py layout.json bild.jpg ausgabe-ordner/
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

TTTOOL = Path(__file__).resolve().parent.parent / "demo" / "tttool-1.11" / "tttool"


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

    yaml_text = build_yaml(data)
    yaml_path = out_dir / "projekt.yaml"
    yaml_path.write_text(yaml_text)
    print(f"geschrieben: {yaml_path}")

    gme_path = out_dir / "projekt.gme"
    subprocess.run([str(TTTOOL), "assemble", str(yaml_path), str(gme_path)], check=True, cwd=out_dir)
    print(f"geschrieben: {gme_path}")

    subprocess.run([str(TTTOOL), "--code-dim", "20", "-f", "PNG", "oid-codes", str(yaml_path)],
                    check=True, cwd=out_dir)

    base = Image.open(image_path).convert("RGB")
    if (base.width, base.height) != (data["imageWidth"], data["imageHeight"]):
        print("Warnung: Bildgrösse weicht vom Designer-Export ab, skaliere Koordinaten.")
        sx = base.width / data["imageWidth"]
        sy = base.height / data["imageHeight"]
    else:
        sx = sy = 1.0

    draw = ImageDraw.Draw(base)
    for z in data["zones"]:
        code_file = out_dir / f"oid-{data['productId']}-{z['id']}.png"
        code_img = Image.open(code_file).convert("RGBA")
        size = int(z["size"] * sx)
        code_img = code_img.resize((size, size))
        cx, cy = int(z["x"] * sx), int(z["y"] * sy)
        pad = max(4, size // 10)
        box = [cx - size // 2 - pad, cy - size // 2 - pad, cx + size // 2 + pad, cy + size // 2 + pad]
        draw.ellipse(box, fill="white", outline="black", width=2)
        base.paste(code_img, (cx - size // 2, cy - size // 2), code_img)
        if z.get("label"):
            draw.text((cx, box[3] + 4), z["label"], fill="black", anchor="ma")

    start_code = Image.open(out_dir / f"oid-{data['productId']}-START.png").convert("RGBA")
    start_size = max(80, base.width // 12)
    start_code = start_code.resize((start_size, start_size))
    sx0, sy0 = 10, 10
    draw.rectangle([sx0 - 4, sy0 - 4, sx0 + start_size + 4, sy0 + start_size + 4], fill="white", outline="black", width=2)
    base.paste(start_code, (sx0, sy0), start_code)
    draw.text((sx0, sy0 + start_size + 4), "START", fill="black", anchor="la")

    out_image = out_dir / "druckvorlage.png"
    base.save(out_image)
    print(f"geschrieben: {out_image}")
    print("\nFertig. GME auf den Stift kopieren, Druckvorlage ausdrucken und testen.")


if __name__ == "__main__":
    main()
