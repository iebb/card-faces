#!/usr/bin/env python3
"""Assemble dist/ for Cloudflare Pages (faces.cardb.al).

The Pages build image only guarantees the Python standard library, so this
re-checks what it can without Pillow (file presence, sha256, byte budget) and
copies manifest.json, the listed faces and public/ into dist/. Full colour and
aspect checks run in CI through tools/validate.py.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import MAX_BYTES, ROOT, SCHEMA_VERSION  # noqa: E402


def check(root: Path) -> tuple[dict, list[str], list[str]]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    files: list[str] = []
    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"manifest.json: schemaVersion must be {SCHEMA_VERSION}")
    for card in manifest.get("cards") or []:
        for design in card.get("designs") or []:
            relative = design.get("file", "")
            path = root / relative
            if not relative.startswith("faces/") or not path.is_file():
                errors.append(f"{relative or card.get('id')}: missing")
                continue
            data = path.read_bytes()
            if len(data) >= MAX_BYTES or len(data) != design.get("bytes"):
                errors.append(f"{relative}: {len(data)} bytes does not match the manifest or budget")
            if hashlib.sha256(data).hexdigest() != design.get("sha256"):
                errors.append(f"{relative}: sha256 does not match the manifest")
            files.append(relative)
    if not files:
        errors.append("manifest.json: no faces listed")
    return manifest, files, errors


def publish(root: Path = ROOT, out: Path | None = None) -> list[str]:
    out = out or root / "dist"
    _, files, errors = check(root)
    if errors:
        return errors
    if out.exists():
        shutil.rmtree(out)
    public = root / "public"
    if public.is_dir():
        shutil.copytree(public, out)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "manifest.json", out / "manifest.json")
    for relative in files:
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
    return []


def main() -> int:
    errors = publish()
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"published to {ROOT / 'dist'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
