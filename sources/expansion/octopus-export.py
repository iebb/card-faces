#!/usr/bin/env python3
"""Optimize native Octopus masters and add verified labels deterministically.

Large native masters remain outside this repository. Pass their three paths
and an external output directory; copy the six resulting PNGs into both
sources/hk/octopus/ and faces/hk/octopus/ before the scoped repository build.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from build import build_face  # noqa: E402
from validate import inspect_face  # noqa: E402

DEFAULT_LATIN_FONT = "/System/Library/Fonts/Helvetica.ttc"
DEFAULT_CHINESE_FONT = "/System/Library/Fonts/STHeiti Light.ttc"
TEXT_LAYOUT = {
    "header": {
        "runs": [["八達通", 52], ["Octopus", 60]],
        "gap": 16,
        "left": 54,
        "top": 56,
    },
    "child": {
        "runs": [["小童", 38], ["Child", 40]],
        "gap": 12,
        "right": 1148,
        "top": 669,
    },
    "elder": {
        "runs": [["長者", 38], ["Elder", 40]],
        "gap": 12,
        "right": 1148,
        "top": 669,
    },
}


def label_mask(layout: dict, latin: str, chinese: str) -> Image.Image:
    """Render exact strings with four coverage levels for a compact palette."""
    scale = 4
    runs = []
    for text, size in layout["runs"]:
        font = ImageFont.truetype(chinese if ord(text[0]) > 127 else latin, size * scale, index=0)
        bounds = font.getbbox(text)
        glyph = Image.new("L", (bounds[2] - bounds[0], bounds[3] - bounds[1]))
        ImageDraw.Draw(glyph).text((-bounds[0], -bounds[1]), text, font=font, fill=255)
        runs.append(glyph)
    gap = layout["gap"] * scale
    width = sum(run.width for run in runs) + gap * (len(runs) - 1)
    height = max(run.height for run in runs)
    label = Image.new("L", (width, height))
    x = 0
    for run in runs:
        label.paste(run, (x, (height - run.height) // 2))
        x += run.width + gap
    label = label.resize((round(width / scale), round(height / scale)), Image.Resampling.LANCZOS)
    coverage = np.asarray(label, dtype=np.uint16)
    coverage = (np.rint(coverage / 255 * 4) * 255 / 4).astype(np.uint8)
    mask = Image.new("L", (1200, 760))
    left = layout.get("left", layout.get("right", 0) - label.width)
    mask.paste(Image.fromarray(coverage), (left, layout["top"]))
    return mask


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("adult", "child", "elder"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--latin-font", default=DEFAULT_LATIN_FONT)
    parser.add_argument("--chinese-font", default=DEFAULT_CHINESE_FONT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    header = label_mask(TEXT_LAYOUT["header"], args.latin_font, args.chinese_font)
    exports = {}
    for design, source in (("default", args.adult), ("child", args.child), ("elder", args.elder)):
        clean = args.output / f"{design}.png"
        build_face(source, clean, denoise=False)
        # Normalize the palette order so scoped rebuilds are byte-identical.
        canonical = args.output / f"{design}-canonical.png"
        build_face(clean, canonical, denoise=False)
        canonical.replace(clean)
        with Image.open(clean) as image:
            image = image.convert("RGB")
        if image.size != (1200, 760):
            raise SystemExit("The verified text layout requires a 1200x760 optimized base.")
        image.paste((255, 255, 255), mask=header)
        if design in ("child", "elder"):
            image.paste((255, 255, 255), mask=label_mask(TEXT_LAYOUT[design], args.latin_font, args.chinese_font))
        raw = args.output / f"{design}-lettered-master.png"
        image.save(raw)
        text_id = "text" if design == "default" else f"{design}-text"
        build_face(raw, args.output / f"{text_id}.png", denoise=False)
        raw.unlink()
        for name in (design, text_id):
            exports[name] = inspect_face(args.output / f"{name}.png")
    print(json.dumps(exports, indent=2))


if __name__ == "__main__":
    main()
