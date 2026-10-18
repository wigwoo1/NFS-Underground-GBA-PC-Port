from pathlib import Path
from types import SimpleNamespace
import time,statistics,json
import owned_sampled_graph_wall_visibility as walls
exec(compile(Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0],'captured_scene_setup','exec'))
prior={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/wall-metadata-pass-20261006/wall-metadata-before.py').read_text(),prior)
try:
 graphs=(prepared.pair.portal.older,prepared.pair.portal.newer)
 for graph in graphs:
  old=prior['wall_metadata'](SimpleNamespace(),graph);new=walls.wall_metadata(SimpleNamespace(),graph)
  assert old==new
  assert all(value[2] is new[2][key] for key,value in new[0].items())
 times={}
 for name,fn in (('prior',prior['wall_metadata']),('shared',walls.wall_metadata)):
  rounds=[]
  for _ in range(7):
   begin=time.perf_counter_ns()
   for repeat in range(500):
    for graph in graphs:fn(SimpleNamespace(),graph)
   rounds.append((time.perf_counter_ns()-begin)/1e6)
  times[name]=statistics.median(rounds)
 portal=prepared.pair.portal
 a=walls.wall_metadata(portal,portal.older)[2];b=walls.wall_metadata(portal,portal.newer)[2]
 rounds=[]
 for _ in range(7):
  begin=time.perf_counter_ns()
  for repeat in range(10000):assert a==b
  rounds.append((time.perf_counter_ns()-begin)/1e6)
 result=dict(result='PASS_EXACT_METADATA',median_1000_cold_builds_ms=times,offset_comparison_us=statistics.median(rounds)/10,scope='Captured endpoint CPU microbenchmark; no live cadence or scanout claim')
 Path('work/camera/wall-metadata-benchmark.json').write_text(json.dumps(result,indent=2));print(result)
finally:prepared.close();history.close()
