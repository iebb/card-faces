#!/usr/bin/env python3
"""Build palette PNG card faces from sources/ and regenerate manifest.json.

Every file in sources/<card id>/ is one design of that card; `default` is the
one the app applies automatically. Each source is flattened onto white,
cover-cropped to 30:19 and quantized without dithering. Generated artwork is
median-filtered first and has stray pixels removed afterwards; clean flat art
(`"denoise": false` in catalog.json) skips both, and keeps its exact palette
when it already fits. The largest size that stays within the colour and byte
budgets wins. pngquant and optipng are used when installed.

    python3 tools/build.py                       # rebuild every design
    python3 tools/build.py cn/2900 kr/tmoney/logo  # rebuild cards or designs, keep the rest
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
from validate import (  # noqa: E402
    DEFAULT_DESIGN, MATCH_KEYS, MAX_BYTES, MAX_COLORS, ROOT, SCHEMA_VERSION, inspect_face, validate,
)

MAX_WIDTH = 1200
MIN_WIDTH = 300
WIDTH_STEP = 60
COLOR_STEPS = [MAX_COLORS, 20, 16]
# Generated artwork has faint noise in flat fields; pngquant spends palette
# slots on those shades, which turns flat areas into incompressible speckle.
MERGE_DISTANCE = 16
SOURCE_SUFFIXES = (".webp", ".png", ".jpg", ".jpeg")


def load_source(path: Path) -> Image.Image:
    image = Image.open(path)
    if image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info:
        flat = Image.new("RGBA", image.size, (255, 255, 255, 255))
        flat.alpha_composite(image.convert("RGBA"))
        return flat.convert("RGB")
    return image.convert("RGB")


def widths_for(image: Image.Image) -> list[int]:
    """Candidate widths, never upscaling past the source's 30:19 crop."""
    widest = min(MAX_WIDTH, image.width, image.height * 30 // 19) // 30 * 30
    return list(range(widest, MIN_WIDTH - 1, -WIDTH_STEP)) or [widest]


def cover(image: Image.Image, width: int) -> Image.Image:
    height = width * 19 // 30
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def exact_palette(image: Image.Image, colors: int) -> tuple[np.ndarray, list[int]] | None:
    pixels = np.asarray(image, dtype=np.uint8).reshape(-1, 3)
    palette, indices = np.unique(pixels, axis=0, return_inverse=True)
    if len(palette) > colors:
        return None
    flat = palette.astype(int).ravel().tolist()
    return indices.reshape(image.height, image.width).astype(np.uint8), flat + [0] * (768 - len(flat))


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


def build_face(source: Path, output: Path, denoise: bool = True) -> tuple[int, int, int]:
    original = load_source(source)
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        candidate = workdir / "face.png"
        for width in widths_for(original):
            resized = cover(original, width)
            if denoise:
                resized = resized.filter(ImageFilter.MedianFilter(3))
            for colors in COLOR_STEPS:
                exact = None if denoise else exact_palette(resized, colors)
                if exact:
                    indices, palette = exact
                else:
                    indices, palette = quantize(resized, colors, workdir)
                    indices = merge_similar(indices, palette)
                    if denoise:
                        indices = despeckle(indices)
                size = encode(indices, palette, candidate, level=2)
                if size >= MAX_BYTES * 1.1:
                    continue
                if size >= MAX_BYTES:
                    size = encode(indices, palette, candidate, level=7)
                if size < MAX_BYTES:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(candidate, output)
                    return width, colors, size
    raise SystemExit(f"{source}: no size/colour combination fits under {MAX_BYTES} bytes")


def design_sources(card_id: str) -> dict[str, Path]:
    """Map design ids to their masters, default first."""
    found: dict[str, Path] = {}
    directory = ROOT / "sources" / card_id
    for path in sorted(directory.iterdir()) if directory.is_dir() else []:
        if path.suffix.lower() in SOURCE_SUFFIXES:
            if path.stem in found:
                raise SystemExit(f"{card_id}: more than one source for design {path.stem}")
            found[path.stem] = path
    if DEFAULT_DESIGN not in found:
        raise SystemExit(f"{card_id}: missing sources/{card_id}/{DEFAULT_DESIGN}.*")
    return {DEFAULT_DESIGN: found.pop(DEFAULT_DESIGN), **found}


def write_manifest(catalog: dict) -> None:
    cards = []
    for entry in catalog["cards"]:
        card_id = entry["path"]
        overrides = entry.get("designs", {})
        unknown = set(overrides) - set(design_sources(card_id))
        if unknown:
            raise SystemExit(f"{card_id}: catalog lists designs without a source: {', '.join(sorted(unknown))}")
        designs = []
        for design_id in design_sources(card_id):
            relative = f"faces/{card_id}/{design_id}.png"
            info = inspect_face(ROOT / relative)
            extra = overrides.get(design_id, {})
            designs.append({
                "id": design_id,
                **({"name": extra["name"]} if "name" in extra else {}),
                **({"bundledAsset": extra["bundledAsset"]} if "bundledAsset" in extra else {}),
                "file": relative,
                **{key: info[key] for key in ("sha256", "bytes", "width", "height", "colors")},
            })
        cards.append({
            "id": card_id,
            "region": card_id[:2].upper(),
            "name": entry["name"],
            **({"city": entry["city"]} if "city" in entry else {}),
            "match": {key: entry["match"].get(key, []) for key in MATCH_KEYS},
            "designs": designs,
        })
    manifest = {"schemaVersion": SCHEMA_VERSION, "cards": cards}
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "manifest.json").write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    targets = [
        (entry, design_id, source)
        for entry in catalog["cards"]
        for design_id, source in design_sources(entry["path"]).items()
    ]
    selected = set(argv)
    known = {entry["path"] for entry, _, _ in targets} | {f"{entry['path']}/{design}" for entry, design, _ in targets}
    if selected - known:
        raise SystemExit(f"unknown cards or designs: {', '.join(sorted(selected - known))}")
    for entry, design_id, source in targets:
        name = f"{entry['path']}/{design_id}"
        if selected and entry["path"] not in selected and name not in selected:
            continue
        output = ROOT / "faces" / entry["path"] / f"{design_id}.png"
        width, colors, size = build_face(source, output, denoise=entry.get("denoise", True))
        print(f"{name}: {width}x{width * 19 // 30}, <= {colors} colours, {size} bytes")
    write_manifest(catalog)
    errors = validate()
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
