import sys,runpy,time,statistics,json
from pathlib import Path
import owned_sampled_graph_wall_visibility as v
from owned_wall_visibility_candidate import batch
original=v.select_wall;calls=[]
def track(*args):calls.append(args);return original(*args)
v.select_wall=track
sys.argv=['verify_captured_live_replay.py',sys.argv[1]]
runpy.run_path('work/camera/verify_captured_live_replay.py',run_name='__main__')
v.select_wall=original
expected=tuple(original(*c) for c in calls);actual=batch(calls);assert actual==expected
times={}
for name,fn in [('python',lambda:tuple(original(*c) for c in calls)),('native',lambda:batch(calls))]:
 rounds=[]
 for _ in range(10):
  start=time.perf_counter_ns()
  for _ in range(100):fn()
  rounds.append((time.perf_counter_ns()-start)/1e6)
 times[name]=statistics.median(rounds)
result=dict(result='PASS_EXACT_CAPTURED_WALL_VISIBILITY',calls=len(calls),median_100_batches_ms=times,scope='Captured wall visibility batch includes packing/output conversion; excludes candidate discovery and live timing')
Path('work/camera/wall-visibility-native-benchmark.json').write_text(json.dumps(result,indent=2));print(result)
