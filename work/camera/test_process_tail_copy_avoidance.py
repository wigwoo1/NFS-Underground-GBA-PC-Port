import runpy,time,statistics,json
from pathlib import Path
from owned_process_preparation_service import encode_samples
v=runpy.run_path('work/camera/test_external_fullscene_transition.py');scope={};exec(compile(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/process-tail-copy-avoidance-20261006/before.py').read_text(),'before.py','exec'),scope);old=scope['encode_samples'];times=[[],[]];checks=0
for repeat in range(6):
 for start in range(0,101,8):
  samples={i/100:v['samples'][i] for i in range(start,min(start+8,101))};results=[None,None]
  for index in ((0,1) if repeat%2==0 else (1,0)):
   begin=time.perf_counter_ns();results[index]=(old if index==0 else encode_samples)(samples);times[index].append(time.perf_counter_ns()-begin)
  assert results[0]==results[1];checks+=len(samples)
result=dict(exact_samples=checks,reference_median_ms=statistics.median(times[0])/1e6,candidate_median_ms=statistics.median(times[1])/1e6,reference_total_ms=sum(times[0])/1e6,candidate_total_ms=sum(times[1])/1e6,scope='alternating isolated output encoding')
Path('work/camera/prototype-runs/process-tail-copy-avoidance.json').write_text(json.dumps(result,indent=2));print(result)
