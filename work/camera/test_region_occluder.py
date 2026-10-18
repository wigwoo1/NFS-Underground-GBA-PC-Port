from pathlib import Path
import os,subprocess,json,struct
from PIL import Image,ImageChops
p=Path(__file__).resolve().parent
raw=(p/'combined-143-combined.bin').read_bytes();s={t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))}
count=struct.unpack_from('<I',s[2],4)[0]
env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(p/'combined-143-combined.clips'),NF_PREVIEW_PHASE='2',NF_PREVIEW_FRACTION='.5',NF_ONLY_SURFACE='22');env.pop('NF_SECOND_SURFACE',None)
def render():
 prefix=p/'region-occluder-scratch'
 subprocess.run([str(p/'isolated-clip-preview.exe'),str(p/'combined-143-combined.bin'),str(p/'object-replay-143-new.bin'),str(prefix)],env=env,check=True,capture_output=True)
 with Image.open(str(prefix)+'-2.ppm') as im:return im.convert('RGB')
base=render();results=[]
for candidate in range(count-7,count):
 env['NF_SECOND_SURFACE']=str(candidate);im=render();diff=ImageChops.difference(im,base)
 identity=struct.unpack_from('<5I',s[5],8+candidate*20)
 results.append(dict(index=candidate,identity=identity,visible_pixels=sum(v!=(0,0,0) for v in diff.get_flattened_data()),bbox=diff.getbbox()))
report=dict(result='PASS',occluder_source=139970292,comparisons=results,scope='Single retained object wall versus all seven midpoint143 entrants. Pairwise color/depth evidence only, not a reason to remove this wall.')
(p/'region-occluder-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
