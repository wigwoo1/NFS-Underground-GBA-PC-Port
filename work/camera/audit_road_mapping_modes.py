"""Inventory original road mapping modes before claiming texture fidelity."""
from pathlib import Path
import json,struct
from scene_batches import records
p=Path('work/camera');cases=[]
for e in records(p/'world.bin'):
 if e['pc']!=0x030032f0:continue
 b=e['blocks'];desc=b[4][1]
 if struct.unpack_from('<H',desc,4)[0] or not struct.unpack_from('<H',desc,8)[0]:continue
 start,count=struct.unpack_from('<2H',b[1][1],242)
 rows=[struct.unpack_from('<6i',b[7][1],(start+j)*24) for j in range(count)]
 if not rows:continue
 affine=struct.unpack_from('<i',b[69][1])[0]!=0
 cases.append(dict(event=e['id'],affine=affine,vertices=count,q_min=min(v[3] for v in rows),q_max=max(v[3] for v in rows)))
assert cases
vary=[c for c in cases if c['affine'] and c['q_min']!=c['q_max']]
report=dict(result='AUDIT',retained_roads=len(cases),affine_roads=sum(c['affine'] for c in cases),perspective_roads=sum(not c['affine'] for c in cases),affine_varying_reciprocal=len(vary),examples=vary[:8],native_world_mapping='road_vertex always supplies UV*q with q=1/camera_z; world packet has no original road mapping-mode field',scope='Original retained mode/reciprocal inventory reveals a fidelity dependency; does not establish original per-pixel error or authorize screen-polygon matching.')
(p/'road-mapping-mode-audit.json').write_text(json.dumps(report,indent=2));print(report)
