import runpy,sys
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
v=runpy.run_path('work/camera/audit_failed_world_motion.py');data=v['data'];scenes=v['scenes'];h=EndpointRoadPlanner(v['rom'],data['table']);roads,_=h.plan(scenes[0].graph);expected=h.fork();expected_roads,_=expected.plan(scenes[1].graph);p=PreparedWorldMotion(*data['frames'],*scenes,h,roads,v['rom']);advanced=None
try:
 assert [r['record'] for r in p.endpoint_roads[1]]==[r['record'] for r in expected_roads]
 before=p.sample(.5);advanced=p.take_next_history()
 assert advanced.refresh==scenes[1].graph.refresh and advanced.epoch==scenes[1].graph.epoch and advanced.scratch
 try:p.take_next_history();raise AssertionError('Duplicate transfer accepted')
 except ValueError:pass
 after=p.sample(.5);assert before[0]==after[0]
 p.close();assert advanced.scratch,'Prepared close destroyed transferred ownership'
 assert h.refresh==scenes[0].graph.refresh and expected.refresh==advanced.refresh
 print('PASS exact endpoint records, single advanced-history transfer, sampled-frame equality and independent cleanup')
finally:
 p.close();h.close();expected.close()
 if advanced:advanced.close()
