from __future__ import annotations
import importlib.util, struct, tempfile
from pathlib import Path
import unittest, numpy as np
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("analyze_owned_glyph_capture",HERE/"analyze_owned_glyph_capture.py")
MODULE=importlib.util.module_from_spec(SPEC);assert SPEC.loader;SPEC.loader.exec_module(MODULE)
def fixture():
    rec=[3418,0x0806ff06,0x03007de8,19,0x06000000,240,0,4,3,4,1,0,0x08097b4d,12,0x0800cd99,0x0806fc60]
    raw=struct.pack("<16I",*rec)+bytes([0,1,0,2,3,0,4,5,0,6,7,0])
    return rec,raw
class OwnedGlyphCaptureTests(unittest.TestCase):
    def write_csv(self,path,return_pc="0806ff0a",destination="06000000"):
        path.write_text("index,begin,end,return_pc,sp,destination,entry_display,exit_display,entry_vcount,exit_vcount\n0,3418,3418,"+return_pc+",03007da4,"+destination+",1f54,1f54,58,63\n",encoding="utf-8")
    def test_sdf_smooths_outline_and_keeps_interior(self):
        mask=np.zeros((5,5),dtype=bool);mask[1:4,1:4]=True
        out=np.asarray(MODULE.sdf_coverage(mask,8))
        self.assertEqual(out[20,20],255)
        self.assertEqual(out[0,0],0)
        self.assertTrue(np.any((out>0)&(out<255)))
        self.assertTrue(np.array_equal(out,out[::-1,:]))
        self.assertTrue(np.array_equal(out,out[:,::-1]))
    def test_sdf_preserves_counter_hole(self):
        mask=np.ones((5,5),dtype=bool);mask[2,2]=False
        out=np.asarray(MODULE.sdf_coverage(mask,8))
        self.assertEqual(out[20,20],0)
        self.assertEqual(out[0,0],255)
    def test_area_balanced_sdf_preserves_ink_weight(self):
        masks=[]
        a=np.zeros((7,5),dtype=bool);a[1:6,2]=True;masks.append(a)
        b=np.zeros((7,7),dtype=bool);b[1:6,1:6]=True;b[2:5,2:5]=False;masks.append(b)
        c=np.ones((3,4),dtype=bool);masks.append(c)
        for mask in masks:
            out=np.asarray(MODULE.sdf_coverage(mask,14,preserve_area=True),dtype=np.float64)/255.0
            ratio=float(out.sum())/(14*14*float(mask.sum()))
            self.assertLessEqual(abs(ratio-1.0),0.001)
    def test_parse_owned_glyph_and_exact_payload(self):
        _,raw=fixture()
        with tempfile.TemporaryDirectory() as td:
            csvp=Path(td)/"done.csv";self.write_csv(csvp)
            got=MODULE.parse_capture(raw,csvp)
        self.assertEqual(len(got),1);self.assertEqual(got[0]["asset"],raw[64:])
        self.assertEqual((got[0]["glyph"],got[0]["width"],got[0]["height"],got[0]["draw_width"]),(19,4,3,4))
    def test_reject_truncated_payload(self):
        _,raw=fixture()
        with tempfile.TemporaryDirectory() as td:
            csvp=Path(td)/"done.csv";self.write_csv(csvp)
            with self.assertRaisesRegex(ValueError,"truncated glyph pixels"):
                MODULE.parse_capture(raw[:-1],csvp)
    def test_reject_completion_destination_mismatch(self):
        _,raw=fixture()
        with tempfile.TemporaryDirectory() as td:
            csvp=Path(td)/"done.csv";self.write_csv(csvp,destination="06000008")
            with self.assertRaisesRegex(ValueError,"metadata mismatch"):
                MODULE.parse_capture(raw,csvp)
    def test_reject_wrong_rom_glyph_target(self):
        rec,raw=fixture();rec[15]=0x0806fc64;raw=struct.pack("<16I",*rec)+raw[64:]
        with tempfile.TemporaryDirectory() as td:
            csvp=Path(td)/"done.csv";self.write_csv(csvp)
            with self.assertRaisesRegex(ValueError,"draw target"):
                MODULE.parse_capture(raw,csvp)
if __name__=="__main__":unittest.main()


