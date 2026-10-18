import runpy
from owned_motion_wall_regions import wall_region_candidates,WallRegionCandidate
from owned_graph_wall_sources import wall_sources
from owned_wall_region_candidates import hidden
v=runpy.run_path('work/camera/audit_failed_world_motion.py');p=v['prepared'] if False else None
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
motion=PreparedMotionPair(*v['data']['frames'],*v['scenes']);portal=PortalMotionPair(v['scenes'][0].graph.graph,v['scenes'][1].graph.graph,v['data']['table'],motion)
for i in range(101):
 alpha=i/100;queue=portal.sample(alpha);graph=portal.newer if alpha==1 else portal.older;selected=frozenset(q[0] for q in queue if not q[5]&8);groups={}
 for wall in wall_sources(graph,validated=True,descriptors=selected):
  if not hidden(wall):groups.setdefault(wall.descriptor,[]).append(wall)
 expected=[]
 for ordinal,q in enumerate(queue):
  if q[5]&8 or q[1]>q[2] or q[3]>q[4]:continue
  for wall in groups.get(q[0],()):expected.append(WallRegionCandidate(ordinal,q[0],wall.edge,tuple(float(x) for x in q[1:5]),q[5],wall))
 assert wall_region_candidates(portal,alpha)==tuple(expected)
assert len(portal._wall_source_cache)==2
print('PASS101 cached wall candidates exact uncached identity/order/material/clip equivalence')
