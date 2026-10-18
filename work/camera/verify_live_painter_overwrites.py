"""GPU diagnostic: preserve source order and measure later world writes over models."""
import json,os,struct,subprocess,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
manifest=Path(sys.argv[1]).resolve();session=json.loads(manifest.read_text(encoding='utf-8-sig'))
camera=Path(__file__).resolve().parent
if 'exports' in session:
 assert session['result']=='PASS'
 packets=[Path(row['path']) for row in session['exports']]
 for row,packet in zip(session['exports'],packets):
  if 'sha256' in row:assert hashlib.sha256(packet.read_bytes()).hexdigest()==row['sha256']
 prefix=camera/'prototype-runs'/('occlusion-'+manifest.stem)
else:
 assert session['status']=='HOST_COMPLETE' and session['live_road_attributes']
 prefix=Path(session['prefix'])
 packets=[Path(str(prefix)+f'-capture-{index:02d}-native-scene.bin') for index in range(1,13)]
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
env.update(NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(camera/'road-correction-reciprocal.bin'))
cases=[]
def render(packet,label,commands):
 target=Path(str(prefix)+'-painter-'+label+'.ppm');settings=dict(env)
 if commands is not None:settings['NF_ENDPOINT_COMMANDS']=','.join(map(str,commands))
 subprocess.run([str(camera/'endpoint-scene-road-order-preview.exe'),str(packet),str(target)],env=settings,check=True,capture_output=True)
 image=Image.open(str(target)+'-0.ppm');assert image.size==(3840,2160)
 return np.asarray(image).copy()
for index,packet in enumerate(packets,1):
 data=packet.read_bytes();sections={}
 for i in range(5):
  tag,offset,size=struct.unpack_from('<III',data,32+i*12);sections[tag]=data[offset:offset+size]
 count=struct.unpack_from('<I',sections[3],4)[0];order=list(struct.unpack_from('<'+str(count)+'I',sections[3],8))
 boundaries=[i for i in range(count-1) if order[i]>=0xfffffff0 and order[i+1]<0xfffffff0]
 for at in boundaries:
  stop=at+1
  while stop<count and order[stop]<0xfffffff0:stop+=1
  label=f'{index:02d}-{at:02d}'
  a=render(packet,label+'-before',order[:at]);b=render(packet,label+'-model',order[:at+1]);c=render(packet,label+'-world',order[:stop])
  model=np.any(a!=b,axis=2);world=np.any(b!=c,axis=2);overlap=model&world
  cases.append(dict(frame=index,packet=str(packet),packet_sha256=hashlib.sha256(data).hexdigest(),order_position=at,model_command=order[at],later_world_commands=order[at+1:stop],model_changed_pixels=int(model.sum()),world_changed_pixels=int(world.sum()),later_world_over_model_pixels=int(overlap.sum())))
  # One complete allow-list control verifies prefix filtering preserves full order.
  if len(cases)==1:
   full=render(packet,f'{index:02d}-full',None);allowed=render(packet,f'{index:02d}-all',order)
   assert np.array_equal(full,allowed),'Allow-list changed full source-order render'
result='PASS' if cases else 'NO_ELIGIBLE_BOUNDARIES'
report=dict(result=result,manifest=str(manifest),cases=cases,full_allowlist_rgb_exact=True if cases else None,scope='Actual native GPU command-prefix renders at owned packet poses. Counts identify later world writes at pixels changed by preceding model. This checks renderer painter behavior; original raster parity, complete visibility, HUD composition, motion and scanout are separate requirements. No eligible boundary is coverage absence, not a passing occlusion test.')
Path(str(prefix)+'-painter-overwrite-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(result=result,packets=len(packets),boundaries=len(cases),overlapping_boundaries=sum(bool(c['later_world_over_model_pixels']) for c in cases),overwritten_pixels=sum(c['later_world_over_model_pixels'] for c in cases))))
