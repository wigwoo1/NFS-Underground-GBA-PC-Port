"""Measure actual GPU effects of separate repeated-source portal commands."""
import hashlib,json,os,struct,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
manifest=Path(sys.argv[1]);session=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=session['prefix'];p=Path(__file__).resolve().parent
identity_path=Path(prefix+'-dense-source-identity-verification.json');identity=json.loads(identity_path.read_text());selected=[(i+1,c) for i,c in enumerate(identity['checks']) if c['duplicate_world_identities']];assert len(selected)==1
index,check=selected[0];packet=Path(prefix+f'-dense-{index:02d}-native-scene.bin');data=packet.read_bytes();sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+j*12) for j in range(5))};order=list(struct.unpack_from('<'+str(struct.unpack_from('<I',sections[3],4)[0])+'I',sections[3],8))
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')};env.update(NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
endpoint_rows={row['identity'][3]:row for row in identity['original_endpoints']};pair=[]
for end in check['source_refreshes']:
 row=endpoint_rows[end];endpoint=Path(row['path']).read_bytes();assert hashlib.sha256(endpoint).hexdigest()==row['sha256'];offset,size=struct.unpack_from('<2I',endpoint,36);models=endpoint[offset:offset+size];model_at=struct.unpack_from('<I',models,8)[0] if models[:4]==b'NML1' else 0;pair.append(models[model_at+48:model_at+104])
camera_path=Path(prefix+f'-dense-{index:02d}-camera-pair.bin');camera_path.write_bytes(b''.join(pair));env['NF_ENDPOINT_CAMERA_PAIR']=str(camera_path)
def render(commands,label):
 target=Path(prefix+'-portal-'+label+'.ppm');subprocess.run([str(p/'endpoint-scene-road-order-preview.exe'),str(packet),str(target)],env=dict(env,NF_ENDPOINT_COMMANDS=','.join(map(str,commands)) if commands else '4294967200'),check=True,capture_output=True)
 image=np.asarray(Image.open(str(target)+'-0.ppm'));assert image.shape==(2160,3840,3);return image
background=render([],'background');checks=[]
for duplicate in check['duplicate_world_identities']:
 for ordinal,bounds in zip(duplicate['ordinals'],duplicate['sampled_bounds']):
  kind=duplicate['identity'][0];left,right,top,bottom=bounds
  if kind==2:left=left//2*2;right=min(240,right//2*2+2);bottom=min(160,bottom+2)
  x0=int(np.ceil(300+left*13.5-.5));x1=int(np.ceil(300+right*13.5-.5));y0=int(np.ceil(top*13.5-.5));y1=int(np.ceil(bottom*13.5-.5))
  isolated=render([ordinal],f'{ordinal}-isolated');mask=np.any(isolated!=background,axis=2);inside=np.zeros(mask.shape,bool);inside[max(0,y0):min(2160,y1),max(0,x0):min(3840,x1)]=True
  outside=int((mask&~inside).sum());assert outside==0,(ordinal,bounds,outside)
  at=order.index(ordinal);before=render(order[:at],f'{ordinal}-before');after=render(order[:at+1],f'{ordinal}-after');delta=np.any(before!=after,axis=2)
  assert not np.any(delta&~inside)
  checks.append(dict(identity=duplicate['identity'],command=ordinal,command_position=at,portal=bounds,native_support_rectangle=[x0,x1,y0,y1],isolated_changed_pixels=int(mask.sum()),prefix_changed_pixels=int(delta.sum()),changed_outside_support=outside,exact_repeated_surface_bytes=duplicate['exact_surface_bytes']))
out=Path(prefix+'-dense-repeated-portals-continuous-camera-audit.json');out.write_text(json.dumps(dict(result='PASS',frame=index,target=check['target'],packet_sha256=hashlib.sha256(data).hexdigest(),camera_pair_sha256=hashlib.sha256(camera_path.read_bytes()).hexdigest(),identity_report_sha256=hashlib.sha256(identity_path.read_bytes()).hexdigest(),checks=checks,scope='Actual native 4K isolated and source-ordered prefix RGB changes using retained original camera endpoints and exact owned alpha as in live rendering. Each repeated command confined to its owned portal support. Supersedes rounded packet-camera portal measurements for live geometry. Identical-value writes invisible; no full raster equivalence or whole-game smoothness proof.'),indent=2));print(out.read_text())
