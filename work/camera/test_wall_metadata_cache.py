import runpy,time,statistics
from pathlib import Path
from owned_sampled_graph_wall_visibility import selected_graph_walls,wall_metadata
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
v=runpy.run_path('work/camera/audit_failed_world_motion.py')
motion=PreparedMotionPair(*v['data']['frames'],*v['scenes']);portal=PortalMotionPair(v['scenes'][0].graph.graph,v['scenes'][1].graph.graph,v['data']['table'],motion)
before={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/wall-metadata-cache-20261006/before.py').read_text(),before)
try:
 for i in range(101):assert selected_graph_walls(portal,i/100)==before['selected_graph_walls'](portal,i/100)
 assert len(portal._wall_metadata_cache)==2
 assert wall_metadata(portal,portal.older) is wall_metadata(portal,portal.older)
 try:wall_metadata(portal,portal.older)[0][0]=None
 except TypeError:pass
 else:raise AssertionError('mutable metadata')
 timings=[[],[]]
 for repeat in range(10):
  for index in ((0,1) if repeat%2==0 else (1,0)):
   begin=time.perf_counter_ns()
   for i in range(1,100):(before['selected_graph_walls'],selected_graph_walls)[index](portal,i/100)
   timings[index].append((time.perf_counter_ns()-begin)/1e6)
 print('PASS101 exact selected walls/materials/clips; bounded immutable metadata; alternating99sample median ms',*[statistics.median(x) for x in timings])
finally:portal._wall_metadata_cache.clear()
