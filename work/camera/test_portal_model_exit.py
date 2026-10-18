"""Complete scenery portal exit follows sampled original portal coverage."""
import runpy
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_sampled_model_visit import sampled_model_visit
from owned_motion_pairs import records
v=runpy.run_path('work/camera/audit_failed_world_motion.py');data=v['data']
history=EndpointRoadPlanner(v['rom'],data['table']);roads,_=history.plan(v['scenes'][0].graph)
p=PreparedWorldMotion(*data['frames'],*v['scenes'],history,roads,v['rom'])
try:
 p.sample(.5);assert p.pair._scenery_portal_exit=={35}
 assert not p.pair._scenery_depth_exit and not p.pair._scenery_deactivation
 record=p.pair._scenery_record_pairs[35]
 assert record.older_allocated and record.newer_allocated
 assert len(record.older_blocks)==len(record.newer_blocks)==12
 assert len({p.pair._scenery_motion.matrix(35,i/100) for i in range(101)})==101
 for i in range(1,100):
  alpha=i/100;visible=any(q[0]==30 and not q[5]&0x88 and q[1]<=q[2] and q[3]<=q[4] for q in p.pair.portal.sample(alpha))
  visit=sampled_model_visit(p.pair,alpha,35)
  assert (visit is not None)==visible
  frame=p.sample(alpha)[0]
  assert sum(r['kind']==3 for r in records(frame)['records'])==1+int(visible)
 for endpoint in (0,1):assert p.sample(endpoint)[0]==data['frames'][endpoint]
 print('PASS exact endpoints, 101 distinct allocated poses and 99 fullscene visibility samples matching recovered portal coverage')
finally:p.close();history.close()
