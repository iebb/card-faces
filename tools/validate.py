#!/usr/bin/env python3
"""Validate the published card faces against manifest.json.

Every face must be a PNG with at most MAX_COLORS distinct colours, smaller than
MAX_BYTES, and match the size and sha256 recorded in the manifest.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = 1
MAX_COLORS = 24
MAX_BYTES = 40_000
ASPECT = 1200 / 760
ID_PATTERN = re.compile(r"^[a-z]{2}-[a-z0-9-]+$")
CODE_PATTERN = re.compile(r"^[0-9A-F]{4}$")
PREFIX_PATTERN = re.compile(r"^[0-9]{6,12}$")


def count_colors(image: Image.Image) -> int:
    colors = image.convert("RGBA").getcolors(maxcolors=1 << 24)
    return len(colors or [])


def inspect_face(path: Path) -> dict:
    data = path.read_bytes()
    with Image.open(path) as image:
        image.load()
        info = {
            "format": image.format,
            "width": image.width,
            "height": image.height,
            "colors": count_colors(image),
        }
    info["bytes"] = len(data)
    info["sha256"] = hashlib.sha256(data).hexdigest()
    return info


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"manifest.json: {exc}"]

    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"manifest.json: schemaVersion must be {SCHEMA_VERSION}")
    faces = manifest.get("faces")
    if not isinstance(faces, list) or not faces:
        return errors + ["manifest.json: faces must be a non-empty list"]

    seen_ids: set[str] = set()
    seen_codes: dict[str, str] = {}
    for face in faces:
        face_id = face.get("id", "<missing id>")
        where = f"{face_id}"
        if not ID_PATTERN.match(face_id):
            errors.append(f"{where}: invalid id")
        if face_id in seen_ids:
            errors.append(f"{where}: duplicate id")
        seen_ids.add(face_id)

        for key in ("city", "name"):
            value = face.get(key) or {}
            if not value.get("zh") or not value.get("en"):
                errors.append(f"{where}: {key} needs zh and en")
        for code in face.get("cityCodes", []) + face.get("cityUnionCodes", []):
            if not CODE_PATTERN.match(code):
                errors.append(f"{where}: invalid city code {code!r}")
        for code in face.get("cityCodes", []):
            if code in seen_codes:
                errors.append(f"{where}: city code {code} also used by {seen_codes[code]}")
            seen_codes[code] = face_id
        for prefix in face.get("cardPrefixes", []):
            if not PREFIX_PATTERN.match(prefix):
                errors.append(f"{where}: invalid card prefix {prefix!r}")
        if not face.get("cityCodes") and not face.get("cityUnionCodes") and not face.get("cardPrefixes"):
            errors.append(f"{where}: needs at least one matching key")

        relative = face.get("file", "")
        path = (root / relative).resolve()
        if not relative.startswith("faces/") or root.resolve() not in path.parents:
            errors.append(f"{where}: file must live under faces/")
            continue
        if not path.is_file():
            errors.append(f"{where}: missing {relative}")
            continue

        actual = inspect_face(path)
        if actual["format"] != "PNG":
            errors.append(f"{where}: {relative} is {actual['format']}, expected PNG")
        if actual["colors"] > MAX_COLORS:
            errors.append(f"{where}: {actual['colors']} colours exceeds {MAX_COLORS}")
        if actual["bytes"] >= MAX_BYTES:
            errors.append(f"{where}: {actual['bytes']} bytes is not under {MAX_BYTES}")
        if abs(actual["width"] / actual["height"] - ASPECT) > 0.01:
            errors.append(f"{where}: aspect ratio {actual['width']}x{actual['height']} is not 30:19")
        for key in ("sha256", "bytes", "width", "height", "colors"):
            if face.get(key) != actual[key]:
                errors.append(f"{where}: manifest {key}={face.get(key)!r}, file has {actual[key]!r}")

    listed = {(root / face.get("file", "")).resolve() for face in faces}
    for path in sorted((root / "faces").rglob("*")):
        if path.is_file() and path.resolve() not in listed:
            errors.append(f"{path.relative_to(root)}: not listed in manifest.json")
    return errors


def main() -> int:
    errors = validate()
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print("card faces OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
