"""Actual 4K GPU portal confinement at independently classified near events."""
import hashlib,json,os,struct,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
manifest=Path(sys.argv[1]);session=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=session['prefix'];p=Path(__file__).resolve().parent
identity_path=Path(prefix+'-dense-source-identity-verification.json');identity=json.loads(identity_path.read_text());motion_path=Path(prefix+'-dense-projected-motion-audit.json');motion=json.loads(motion_path.read_text());rows={row['identity'][3]:row for row in identity['original_endpoints']}
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')};env.update(NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
events=[dict(from_index=st['from_index'],to_index=st['to_index'],**e) for st in motion['steps'] for e in st['clipping_events'] if e['near_crossing_vertices']];assert events
checks=[]
for event in events:
 assert event['kind']=='world'
 endpoint_checks=[]
 for index,ordinal in [(event['from_index'],event['from_ordinal']),(event['to_index'],event['to_ordinal'])]:
  base=prefix+f'-dense-{index:02d}';packet=Path(base+'-native-scene.bin');data=packet.read_bytes();assert hashlib.sha256(data).hexdigest()==motion['frames'][index-1]['packet_sha256'];sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+j*12) for j in range(5))}
  source_identity=list(struct.unpack_from('<5I',sections[5],8+ordinal*20));assert source_identity==event['identity'][:5]
  check=identity['checks'][index-1];pair=[]
  for end in check['source_refreshes']:
   row=rows[end];endpoint=Path(row['path']).read_bytes();assert hashlib.sha256(endpoint).hexdigest()==row['sha256'];offset,size=struct.unpack_from('<2I',endpoint,36);models=endpoint[offset:offset+size];at=struct.unpack_from('<I',models,8)[0] if models[:4]==b'NML1' else 0;pair.append(models[at+48:at+104])
  camera_path=Path(base+'-near-camera-pair.bin');camera_path.write_bytes(b''.join(pair));local_env=dict(env,NF_ENDPOINT_CAMERA_PAIR=str(camera_path))
  def render(commands,label):
   target=Path(base+f'-near-{ordinal}-{label}.ppm');trace_env=dict(local_env)
   if label=='isolated':trace_env.update(NF_CAPTURE_ROAD_EDGES='1',NF_ENDPOINT_ROAD_EDGE_TRACE=str(target)+'.edges.csv')
   subprocess.run([str(p/'endpoint-scene-road-order-preview.exe'),str(packet),str(target)],env=dict(trace_env,NF_ENDPOINT_COMMANDS=','.join(map(str,commands)) if commands else '4294967200'),check=True,capture_output=True)
   with Image.open(str(target)+'-0.ppm') as im:image=np.array(im)
   assert image.shape==(2160,3840,3);return image
  order=list(struct.unpack_from('<'+str(struct.unpack_from('<I',sections[3],4)[0])+'I',sections[3],8));assert order.count(ordinal)==1
  bounds=event['from_portal'] if index==event['from_index'] else event['to_portal'];left,right,top,bottom=bounds
  if source_identity[0]==2:left=left//2*2;right=min(240,right//2*2+2);bottom=min(160,bottom+2)
  x0=int(np.ceil(300+left*13.5-.5))
  if source_identity[0]==1:
   # Road geometry uses inclusive <= right/bottom. Include a pixel centre
   # exactly on that boundary; this is not the half-open wall GL scissor.
   x1=int(np.floor(300+right*13.5-.5))+1;y0=int(np.ceil(top*13.5-.5));y1=int(np.floor(bottom*13.5-.5))+1
  else:
   x1=int(np.ceil(300+right*13.5-.5));y0=2160-int(np.ceil((160-top)*13.5-.5));y1=2160-int(np.ceil((160-bottom)*13.5-.5))
  inside=np.zeros((2160,3840),bool);inside[max(0,y0):min(2160,y1),max(0,x0):min(3840,x1)]=True
  background=render([],'background');isolated=render([ordinal],'isolated');mask=np.any(isolated!=background,axis=2);assert not np.any(mask&~inside)
  at=order.index(ordinal);before=render(order[:at],'before');after=render(order[:at+1],'after');delta=np.any(before!=after,axis=2);assert not np.any(delta&~inside)
  endpoint_checks.append(dict(index=index,ordinal=ordinal,packet_sha256=hashlib.sha256(data).hexdigest(),camera_pair_sha256=hashlib.sha256(camera_path.read_bytes()).hexdigest(),portal=bounds,native_support_rectangle=[x0,x1,y0,y1],isolated_changed_pixels=int(mask.sum()),prefix_changed_pixels=int(delta.sum()),changed_outside_support=0))
 checks.append(dict(event=event,endpoints=endpoint_checks));print(json.dumps(dict(completed_events=len(checks),total_events=len(events))),flush=True)
out=Path(prefix+'-dense-near-events-gpu-audit.json');out.write_text(json.dumps(dict(result='PASS',motion_report_sha256=hashlib.sha256(motion_path.read_bytes()).hexdigest(),identity_report_sha256=hashlib.sha256(identity_path.read_bytes()).hexdigest(),renderer_sha256=hashlib.sha256((p/'endpoint-scene-road-order-preview.exe').read_bytes()).hexdigest(),checks=checks,scope='Actual native4K isolated and source-order prefix renders at both endpoints of continuous-camera near-mask changes. Exact packet/source camera hashes. RGB changes confined to owned portal support: roads inclusive geometric boundaries; walls exact bottom-up GL scissor transformed to top-down image rows. Identical-value writes invisible; no raster parity, near-clipped UV continuity or full-game smoothness proof.'),indent=2));print(str(out))
