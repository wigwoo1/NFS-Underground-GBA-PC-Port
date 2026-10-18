import runpy,ctypes as C,time,statistics
from pathlib import Path
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_motion import PreparedWorldMotion
from owned_sampled_world_frame import assemble_world
v=runpy.run_path('work/camera/test_external_fullscene_transition.py');before={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/assembler-endpoint-record-reuse-20261006/before.py').read_text(),before)
h=EndpointRoadPlanner(v['rom'],v['table']);roads,_=h.plan(v['scenes'][0].graph);p=PreparedWorldMotion(*v['frames'],*v['scenes'],h,roads,v['rom'])
def key(result):
 from owned_motion_pairs import records
 rows=records(result[0])['records'];clips=list(result[3])
 # The new model bounds channel is checked separately; surface bytes stay exact.
 for index,row in enumerate(rows):
  if row['kind']==3:clips[index*4:index*4+4]=[0,0,0,0]
 return (result[0],*[None if x is None else bytes(x) for x in result[1:3]],tuple(clips),result[4])
try:
 for i in range(101):
  a=before['assemble_world'](p.pair,p.roads,p.endpoint_roads,i/100,p.rom);b=p.sample(i/100)
  assert key(a)==key(b),i
 timings=[[],[]]
 for repeat in range(6):
  for index in ((0,1) if repeat%2==0 else (1,0)):
   begin=time.perf_counter_ns()
   for alpha in (.25,.5,.75):(before['assemble_world'],assemble_world)[index](p.pair,p.roads,p.endpoint_roads,alpha,p.rom)
   timings[index].append((time.perf_counter_ns()-begin)/1e6)
 print('PASS101 fullframe/camera/model/surface-clip/detail exact parity; median3samples ms',*[statistics.median(x) for x in timings])
finally:p.close();h.close()
