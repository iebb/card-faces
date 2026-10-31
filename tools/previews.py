#!/usr/bin/env python3
"""Render current collection previews using only published manifest entries."""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from validate import validate

ROOT = Path(__file__).resolve().parent.parent
FONT = "/System/Library/Fonts/Helvetica.ttc"
BACKGROUND = "#f3f0e9"
INK = "#183b30"
EXPANSION_DESIGNS = {
    ("cn/2900", "interconnect-10th-2025"),
    ("cn/1000", "china-70-reform-2019"),
    ("cn/5810", "first-issue-five-rams-2018"),
    ("cn/5840", "persimmons-good-fortune"),
    ("jp/suica", "welcome-sakura"),
    ("jp/icoca", "wind-thunder"),
    ("fr/la-carte", "tour-2024-yellow-jersey"),
    ("sg/ezlink", "singapore-skyline"),
}


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size)


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, width: int) -> None:
    size = 17
    while draw.textlength(text, font=font(size)) > width and size > 10:
        size -= 1
    draw.text(xy, text, font=font(size), fill=INK)


def thumbnail(design: dict, width: int) -> Image.Image:
    with Image.open(ROOT / design["file"]) as image:
        return image.convert("RGB").resize((width, width * 19 // 30), Image.Resampling.LANCZOS)


def sheet(items: list[tuple[dict, dict]], filename: str, title: str, columns: int, width: int) -> None:
    margin, gap, header = 24, 20, 104
    row_height = width * 19 // 30 + 62
    canvas = Image.new(
        "RGB",
        (margin * 2 + columns * width + (columns - 1) * gap, header + math.ceil(len(items) / columns) * row_height),
        BACKGROUND,
    )
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 20), title, font=font(30), fill=INK)
    draw.text((margin, 62), f"{len(items)} current choices / active published PNGs only", font=font(18), fill=INK)
    for index, (card, design) in enumerate(items):
        x = margin + index % columns * (width + gap)
        y = header + index // columns * row_height
        canvas.paste(thumbnail(design, width), (x, y))
        label(draw, (x, y + width * 19 // 30 + 8), f"{card['id']}/{design['id']}", width)
        name = design.get("name", {}).get("en", card["name"]["en"])
        label(draw, (x, y + width * 19 // 30 + 30), name, width)
    canvas.save(ROOT / "previews" / filename, optimize=True)


def comparisons(items: list[tuple[dict, dict]]) -> int:
    pairs = []
    for card, design in items:
        text_id = "text" if design["id"] == "default" else f"{design['id']}-text"
        alternative = next((item for item in card["designs"] if item["id"] == text_id), None)
        if alternative:
            pairs.append((card, design, alternative))
    width, gap, columns, margin, header = 240, 12, 3, 24, 104
    pair_width = width * 2 + gap
    row_height = width * 19 // 30 + 60
    canvas = Image.new(
        "RGB",
        (margin * 2 + pair_width * columns + gap * (columns - 1), header + math.ceil(len(pairs) / columns) * row_height),
        BACKGROUND,
    )
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 20), "Current artwork / text alternatives", font=font(30), fill=INK)
    draw.text((margin, 62), f"{len(pairs)} retained pairs / cleaned left, text right", font=font(18), fill=INK)
    for index, (card, clean, text) in enumerate(pairs):
        x = margin + index % columns * (pair_width + gap)
        y = header + index // columns * row_height
        canvas.paste(thumbnail(clean, width), (x, y))
        canvas.paste(thumbnail(text, width), (x + width + gap, y))
        label(draw, (x, y + width * 19 // 30 + 8), f"{card['id']}/{clean['id']}", pair_width)
    canvas.save(ROOT / "previews/text-free-comparison.png", optimize=True)
    return len(pairs)


def main() -> None:
    errors = validate(ROOT)
    if errors:
        raise SystemExit("\n".join(errors))
    manifest = json.loads((ROOT / "manifest.json").read_text())
    cleaned = [
        (card, design)
        for card in manifest["cards"]
        for design in card["designs"]
        if design["id"] != "text" and not design["id"].endswith("-text")
    ]
    sheet(cleaned, "text-free-all.png", "Current cleaned card faces", columns=5, width=260)
    sheet(
        [(card, design) for card, design in cleaned if card["region"] == "KR"],
        "korean-designs.png", "Current Korean transit designs", columns=3, width=360,
    )
    sheet(
        [(card, design) for card, design in cleaned if (card["id"], design["id"]) in EXPANSION_DESIGNS],
        "expansion-designs.png", "Retained researched card designs", columns=3, width=360,
    )
    count = comparisons(cleaned)
    print(f"Rendered four previews from {len(cleaned)} current choices and {count} text pairs.")


if __name__ == "__main__":
    main()
