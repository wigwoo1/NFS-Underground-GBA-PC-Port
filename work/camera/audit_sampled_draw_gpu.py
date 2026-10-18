"""Native sampled packet GPU support and deterministic owned-camera replay."""
import json,os,subprocess,struct,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent;r=json.loads((Path(sys.argv[1]) if len(sys.argv)>1 else p/'draw-camera-pair-tests.json').read_text());checks=[];tiles=[]
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')};env.update(NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
def render(item,label,command=None):
 target=str(Path(item['packet']).with_suffix(''))+'-'+label+'.ppm';e=dict(env,NF_ENDPOINT_COMMAND_CAMERAS=item['cameras'])
 if command is not None:e['NF_ENDPOINT_COMMANDS']=str(command)
 subprocess.run([str(p/'sampled-scene-preview.exe'),item['packet'],target],env=e,check=True,capture_output=True)
 return np.array(Image.open(target+'-0.ppm'))
for item in r['sample_exports']:
 raw=Path(item['packet']).read_bytes();assert hashlib.sha256(raw).hexdigest()==item['packet_sha256'];assert hashlib.sha256(Path(item['cameras']).read_bytes()).hexdigest()==item['cameras_sha256']
 sections={t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+j*12) for j in range(5))};ids=sections[5];world=struct.unpack_from('<I',sections[2],4)[0];count=struct.unpack_from('<I',ids,4)[0];at=8+count*20;assert ids[at:at+4]==b'NFB2';bounds=[struct.unpack_from('<4H',ids,at+16+j*8) for j in range(count)]
 full=render(item,'full');assert full.shape==(2160,3840,3);repeat=render(item,'repeat');assert np.array_equal(full,repeat);empty=render(item,'empty',4294967200)
 wall=next(j for j in range(world) if struct.unpack_from('<I',ids,8+j*20)[0]==2)
 supports=[]
 for index,command,label in [(wall,wall,'wall'),(world,4294967295,'model')]:
  left,right,top,bottom=bounds[index]
  if label=='wall':left=left//2*2;right=min(240,right//2*2+2);bottom=min(160,bottom+2)
  x0,x1,y0,y1=[int(np.ceil(v-.5)) for v in [300+left*13.5,300+right*13.5,top*13.5,bottom*13.5]]
  isolated=render(item,label,command);changed=np.any(isolated!=empty,axis=2);inside=np.zeros(changed.shape,bool);inside[y0:y1,x0:x1]=True;outside=int((changed&~inside).sum());assert outside==0
  supports.append(dict(kind=label,portal=bounds[index],support=[x0,x1,y0,y1],changed_pixels=int(changed.sum()),outside_support=outside))
 tiles.append(Image.fromarray(full).resize((768,432)));checks.append(dict(alpha=item['alpha'],deterministic_full4k=True,supports=supports))
review=Path(r['sample_exports'][0]['packet']).parent/'sampled-review.png';contact=Image.new('RGB',(768*3,432))
for j,tile in enumerate(tiles):contact.paste(tile,(j*768,0))
contact.save(review);report=dict(result='PASS',checks=checks,review=str(review),scope='Three complete native 4K diagnostic renders and repeat equality; isolated wall/model portal support only. No independent original midpoint image or full-scene60fps claim.');(p/'sampled-draw-gpu-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
