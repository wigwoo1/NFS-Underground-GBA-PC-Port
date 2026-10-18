import sys,runpy,time,statistics,json
from pathlib import Path
import owned_continuous_wall_visibility as visibility
prior={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/portal-transform-batch-integration-20261006/visibility-before.py').read_text(),prior)
from owned_ring_correction_candidate import corrections as original
keys=set()
def track(*args):keys.add(args);return original(*args)
visibility._ring_endpoint_corrections=track
sys.argv=['verify_captured_live_replay.py',sys.argv[1]]
runpy.run_path('work/camera/verify_captured_live_replay.py',run_name='__main__')
visibility._ring_endpoint_corrections=original
for args in keys:assert original.__wrapped__(*args)==prior['_ring_endpoint_corrections'].__wrapped__(*args)
times={}
for name,fn in [('before',prior['_ring_endpoint_corrections'].__wrapped__),('after',original.__wrapped__)]:
 batches=[]
 for _ in range(10):
  start=time.perf_counter_ns()
  for _ in range(100):
   for args in keys:fn(*args)
  batches.append((time.perf_counter_ns()-start)/1e6)
 times[name]=statistics.median(batches)
result=dict(result='PASS_EXACT_RING_CORRECTIONS',unique_rings=len(keys),repeats_per_batch=100,median_batch_ms=times,scope='Actual captured ring/camera/endpoints; uncached correction computation including packing and validation; not live cadence')
Path('work/camera/whole-ring-native-batch-benchmark.json').write_text(json.dumps(result,indent=2));print(result)
