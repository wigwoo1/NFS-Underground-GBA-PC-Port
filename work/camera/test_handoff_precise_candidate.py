import ctypes as C,time,threading,json,statistics
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-frame-handoff-precise-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64
for n,a,z in [('create',[U],P),('destroy',[P],None),('pause',[P,C.c_uint],C.c_int),('epoch',[P,U],C.c_int),('close',[P],None),('wait_token',[P,U,U,P],C.c_int)]:
 f=getattr(d,'nf_owned_handoff_'+n);f.argtypes=a;f.restype=z
late=[]
for duration in [1000000,2000000,5000000]*20:
 q=d.nf_owned_handoff_create(1);v=(U*4)();deadline=time.perf_counter_ns()+duration
 try:
  assert d.nf_owned_handoff_wait_token(q,1,1,deadline,v)==1
  assert v[1]==deadline and v[2]>=deadline and v[0]<=v[2];late.append((v[2]-deadline)/1e6)
 finally:d.nf_owned_handoff_destroy(q)
checks=[]
for mode in ['pause','epoch','close']:
 q=d.nf_owned_handoff_create(1);v=(U*4)();result=[];started=threading.Event()
 def run():
  started.set();result.append(d.nf_owned_handoff_wait_token(q,1,1,time.perf_counter_ns()+500000000,v))
 t=threading.Thread(target=run);t.start();assert started.wait(1);time.sleep(.01)
 began=time.perf_counter_ns()
 if mode=='pause':assert d.nf_owned_handoff_pause(q,1)==1
 elif mode=='epoch':assert d.nf_owned_handoff_epoch(q,2)==1
 else:d.nf_owned_handoff_close(q)
 t.join(1);assert not t.is_alive() and result==[0];checks.append(dict(mode=mode,cancel_ms=(time.perf_counter_ns()-began)/1e6));d.nf_owned_handoff_destroy(q)
v=(U*4)();q=d.nf_owned_handoff_create(1)
try:
 assert d.nf_owned_handoff_wait_token(q,1,1,time.perf_counter_ns()+3000000000,v)==-1
 assert d.nf_owned_handoff_wait_token(q,1,2,time.perf_counter_ns(),v)==0
finally:d.nf_owned_handoff_destroy(q)
out=dict(result='PASS_NO_EARLY_RETURN_AND_RETIREMENT',deadlines=len(late),median_lateness_ms=statistics.median(late),max_lateness_ms=max(late),cancellations=checks,scope='Local component deadline and lifecycle checks; timers recheck original absolute deadline, no live smoothness or scheduler latency bound.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/handoff-precise-20261008');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(out,indent=2));print(out)
