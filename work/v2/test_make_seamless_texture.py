import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from make_seamless_texture import create


class SeamlessTextureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.png"
        image = Image.new("RGBA", (64, 64), (84, 86, 90, 255))
        draw = ImageDraw.Draw(image)
        for y in range(0, 64, 8):
            for x in range((y // 8 % 2) * 4, 64, 8):
                draw.rectangle((x, y, x + 3, y + 4), fill=(177, 183, 187, 255))
        image.save(self.source)

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_repeat_edges_alpha_and_grid_layout(self):
        output = self.root / "upscaled.png"
        report = create(self.source, output, edge_width_source=2)
        actual = np.asarray(Image.open(output).convert("RGBA"))
        self.assertEqual(actual.shape, (256, 256, 4))
        np.testing.assert_array_equal(actual[0, :, :3], actual[-1, :, :3])
        np.testing.assert_array_equal(actual[:, 0, :3], actual[:, -1, :3])
        expected_alpha = np.asarray(Image.open(self.source).convert("RGBA").resize(
            (256, 256), Image.Resampling.NEAREST))[..., 3]
        np.testing.assert_array_equal(actual[..., 3], expected_alpha)
        source = np.asarray(Image.open(self.source).convert("RGB"), dtype=np.float32)
        reduced = np.asarray(Image.open(output).convert("RGB").resize(
            (64, 64), Image.Resampling.BOX), dtype=np.float32)
        source_cells = source.reshape(8, 8, 8, 8, 3).mean(axis=(1, 3, 2))
        output_cells = reduced.reshape(8, 8, 8, 8, 3).mean(axis=(1, 3, 2))
        correlation = np.corrcoef(source_cells.ravel(), output_cells.ravel())[0, 1]
        self.assertGreater(correlation, 0.85)
        self.assertEqual(report["output_size"], [256, 256])
        self.assertLess(report["rgb_seam_mean_after"], 0.01)
        self.assertFalse(report["complete_pack"])

    def test_generated_detail_preserves_source_alpha_and_seams(self):
        detail = self.root / "detail.png"
        Image.new("RGB", (31, 29), (120, 80, 65)).save(detail)
        source = Image.open(self.source).convert("RGBA")
        source.putpixel((0, 0), (0, 0, 0, 0))
        source.save(self.source)
        output = self.root / "detail-upscaled.png"
        report = create(self.source, output, detail_path=detail, preserve_bright_threshold=180)
        actual = np.asarray(Image.open(output).convert("RGBA"))
        np.testing.assert_array_equal(actual[0, :, :3], actual[-1, :, :3])
        np.testing.assert_array_equal(actual[:, 0, :3], actual[:, -1, :3])
        expected_alpha = np.asarray(Image.open(self.source).convert("RGBA").resize(
            (256, 256), Image.Resampling.NEAREST))[..., 3]
        np.testing.assert_array_equal(actual[..., 3], expected_alpha)
        self.assertEqual(report["detail_image"], str(detail))
        self.assertEqual(report["preserve_bright_threshold"], 180)
        self.assertFalse(report["complete_pack"])

    def test_uv_atlas_mode_keeps_opposite_borders_independent(self):
        source = Image.open(self.source).convert("RGBA")
        pixels = np.asarray(source).copy()
        pixels[:, 0, :] = (245, 24, 32, 255)
        pixels[:, -1, :] = (18, 36, 240, 255)
        Image.fromarray(pixels, "RGBA").save(self.source)
        output = self.root / "uv-atlas.png"
        report = create(self.source, output, seamless=False)
        actual = np.asarray(Image.open(output).convert("RGBA"))
        self.assertFalse(report["seamless"])
        self.assertEqual(report["edge_blend_output_pixels"], 0)
        self.assertFalse(np.array_equal(actual[:, 0, :3], actual[:, -1, :3]))
        expected_alpha = np.asarray(Image.open(self.source).convert("RGBA").resize(
            (256, 256), Image.Resampling.NEAREST))[..., 3]
        np.testing.assert_array_equal(actual[..., 3], expected_alpha)
        self.assertFalse(report["complete_pack"])

    def test_validation_and_no_overwrite(self):
        output = self.root / "tile.png"
        with self.assertRaises(ValueError):
            create(self.source, output, scale=1)
        with self.assertRaises(ValueError):
            create(self.source, output, edge_width_source=0)
        with self.assertRaises(ValueError):
            create(self.source, output, sharpen_percent=301)
        create(self.source, output)
        with self.assertRaises(FileExistsError):
            create(self.source, output)


if __name__ == "__main__":
    unittest.main()


