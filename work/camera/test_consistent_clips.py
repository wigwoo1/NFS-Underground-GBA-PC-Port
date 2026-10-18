"""Controlled endpoint comparison: same camera, shared materials and clip state."""
from pathlib import Path
import json,struct,os,subprocess
from PIL import Image,ImageChops
from clip_metadata import packet_layout,validate,build
p=Path('work/camera').resolve();captured=json.loads((p/'clip-scene-141.json').read_text());validate((p/'clip-scene-141.bin').read_bytes(),captured['epoch'],captured)
by_id={tuple(r['identity']):r['bounds'] for r in captured['records']}
assert len(by_id)==len(captured['records']) # This controlled fixture has no duplicates.
old=p/'portal-fixed-candidate-140.bin';new=p/'boundary-fixed-material-141.bin'
def render(packet,alpha,label):
 data=packet.read_bytes();h,order,ids=packet_layout(data)
 draws=[dict(ordinal=i,identity=ids[index],bounds=by_id[tuple(ids[index])]) for i,index in enumerate(order)]
 meta=build(data,captured['epoch'],draws) # Synthesized controlled metadata, NOT original scene140 bounds.
 meta['provenance']='Controlled fixture: scene141 bounds transferred by unique identity to fixed-pose/material packets.'
 (p/(label+'.json')).write_text(json.dumps(meta,indent=2))
 binary=struct.pack('<5I',0x3150434e,h[4],h[5],h[6],len(ids))
 for r in sorted(meta['records'],key=lambda x:x['index']):binary+=struct.pack('<5I4H',*r['identity'],*r['bounds'])
 clip=p/(label+'.clips');clip.write_bytes(binary)
 env=os.environ.copy();env['NF_CAPTURE_CLIPS']=str(clip);env['NF_PREVIEW_FRACTION']=str(alpha);env['NF_PREVIEW_PHASE']='2'
 subprocess.run([str(p/'captured-clip-preview.exe'),str(old),str(new),str(p/label)],env=env,check=True,capture_output=True)
 with Image.open(p/(label+'-2.ppm')) as im:return im.copy()
a=render(old,0,'consistent-before');b=render(new,1,'consistent-after');diff=ImageChops.difference(a,b);r,g,bl=diff.split();changed=a.width*a.height-ImageChops.lighter(ImageChops.lighter(r,g),bl).histogram()[0]
report=dict(result='PASS' if changed==0 else 'MISMATCH',changed_pixels=changed,bounds=diff.getbbox(),scope='Synthetic exact endpoint control with scene141 clips on both sides. Not interpolated visibility or original raster parity.')
(p/'consistent-clip-tests.json').write_text(json.dumps(report,indent=2));print(report);assert changed==0
