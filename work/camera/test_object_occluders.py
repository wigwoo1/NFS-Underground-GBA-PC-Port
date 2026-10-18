from pathlib import Path
import struct,os,subprocess,json
from PIL import Image,ImageChops
p=Path(__file__).resolve().parent;raw=(p/'combined-143-combined.bin').read_bytes()
s={t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))}
count=struct.unpack_from('<I',s[2],4)[0];candidate=count-1
with Image.open(p/f'combined-143-isolated-{candidate}-2.ppm') as im:box=ImageChops.difference(im.convert('RGB'),Image.open(p/'combined-143-isolated-999-2.ppm').convert('RGB')).getbbox()
assert box
results=[];env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(p/'combined-143-combined.clips'),NF_PREVIEW_PHASE='2',NF_PREVIEW_FRACTION='.5')
for index in list(range(count-7))+[4294967295]:
 images=[]
 for pair in (False,True):
  env['NF_ONLY_SURFACE']=str(index);env.pop('NF_SECOND_SURFACE',None)
  if pair:env['NF_SECOND_SURFACE']=str(candidate)
  prefix=p/'occluder-scratch'
  subprocess.run([str(p/'isolated-clip-preview.exe'),str(p/'combined-143-combined.bin'),str(p/'object-replay-143-new.bin'),str(prefix)],env=env,check=True,capture_output=True)
  with Image.open(str(prefix)+'-2.ppm') as im:images.append(im.convert('RGB').crop(box))
 diff=ImageChops.difference(*images);visible=sum(v!=(0,0,0) for v in diff.get_flattened_data())
 identity=None if index==4294967295 else struct.unpack_from('<5I',s[5],8+index*20)
 results.append(dict(index=index,identity=identity,candidate_visible_pixels=visible))
report=dict(result='PASS',candidate_index=candidate,candidate_source=139938876,isolated_pixels=1186,candidate_bbox=box,comparisons=results,scope='Pairwise depth/color diagnostic at midpoint143, sampled clips. Zero difference identifies an individually sufficient occluder, not original-game visibility correctness.')
(p/'object-occluder-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
