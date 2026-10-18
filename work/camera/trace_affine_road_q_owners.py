from pathlib import Path
import json,struct
from scene_batches import records
p=Path('work/camera');events=list(records(p/'motion-original-source-8750-8781.bin'));cases=json.loads((p/'affine-road-scratch-q-audit.json').read_text())['checks'];checks=[]
for case in cases:
 before=next(e for e in events if e['pc']==0x03001800 and e['frame']>=case['begin'] and e['blocks'][4][0]==case['source'] and [struct.unpack_from('<i',e['blocks'][7][1],j*24+12)[0] for j in range(case['vertices'])]==case['before_q'])
 address=before['blocks'][7][0];owners=[]
 for slot,value in enumerate(case['before_q']):
  absolute=address+slot*24+12;observed=[]
  for e in events:
   if e['id']>=before['id']:break
   if 7 not in e['blocks']:continue
   base,data=e['blocks'][7];off=absolute-base
   if 0<=off<=len(data)-4:observed.append((e,struct.unpack_from('<i',data,off)[0]))
  latest_change=None;previous=None
  for e,q in observed:
   if q!=previous:latest_change=(e,q);previous=q
  owner=None
  if latest_change:
   e,q=latest_change;owner=dict(event=e['id'],pc=hex(e['pc']),refresh=e['frame'],source=e['blocks'].get(4,(None,b''))[0],value=q,initial_observation=latest_change[0] is observed[0][0])
  owners.append(dict(slot=slot,absolute_address=absolute,value=value,latest_observation_equal=bool(observed) and observed[-1][1]==value,last_observed_change=owner))
 checks.append(dict(begin=case['begin'],source=case['source'],before_event=before['id'],stream_address=address,owners=owners))
r=dict(result='SCRATCH_Q_OBSERVED_OWNER_TRACE',checks=checks,scope='Snapshot value changes are observations, not instruction write tracing. Initial unchanged values require earlier capture. No renderer seed from these projected values.')
(p/'affine-road-q-owners.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
