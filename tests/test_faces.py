import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build  # noqa: E402
import validate  # noqa: E402


class RepositoryTests(unittest.TestCase):
    def test_published_faces_are_valid(self):
        self.assertEqual(validate.validate(ROOT), [])

    def test_manifest_matches_catalog(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [f"cn-{entry['slug']}" for entry in catalog["faces"]],
            [face["id"] for face in manifest["faces"]],
        )
        for entry, face in zip(catalog["faces"], manifest["faces"]):
            self.assertEqual(entry["cityCodes"], face["cityCodes"])
            self.assertEqual(entry["cardPrefixes"], face["cardPrefixes"])

    def test_every_face_has_a_source(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        for entry in catalog["faces"]:
            self.assertTrue(build.find_source("cn", entry["slug"]).is_file())


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "faces" / "cn").mkdir(parents=True)

    def write_face(self, image):
        path = self.root / "faces" / "cn" / "test.png"
        image.save(path, optimize=True)
        info = validate.inspect_face(path)
        face = {
            "id": "cn-test",
            "city": {"zh": "测试", "en": "Test"},
            "name": {"zh": "测试卡", "en": "Test Card"},
            "cityCodes": ["9990"],
            "cityUnionCodes": [],
            "cardPrefixes": ["31049990"],
            "file": "faces/cn/test.png",
            **{key: info[key] for key in ("sha256", "bytes", "width", "height", "colors")},
        }
        manifest = {"schemaVersion": validate.SCHEMA_VERSION, "faces": [face]}
        (self.root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return face

    def test_accepts_small_palette_face(self):
        self.write_face(Image.new("RGB", (300, 190), (200, 30, 40)))
        self.assertEqual(validate.validate(self.root), [])

    def test_rejects_too_many_colours(self):
        pixels = np.zeros((190, 300, 3), dtype=np.uint8)
        pixels[:, :, 0] = np.arange(300) % 30 * 8
        self.write_face(Image.fromarray(pixels, "RGB"))
        self.assertTrue(any("colours exceeds" in error for error in validate.validate(self.root)))

    def test_rejects_oversized_file(self):
        rng = np.random.default_rng(1)
        indices = rng.integers(0, 24, size=(380, 600), dtype=np.uint8)
        image = Image.fromarray(indices, "P")
        image.putpalette([value for index in range(24) for value in (index * 10, 255 - index * 10, 90)])
        self.write_face(image)
        self.assertTrue(any("not under" in error for error in validate.validate(self.root)))

    def test_rejects_stale_hash_and_unlisted_files(self):
        face = self.write_face(Image.new("RGB", (300, 190), (0, 90, 200)))
        face["sha256"] = "0" * 64
        manifest = {"schemaVersion": validate.SCHEMA_VERSION, "faces": [face]}
        (self.root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        Image.new("RGB", (300, 190)).save(self.root / "faces" / "cn" / "extra.png")
        errors = validate.validate(self.root)
        self.assertTrue(any("manifest sha256" in error for error in errors))
        self.assertTrue(any("extra.png: not listed" in error for error in errors))

    def test_rejects_wrong_aspect_ratio(self):
        self.write_face(Image.new("RGB", (300, 300), (0, 0, 0)))
        self.assertTrue(any("aspect ratio" in error for error in validate.validate(self.root)))


class BuildHelperTests(unittest.TestCase):
    def test_merge_similar_folds_near_duplicates(self):
        palette = [228, 43, 52, 227, 42, 50, 255, 255, 255] + [0] * (3 * 253)
        indices = np.array([[0, 0, 1], [2, 2, 1]], dtype=np.uint8)
        merged = build.merge_similar(indices, palette)
        self.assertEqual(sorted(np.unique(merged).tolist()), [0, 2])

    def test_despeckle_removes_lone_pixels_but_keeps_lines(self):
        indices = np.zeros((9, 9), dtype=np.uint8)
        indices[2, 2] = 1  # lone speck
        indices[6, 1:8] = 2  # one-pixel line
        cleaned = build.despeckle(indices)
        self.assertEqual(cleaned[2, 2], 0)
        self.assertTrue((cleaned[6, 2:7] == 2).all())

    def test_cover_crops_to_card_ratio(self):
        image = build.cover(Image.new("RGB", (1576, 998)), 960)
        self.assertEqual(image.size, (960, 608))


if __name__ == "__main__":
    unittest.main()
