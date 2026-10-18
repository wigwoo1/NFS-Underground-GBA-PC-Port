from pathlib import Path
import tempfile
import unittest
import numpy as np
from PIL import Image
from regenerate_asphalt_texture import _make_periodic, regenerate, source_hash


class AsphaltRegenerationTest(unittest.TestCase):
    def test_material_detail_wraps_on_both_axes_without_changing_center(self):
        detail = np.arange(12 * 20, dtype=np.float32).reshape(12, 20)
        horizontal = _make_periodic(detail, axis=1, band=3)
        vertical = _make_periodic(detail, axis=0, band=2)
        self.assertTrue(np.array_equal(horizontal[:, 0], horizontal[:, -1]))
        self.assertTrue(np.array_equal(vertical[0, :], vertical[-1, :]))
        self.assertTrue(np.array_equal(horizontal[:, 3:-3], detail[:, 3:-3]))
        self.assertTrue(np.array_equal(vertical[2:-2, :], detail[2:-2, :]))

    def test_layout_alpha_and_hash_are_preserved_while_asphalt_gains_detail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_path, material_path, output_path = root / "source.png", root / "material.png", root / "upscaled.png"
            repeat_path = root / "upscaled-repeat.png"
            source = np.zeros((8, 16, 4), dtype=np.uint8)
            source[..., :3] = (112, 116, 112)
            source[..., 3] = 255
            source[:, :2, :3] = (24, 24, 24)              # dark rail
            source[:, 7:9, :3] = (238, 238, 238)          # white stripe
            source[2:6, 11:13, :3] = (230, 190, 18)       # yellow paint
            source[0, :, 3] = 0                           # transparent alpha edge
            Image.fromarray(source, "RGBA").save(source_path)
            detail = np.indices((64, 128)).sum(axis=0) % 2 * 255
            Image.fromarray(detail.astype(np.uint8), "L").convert("RGB").save(material_path)

            report = regenerate(source_path, material_path, output_path, scale=4, strength=8)
            repeat_report = regenerate(source_path, material_path, repeat_path,
                                       scale=4, strength=8, grain_strength=4)
            original = Image.open(source_path).convert("RGBA")
            base = np.asarray(original.resize((64, 32), Image.Resampling.NEAREST), dtype=np.uint8)
            actual = np.asarray(Image.open(output_path).convert("RGBA"), dtype=np.uint8)
            labels = np.asarray(original.convert("RGB"), dtype=np.uint8)
            maximum = labels.max(axis=2).astype(np.int16)
            minimum = labels.min(axis=2).astype(np.int16)
            luma = labels[..., 0] * .2126 + labels[..., 1] * .7152 + labels[..., 2] * .0722
            asphalt = ((luma >= 58) & (luma <= 190) & ((maximum - minimum) <= 38) &
                       (np.asarray(original.getchannel("A")) > 0))
            expanded_mask = np.repeat(np.repeat(asphalt, 4, axis=0), 4, axis=1)
            self.assertEqual(actual.shape, (32, 64, 4))
            self.assertEqual(report["source_hash_fnv1a64"], f"{source_hash(original):016x}")
            self.assertGreater(np.any(actual[..., :3] != base[..., :3], axis=2)[expanded_mask].sum(), 0)
            self.assertTrue(np.array_equal(actual[..., :3][~expanded_mask], base[..., :3][~expanded_mask]))
            self.assertTrue(np.array_equal(actual[..., 0][expanded_mask], actual[..., 1][expanded_mask]))
            self.assertTrue(np.array_equal(actual[..., 1][expanded_mask], actual[..., 2][expanded_mask]))
            expected_alpha = np.asarray(original.getchannel("A").resize((64, 32), Image.Resampling.NEAREST))
            self.assertTrue(np.array_equal(actual[..., 3], expected_alpha))
            self.assertFalse(report["complete_pack"])
            self.assertEqual(report["grain_strength"], 4)
            self.assertEqual(repeat_report["source_hash_fnv1a64"], report["source_hash_fnv1a64"])
            self.assertTrue(np.array_equal(actual, np.asarray(
                Image.open(repeat_path).convert("RGBA"), dtype=np.uint8)))
            with self.assertRaises(FileExistsError):
                regenerate(source_path, material_path, output_path, scale=4, strength=8)

    def test_rejects_out_of_range_scale_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = Image.new("RGBA", (2, 2), (90, 90, 90, 255)); source.save(root / "s.png")
            Image.new("RGB", (8, 8), (100, 100, 100)).save(root / "m.png")
            with self.assertRaises(ValueError):
                regenerate(root / "s.png", root / "m.png", root / "o.png", scale=1)
            self.assertFalse((root / "o.png").exists())

    def test_rejects_out_of_range_grain_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            Image.new("RGBA", (2, 2), (90, 90, 90, 255)).save(root / "s.png")
            Image.new("RGB", (8, 8), (100, 100, 100)).save(root / "m.png")
            with self.assertRaises(ValueError):
                regenerate(root / "s.png", root / "m.png", root / "o.png",
                           scale=4, grain_strength=17)
            self.assertFalse((root / "o.png").exists())


if __name__ == "__main__":
    unittest.main()

