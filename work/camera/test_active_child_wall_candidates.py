"""Source-owned child walls with inherited sampled clips; no composition claim."""
import audit_active_road_child_actions as f
from owned_sampled_graph_wall_visibility import selected_graph_walls
from owned_motion_wall_regions import wall_region_candidates
import json
from pathlib import Path
checks=[]
for i in range(101):
 alpha=i/100
 roots=[q for q in f.portal.sample(alpha) if q[0]==22 and not q[5]&8];assert len(roots)==1
 child=(228,*roots[0][1:])
 candidates=wall_region_candidates(f.portal,alpha,queue=(child,))
 assert len(candidates)==4 and {x.edge for x in candidates}=={0,1,2,3}
 assert all(x.descriptor==228 and x.bounds==tuple(float(v) for v in roots[0][1:5]) for x in candidates)
 selected=selected_graph_walls(f.portal,alpha,queue=(child,))
 checks.append(dict(alpha=alpha,bounds=child[1:5],visible_edges=[x.edge for x,v in selected],deferred=[x.edge for x,v in selected if v.flags&2]))
result=dict(result='PASS',samples=101,source_wall_candidates=404,checks=checks,scope='Child-owned edge camera and inherited clip selection only; parent recursion eligibility, composed draw ordering and GPU parity unverified')
Path('work/camera/active-child-wall-candidates-tests.json').write_text(json.dumps(result,indent=2))
print(dict(result='PASS',samples=101,source_wall_candidates=404,visible_samples=sum(bool(x['visible_edges']) for x in checks),deferred_samples=sum(bool(x['deferred']) for x in checks)))
