import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path('work/camera').resolve()))
import owned_portal_traversal as old
import owned_portal_point_reuse_candidate as new
setup=Path('work/camera/test_owned_portal_queue.py').read_text().split('checks=[]')[0]
ns={};exec(compile(setup,'portal-fixture','exec'),ns)
checks=0;times=[0,0]
for scene in ns['scenes'].values():
 args=(scene['graph'],scene['matrix'],scene['framebuffer'],scene['expected'][0],ns['reciprocal'])
 normal=tuple(float(v)/256 if i<9 else float(v) for i,v in enumerate(scene['matrix']))
 for mode in (None,normal):
  kw={} if mode is None else dict(sampled_camera=mode,endpoint_correction=(scene['matrix'],scene['matrix'],normal,normal,.35))
  expected=old.traverse(*args,**kw);actual=new.traverse(*args,**kw);assert actual==expected;checks+=1
  if mode is None:assert actual==scene['expected']
  for repeat in range(20):
   for i,fn in ((0,old.traverse),(1,new.traverse)) if repeat%2==0 else ((1,new.traverse),(0,old.traverse)):
    begin=time.perf_counter_ns();assert fn(*args,**kw)==expected;times[i]+=time.perf_counter_ns()-begin
out=dict(result='PASS_LOCAL_PORTAL_POINT_REUSE_QUEUE_PARITY',checks=checks,reference_ns=times[0],candidate_ns=times[1],scope='Captured raw graph queues and same-camera corrected continuous samples; exact queue parity. Cache is per traversal, immutable two-coordinate key and tuple results. Not fullscene4K/spawn/live/independent fractional fidelity proof.')
Path('work/camera/prototype-runs/portal-point-reuse-20261009.json').write_text(json.dumps(out,indent=2));print(out)
