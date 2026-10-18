from pathlib import Path
import struct,json
from normalize_source_triangle_packets_candidate import normalize
p=Path('work/camera/prototype-runs');r=normalize((p/'source-draw-state-records.bin').read_bytes(),(p/'source-draw-state-payload.bin').read_bytes());groups={};index=None
for op in r['ops']:
 if op['op']=='begin_frame':index=op['identity'][2];groups[index]=[]
 if op['op']=='draw_triangles' and op['source_primitive']==4 and not op['program']:groups[index].append(op)
checks=[]
for i,draws in groups.items():
 states=list(struct.iter_unpack('<8f8i2I',(p/f'source-owned-state-{i}.bin').read_bytes()));assert len(states)==len(draws)
 for state,op in zip(states,draws):
  assert list(state[:4])==op['projection'][:4];assert state[4:8]==(1,1,.5,0);x,y,w,h=op['state']['scissor'];assert list(state[8:12])==[x,2160-y-h,x+w,2160-y];assert list(state[12:16])==op['state']['viewport'];assert state[16:]==(3,0)
  assert set(op['state']['enabled'])=={0xbc0,0xc11,0xde1};assert op['state']['alpha']==[516,.5]
 checks.append(dict(frame=i,draws=len(draws),exact_state_match=True))
result=dict(result='PASS_OWNED_SOURCE_STATE_VS_RENDERER',checks=checks,scope='Five fixture geometry frames only; source-defined state checked against independently captured actual GL commands. Sky/HUD pending.')
(p/'source-draw-state-parity.json').write_text(json.dumps(result,indent=2));print(result)
