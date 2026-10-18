from pathlib import Path
import ctypes as C,bisect,json,math,random
from scene_batches import batches
class Entry(C.Structure):_fields_=[('time',C.c_double),('id',C.c_uint64)]
class Timeline(C.Structure):_fields_=[('epoch',C.c_uint64),('count',C.c_uint),('entries',Entry*16)]
class Sample(C.Structure):_fields_=[('epoch',C.c_uint64),('older',C.c_uint64),('newer',C.c_uint64),('alpha',C.c_double),('target',C.c_double)]
d=C.CDLL(str(Path('work/camera/presentation_timeline.dll').resolve()))
d.nf_timeline_push.argtypes=[C.POINTER(Timeline),C.c_uint64,C.c_uint64,C.c_double]
d.nf_timeline_sample.argtypes=[C.POINTER(Timeline),C.c_double,C.c_double,C.POINTER(Sample)]
report=[]
for filename in ['world.bin','stationary.bin']:
 times=[s['end_refresh'] for s in batches(Path('work/camera')/filename)];t=Timeline();sample=Sample();next_index=0;ready=0;before=0
 for now in range(times[0],times[-1]+1):
  while next_index<len(times) and times[next_index]<=now:
   assert d.nf_timeline_push(C.byref(t),1,next_index,times[next_index]);next_index+=1
  state=d.nf_timeline_sample(C.byref(t),now,5,C.byref(sample))
  if now-5<times[0]:assert state==1;before+=1;continue
  assert state==2,(filename,now,state)
  index=bisect.bisect_right(times,now-5)-1;assert sample.older==index
  interpolated=times[sample.older]*(1-sample.alpha)+times[sample.newer]*sample.alpha
  assert abs(interpolated-(now-5))<1e-9
  ready+=1
 report.append({'capture':filename,'scenes':len(times),'ready_display_samples':ready,'startup_hold_samples':before,'starved_after_startup':0})
t=Timeline();sample=Sample();r=random.Random(60);times=[]
for index in range(1000):
 time=(times[-1] if times else 0)+r.uniform(.01,5);times.append(time)
 assert d.nf_timeline_push(C.byref(t),2,index,time)
 for _ in range(3):
  target=r.uniform(times[max(0,index-15)],time)
  assert d.nf_timeline_sample(C.byref(t),target,0,C.byref(sample))==2
  expected=bisect.bisect_right(times,target)-1;assert sample.older==expected
  assert 0<=sample.alpha<=1
assert not d.nf_timeline_push(C.byref(t),2,1001,times[-1])
assert not d.nf_timeline_push(C.byref(t),1,1001,times[-1]+1)
assert not d.nf_timeline_push(C.byref(t),2,1001,math.nan)
assert d.nf_timeline_push(C.byref(t),3,9000,0) and t.count==1
assert d.nf_timeline_sample(C.byref(t),1,0,C.byref(sample))==3 and sample.older==sample.newer==9000
assert d.nf_timeline_sample(C.byref(t),0,0,C.byref(sample))==2
assert d.nf_timeline_sample(C.byref(t),0,-1,C.byref(sample))==0
result={'result':'PASS','capture_tests':report,'random_bracket_checks':3000,'scope':'Timestamp selection and discrete material timing only. Five-refresh diagnostic delay adds presentation latency. No GPU pacing, live buffer ownership, or input latency verification.'}
Path('work/camera/timeline-tests.json').write_text(json.dumps(result,indent=2));print(result)
