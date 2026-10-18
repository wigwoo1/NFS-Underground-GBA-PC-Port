from pathlib import Path
import json,struct
from scene_batches import records
p=Path('work/camera');events=list(records(p/'motion-original-source-8750-8781.bin'));capture=json.loads((p/'motion-original-road-source-intervals.json').read_text());checks=[]
for scene in capture['scenes']:
 for road in scene['roads']:
  affine=struct.unpack('<2I',bytes.fromhex(road['blocks']['69']['hex']))[0]
  if not affine:continue
  before=max((e for e in events if e['id']<road['event'] and e['pc']==0x03001800 and e['blocks'][4][0]==road['source']),key=lambda e:e['id']);after=min((e for e in events if before['id']<e['id']<road['event'] and e['pc']==0x03002964 and e['blocks'][4][0]==road['source']),key=lambda e:e['id']);n=struct.unpack_from('<H',after['blocks'][1][1],242)[0];pre=before['blocks'][7][1];post=after['blocks'][7][1];qs=[[struct.unpack_from('<i',data,j*24+12)[0] for j in range(n)] for data in (pre,post)];xyuv_changed=sum(any(pre[j*24+k:j*24+k+4]!=post[j*24+k:j*24+k+4] for k in (0,4,16,20)) for j in range(n));checks.append(dict(begin=scene['begin'],source=road['source'],vertices=n,before_q=qs[0],after_q=qs[1],q_unchanged=qs[0]==qs[1],xyuv_changed_vertices=xyuv_changed))
r=dict(result='AFFINE_Q_PRESERVED_SCRATCH' if checks and all(v['q_unchanged'] for v in checks) else 'AFFINE_Q_WRITES_PRESENT',checks=checks,scope='Original before/after source emission snapshots establish field preservation only. Scheduler and raster use still require verification.')
(p/'affine-road-scratch-q-audit.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
