import runpy,ctypes as C
from pathlib import Path
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
v=runpy.run_path('work/camera/test_removed_scenery_records.py');history=EndpointRoadPlanner(v['rom'],v['table']);roads,_=history.plan(v['scenes'][0].graph);prepared=PreparedWorldMotion(*v['frames'],*v['scenes'],history,roads,v['rom']);counts=[]
try:
 for alpha in (0,.1,.25,.5,.75,.99,1):
  frame,camera,models,bounds,detail=prepared.sample(alpha);counts.append(sum(r['kind']==3 for r in records(frame)['records']))
  if alpha in (0,1):assert frame==v['frames'][int(alpha)]
 assert counts==[7,7,7,7,7,7,6],counts
 assert prepared.pair._scenery_deactivation=={31:1.0}
 print('PASS: source removal preserves exact endpoints and seven sampled model counts',counts)
finally:prepared.close();history.close()
