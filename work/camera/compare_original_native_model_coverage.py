"""Source-joined model change masks: original mode4 vs native GPU at pixel centers."""
import json,struct,sys,os,subprocess,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from scene_batches import batches
p=Path(__file__).resolve().parent;overlap_path=Path(sys.argv[1]);overlap=json.loads(overlap_path.read_text())
capture=json.loads(Path(overlap['source_report']).read_text());trace=Path(capture['trace']);assert hashlib.sha256(trace.read_bytes()).hexdigest()==capture['trace_sha256']
sources=json.loads(Path(sys.argv[2]).read_text());packet_rows={tuple(r['identity'][2:]):r for r in sources['original_endpoints']}
scenes={tuple((s['begin_refresh'],s['end_refresh'])):s for s in overlap['scenes'] if s['all_observed_routines_captured']}
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')};env.update(NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
def render(packet,commands,label):
 target=p/'prototype-runs'/('model-coverage-'+label+'.ppm');settings=dict(env);settings['NF_ENDPOINT_COMMANDS']=','.join(map(str,commands))
 subprocess.run([str(p/'endpoint-scene-road-order-preview.exe'),str(packet),str(target)],env=settings,check=True,capture_output=True)
 image=np.asarray(Image.open(str(target)+'-0.ppm'));assert image.shape==(2160,3840,3)
 return image
def bbox(mask):
 y,x=np.nonzero(mask)
 return None if not len(x) else [int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1]
def expand(mask):
 pad=np.pad(mask,1);return np.logical_or.reduce([pad[y:y+160,x:x+240] for y in range(3) for x in range(3)])
checks=[]
for batch in batches(trace):
 key=(batch['begin_refresh'],batch['end_refresh'])
 if key not in scenes or key not in packet_rows:continue
 scene=scenes[key];row=packet_rows[key];packet=Path(row['path']);data=packet.read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
 sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+i*12) for i in range(5))}
 world=struct.unpack_from('<I',sections[2],4)[0];models=struct.unpack_from('<I',sections[1],4)[0]
 ids=[struct.unpack_from('<5I',sections[5],8+20*i) for i in range(world+models)]
 count=struct.unpack_from('<I',sections[3],4)[0];order=list(struct.unpack_from('<'+str(count)+'I',sections[3],8))
 model_draws={d['draw_id']:d for d in scene['draws'] if d['model_object'] is not None};pending={}
 for event in batch['events']:
  if event['pc']!=0xffff0084:continue
  stage,identity,pc,*_=struct.unpack('<8I',event['blocks'][85][1][:32])
  if identity not in model_draws:continue
  image=np.frombuffer(event['blocks'][84][1],np.uint8)
  if stage==0:pending[identity]=image.copy();continue
  if identity not in pending:continue
  before=pending.pop(identity);start=batch['display_page']*0xa000
  original=(before[start:start+38400]!=image[start:start+38400]).reshape(160,240)
  draw=model_draws[identity];object_address=int(draw['model_object'],16)
  matches=[i-world for i,v in enumerate(ids) if v[0]==3 and v[2]==object_address];assert len(matches)==1
  command=0xffffffff-matches[0];at=order.index(command);label=f'{key[0]}-{identity}'
  a=render(packet,order[:at],label+'-before');b=render(packet,order[:at+1],label+'-after')
  ys=((np.arange(160)+.5)*13.5).astype(int);xs=(300+(np.arange(240)+.5)*13.5).astype(int)
  native=np.any(a[ys[:,None],xs]!=b[ys[:,None],xs],axis=2)
  checks.append(dict(interval=key,draw_id=identity,object=hex(object_address),command=command,closure=draw['closure'],original_changed_pixels=int(original.sum()),native_center_changed_pixels=int(native.sum()),original_bbox=bbox(original),native_bbox=bbox(native),intersection=int((original&native).sum()),original_without_native_within_one_pixel=int((original&~expand(native)).sum()),native_without_original_within_one_pixel=int((native&~expand(original)).sum())))
assert len(checks)==12
out=overlap_path.with_name(overlap_path.stem+'-model-coverage.json');out.write_text(json.dumps(dict(result='COMPARED',checks=checks,scope='Same original scene/source objects and native command prefixes; original framebuffer value changes versus native changes sampled at GBA pixel centers in 3240x2160 viewport. One-pixel neighborhood counts characterize rounding/raster differences, not an acceptance threshold. Identical-value writes are invisible; original palette/texture quantization and complete raster parity not proven.'),indent=2));print(json.dumps(dict(report=str(out),models=len(checks),original_pixels=sum(c['original_changed_pixels'] for c in checks),native_pixels=sum(c['native_center_changed_pixels'] for c in checks),original_outside=sum(c['original_without_native_within_one_pixel'] for c in checks),native_outside=sum(c['native_without_original_within_one_pixel'] for c in checks))))
