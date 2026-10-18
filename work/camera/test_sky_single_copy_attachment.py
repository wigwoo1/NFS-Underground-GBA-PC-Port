import runpy,time,json,statistics
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-single-copy-attachment-20261006')
ns=runpy.run_path('work/camera/test_owned_sky_frame.py');new=ns['attach_sky'];old=runpy.run_path(str(cp/'before.py'))['attach_sky'];scene=ns['scene'];frame=ns['original'];offset=ns['offset'];checks=[]
image,mask=scene.sky.boundary.plane()
cases=[]
for label,coverage in [('uncovered',0),('covered',1),('invalid',2),('conflict',1)]:
 b=bytearray(frame);b[offset+38400+10560:offset+38400+25696]=bytes([coverage])*15136
 if coverage==1:b[offset+10560:offset+25696]=image[10560:25696]
 if label=='conflict':b[offset+10560]^=1
 cases.append((label,bytes(b)))
for label,b in cases:
 outcomes=[]
 for api in [old,new]:
  try:outcomes.append(('ok',api(b,scene)))
  except ValueError as e:outcomes.append(('error',str(e)))
 assert outcomes[0]==outcomes[1],label;checks.append(dict(case=label,result=outcomes[0][0]))
for variant in [cases[0][1],bytearray(cases[0][1]),memoryview(cases[0][1])]:
 assert old(variant,scene)==new(variant,scene)
checks.append(dict(case='bytes_bytearray_memoryview',result='ok'))
results={}
for name,api in [('before',old),('after',new)]:
 times=[]
 for i in range(20):
  start=time.perf_counter_ns();actual=api(cases[0][1],scene);times.append((time.perf_counter_ns()-start)/1e6)
 assert actual==new(cases[0][1],scene)
 results[name]=dict(median_ms=statistics.median(times),max_ms=max(times))
(cp/'equivalence-timing.json').write_text(json.dumps(dict(checks=checks,timing=results,scope='Recorded endpoint attachment component benchmark, not live cadence proof'),indent=2));print('PASS',checks,results)
