#!/usr/bin/env python3
"""Baut aus layout.json (vom Zonen-Designer) + Originalbild eine Tiptoi-GME-Datei
und eine fertige A4-Druckvorlage mit echten OID-Codes, inklusive Start/Wiederholen/Stopp.

ponytail: ein Script, kein Paket. tttool macht Codes+GME, wir machen nur das Compositing.

Seiten-Layout ist fix A4, die Aufloesung kommt aus layout.json ("pageDpi") --
dieselben mm-Konstanten wie in index.html, damit die im Designer geklickten
Positionen 1:1 auf der gedruckten Seite landen.

Wichtig: Der OID-Code wird von tttool in einer festen physischen Grösse (mm) erzeugt
und 1:1 (ohne Resize) eingefügt. Nachträgliches Skalieren würde den Punktabstand
verzerren und den Code für den Stift unlesbar machen. Das Originalfoto dagegen wird
ganz normal skaliert (contain-fit) -- das ist nur Dekoration, kein Code.

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
MIN_DPI = 210  # gemessen: tttool verweigert Codes unterhalb von ~201dpi ("Dots too large")
DEFAULT_PAGE_DPI = 600  # Fallback fuer alte layout.json ohne "pageDpi" (Designer schrieb frueher 300)

def safe_pixel_size(dpi: float) -> int:
    """Groesstmoegliche Punktdicke, die bei dieser dpi noch unter tttools
    'Dots too large'-Grenze bleibt (gemessen: ab ~201dpi bei pixel-size 1).
    Boldere Punkte sind laut Community-Erfahrung zuverlässiger beim Drucken,
    darum nicht einfach bei 1 bleiben, wenn die dpi mehr hergibt."""
    return max(1, min(4, int(dpi // 210)))


# Seiten-Layout in mm -- muss zu den Konstanten in index.html passen. Die dpi kommt
# zur Laufzeit aus layout.json (pageDpi), damit alte Exports gueltig bleiben, auch
# wenn der Designer inzwischen mit einer anderen Standard-Aufloesung arbeitet.
PAGE_W_MM, PAGE_H_MM = 210, 297
MARGIN_MM = 10
FOOTER_H_MM = 35
FOOTER_BUTTONS = ["START", "REPLAY", "STOP"]  # "Modus"-Slot folgt spaeter, hier bewusst weggelassen


def page_geometry(dpi: float) -> dict:
    mm = dpi / MM_PER_INCH
    content = {
        "x": MARGIN_MM * mm,
        "y": MARGIN_MM * mm,
        "w": (PAGE_W_MM - 2 * MARGIN_MM) * mm,
        "h": (PAGE_H_MM - 2 * MARGIN_MM - FOOTER_H_MM) * mm,
    }
    footer = {
        "x": MARGIN_MM * mm,
        "y": (PAGE_H_MM - MARGIN_MM - FOOTER_H_MM) * mm,
        "w": (PAGE_W_MM - 2 * MARGIN_MM) * mm,
        "h": FOOTER_H_MM * mm,
    }
    return {
        "page_w": round(PAGE_W_MM * mm),
        "page_h": round(PAGE_H_MM * mm),
        "content": content,
        "footer": footer,
    }


def fit_rect(content: dict, natural_w: float, natural_h: float) -> dict:
    scale = min(content["w"] / natural_w, content["h"] / natural_h)
    w, h = natural_w * scale, natural_h * scale
    return {
        "x": content["x"] + (content["w"] - w) / 2,
        "y": content["y"] + (content["h"] - h) / 2,
        "w": w, "h": h,
    }


def control_button_centers(footer: dict) -> list[dict]:
    n = len(FOOTER_BUTTONS) + 1  # +1 reservierter, leerer "Modus"-Slot, siehe index.html
    cy = footer["y"] + footer["h"] / 2
    return [
        {"label": label, "x": footer["x"] + footer["w"] * (i + 0.5) / n, "y": cy}
        for i, label in enumerate(FOOTER_BUTTONS)
    ]


def build_yaml(data: dict) -> str:
    fields = [f for f in data["fields"] if f["positions"]]  # Felder ohne Position ergeben keinen Sinn
    lines = [
        f"product-id: {data['productId']}",
        f"comment: {json.dumps(data.get('title', 'Tiptoi-Projekt'))}",
        "language: de",
        "",
        "speak:",
    ]
    for f in fields:
        text = f["text"].strip() or f["id"]
        lines.append(f"  {f['id']}: {json.dumps(text)}")
    lines.append("")
    lines.append("scripts:")
    for f in fields:
        lines.append(f"  {f['id']}: P({f['id']})")
    return "\n".join(lines) + "\n"


def paste_code(base: Image.Image, code_path: Path, cx: int, cy: int):
    """Echter Druck-Code: tttool liefert die Codes bereits mit Alpha-Transparenz
    (nur die Punkte selbst sind undurchsichtig). Direkt so übers Bild legen --
    kein weisser Kasten drumherum, genau wie bei echten Tiptoi-Büchern, wo die
    Codes unauffällig auf der bunten Illustration liegen."""
    code_img = Image.open(code_path).convert("RGBA")  # native Grösse, kein resize()
    w, h = code_img.size
    base.paste(code_img, (cx - w // 2, cy - h // 2), code_img)


def paste_code_debug(base: Image.Image, draw: ImageDraw.ImageDraw, code_path: Path,
                      cx: int, cy: int, label: str):
    """Nur für die Kontroll-Vorschau: Kasten + Beschriftung, damit man vor dem
    Drucken sieht, wo die Codes tatsächlich landen. Nicht die Druckvorlage!"""
    code_img = Image.open(code_path).convert("RGBA")
    w, h = code_img.size
    pad = max(4, w // 10)
    box = [cx - w // 2 - pad, cy - h // 2 - pad, cx + w // 2 + pad, cy + h // 2 + pad]
    draw.rectangle(box, outline="red", width=2)
    base.paste(code_img, (cx - w // 2, cy - h // 2), code_img)
    draw.text((cx, box[3] + 4), label, fill="red", anchor="ma")


def main():
    if len(sys.argv) != 4:
        print(f"Aufruf: {sys.argv[0]} layout.json bild.jpg ausgabe-ordner/")
        sys.exit(1)

    layout_path = Path(sys.argv[1]).resolve()
    image_path = Path(sys.argv[2]).resolve()
    out_dir = Path(sys.argv[3]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(layout_path.read_text())

    data["fields"] = [f for f in data["fields"] if f["positions"]]
    if not data["fields"]:
        sys.exit("Keine Felder mit Positionen im Layout — zuerst im Designer Felder anlegen und platzieren.")

    code_size_mm = data.get("codeSizeMm", 25)
    page_dpi = data.get("pageDpi", DEFAULT_PAGE_DPI)
    geo = page_geometry(page_dpi)

    if page_dpi < MIN_DPI:
        sys.exit(f"pageDpi ({page_dpi}) liegt unter dem von tttool verlangten Minimum ({MIN_DPI}).")

    yaml_text = build_yaml(data)
    yaml_path = out_dir / "projekt.yaml"
    yaml_path.write_text(yaml_text)
    print(f"geschrieben: {yaml_path}")

    gme_path = out_dir / "projekt.gme"
    subprocess.run([str(TTTOOL), "assemble", str(yaml_path), str(gme_path)], check=True, cwd=out_dir)
    print(f"geschrieben: {gme_path}")

    subprocess.run(
        [str(TTTOOL), "--code-dim", str(code_size_mm), "--dpi", str(page_dpi), "--pixel-size",
         str(safe_pixel_size(page_dpi)),
         "-f", "PNG", "oid-codes", str(yaml_path)],
        check=True, cwd=out_dir,
    )

    # A4-Seite aufbauen: weisser Hintergrund, Foto contain-gefittet in den Inhaltsbereich.
    artwork = Image.new("RGB", (geo["page_w"], geo["page_h"]), "white")
    photo = Image.open(image_path).convert("RGB")
    rect = fit_rect(geo["content"], photo.width, photo.height)
    resized = photo.resize((round(rect["w"]), round(rect["h"])), Image.LANCZOS)
    artwork.paste(resized, (round(rect["x"]), round(rect["y"])))

    positions = []  # [(code_file, x, y, label)], fuer beide Varianten gemeinsam genutzt
    for i, f in enumerate(data["fields"]):
        code_file = out_dir / f"oid-{data['productId']}-{f['id']}.png"
        label = f"Feld {i + 1}"
        for pos in f["positions"]:
            positions.append((code_file, int(pos["x"]), int(pos["y"]), label))
    for btn in control_button_centers(geo["footer"]):
        code_file = out_dir / f"oid-{data['productId']}-{btn['label']}.png"  # tttool-Sondernamen
        positions.append((code_file, round(btn["x"]), round(btn["y"]), btn["label"]))

    # Echte Druckvorlage: Codes unauffaellig direkt auf dem Bild, wie bei echten Tiptoi-Buechern.
    page = artwork.copy()
    for code_file, x, y, _ in positions:
        paste_code(page, code_file, x, y)

    out_png = out_dir / "druckvorlage.png"
    page.save(out_png, dpi=(page_dpi, page_dpi))
    print(f"geschrieben: {out_png} (A4 @ {page_dpi}dpi)")

    out_pdf = out_dir / "druckvorlage.pdf"
    page.save(out_pdf, resolution=page_dpi)
    print(f"geschrieben: {out_pdf}")

    # Nur zur Kontrolle vorm Drucken: dieselbe Seite mit roten Kaestchen + Beschriftung,
    # damit man sieht wo die Codes effektiv liegen. NICHT drucken/ausgeben.
    content, footer = geo["content"], geo["footer"]
    debug_page = artwork.copy()
    debug_draw = ImageDraw.Draw(debug_page)
    for code_file, x, y, label in positions:
        paste_code_debug(debug_page, debug_draw, code_file, x, y, label)
    debug_draw.rectangle([content["x"], content["y"], content["x"] + content["w"], content["y"] + content["h"]],
                          outline="#ccc", width=1)
    debug_draw.line([footer["x"], footer["y"], footer["x"] + footer["w"], footer["y"]], fill="#ccc", width=1)
    out_debug = out_dir / "kontrolle-mit-markierungen.png"
    debug_page.save(out_debug, dpi=(page_dpi, page_dpi))
    print(f"geschrieben: {out_debug} (nur zur Kontrolle, nicht drucken)")

    print("\nFertig. GME auf den Stift kopieren.")
    print("PDF in Originalgrösse (100%) drucken, NICHT 'An Seite anpassen' — sonst werden die Codes mitskaliert und unlesbar.")


if __name__ == "__main__":
    main()
