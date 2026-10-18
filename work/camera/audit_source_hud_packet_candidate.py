from pathlib import Path
import json,struct,hashlib
from normalize_source_triangle_packets_candidate import normalize
p=Path('work/camera/prototype-runs');payload=(p/'source-hud-batches-payload.bin').read_bytes();ops=normalize((p/'source-hud-batches-records.bin').read_bytes(),payload)['ops'];groups={};i=None;texture_hashes={}
for op in ops:
 if op['op'] in ('allocate_texture','update_texture') and op['payload_bytes']==153600:texture_hashes[op['target'][0]]=hashlib.sha256(payload[op['payload_offset']:op['payload_offset']+op['payload_bytes']]).hexdigest()
 if op['op']=='draw_triangles' and op['program']:op['plane_hashes']={name:texture_hashes.get(op['textures'][str(int(op['uniforms'][name][0]))]['resource'][0]) for name in ('candidateColor','candidateMetadata','ownedText')}
 if op['op']=='begin_frame':i=op['identity'][2];groups[i]=[]
 if i is not None:groups[i].append(op)
report=json.loads((p/'source-hud-batches-component.json').read_text());checks=[]
for row in report['source_packet_checks']:
 i=row['frame'];draws=[o for o in groups[i] if o['op']=='draw_triangles' and o['program']];batches=list(struct.iter_unpack('<20fi3f4i',(p/f'source-owned-hud-batches-{i}.bin').read_bytes()));assert len(batches)==len(draws)==row['hud_batches']
 uploads={hashlib.sha256(payload[o['payload_offset']:o['payload_offset']+o['payload_bytes']]).hexdigest() for o in groups[i] if o['op'] in ('allocate_texture','update_texture') and o['payload_bytes']==153600}
 assert all(d['plane_hashes']['candidateColor']==row['hud_hashes'][0] and d['plane_hashes']['candidateMetadata']==row['hud_hashes'][1] for d in draws)
 if row['hud_info'][1]:assert all(d['plane_hashes']['ownedText']==row['hud_hashes'][2] for d in draws)
 last=0
 for batch,draw in zip(batches,draws):
  u=draw['uniforms'];values=[]
  for name in ('backdropColor','effectParameters','firstTargets','secondTargets','coefficients'):values.extend(u[name])
  assert list(batch[:20])==values;assert batch[20]==int(u['ownedTextEnabled'][0]);assert batch[21:24]==(0,0,0)
  x,y,w,h=draw['state']['scissor'];assert list(batch[24:])==[x,2160-y-h,x+w,2160-y]
  assert batch[25]==last;last=batch[27]
 assert last==2160
 checks.append(dict(frame=i,batches=len(batches),planes_match=True,uniforms_and_clips_exact=True,whole_height_covered=True))
result=dict(result='PASS_SOURCE_HUD_PACKETS_VS_RENDERER',checks=checks,scope='Five full-scene fixture frames; independent owned data vs actual command capture. Not D3D live/presentation proof.')
(p/'source-hud-packet-parity.json').write_text(json.dumps(result,indent=2));print(result)

