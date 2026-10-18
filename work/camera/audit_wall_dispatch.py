from pathlib import Path
import json,struct
from scene_batches import batches
root=Path('work/camera');scene=next(batches(root/'shading-spans.bin'));active=None;rows=[]
for event in scene['events']:
 if event['pc']==0x03000304:
  edge=struct.unpack_from('<2h',event['blocks'][6][1]);left=edge[0]>>1;right=(edge[1]+1)>>1
  active=dict(source=hex(event['blocks'][5][0]),flags=hex(event['regs'][2]),left=left,right=right,columns=[])
  rows.append(active)
 elif event['pc'] in (0x03005320,0x030053e8) and active is not None:
  dest=event['regs'][1];page=0x0600a000 if dest>=0x0600a000 else 0x06000000
  active['columns'].append((dest-page)//2)
for row in rows:
 expected=set(range(max(0,row['left']),min(120,row['right'])))
 actual=set(row['columns']);row['missing_in_viewport_columns']=sorted(expected-actual)
 row['dispatches']=len(row['columns'])
assert len(rows)==22
arrow=next(r for r in rows if r['source']=='0x857c6f4');assert arrow['dispatches']==11
report=dict(scene=0,walls=rows,arrow_wall_dispatches=arrow['dispatches'],
 scope='Captured original column dispatch coverage. Missing columns may reflect clipping/visibility or other control flow; not yet a recovered visibility rule.')
(root/'wall-dispatch-audit.json').write_text(json.dumps(report,indent=2));print('walls',len(rows),'arrow dispatches',arrow['dispatches'])
