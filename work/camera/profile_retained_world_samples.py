import runpy,cProfile,pstats,time
from pathlib import Path
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
v=runpy.run_path('work/camera/audit_failed_world_motion.py');h=EndpointRoadPlanner(v['rom'],v['data']['table']);roads,_=h.plan(v['scenes'][0].graph);prepared=PreparedWorldMotion(*v['data']['frames'],*v['scenes'],h,roads,v['rom'])
def samples():
 for i in range(20):
  for alpha in (.25,.5,.75):prepared.sample(alpha)
try:
 prepared.sample(.5);profile=cProfile.Profile();profile.runcall(samples);output=Path('work/camera/prototype-runs')/('isolated-world-samples-'+str(time.time_ns())+'.prof');profile.dump_stats(str(output))
 with output.with_suffix('.txt').open('w',encoding='utf-8') as stream:pstats.Stats(profile,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(25)
 print(output.with_suffix('.txt').read_text())
finally:prepared.close();h.close()
