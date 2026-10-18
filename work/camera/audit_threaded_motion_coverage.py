"""Audit capture temporal coverage and every persistent model's position movement."""
import csv,hashlib,json,math,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
manifest=Path(sys.argv[1]); session=json.loads(manifest.read_text(encoding='utf-8-sig')); prefix=session['prefix']; frames=[]; previous=None; steps=[]
def rotation_degrees(a,b):
 assert all(math.isfinite(v) for v in (*a,*b))
 assert abs(sum(v*v for v in a)-1)<1e-6 and abs(sum(v*v for v in b)-1)<1e-6
 return math.degrees(2*math.acos(min(1,abs(sum(x*y for x,y in zip(a,b))))))
dense='--dense' in sys.argv; count=session['dense_frames'] if dense else 12; assert 0<count<=60
worker=list(csv.DictReader(Path(prefix+'-worker.csv').open())) if dense else []
provenance=None
if session.get('sampled_draw_scene'):
 provenance=json.loads(Path(prefix+'-sampled-provenance.json').read_text());assert provenance['result']=='PASS';provenance={x['target']:x for x in provenance['checks']}

for i in range(1,count+1):
 base=Path(prefix+f'-{"dense" if dense else "capture"}-{i:02d}'); meta=json.loads(Path(str(base)+'-native-source.json').read_text()); data=Path(str(base)+'-native-scene.bin').read_bytes()
 if dense:
  matches=[r for r in worker if abs(float(r['target'])-meta['target'])<1e-9 and int(r['committed'])==1 and int(r['epoch'])==meta['epoch']]; assert len(matches)==1
 assert len(data)==meta['packet_bytes']; sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+j*12) for j in range(5))}
 models=sections[1]; assert models[:4] in (b'NML1',b'NFM2'); model_count=struct.unpack_from('<I',models,4)[0] if models[:4]==b'NML1' else 1; offsets=[struct.unpack_from('<I',models,8+j*8)[0] for j in range(model_count)] if models[:4]==b'NML1' else [0]
 world_count=struct.unpack_from('<I',sections[2],4)[0]; positions={}; rotations={}; cameras=[]; alpha=struct.unpack_from('<d',sections[5],8+(world_count+model_count)*20+8)[0]; bounds_alpha=alpha
 if provenance is not None:
  proof=provenance[meta['target']];assert proof['packet_sha256']==hashlib.sha256(data).hexdigest() and proof['command_cameras_exact'];assert bounds_alpha==0;alpha=proof['alpha_binary_exact']
 else:assert abs(alpha-meta['alpha'])<1e-10
 for j,offset in enumerate(offsets):
  model=models[offset:]; assert model[:4]==b'NFM2'; poses=[struct.unpack_from('<7d',model,48+k*56) for k in range(2)]; camera=poses[0][:3]; cameras.append(camera)
  identity=struct.unpack_from('<5I',sections[5],8+(world_count+j)*20); assert identity[0]==3
  assert identity not in positions; positions[identity]=poses[1][:3];rotations[identity]=poses[1][3:];rotation_degrees(poses[1][3:],poses[1][3:])
 assert all(c==cameras[0] for c in cameras)
 image=np.asarray(Image.open(str(base)+'-native.ppm')); assert image.shape==(2160,3840,3)
 # Full native geometry viewport; this counts changed RGB, never derives geometry.
 scene=image[:,300:3540]; frame=dict(index=i,target=meta['target'],alpha=alpha,models=model_count,packet_sha256=hashlib.sha256(data).hexdigest(),image_sha256=hashlib.sha256(image.tobytes()).hexdigest())
 if provenance is not None:frame.update(bounds_alpha=bounds_alpha,sampled=proof['sampled'])
 if dense:frame['live_render_lateness_ms']=(int(matches[0]['draw_end_ns'])-int(matches[0]['deadline_ns']))/1e6
 if previous:
  old,oldcamera,oldpositions,oldscene,oldrotations=previous; dt=(frame['target']-old['target'])*280896/16777216; slots=dt*60; assert dt>0 and abs(slots-round(slots))<1e-7
  common=positions.keys()&oldpositions.keys(); movements=[dict(identity=list(key),distance=math.dist(oldpositions[key],positions[key]),rotation_degrees=rotation_degrees(oldrotations[key],rotations[key])) for key in sorted(common)]
  changed=np.any(scene!=oldscene,axis=2)
  steps.append(dict(from_index=old['index'],to_index=i,display_slots=int(round(slots)),uncaptured_slots=int(round(slots))-1,camera_position_distance=math.dist(oldcamera,cameras[0]),persistent_model_movement=movements,entered_models=[list(k) for k in positions.keys()-oldpositions.keys()],left_models=[list(k) for k in oldpositions.keys()-positions.keys()],native_viewport_changed_pixels=int(changed.sum()),changed_pixels_by_vertical_quarter=[int(part.sum()) for part in np.array_split(changed,4)]))
 previous=(frame,cameras[0],positions,scene.copy(),rotations);frames.append(frame)
assert len(frames)==count
out=Path(prefix+('-dense' if dense else '')+'-motion-coverage-audit.json'); report=dict(result='AUDITED',dense_retention=dense,manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),frames=frames,steps=steps,consecutive_slot_pairs=sum(s['display_slots']==1 for s in steps),uncaptured_slots=sum(s['uncaptured_slots'] for s in steps),smooth_60fps_verified=False,scope='All captured already-sampled NFM2 model positions and shared camera positions, source-clock slot coverage, and complete native viewport RGB changes. Dense frames join actual successful live worker commits and are rendered from retained immutable submissions after timing loop; clone costs still affect live deadlines. Effective per-command camera interpolation, rotation endpoint fidelity, between-capture behavior, full-scene fidelity and physical scanout are not proven.')
out.write_text(json.dumps(report,indent=2));print(json.dumps(dict(report=str(out),consecutive_slot_pairs=report['consecutive_slot_pairs'],uncaptured_slots=report['uncaptured_slots'],steps=steps)))
if dense:
 contact=Image.new('RGB',(1280,1140)); draw=ImageDraw.Draw(contact)
 for tile,index in enumerate(tuple(1+round(j*(count-1)/5) for j in range(6))):
  frame=frames[index-1]; x=(tile%2)*640; y=(tile//2)*380
  contact.paste(Image.open(prefix+f'-dense-{index:02d}-native.ppm').resize((640,360)),(x,y));draw.text((x+4,y+362),f"{index}: {frame['target']:.3f} alpha {frame['alpha']:.3f} cars {frame['models']}",fill='white')
 contact.save(prefix+'-dense-contact.png')

