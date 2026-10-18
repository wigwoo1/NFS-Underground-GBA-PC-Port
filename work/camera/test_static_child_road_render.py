"""Owned static-child road asset, identity and sampled-camera 4K replay."""
from pathlib import Path
import json,struct,hashlib,os,subprocess
from PIL import Image,ImageChops
p=Path('work/camera').resolve();f=p/'overflow-scene-171';m=json.loads((f/'manifest.json').read_text())
child=m['static_children'][0];assert child['record'][0]==228 and child['road_extracted']
source=child['road_descriptor'];assert source==139900368
asset=(f/f'road-{source}.bin').read_bytes();metadata=m['road_assets'][str(source)]
assert metadata['origin']=='static child' and hashlib.sha256(asset).hexdigest()==metadata['sha256']
v,w,h=struct.unpack_from('<3I',asset);assert len(asset)==12+v*40+w*h*4
packet=(f/'old.bin').read_bytes();sections={t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+i*12) for i in range(5))}
n=struct.unpack_from('<I',sections[2],4)[0];identities=[struct.unpack_from('<5I',sections[5],8+i*20) for i in range(n)]
matches=[i for i,identity in enumerate(identities) if identity==(1,m['state'],source,8,0)];assert len(matches)==1;index=matches[0]
cursor=8;captured=None
for i in range(n):
 vertices,width,height=struct.unpack_from('<3I',sections[2],cursor);size=12+vertices*40+width*height*4
 if i==index:captured=sections[2][cursor:cursor+size]
 cursor+=size
assert captured==asset
cases=[]
for alpha in ('0.25','0.5','0.75'):
 trace=json.loads((p/f'sampled-object-dispatch-{alpha}-tests.json').read_text());draw=next(d for d in trace['draws'] if d['kind']=='road' and d['source']==source);invocation=trace['calls'][draw['owner']]
 assert invocation['region']==228 and invocation['caller']==0x03002ae8
 bounds=invocation['record'][1:5];header=struct.unpack_from('<8I',packet)
 clips=struct.pack('<5Id',0x3150434e,*header[4:7],n,float(alpha))
 for i,identity in enumerate(identities):clips+=struct.pack('<5I4H',*identity,*(bounds if i==index else [0,240,0,160]))
 clip_path=f/f'child-road-{alpha}.clips';clip_path.write_bytes(clips)
 env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(clip_path),NF_PREVIEW_FRACTION=alpha,NF_PREVIEW_PHASE='2')
 images=[]
 for surface in (999,index):
  env['NF_ONLY_SURFACE']=str(surface);prefix=f/f'child-road-{alpha}-{surface}'
  subprocess.run([str(p/'isolated-clip-preview.exe'),str(f/'old.bin'),str(f/'new.bin'),str(prefix)],env=env,check=True,capture_output=True)
  with Image.open(str(prefix)+'-2.ppm') as im:images.append(im.convert('RGB'));assert im.size==(3840,2160)
 diff=ImageChops.difference(images[0],images[1]);pixels=sum(v!=(0,0,0) for v in diff.get_flattened_data());assert pixels>0
 cases.append(dict(alpha=float(alpha),bounds=bounds,pixels=pixels,bbox=diff.getbbox()))
report=dict(result='PASS',source=source,captured_asset_exact=True,road_clipping_verified=False,texture_size=[w,h],cases=cases,scope='Isolated static road asset with inherited bounds recorded in sidecar. Preview applies scissor only to walls, so road clipping is NOT verified. Camera interpolation remains existing replay path; not full sampled scene composition or gameplay.')
(p/'static-child-road-render-tests.json').write_text(json.dumps(report,indent=2));print(report)
