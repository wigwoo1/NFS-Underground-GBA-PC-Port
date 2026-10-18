import ctypes as C,runpy,json,time,statistics
from pathlib import Path
from owned_source_model_anchor_candidate import SourceModelAnchors
base=runpy.run_path('work/camera/owned_source_model_anchor_candidate.py.before-buffer-copy')['SourceModelAnchors']
source=Path('work/camera/test_precomputed_source_eight_samples.py').read_text();ns={};exec(source[:source.index(' import gc')]+'\nfinally: pass\n',ns)
owner=ns['cached'];new=ns['anchors'];old=base.__new__(base);old.__dict__.update(new.__dict__);cases=list(owner.samples.items());owner.close();ns['history'].close()
for alpha,(frame,camera,models,bounds,detail) in cases:
 a=old.sample(frame,models,alpha);b=new.sample(frame,models,alpha)
 assert bytes(a)==bytes(b)
 original=bytes(models);b[0]+=1;assert bytes(models)==original and bytes(a)!=bytes(b)
 # Existing generic sequence callers remain supported.
 assert bytes(old.sample(frame,list(models),alpha))==bytes(new.sample(frame,list(models),alpha))
times={'baseline':[],'buffer_copy':[]}
for trial in range(20):
 for label,anchor in ([('baseline',old),('buffer_copy',new)] if trial%2==0 else [('buffer_copy',new),('baseline',old)]):
  start=time.perf_counter_ns()
  for repeat in range(50):
   for alpha,(frame,_,models,_,_) in cases:anchor.sample(frame,models,alpha)
  times[label].append((time.perf_counter_ns()-start)/1e6)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-anchor-buffer-copy-20261007');cp.mkdir(exist_ok=True)
result=dict(result='PASS',captured_samples=len(cases),private_output_independent=True,generic_sequence_parity=True,median_400_calls_ms={k:statistics.median(v) for k,v in times.items()},trials_ms=times,scope='Captured source model matrices after owner close; baseline byte parity and independence, component benchmark only. Not live smoothness proof.')
(cp/'result.json').write_text(json.dumps(result,indent=2))
for name in ('test_source_anchor_buffer_copy.py','owned_source_model_anchor_candidate.py','owned_source_model_anchor_candidate.py.before-buffer-copy'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
print(result['median_400_calls_ms'])