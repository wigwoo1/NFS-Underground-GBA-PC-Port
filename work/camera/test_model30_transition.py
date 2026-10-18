"""Model30 birth uses original source identity and exact captured pose."""
import runpy, struct
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
v=runpy.run_path('work/camera/audit_failed_world_motion.py');data=v['data']
history=EndpointRoadPlanner(v['rom'],data['table']);roads,_=history.plan(v['scenes'][0].graph)
p=PreparedWorldMotion(*data['frames'],*v['scenes'],history,roads,v['rom'])
try:
 p.sample(.5)
 pair=p.pair._scenery_record_pairs[37]
 assert not pair.older_allocated and pair.newer_allocated
 assert len(pair.older_blocks)==len(pair.newer_blocks)==12
 owner=p.pair._model_record_owners[1]
 row=next(r for i,r in enumerate(records(data['frames'][1])['records']) if owner.get(i)==37)
 assert pair.newer_blocks[2]==bytes(row['blocks'][2])
 assert len({p.pair._scenery_motion.matrix(37,i/100) for i in range(101)})==101
 for alpha in (0,1): assert p.sample(alpha)[0]==data['frames'][alpha]
 print('PASS model30 complete birth records, exact original newer pose, 101 distinct poses and exact endpoint frames')
finally:p.close();history.close()
