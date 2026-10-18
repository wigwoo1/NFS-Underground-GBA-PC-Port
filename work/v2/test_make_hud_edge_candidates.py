from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("make_hud_edge_candidates", HERE / "make_hud_edge_candidates.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
class HudEdgeCandidateTests(unittest.TestCase):
    def test_transparent_color_does_not_bleed_into_edge(self):
        src = np.zeros((2, 2, 4), dtype=np.uint8)
        src[0, 0] = (240, 20, 10, 255)
        src[0, 1:] = (0, 240, 250, 0)
        src[1] = (0, 240, 250, 0)
        out = MODULE.resize_premultiplied(src, (18, 18), Image.Resampling.BILINEAR)
        partial = out[(out[..., 3] > 0) & (out[..., 3] < 255), :3]
        self.assertGreater(len(partial), 0)
        self.assertTrue(np.all(np.abs(partial.astype(int) - np.array([240,20,10])) <= 1))
        self.assertTrue(np.all(out[out[...,3] == 0, :3] == 0))
    def test_opaque_interiors_keep_exact_source_color(self):
        src = np.zeros((4, 4, 4), dtype=np.uint8); src[:] = (12, 100, 225, 255)
        out = MODULE.resize_premultiplied(src, (40, 40), Image.Resampling.BICUBIC)
        self.assertTrue(np.all(out[..., :3] == (12, 100, 225)))
        self.assertTrue(np.all(out[..., 3] == 255))
    def test_candidate_requires_expected_source_dimensions(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "bad.png"; Image.new("RGBA", (16, 16)).save(source)
            with self.assertRaisesRegex(ValueError, "expected 240x160"):
                MODULE.create_candidates(source, Path(td) / "out")
    def test_hash_named_capture_rejects_changed_pixels(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "0000000000000000.png"
            Image.new("RGBA", MODULE.SOURCE_SIZE, (80,120,200,0)).save(source)
            with self.assertRaisesRegex(ValueError, "captured source ID mismatch"):
                MODULE.create_candidates(source, Path(td) / "out")
    def test_candidate_manifest_is_review_only_and_hashes_source(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "hud.png"; Image.new("RGBA", MODULE.SOURCE_SIZE, (80,120,200,0)).save(source)
            out = Path(td) / "review"; report = MODULE.create_candidates(source, out)
            self.assertFalse(report["release_candidate"]); self.assertFalse(report["runtime_integrated"])
            rgba=np.asarray(Image.open(source).convert("RGBA"))
            self.assertEqual(report["canonical_capture_id"], MODULE.canonical_source_id(rgba))
            self.assertEqual(report["source_pixel_sha256"], MODULE.source_digest(rgba))
            self.assertEqual(len(report["outputs"]), 3)
            for name in report["outputs"]:
                with Image.open(out / name) as im: self.assertEqual(im.size, MODULE.OUTPUT_SIZE)
if __name__ == "__main__": unittest.main()
