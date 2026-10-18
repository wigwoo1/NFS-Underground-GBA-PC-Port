"""Topology limit audit: clipped intersection must approach retained endpoint."""
from pathlib import Path
import ctypes as C,json
p=Path('work/camera');fn=C.CDLL(str((p/'road-near-continuous.dll').resolve())).nf_road_near_continuous;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p]
# Reuse source-derived world camera data, not original projected polygons.
exec(compile((p/'test_road_world_near_project.py').read_text(),'source_endpoint_setup','exec'),globals())
rows=[]
for e in events:
 j=next(j for j in joins if j['source']==e['source']);g=next(g for g in geo['roads'] if g['surface']==j['surface']);mapping=next(m for m in maps if m['source']==e['source']);m=(C.c_int32*12)(*struct.unpack('<12i',bytes.fromhex(e['blocks']['2']['hex'])));points=[]
 for v in g['vertices']:
  out=(C.c_double*3)();assert cam((C.c_double*3)(*v),m,out);points.append(list(out))
 for row in mapping['mapping']:
  if not row['near_generated']:continue
  a=row['source_edge'];b=(a+1)%len(points);aa=points[a]+g['source_attributes'][a];bb=points[b]+g['source_attributes'][b];visible=0 if aa[2]>=64 else 1;pair=[aa,bb];pair[visible]=pair[visible].copy();pair[visible][2]=64
  target=pair[visible];samples=[]
  for eps in (1e-3,1e-6,1e-9):
   moved=[x.copy() for x in pair];moved[visible][2]+=eps;out=(C.c_double*5)();assert fn((C.c_double*5)(*moved[0]),(C.c_double*5)(*moved[1]),64,buf,out)
   samples.append(dict(epsilon=eps,max_endpoint_gap=max(abs(x-y) for x,y in zip(out,target)),difference=[x-y for x,y in zip(out,target)]))
  rows.append(dict(source=e['source'],edge=a,samples=samples))
assert len(rows)==4
assert all(r['samples'][-1]['max_endpoint_gap']<1e-6 for r in rows)
report=dict(result='PASS_TRANSITION_LIMIT' ,checks=rows,scope='One-depth-unit boundary correction converges to retained endpoint on four source edges; no production or full motion proof.')
(p/'road-near-topology-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

