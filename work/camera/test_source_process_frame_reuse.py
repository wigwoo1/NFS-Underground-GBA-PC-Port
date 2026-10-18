import json,time,statistics
from pathlib import Path
from owned_source_process_service_candidate import ProcessSamples,encode_samples
from owned_source_process_sidecar_candidate import encode
source=Path('work/camera/test_precomputed_source_eight_samples.py').read_text();ns={};exec(source[:source.index(' import gc')]+'\nfinally: pass\n',ns)
owner=ns['cached'];identity=(ns['scenes'][0].graph.epoch,ns['scenes'][0].graph.refresh,ns['scenes'][1].graph.refresh);payload=encode_samples(owner.samples);payload['source_sidecar']=encode(owner,identity);owner.close();times={False:[],True:[]};checks=[]
try:
 for trial in range(12):
  outputs={}
  for reuse in ((False,True) if trial%2==0 else (True,False)):
   ProcessSamples.reuse_immutable_frames=reuse;start=time.perf_counter_ns();out=ProcessSamples(payload,identity);times[reuse].append((time.perf_counter_ns()-start)/1e6);outputs[reuse]=out
  a,b=outputs[False],outputs[True]
  try:
   for alpha in a.samples:
    x,y=a.samples[alpha],b.samples[alpha];assert x[0]==y[0] and all(bytes(i)==bytes(j) for i,j in zip(x[1:4],y[1:4]));m,n=a.source_masks[alpha],b.source_masks[alpha];assert bytes(m[0])==bytes(n[0]) and bytes(m[1])==bytes(n[1]) and m[2:]==n[2:]
   keys=list(b.samples);unique=len({id(x[0]) for x in b.samples.values()});assert unique==len({x[0] for x in b.samples.values()})
   old=bytes(a.samples[keys[0]][2]);b.samples[keys[0]][2][0]+=1;assert bytes(a.samples[keys[0]][2])==old
   if trial==0:checks=dict(samples=len(keys),unique_frame_objects=unique,logical_frame_bytes=sum(len(x[0]) for x in b.samples.values()),unique_frame_bytes=sum(len(x[0]) for i,x in enumerate(b.samples.values()) if id(x[0]) not in {id(y[0]) for y in list(b.samples.values())[:i]}))
  finally:a.close();b.close()
finally:ProcessSamples.reuse_immutable_frames=True;ns['history'].close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-process-frame-reuse-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',checks=checks,median_ms={str(k):statistics.median(v) for k,v in times.items()},samples_ms={str(k):v for k,v in times.items()},scope='Actual eight source samples decoded after original owner close; immutable frame reuse and mutable native buffer independence, component timings only.'),indent=2))
for name in ('test_source_process_frame_reuse.py','owned_source_process_service_candidate.py'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
print(checks,{str(k):statistics.median(v) for k,v in times.items()})
