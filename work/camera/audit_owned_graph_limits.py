from pathlib import Path
import json
from sample_owned_motion import PreparedMotionPair
from owned_portal_traversal import traverse
from owned_portal_pose_residual import correction
exec(compile(Path('work/camera/test_owned_sampled_graph.py').read_text().split('older,newer=')[0],'graph_setup','exec'))
older,newer=8758,8762
a=(p/'motion-actual-scanline-assets'/f'{older}-native-complete-frame.bin').read_bytes();b=(p/'motion-actual-scanline-assets'/f'{newer}-native-complete-frame.bin').read_bytes();pair=PreparedMotionPair(a,b)
source_refreshes={label:next(k for k,v in scenes.items() if v['matrix']==struct.unpack('<12i',pair.arguments[0]['camera_'+label])) for label in ('older','newer')}
assert graphs[source_refreshes['older']]==graphs[source_refreshes['newer']]
checks=[]
for alpha in (0,1e-8,1e-6,.0001,.001,.01,.99,.999,.9999,1-1e-6,1-1e-8,1):
 scene=scenes[source_refreshes['newer' if alpha==1 else 'older']];_,camera,_=pair.sample(alpha)
 regions=traverse(graphs[source_refreshes['older']],scene['matrix'],scene['framebuffer'],scene['expected'][0],reciprocal,sampled_camera=camera,endpoint_correction=correction(pair,alpha))
 checks.append(dict(alpha=alpha,regions=[list(x) for x in regions]))
comparisons=[]
for endpoint,neighbor in ((checks[0],checks[1]),(checks[-1],checks[-2])):
 exact={x[0]:x for x in endpoint['regions']};near={x[0]:x for x in neighbor['regions']};shared=exact.keys()&near.keys()
 comparisons.append(dict(endpoint=endpoint['alpha'],missing=sorted(exact.keys()-near.keys()),extra=sorted(near.keys()-exact.keys()),max_shared_bound_error=max((abs(exact[k][j]-near[k][j]) for k in shared for j in (1,2)),default=0)))
r=dict(result='SAMPLED_GRAPH_ENDPOINT_LIMIT_AUDIT',checks=checks,comparisons=comparisons,source_refreshes=source_refreshes,scope='One actual camera pair; analytic projection vs original fixed arithmetic can change thin-region visibility.')
(p/'owned-graph-limit-audit.json').write_text(json.dumps(r,indent=2));print(comparisons)
