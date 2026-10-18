"""Measure all-wall sampled handoff and isolate shared world texture changes."""
from pathlib import Path
import os,subprocess,json
from PIL import Image,ImageChops
p=Path('work/camera').resolve()
def render(exe,older,newer,clips,alpha,label):
 env=os.environ.copy();env['NF_CAPTURE_CLIPS']=str(p/clips);env['NF_PREVIEW_FRACTION']=str(alpha);env['NF_PREVIEW_PHASE']='2'
 subprocess.run([str(p/exe),str(p/older),str(p/newer),str(p/label)],env=env,check=True,capture_output=True)
 with Image.open(p/(label+'-2.ppm')) as im:return im.copy()
a=render('sampled-clip-preview.exe','candidate-140.bin','order-boundary-141.bin','sampled-all-0.999999.clips',.999999,'handoff-sampled')
b=render('captured-clip-preview.exe','clip-scene-140.bin','clip-scene-141.bin','captured-141.clips',1,'handoff-captured')
c=render('captured-clip-preview.exe','portal-fixed-candidate-140.bin','boundary-fixed-material-141.bin','consistent-after.clips',1,'handoff-fixed-material')
fixed_pose=render('sampled-clip-preview.exe','portal-fixed-candidate-140.bin','boundary-fixed-material-141.bin','sampled-all-0.999999.clips',.999999,'handoff-fixed-pose')
def compare(a,b):
 d=ImageChops.difference(a,b);r,g,b=d.split();mask=ImageChops.lighter(ImageChops.lighter(r,g),b)
 return dict(changed_pixels=d.width*d.height-mask.histogram()[0],bounds=d.getbbox())
report=dict(exact_pose_material=compare(fixed_pose,c),raw_handoff=compare(a,b),shared_material_fixed=compare(a,c),material_only=compare(c,b),scope='Near-end sampled pose versus captured exact endpoint, consistent wall clipping; only shared world RGBA fixed in control, no simulation changes.')
assert report['exact_pose_material']['changed_pixels']==0
assert report['shared_material_fixed']['changed_pixels']==33
assert report['material_only']['changed_pixels']==134339
(p/'sampled-handoff-tests.json').write_text(json.dumps(report,indent=2));print(report)
