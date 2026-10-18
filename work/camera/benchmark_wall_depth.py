from pathlib import Path
from unittest.mock import patch
import time,statistics,json
setup=Path('work/camera/test_wall_depth_equivalence.py').read_text().split('try:')[0]
exec(compile(setup,'captured_projection_setup','exec'))
cases=[]
def capture(*args):cases.append(args);return visibility.select_wall(*args)
try:
 with patch.object(walls,'select_wall',capture):
  for alpha in (.1,.3,.5,.7,.9):walls.selected_graph_walls(prepared.pair.portal,alpha)
 for args in cases:
  a=visibility.select_wall(*args);b=namespace['select_wall'](*args)
  assert (a.visible,a.reason,a.x,a.y,a.flags)==(b.visible,b.reason,b.x,b.y,b.flags)
 old_coordinate=namespace['coordinate'];count=[0]
 def old_count(*args):count[0]+=1;return old_coordinate(*args)
 namespace['coordinate']=old_count
 for args in cases:namespace['select_wall'](*args)
 old_depth_evaluations=count[0];namespace['coordinate']=old_coordinate
 with patch.object(visibility,'projection_depth',wraps=visibility.projection_depth) as measured:
  for args in cases:visibility.select_wall(*args)
  new_depth_evaluations=measured.call_count
 timings={}
 for name,fn in (('original',namespace['select_wall']),('shared',visibility.select_wall)):
  rounds=[]
  for _ in range(7):
   begin=time.perf_counter_ns()
   for repeat in range(20):
    for args in cases:fn(*args)
   rounds.append(time.perf_counter_ns()-begin)
  timings[name]=statistics.median(rounds)/1e6
 result=dict(result='PASS_EXACT_CAPTURED_WALLS',cases=len(cases),old_depth_evaluations=old_depth_evaluations,new_depth_evaluations=new_depth_evaluations,median_batch_ms=timings,scope='Fixed captured CPU wall-selector microbenchmark,20 repetitions/7 rounds; not live cadence or GPU timing')
 Path('work/camera/wall-depth-benchmark.json').write_text(json.dumps(result,indent=2));print(result)
finally:prepared.close();history.close()
