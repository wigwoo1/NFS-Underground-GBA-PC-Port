#!/usr/bin/env python3
"""Regression tests for source-bound 4K menu-label reconstruction."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import remaster_ui_text as remaster
from texture_hash import source_hash


def synthetic_screen(screen: str, path: Path) -> None:
    image = Image.new("RGBA", (240, 160), (92, 169, 187, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((57, 17, 187, 30), fill=(0, 0, 0, 255))
    draw.rectangle((37, 38, 201, 51), fill=(130, 233, 218, 255))
    font = ImageFont.truetype(str(remaster.FONT_DEFAULT), 8)
    config = remaster.LAYOUTS[screen]
    header, rows = config["header"], config["rows"]
    draw.text((84, 19), header[0], font=font, fill=(242, 225, 0, 255))
    row_y = (40, 56, 72, 88)
    for index, (text, _, _) in enumerate(rows):
        draw.text((40, row_y[index]), text, font=font, fill=(17, 29, 36, 255))
    for text, region, role in config.get("extras", []):
        color = (242, 225, 0, 255) if role == "yellow" else (17, 29, 36, 255)
        draw.text((region[0], region[1]), text, font=font, fill=color)
    image.save(path)


class RemasterUiTextTests(unittest.TestCase):
    def test_all_layouts_produce_hash_bound_4k_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for screen in ("main-menu", "quick-race", "pause", "game-options", "audio-options"):
                source = root / f"{screen}.png"
                output = root / f"{screen}-upscaled.png"
                synthetic_screen(screen, source)
                before = source.read_bytes()
                result = remaster.remaster(screen, source, output, remaster.FONT_DEFAULT)
                self.assertEqual(source.read_bytes(), before)
                with Image.open(source) as original:
                    expected = source_hash(original.convert("RGBA").tobytes(), 240, 160)
                self.assertEqual(result["source_hash"], f"{expected:016x}")
                with Image.open(output) as candidate:
                    self.assertEqual(candidate.size, (3240, 2160))
                    pixels = np.asarray(candidate.convert("RGBA"))
                    self.assertTrue(np.all(pixels[..., 3] == 255))
                    self.assertGreater(len(np.unique(pixels.reshape(-1, 4), axis=0)), 256)

    def test_candidate_overwrite_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "source.png", root / "candidate.png"
            synthetic_screen("quick-race", source)
            remaster.remaster("quick-race", source, output, remaster.FONT_DEFAULT)
            before = output.read_bytes()
            with self.assertRaises(FileExistsError):
                remaster.remaster("quick-race", source, output, remaster.FONT_DEFAULT)
            self.assertEqual(output.read_bytes(), before)

    def test_invalid_dimensions_and_variable_alpha_overlay_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "candidate.png"
            Image.new("RGBA", (239, 160), (20, 30, 40, 255)).save(root / "wrong-size.png")
            with self.assertRaisesRegex(ValueError, "240x160"):
                remaster.remaster("quick-race", root / "wrong-size.png", output, remaster.FONT_DEFAULT)
            image = Image.new("RGBA", (240, 160), (92, 169, 187, 255))
            ImageDraw.Draw(image).rectangle((57, 17, 187, 30), fill=(0, 0, 0, 255))
            image.putpixel((0, 0), (0, 0, 0, 0))
            image.save(root / "transparent.png")
            with self.assertRaisesRegex(ValueError, "uniform alpha"):
                remaster.remaster("main-menu", root / "transparent.png", output, remaster.FONT_DEFAULT)

    def test_uniform_capture_alpha_is_preserved_at_4k(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "pause-source.png", root / "pause-upscaled.png"
            synthetic_screen("pause", source)
            with Image.open(source) as image:
                rgba = image.convert("RGBA")
                rgba.putalpha(Image.new("L", rgba.size, 40))
                rgba.save(source)

            result = remaster.remaster("pause", source, output, remaster.FONT_DEFAULT)
            with Image.open(source) as original, Image.open(output) as candidate:
                src = np.asarray(original.convert("RGBA"))
                dst = np.asarray(candidate.convert("RGBA"))
                expected_hash = source_hash(src.tobytes(), 240, 160)
                expected_alpha = np.asarray(
                    Image.fromarray(src[..., 3], "L").resize(
                        (3240, 2160), Image.Resampling.NEAREST
                    )
                )
            self.assertEqual(result["source_hash"], f"{expected_hash:016x}")
            self.assertEqual(dst.shape, (2160, 3240, 4))
            np.testing.assert_array_equal(dst[..., 3], expected_alpha)
            self.assertTrue(np.all(dst[..., 3] == 40))


if __name__ == "__main__":
    unittest.main()
