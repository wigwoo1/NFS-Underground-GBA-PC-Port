from pathlib import Path
import json,hashlib
from normalize_source_triangle_packets_candidate import normalize
p=Path('work/camera/prototype-runs');ops=normalize((p/'source-hud-batches-records.bin').read_bytes(),(p/'source-hud-batches-payload.bin').read_bytes())['ops'];groups={};frame=None
for op in ops:
 if op['op']=='begin_frame':frame=op['identity'][2];groups[frame]=[]
 if frame is not None:groups[frame].append(op)
checks=[]
for i in range(5):
 rows=(p/f'source-owned-backdrop-{i}.rgba').read_bytes();draws=[o for o in groups[i] if o['op']=='draw_triangles' and not o['program'] and 3553 not in o['state']['enabled']];assert len(draws)==160,len(draws)
 for y,o in enumerate(draws):
  assert o['state']['viewport']==[300,0,3240,2160]
  assert [v[:2] for v in o['vertices']]==[[0.,float(y)],[240.,float(y)],[240.,float(y+1)],[0.,float(y+1)]]
  expected=[v/255 for v in rows[y*4:y*4+4]];assert all(v[6:10]==expected for v in o['vertices'])
 checks.append(dict(frame=i,rows=160,colors_and_positions_exact=True,sha256=hashlib.sha256(rows).hexdigest()))
r=dict(result='PASS_SOURCE_BACKDROP_VS_ACTUAL_DRAW_COMMANDS',checks=checks,scope='Five source fixture frames; independent command capture vs owned palette rows; no live cadence proof.');(p/'source-backdrop-parity.json').write_text(json.dumps(r,indent=2));print(r)
