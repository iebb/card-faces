#!/usr/bin/env python3
"""Export the two original rectangle-only SVG designs into compact PNG inputs."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from build import build_face
from validate import ROOT, inspect_face


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        raw = Path(temporary) / "render.png"
        for name in ("duty-free", "myeongdong"):
            vector = ROOT / "sources/kr/ezl" / f"{name}.svg"
            source = vector.with_suffix(".png")
            face = ROOT / "faces/kr/ezl" / f"{name}.png"
            subprocess.run(["rsvg-convert", "--output", str(raw), str(vector)], check=True)
            build_face(raw, face, denoise=False)
            shutil.copyfile(face, source)
            print(f"{name}: {inspect_face(face)}")


if __name__ == "__main__":
    main()
