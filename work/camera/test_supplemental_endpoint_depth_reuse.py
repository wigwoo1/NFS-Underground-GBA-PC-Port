import runpy,time,json,statistics
from pathlib import Path
import owned_complete_supplemental_candidates as module
scope={};exec(compile(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/supplemental-endpoint-depth-reuse-20261006/before.py').read_text(),'before.py','exec'),scope);old=scope['CompleteSupplementalCandidates'].sample;new=module.CompleteSupplementalCandidates.sample;times=[[],[]];checks=0
def compare(self,alpha):
 global checks
 result=[None,None]
 for index in ((0,1) if checks%2==0 else (1,0)):
  begin=time.perf_counter_ns();result[index]=(old if index==0 else new)(self,alpha);times[index].append(time.perf_counter_ns()-begin)
 assert [vars(x) for x in result[0]]==[vars(x) for x in result[1]],alpha;checks+=1
 return result[1]
module.CompleteSupplementalCandidates.sample=compare
runpy.run_path('work/camera/test_external_fullscene_transition.py')
result=dict(exact_candidate_calls=checks,reference_total_ms=sum(times[0])/1e6,candidate_total_ms=sum(times[1])/1e6,reference_median_ms=statistics.median(times[0])/1e6,candidate_median_ms=statistics.median(times[1])/1e6,scope='supplemental selection component, not live timing')
Path('work/camera/prototype-runs/supplemental-endpoint-depth-reuse.json').write_text(json.dumps(result,indent=2));print(result)
