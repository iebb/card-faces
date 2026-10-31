import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build  # noqa: E402
import publish  # noqa: E402
import validate  # noqa: E402


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class RepositoryTests(unittest.TestCase):
    def test_published_faces_are_valid(self):
        self.assertEqual(validate.validate(ROOT), [])

    def test_manifest_matches_catalog(self):
        catalog, manifest = load("catalog.json"), load("manifest.json")
        self.assertEqual([entry["path"] for entry in catalog["cards"]], [card["id"] for card in manifest["cards"]])
        for entry, card in zip(catalog["cards"], manifest["cards"]):
            for key in validate.MATCH_KEYS:
                self.assertEqual(entry["match"].get(key, []), card["match"][key])
            self.assertEqual(list(build.design_sources(entry["path"])), [design["id"] for design in card["designs"]])

    def test_chinese_cards_are_filed_by_city_code(self):
        chinese = [card for card in load("manifest.json")["cards"] if card["region"] == "CN"]
        self.assertEqual(len(chinese), 20)
        for card in chinese:
            self.assertEqual(card["id"], f"cn/{card['match']['cityCodes'][0].lower()}")
            self.assertEqual(card["designs"][0]["file"], f"faces/{card['id']}/default.png")

    def test_bundled_assets_are_unique(self):
        assets = [
            design["bundledAsset"]
            for card in load("manifest.json")["cards"]
            for design in card["designs"]
            if "bundledAsset" in design
        ]
        self.assertEqual(len(assets), len(set(assets)))

    def test_package_budget_includes_new_sources_but_ignores_build_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", "--initial-branch=master", str(root)], check=True)
            (root / ".gitignore").write_text("dist/\n")
            (root / "dist").mkdir()
            (root / "dist" / "ignored.png").write_bytes(b"x" * 100)
            (root / "source.png").write_bytes(b"x" * 10)
            self.assertEqual(validate.check_package_size(root, max_bytes=20), [])
            (root / "another-source.png").write_bytes(b"x" * 10)
            self.assertTrue(any("package budget" in error for error in validate.check_package_size(root, max_bytes=20)))


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, image, card_id="cn/9990", designs=("default",), match=None):
        entries = []
        for design_id in designs:
            path = self.root / "faces" / card_id / f"{design_id}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path, optimize=True)
            info = validate.inspect_face(path)
            entries.append({
                "id": design_id,
                "file": f"faces/{card_id}/{design_id}.png",
                **{key: info[key] for key in ("sha256", "bytes", "width", "height", "colors")},
            })
        card = {
            "id": card_id,
            "region": card_id[:2].upper(),
            "name": {"zh": "测试卡", "en": "Test Card"},
            "city": {"zh": "测试", "en": "Test"},
            "match": match or {"cityCodes": ["9990"], "cardPrefixes": ["31049990"]},
            "designs": entries,
        }
        self.save([card])
        return card

    def save(self, cards):
        manifest = {"schemaVersion": validate.SCHEMA_VERSION, "cards": cards}
        (self.root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def errors(self):
        return validate.validate(self.root)

    def test_accepts_small_palette_face_with_alternate_design(self):
        self.write(Image.new("RGB", (300, 190), (200, 30, 40)), designs=("default", "metro"))
        self.assertEqual(self.errors(), [])

    def test_rejects_too_many_colours(self):
        pixels = np.zeros((190, 300, 3), dtype=np.uint8)
        pixels[:, :, 0] = np.arange(300) % 30 * 8
        self.write(Image.fromarray(pixels, "RGB"))
        self.assertTrue(any("colours exceeds" in error for error in self.errors()))

    def test_rejects_oversized_file(self):
        rng = np.random.default_rng(1)
        image = Image.fromarray(rng.integers(0, 24, size=(380, 600), dtype=np.uint8), "P")
        image.putpalette([value for index in range(24) for value in (index * 10, 255 - index * 10, 90)])
        self.write(image)
        self.assertTrue(any("not under" in error for error in self.errors()))

    def test_rejects_stale_hash_and_unlisted_files(self):
        card = self.write(Image.new("RGB", (300, 190), (0, 90, 200)))
        card["designs"][0]["sha256"] = "0" * 64
        self.save([card])
        Image.new("RGB", (300, 190)).save(self.root / "faces" / "cn" / "9990" / "extra.png")
        errors = self.errors()
        self.assertTrue(any("manifest sha256" in error for error in errors))
        self.assertTrue(any("extra.png: not listed" in error for error in errors))

    def test_rejects_wrong_aspect_ratio(self):
        self.write(Image.new("RGB", (300, 300), (0, 0, 0)))
        self.assertTrue(any("aspect ratio" in error for error in self.errors()))

    def test_requires_default_design_first(self):
        self.write(Image.new("RGB", (300, 190)), designs=("metro", "default"))
        self.assertTrue(any("first design must be 'default'" in error for error in self.errors()))

    def test_chinese_cards_live_under_city_code(self):
        self.write(Image.new("RGB", (300, 190)), match={"cityCodes": ["2900"]})
        self.assertTrue(any("first T-Union city code" in error for error in self.errors()))

    def test_other_regions_need_only_an_english_name(self):
        card = self.write(Image.new("RGB", (300, 190)), card_id="jp/test", match={"families": ["test"]})
        del card["city"]
        card["name"] = {"en": "Test"}
        self.save([card])
        self.assertEqual(self.errors(), [])

    def test_rejects_duplicate_city_codes(self):
        card = self.write(Image.new("RGB", (300, 190)))
        twin = copy.deepcopy(card)
        twin["id"] = "cn/9991"
        twin["match"]["cityCodes"] = ["9991", "9990"]
        self.save([card, twin])
        self.assertTrue(any("also used by cn/9990" in error for error in self.errors()))


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

    def test_widths_never_upscale(self):
        self.assertEqual(build.widths_for(Image.new("RGB", (2000, 1300)))[0], 1200)
        self.assertEqual(build.widths_for(Image.new("RGB", (400, 253))), [390, 330])

    def test_exact_palette_keeps_flat_colours(self):
        image = Image.new("RGB", (30, 19), (12, 34, 56))
        image.paste((250, 250, 250), (0, 0, 10, 19))
        indices, palette = build.exact_palette(image, 24)
        colors = {tuple(palette[3 * index: 3 * index + 3]) for index in np.unique(indices)}
        self.assertEqual(colors, {(12, 34, 56), (250, 250, 250)})
        self.assertIsNone(build.exact_palette(image, 1))

    def test_transparent_sources_flatten_onto_white(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "face.png"
            Image.new("RGBA", (30, 19), (0, 0, 0, 0)).save(path)
            self.assertEqual(build.load_source(path).getpixel((0, 0)), (255, 255, 255))


class PublishTests(unittest.TestCase):
    def test_publishes_manifest_faces_and_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            self.assertEqual(publish.publish(ROOT, out), [])
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            files = [design["file"] for card in manifest["cards"] for design in card["designs"]]
            self.assertEqual(sorted(str(path.relative_to(out)) for path in (out / "faces").rglob("*.png")), sorted(files))
            self.assertIn("Access-Control-Allow-Origin: *", (out / "_headers").read_text(encoding="utf-8"))

    def test_refuses_mismatched_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "faces", root / "faces")
            manifest = load("manifest.json")
            manifest["cards"][0]["designs"][0]["sha256"] = "0" * 64
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            errors = publish.publish(root, root / "dist")
            self.assertTrue(any("sha256" in error for error in errors))
            self.assertFalse((root / "dist").exists())


if __name__ == "__main__":
    unittest.main()
