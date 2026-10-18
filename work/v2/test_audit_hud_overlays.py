import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_hud_overlays import audit
from texture_hash import source_hash

class HudOverlayAuditTests(unittest.TestCase):
    def _fixture(self, root):
        export = root / "export"; export.mkdir()
        rows=[]
        for serial, points in ((1, [(2,3),(8,9)]), (2, [(2,3),(9,9)])):
            rgba=np.zeros((160,240,4), dtype=np.uint8)
            for x,y in points: rgba[y,x]=(20,210,240,255)
            raw=rgba.tobytes(); key=f"{source_hash(raw,240,160):016x}"
            Image.fromarray(rgba,"RGBA").save(export/f"{key}.png")
            rows.append({"hash":key,"width":240,"height":160,"kind":4,"source":f"{key}.png","first_seen_process_id":123,"first_seen_draw_serial":serial})
        manifest={"format":"NFSUG-SOURCE-TEXTURE-INVENTORY-1","complete":False,"textures":rows}
        (export/"inventory.json").write_text(json.dumps(manifest),encoding="utf-8")
        return export
    def test_hashes_masks_and_transition_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); export=self._fixture(root)
            report=audit(export,root/"out",0.9)
            self.assertEqual(report["source_hashes_verified"],2)
            self.assertEqual(report["persistent_art_pixels"],1)
            self.assertEqual(report["state_varying_pixels"],2)
            self.assertEqual(report["adjacent_capture_transitions"][0]["visible_mask_changed_pixels"],2)
            self.assertTrue((root/"out"/"occupancy-map.png").is_file())
            saved=json.loads((root/"out"/"hud-overlay-spatial-audit.json").read_text())
            self.assertFalse(saved["complete"])
    def test_corrupt_source_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); export=self._fixture(root)
            row=json.loads((export/"inventory.json").read_text())["textures"][0]
            image=np.zeros((160,240,4),dtype=np.uint8); image[3,2]=(30,210,240,255)
            Image.fromarray(image,"RGBA").save(export/row["source"])
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                audit(export,root/"out")
    def test_invalid_persistent_fraction_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); export=self._fixture(root)
            with self.assertRaisesRegex(ValueError,"persistent_fraction"):
                audit(export,root/"out",0.49)

if __name__ == "__main__": unittest.main()
