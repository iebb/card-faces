#!/usr/bin/env python3
"""Build palette PNG card faces from sources/ and regenerate manifest.json.

Each source is cover-cropped to 30:19, median-filtered, quantized without
dithering, has near-identical palette entries merged and isolated stray pixels
removed, then compressed. The largest size that stays within the colour and
byte budgets wins. pngquant and optipng are used when installed.

    python3 tools/build.py            # rebuild every face
    python3 tools/build.py shanghai   # rebuild selected slugs, keep the rest
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import MAX_BYTES, MAX_COLORS, ROOT, SCHEMA_VERSION, inspect_face, validate  # noqa: E402

WIDTHS = [1200, 1140, 1080, 1020, 960, 900, 840, 780, 720, 660, 600]
COLOR_STEPS = [MAX_COLORS, 20, 16]
# Generated artwork has faint noise in flat fields; pngquant spends palette
# slots on those shades, which turns flat areas into incompressible speckle.
MERGE_DISTANCE = 16
SOURCE_SUFFIXES = (".webp", ".png", ".jpg", ".jpeg")


def cover(image: Image.Image, width: int) -> Image.Image:
    height = width * 19 // 30
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def quantize(image: Image.Image, colors: int, workdir: Path) -> tuple[np.ndarray, list[int]]:
    if shutil.which("pngquant"):
        src, dst = workdir / "in.png", workdir / "q.png"
        image.save(src)
        subprocess.run(
            ["pngquant", "--nofs", "--speed", "1", "--force", "--output", str(dst), str(colors), str(src)],
            check=True,
        )
        quantized = Image.open(dst)
        quantized.load()
    else:
        quantized = image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return np.array(quantized, dtype=np.uint8), quantized.getpalette()[: 3 * 256]


def merge_similar(indices: np.ndarray, palette: list[int], distance: float = MERGE_DISTANCE) -> np.ndarray:
    """Fold palette entries within `distance` (RGB) into the more common one."""
    colors = np.array(palette, dtype=float).reshape(-1, 3)
    counts = np.bincount(indices.ravel(), minlength=len(colors))
    remap = np.arange(len(colors))
    kept: list[int] = []
    for index in np.argsort(-counts, kind="stable"):
        if counts[index] == 0:
            continue
        match = next((k for k in kept if np.linalg.norm(colors[index] - colors[k]) < distance), None)
        if match is None:
            kept.append(index)
        else:
            remap[index] = match
    return remap[indices].astype(np.uint8)


def despeckle(indices: np.ndarray, passes: int = 2) -> np.ndarray:
    """Recolour isolated pixels and isolated pixel pairs.

    A pixel is stray when none of its 8 neighbours share its colour, or when its
    only same-coloured neighbour is stray in the same way. Line ends always join
    a pixel with two matches, so lines and text keep their length while lone
    anti-aliasing pixels take the dominant neighbouring colour.
    """
    height, width = indices.shape
    offsets = [(dy, dx) for dy in range(3) for dx in range(3) if (dy, dx) != (1, 1)]
    for _ in range(passes):
        padded = np.pad(indices, 1, mode="edge")
        neighbours = [padded[dy:dy + height, dx:dx + width] for dy, dx in offsets]
        matches = [n == indices for n in neighbours]
        same = sum(m.astype(np.uint8) for m in matches)
        padded_same = np.pad(same, 1, mode="constant", constant_values=8)
        partner_stray = np.zeros_like(matches[0])
        for (dy, dx), match in zip(offsets, matches):
            partner_stray |= match & (padded_same[dy:dy + height, dx:dx + width] <= 1)
        lonely = (same == 0) | ((same == 1) & partner_stray)
        if not lonely.any():
            break
        counts = np.zeros((int(indices.max()) + 1,) + indices.shape, dtype=np.uint8)
        for color in np.unique(indices):
            counts[color] = sum((n == color).astype(np.uint8) for n in neighbours)
        indices = np.where(lonely & (counts.max(0) >= 5), counts.argmax(0).astype(np.uint8), indices)
    return indices


def encode(indices: np.ndarray, palette: list[int], path: Path, level: int) -> int:
    used = np.unique(indices)
    remap = np.zeros(256, dtype=np.uint8)
    remap[used] = np.arange(len(used), dtype=np.uint8)
    compact = []
    for index in used:
        compact += palette[3 * index: 3 * index + 3]
    image = Image.fromarray(remap[indices], "P")
    image.putpalette(compact)
    image.save(path, optimize=True)
    if shutil.which("optipng"):
        subprocess.run(["optipng", "-quiet", "-strip", "all", f"-o{level}", str(path)], check=True)
    return path.stat().st_size


def build_face(source: Path, output: Path) -> tuple[int, int, int]:
    original = Image.open(source).convert("RGB")
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        candidate = workdir / "face.png"
        for width in WIDTHS:
            resized = cover(original, width).filter(ImageFilter.MedianFilter(3))
            for colors in COLOR_STEPS:
                indices, palette = quantize(resized, colors, workdir)
                indices = despeckle(merge_similar(indices, palette))
                size = encode(indices, palette, candidate, level=2)
                if size >= MAX_BYTES * 1.1:
                    continue
                if size >= MAX_BYTES:
                    size = encode(indices, palette, candidate, level=7)
                if size < MAX_BYTES:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(candidate, output)
                    return width, colors, size
    raise SystemExit(f"{source.name}: no size/colour combination fits under {MAX_BYTES} bytes")


def find_source(region: str, slug: str) -> Path:
    for suffix in SOURCE_SUFFIXES:
        path = ROOT / "sources" / region / f"{slug}{suffix}"
        if path.is_file():
            return path
    raise SystemExit(f"missing source for {region}/{slug}")


def write_manifest(catalog: dict) -> None:
    faces = []
    for entry in catalog["faces"]:
        region = entry.get("region", "cn")
        relative = f"faces/{region}/{entry['slug']}.png"
        info = inspect_face(ROOT / relative)
        faces.append({
            "id": f"{region}-{entry['slug']}",
            "region": region.upper(),
            "city": entry["city"],
            "name": entry["name"],
            "cityCodes": entry.get("cityCodes", []),
            "cityUnionCodes": entry.get("cityUnionCodes", []),
            "cardPrefixes": entry.get("cardPrefixes", []),
            "file": relative,
            "sha256": info["sha256"],
            "bytes": info["bytes"],
            "width": info["width"],
            "height": info["height"],
            "colors": info["colors"],
        })
    manifest = {"schemaVersion": SCHEMA_VERSION, "faces": faces}
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "manifest.json").write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    selected = set(argv)
    unknown = selected - {entry["slug"] for entry in catalog["faces"]}
    if unknown:
        raise SystemExit(f"unknown slugs: {', '.join(sorted(unknown))}")
    for entry in catalog["faces"]:
        if selected and entry["slug"] not in selected:
            continue
        region = entry.get("region", "cn")
        output = ROOT / "faces" / region / f"{entry['slug']}.png"
        width, colors, size = build_face(find_source(region, entry["slug"]), output)
        print(f"{region}/{entry['slug']}: {width}x{width * 19 // 30}, <= {colors} colours, {size} bytes")
    write_manifest(catalog)
    errors = validate()
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
