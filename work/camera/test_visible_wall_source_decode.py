import runpy,time,json
from pathlib import Path
import owned_motion_wall_regions as module
scope={};exec(compile(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/visible-wall-source-decode-20261006/before.py').read_text(),'before.py','exec'),scope);old=scope['wall_region_candidates'];new=module.wall_region_candidates;times=[0,0];checks=0
# Old and new have distinct private per-portal caches for a fair cold-to-warm comparison.
def compare(portal,alpha):
 global checks
 results=[]
 for index,fn in enumerate((old,new)):
  attr='_reference_wall_source_cache' if index==0 else '_candidate_wall_source_cache'
  if hasattr(portal,attr):portal._wall_source_cache=getattr(portal,attr)
  elif hasattr(portal,'_wall_source_cache'):del portal._wall_source_cache
  begin=time.perf_counter_ns();results.append(fn(portal,alpha));times[index]+=time.perf_counter_ns()-begin
  setattr(portal,attr,portal._wall_source_cache)
 assert [vars(x) for x in results[0]]==[vars(x) for x in results[1]],alpha;checks+=1
 return results[1]
module.wall_region_candidates=compare
import owned_sampled_graph_wall_visibility as selection
selection.wall_region_candidates=compare
runpy.run_path('work/camera/test_external_fullscene_transition.py')
result=dict(exact_candidate_calls=checks,reference_total_ms=times[0]/1e6,candidate_total_ms=times[1]/1e6,scope='101-scene alpha candidate decode; visibility always sampled fresh')
Path('work/camera/prototype-runs/visible-wall-source-decode.json').write_text(json.dumps(result,indent=2));print(result)
