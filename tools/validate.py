#!/usr/bin/env python3
"""Validate the published card faces against manifest.json.

Every design must be a PNG with at most MAX_COLORS distinct colours, smaller
than MAX_BYTES, live at faces/<card id>/<design id>.png, and match the size and
sha256 recorded in the manifest. Chinese cards are filed under their T-Union
city code and every card needs a default design.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = 2
MAX_COLORS = 24
MAX_BYTES = 40_000
MAX_PACKAGE_BYTES = 50_000_000
ASPECT = 30 / 19
DEFAULT_DESIGN = "default"
CARD_ID_PATTERN = re.compile(r"^[a-z]{2}/[a-z0-9][a-z0-9-]*$")
DESIGN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CODE_PATTERN = re.compile(r"^[0-9A-F]{4}$")
PREFIX_PATTERN = re.compile(r"^[0-9]{6,12}$")
SERIAL_PREFIX_PATTERN = re.compile(r"^[A-Z0-9]{2,4}$")
REMOTE_TOKEN_PATTERN = re.compile(r"remote\.([a-z]{2})\.([a-z0-9][a-z0-9-]*)\.([a-z0-9][a-z0-9-]*)\.png", re.ASCII)
MATCH_KEYS = ("cityCodes", "cityUnionCodes", "cardPrefixes", "families", "serialPrefixes")
# Keys that identify exactly one card; families may legitimately overlap.
UNIQUE_MATCH_KEYS = ("cityCodes", "cityUnionCodes", "cardPrefixes", "serialPrefixes")


def remote_token(card_id: str, design_id: str) -> str:
    return f"remote.{card_id.replace('/', '.')}.{design_id}.png"


def check_retired_designs(retired, cards: list[dict]) -> list[str]:
    """Retired selections resolve directly to a live default on the same card."""
    if not isinstance(retired, dict):
        return ["retiredDesigns: must map retired remote tokens to existing default remote tokens"]
    live = set()
    for card in cards:
        designs = card.get("designs")
        if not isinstance(card.get("id"), str) or not isinstance(designs, list):
            continue
        for design in designs:
            if isinstance(design, dict) and isinstance(design.get("id"), str):
                live.add(remote_token(card["id"], design["id"]))
    errors = []
    for old, target in retired.items():
        origin = REMOTE_TOKEN_PATTERN.fullmatch(old) if isinstance(old, str) else None
        replacement = REMOTE_TOKEN_PATTERN.fullmatch(target) if isinstance(target, str) else None
        if not origin or not replacement:
            errors.append(f"retiredDesigns: invalid remote token mapping {old!r} -> {target!r}")
            continue
        if old in live:
            errors.append(f"retiredDesigns: retired token {old} is still published")
        if origin.group(1, 2) != replacement.group(1, 2):
            errors.append(f"retiredDesigns: {old} must target the same card")
        if replacement.group(3) != DEFAULT_DESIGN or target not in live:
            errors.append(f"retiredDesigns: {old} must target an existing default remote token")
    return errors


def count_colors(image) -> int:
    colors = image.convert("RGBA").getcolors(maxcolors=1 << 24)
    return len(colors or [])


def inspect_face(path: Path) -> dict:
    # Imported here so tools/publish.py can reuse the constants without Pillow.
    from PIL import Image

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


def check_package_size(root: Path, max_bytes: int = MAX_PACKAGE_BYTES) -> list[str]:
    """Count the Git package, including new masters but excluding build caches."""
    if not (root / ".git").exists():
        return []
    paths = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    ).decode("utf-8").split("\0")
    size = sum((root / path).lstat().st_size for path in set(paths) if path and (root / path).is_file())
    if size >= max_bytes:
        return [f"repository: {size} bytes is not under the {max_bytes}-byte fallback CDN package budget"]
    return []


def check_names(where: str, value, required: tuple[str, ...]) -> list[str]:
    if not isinstance(value, dict) or not all(isinstance(text, str) and text for text in value.values()):
        return [f"{where}: must map languages to non-empty text"]
    return [f"{where}: needs {language}" for language in required if not value.get(language)]


def check_match(card_id: str, match) -> list[str]:
    if not isinstance(match, dict) or set(match) - set(MATCH_KEYS):
        return [f"{card_id}: match keys must be among {', '.join(MATCH_KEYS)}"]
    errors = []
    patterns = {
        "cityCodes": CODE_PATTERN,
        "cityUnionCodes": CODE_PATTERN,
        "cardPrefixes": PREFIX_PATTERN,
        "serialPrefixes": SERIAL_PREFIX_PATTERN,
    }
    for key in MATCH_KEYS:
        values = match.get(key, [])
        if not isinstance(values, list) or len(set(values)) != len(values):
            errors.append(f"{card_id}: match.{key} must be a list without duplicates")
            continue
        for value in values:
            pattern = patterns.get(key)
            if pattern:
                valid = isinstance(value, str) and pattern.match(value)
            else:
                valid = isinstance(value, str) and value.strip() and value == value.lower()
            if not valid:
                errors.append(f"{card_id}: invalid match.{key} value {value!r}")
    if not any(match.get(key) for key in MATCH_KEYS):
        errors.append(f"{card_id}: needs at least one matching key")
    if card_id.startswith("cn/"):
        codes = match.get("cityCodes") or []
        if not codes or codes[0].lower() != card_id[3:]:
            errors.append(f"{card_id}: Chinese cards live under their first T-Union city code")
    return errors


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"manifest.json: {exc}"]

    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"manifest.json: schemaVersion must be {SCHEMA_VERSION}")
    cards = manifest.get("cards")
    if not isinstance(cards, list) or not cards:
        return errors + ["manifest.json: cards must be a non-empty list"]

    seen_ids: set[str] = set()
    claimed: dict[tuple[str, str], str] = {}
    listed: set[Path] = set()
    for card in cards:
        card_id = card.get("id", "<missing id>")
        if not CARD_ID_PATTERN.match(card_id):
            errors.append(f"{card_id}: invalid id")
            continue
        if card_id in seen_ids:
            errors.append(f"{card_id}: duplicate id")
        seen_ids.add(card_id)
        is_chinese = card_id.startswith("cn/")
        if card.get("region") != card_id[:2].upper():
            errors.append(f"{card_id}: region must be {card_id[:2].upper()}")
        errors += check_names(f"{card_id}: name", card.get("name"), ("zh", "en") if is_chinese else ("en",))
        if is_chinese or "city" in card:
            errors += check_names(f"{card_id}: city", card.get("city"), ("zh", "en") if is_chinese else ("en",))
        match = card.get("match")
        match_errors = check_match(card_id, match)
        errors += match_errors
        if not match_errors:
            for key in UNIQUE_MATCH_KEYS:
                for value in match.get(key, []):
                    owner = claimed.setdefault((key, value), card_id)
                    if owner != card_id:
                        errors.append(f"{card_id}: match.{key} {value} also used by {owner}")

        designs = card.get("designs")
        if not isinstance(designs, list) or not designs:
            errors.append(f"{card_id}: designs must be a non-empty list")
            continue
        if designs[0].get("id") != DEFAULT_DESIGN:
            errors.append(f"{card_id}: the first design must be {DEFAULT_DESIGN!r}")
        design_ids = [design.get("id") for design in designs]
        if len(set(design_ids)) != len(design_ids):
            errors.append(f"{card_id}: duplicate design ids")
        for design in designs:
            design_id = design.get("id") or "<missing id>"
            where = f"{card_id}/{design_id}"
            if not DESIGN_ID_PATTERN.match(design_id):
                errors.append(f"{where}: invalid design id")
                continue
            if "name" in design:
                errors += check_names(f"{where}: name", design["name"], ("en",))
            asset = design.get("bundledAsset")
            if asset is not None and not (isinstance(asset, str) and DESIGN_ID_PATTERN.match(asset)):
                errors.append(f"{where}: invalid bundledAsset {asset!r}")

            relative = f"faces/{card_id}/{design_id}.png"
            if design.get("file") != relative:
                errors.append(f"{where}: file must be {relative}")
            path = root / relative
            listed.add(path.resolve())
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
                if design.get(key) != actual[key]:
                    errors.append(f"{where}: manifest {key}={design.get(key)!r}, file has {actual[key]!r}")

    for path in sorted((root / "faces").rglob("*")):
        if path.is_file() and path.resolve() not in listed:
            errors.append(f"{path.relative_to(root)}: not listed in manifest.json")
    if "retiredDesigns" in manifest:
        errors += check_retired_designs(manifest["retiredDesigns"], cards)
    errors += check_package_size(root)
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
