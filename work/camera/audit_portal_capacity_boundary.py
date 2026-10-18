import audit_deferred_wall_boundary as f
from owned_portal_traversal import traverse
from owned_motion_visibility import sampled_root
import struct,json
from pathlib import Path
checks=[]
a=f.scenes[0].graph.graph;b=f.scenes[1].graph.graph
ma=struct.unpack_from('<12i',a.context,256);mb=struct.unpack_from('<12i',b.context,256)
for alpha in (.70,.71,.72,.98,.99):
 _,camera,_=f.portal.motion.sample(alpha)
 root=struct.unpack_from('<8H',a.context,368)
 if root[0]!=struct.unpack_from('<H',b.context,368)[0]:root=(sampled_root(a,b,camera,alpha,f.portal.endpoints),*root[1:5],0,0,0)
 trace=[];error=None;queue=None
 try:queue=traverse(a.graph()[0],ma,a.context[304:368],root,f.table,sampled_camera=tuple(camera),endpoint_correction=(ma,mb,*f.portal.endpoints,alpha),diagnostic_trace=trace)
 except ValueError as e:error=str(e)
 checks.append(dict(alpha=alpha,error=error,queue_count=len(queue) if queue else None,trace=trace))
result=dict(result='PORTAL_CAPACITY_TRACE',checks=checks,scope='Accepted source-edge insertion diagnostics; no capacity or traversal behavior change')
Path('work/camera/portal-capacity-boundary-audit.json').write_text(json.dumps(result,indent=2))
for row in checks:
 print(row['alpha'],row['error'],row['queue_count'],row['trace'][-3:])
