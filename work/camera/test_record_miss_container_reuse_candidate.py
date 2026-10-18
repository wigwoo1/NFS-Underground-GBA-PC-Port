import json,sys,time,statistics,types
from pathlib import Path
import owned_motion_pairs as module
report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture']);frames=[(folder/(n+'.frame.bin')).read_bytes() for n in ('older','newer')]
original=types.FunctionType(module.records.__code__,module.records.__globals__,argdefs=module.records.__defaults__)
import owned_record_miss_container_reuse_install_candidate
candidate=module.records;times=[[],[]]
for trial in range(32):
 values=[]
 for mode,fn in enumerate((original,candidate)):
  module._record_cache.entries=[];begin=time.perf_counter_ns();value=[fn(f) for f in frames];times[mode].append(time.perf_counter_ns()-begin);values.append(value)
 assert values[0]==values[1]
 # Caller mutation cannot alter immutable cache contents or another return.
 pristine=candidate(frames[-1]);modified=candidate(frames[-1]);modified['records'][0]['blocks'].clear();modified['records'][0]['kind']=99;modified['records'].clear();assert candidate(frames[-1])==pristine
out=dict(result='PASS_CAPTURED_RECORD_MISS_REUSE',comparisons=64,mutation_checks=32,original_median_ms=statistics.median(times[0])/1e6,candidate_median_ms=statistics.median(times[1])/1e6,scope='Captured2endpoint record decode and caller isolation; no native pixels/live cadence proof.')
Path('work/camera/prototype-runs/record-miss-container-reuse-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));module._record_cache.entries=[]
