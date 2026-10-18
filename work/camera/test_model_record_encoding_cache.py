import sys,runpy,time,statistics,json,ctypes as C
from pathlib import Path
import owned_prepared_world_motion as module
candidate_scope={};exec(compile(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/model-record-encoding-cache-20261006/candidate.py').read_text(),'candidate.py','exec'),candidate_scope);candidate=candidate_scope['assemble_world']
scope={};exec(compile(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/model-record-encoding-cache-20261006/before.py').read_text(),'before.py','exec'),scope);reference=scope['assemble_world']
times=[[],[]];checked=0
def key(value):
 return (value[0],*(None if x is None else bytes(x) for x in value[1:4]),value[4])
def compare(*args):
 global checked
 results=[None,None]
 for which in ((0,1) if checked%2==0 else (1,0)):
  start=time.perf_counter_ns();results[which]=(reference if which==0 else candidate)(*args);elapsed=time.perf_counter_ns()-start
  if 0<args[3]<1:times[which].append(elapsed)
 assert key(results[0])==key(results[1]),args[3]
 checked+=1
 return results[1]
module.assemble_world=compare
runpy.run_path('work/camera/test_external_fullscene_transition.py')
result=dict(exact_samples=checked,reference_median_ms=statistics.median(times[0])/1e6,candidate_median_ms=statistics.median(times[1])/1e6,reference_total_ms=sum(times[0])/1e6,candidate_total_ms=sum(times[1])/1e6,scope='alternating complete scene assembly wall time, no live throughput claim')
Path('work/camera/prototype-runs/model-record-encoding-cache-'+sys.argv[2]+'.json').write_text(json.dumps(result,indent=2));print(result)
