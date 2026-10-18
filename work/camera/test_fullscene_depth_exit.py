import runpy
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
v=runpy.run_path('work/camera/test_depth_hidden_scenery_records.py');history=EndpointRoadPlanner(v['rom'],v['v']['table']);roads,_=history.plan(v['scenes'][0].graph);prepared=PreparedWorldMotion(*v['v']['frames'],*v['scenes'],history,roads,v['rom']);counts=[]
try:
 for alpha in (0,.1,.25,.5,.75,.9,.99,1):
  frame,*_=prepared.sample(alpha);counts.append(sum(r['kind']==3 for r in records(frame)['records']))
  if alpha in (0,1):assert frame==v['v']['frames'][int(alpha)]
 assert counts[0]-counts[-1]==2 and all(a>=b for a,b in zip(counts,counts[1:])),counts
 assert prepared.pair._scenery_depth_exit=={34,37}
 print('PASS sampled depth exit world assembly, exact endpoints, monotone model visibility',counts)
finally:prepared.close();history.close()
