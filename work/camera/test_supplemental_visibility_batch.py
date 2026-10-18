import json,time,statistics
from pathlib import Path
from owned_sample_signature import signature
import owned_sampled_world_frame as module
from owned_complete_supplemental_gpu import sampled_gpu_records as candidate
from owned_continuous_wall_visibility import select_wall as select
setup=Path('work/camera/test_sky_native_present_callback.py').read_text().split('class Context')[0];exec(compile(setup,'fixture','exec'))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/supplemental-visibility-batch-20261006');old={'__file__':str(Path('work/camera/owned_wall_visibility_candidate.py').resolve())};exec(compile((cp/'owned_complete_supplemental_gpu.py.before').read_text().replace('sampled_edge,select_wall','sampled_edge'),'reference','exec'),old)
counts=[0,0];times=[[],[]]
def reference_select(*args):counts[0]+=1;return select(*args)
def candidate_select(*args):counts[1]+=1;return select(*args)
old['select_wall']=reference_select;import owned_wall_visibility_candidate as visibility_module;original_visibility_select=visibility_module.select_wall;visibility_module.select_wall=candidate_select;checks=[]
try:
 for i in range(101):
  alpha=i/100;outputs=[]
  for mode in ((0,1) if i%2==0 else (1,0)):
   module.sampled_gpu_records=old['sampled_gpu_records'] if mode==0 else candidate
   began=time.perf_counter_ns();sample=prepared.sample(alpha);times[mode].append((time.perf_counter_ns()-began)/1e6);outputs.append(signature(sample))
  assert outputs[0]==outputs[1],alpha;checks.append(dict(alpha=alpha,signature=outputs[0]))
 result=dict(result='PASS_ALL_COMPLETE_SIGNATURES',samples=101,python_fallback_reference=counts[0],python_fallback_candidate=counts[1],reference_median_ms=statistics.median(times[0]),candidate_median_ms=statistics.median(times[1]),checks=checks,scope='One complete captured interval at101poses, fullframe/camera/model/clip/details exact. Alternating shared transform caches, component timing not live60fpsproof.')
finally:module.sampled_gpu_records=candidate;visibility_module.select_wall=original_visibility_select;prepared.close();history.close()
(cp/'complete-signatures.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='checks'})
