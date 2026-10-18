import ctypes as C,json,time,statistics
from pathlib import Path
from owned_sample_signature import signature
import owned_sampled_graph_gpu as graph_gpu
from owned_scene_gpu_wall import encode_draws as candidate
setup=Path('work/camera/test_sky_native_present_callback.py').read_text().split('class Context')[0];exec(compile(setup,'complete-fixture','exec'))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-static-record-cache-20261006');old={};exec(compile((cp/'owned_scene_gpu_wall.py.before').read_text(),'reference-wall-encoder','exec'),old)
def reference(*args,**kwargs):kwargs.pop('cache',None);return old['encode_draws'](*args,**kwargs)
checks=[];timings=[[],[]]
try:
 for i in range(101):
  alpha=i/100;outputs=[]
  for mode in ((0,1) if i%2==0 else (1,0)):
   graph_gpu.encode_draws=reference if mode==0 else candidate
   began=time.perf_counter_ns();sample=prepared.sample(alpha);timings[mode].append((time.perf_counter_ns()-began)/1e6);outputs.append((mode,signature(sample)))
  assert outputs[0][1]==outputs[1][1],alpha
  checks.append(dict(alpha=alpha,signature=outputs[0][1]))
 cache=prepared.pair.portal._gpu_wall_encoding_cache;assert 0<len(cache)<=4096
 result=dict(result='PASS_COMPLETE_SIGNATURES',complete_samples=len(checks),cache_entries=len(cache),reference_median_ms=statistics.median(timings[0]),candidate_median_ms=statistics.median(timings[1]),checks=checks,scope='Alternating full-frame/camera/model/clip/detail parity across101poses of one complete captured interval. Shared transform caches and scheduling affect timings; not live60fpsproof.')
finally:graph_gpu.encode_draws=candidate;prepared.close();history.close()
(cp/'complete-signatures.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='checks'})
