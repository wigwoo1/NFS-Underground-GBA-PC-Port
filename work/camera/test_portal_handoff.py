"""Separate portal clipping from pose and shared world texture changes."""
from pathlib import Path
import struct,json,os,subprocess,sys
from PIL import Image,ImageChops
p=Path('work/camera').resolve()
subprocess.run([sys.executable,str(p/'make_boundary_variants.py'),'140'],check=True)
b=bytearray((p/'candidate-140.bin').read_bytes());n=(p/'boundary-fixed-material-141.bin').read_bytes()
def model_offset(data):return next(o for t,o,size in (struct.unpack_from('<3I',data,32+i*12) for i in range(5)) if t==1)
o=model_offset(b);z=model_offset(n);b[o+48:o+160]=n[z+48:z+160];(p/'portal-fixed-candidate-140.bin').write_bytes(b)
def render(alpha,label,bounds):
 env=os.environ.copy();env['NF_PREVIEW_FRACTION']=str(alpha);env['NF_PREVIEW_PHASE']='2';env['NF_CANDIDATE_PORTAL']=bounds
 subprocess.run([str(p/'portal-candidate-preview.exe'),str(p/'portal-fixed-candidate-140.bin'),str(p/'boundary-fixed-material-141.bin'),str(p/label)],env=env,capture_output=True,check=True)
 with Image.open(p/(label+'-2.ppm')) as im:return im.copy()
a=render(.999999,'portal-fixed-before','2,60,0,158');b=render(1,'portal-fixed-after','2,60,0,158');c=render(.999999,'portal-fixed-full','0,240,0,160')
def compare(x,y):
 diff=ImageChops.difference(x,y);r,g,b=diff.split();return dict(changed_pixels=x.width*x.height-ImageChops.lighter(ImageChops.lighter(r,g),b).histogram()[0],bounds=diff.getbbox())
report=dict(portal_to_captured=compare(a,b),full_to_captured=compare(c,b),scope='Exact endpoint camera/object poses and shared world RGBA fixed; candidate material retained. Diagnostic only; full viewport is a control, not a visibility policy.')
assert report['full_to_captured']['changed_pixels']==0
assert report['portal_to_captured']==dict(changed_pixels=2005,bounds=(300,1152,327,1228))
(p/'portal-handoff-tests.json').write_text(json.dumps(report,indent=2));print(report)
canvas=Image.new('RGB',(900,350))
for i,im in enumerate([a,b,ImageChops.difference(a,b)]):canvas.paste(im.crop((300,1050,450,1400)).resize((300,350)),(300*i,0))
canvas.save(p/'portal-handoff-crop.png')
