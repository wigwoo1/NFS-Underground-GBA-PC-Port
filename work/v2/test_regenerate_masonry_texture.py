import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from regenerate_masonry_texture import regenerate

class MasonryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.base=Path(self.temp.name)
  self.source=self.base/'source.png'; self.material=self.base/'material.png'
  src=Image.new('RGBA',(32,128),(108,88,78,255)); d=ImageDraw.Draw(src)
  for y in range(0,128,8):
   for x in range((y//8%2)*8,32,16):
    d.rectangle((x,y,min(x+6,31),min(y+2,127)),fill=(148,126,112,255))
  d.rectangle((10,17,22,38),fill=(38,44,48,255)); d.rectangle((12,20,20,35),fill=(88,126,137,255))
  src.save(self.source)
  tile=Image.new('RGB',(128,128),(95,70,60)); td=ImageDraw.Draw(tile)
  for y in range(0,128,16):
   for x in range((y//16%2)*8,128,16):td.rectangle((x,y,x+13,y+12),fill=(132,94,78))
  tile.save(self.material)
 def tearDown(self):self.temp.cleanup()
 def test_feature_shape_alpha_and_material(self):
  out=self.base/'upscaled.png'; poly=[(10,17),(23,17),(22,38),(10,38)]
  report=regenerate(self.source,self.material,out,(8,14,26,41),4,0.0,2.0,poly)
  actual=np.asarray(Image.open(out).convert('RGBA'))
  source=Image.open(self.source).convert('RGBA')
  nearest=np.asarray(source.resize((128,512),Image.Resampling.NEAREST))
  self.assertEqual(actual.shape,(512,128,4)); self.assertEqual(report['preserved_polygon'],poly)
  np.testing.assert_array_equal(actual[...,3],nearest[...,3])
  interior=np.asarray(source.resize((128,512),Image.Resampling.LANCZOS).convert('RGB').filter(
   ImageFilter.UnsharpMask(radius=1.6,percent=125,threshold=2)))
  np.testing.assert_array_equal(actual[80:136,48:84,:3],interior[80:136,48:84])
  self.assertGreater(np.count_nonzero(np.any(actual[...,:3]!=nearest[...,:3],axis=2)),3000)
  self.assertGreaterEqual(report['regenerated_pixel_fraction'],0); self.assertLessEqual(report['regenerated_pixel_fraction'],1)
  self.assertFalse(report['complete_pack'])
 def test_multiple_windows_are_preserved(self):
  out=self.base/'multiple.png'
  polygons=[[(10,17),(23,17),(22,38),(10,38)],[(2,60),(9,60),(9,74),(2,74)]]
  report=regenerate(self.source,self.material,out,(0,0,32,128),4,0.0,2.0,
                    preserve_polygons=polygons)
  actual=np.asarray(Image.open(out).convert('RGBA'))
  smooth=np.asarray(Image.open(self.source).convert('RGBA').resize(
      (128,512),Image.Resampling.LANCZOS).convert('RGB').filter(
          ImageFilter.UnsharpMask(radius=1.6,percent=125,threshold=2)))
  self.assertEqual(report['preserved_polygons'],polygons)
  np.testing.assert_array_equal(actual[82:136,50:78,:3],np.asarray(smooth)[82:136,50:78])
  np.testing.assert_array_equal(actual[248:288,12:28,:3],np.asarray(smooth)[248:288,12:28])
  self.assertGreater(report['regenerated_pixel_fraction'],0.5)
 def test_invalid_and_no_overwrite(self):
  out=self.base/'bad.png'
  with self.assertRaises(ValueError):regenerate(self.source,self.material,out,(8,14,26,41),1)
  with self.assertRaises(ValueError):regenerate(self.source,self.material,out,(8,14,26,41),4,0.0,17)
  with self.assertRaises(ValueError):regenerate(self.source,self.material,out,(8,14,26,41),4,0.0,2,[(0,0),(32,0),(4,4)])
  with self.assertRaises(ValueError):regenerate(self.source,self.material,out,(8,14,26,41),4,0.0,2,
      preserve_polygon=[(1,1),(5,1),(5,5)],preserve_polygons=[[(10,10),(14,10),(14,14)]])
  with self.assertRaises(ValueError):regenerate(self.source,self.material,out,(8,14,26,41),4,0.0,2,
      preserve_polygons=[])
  regenerate(self.source,self.material,out,(8,14,26,41))
  with self.assertRaises(FileExistsError):regenerate(self.source,self.material,out,(8,14,26,41))

if __name__=='__main__':unittest.main()
