import ctypes as C,time,threading,json
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-batch-present-availability-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P);Init=C.CFUNCTYPE(C.c_int);Poll=C.CFUNCTYPE(C.c_int,C.c_uint)
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
for n,a in [('destroy',[P]),('close',[P]),('pause',[P,C.c_uint]),('epoch',[P,U])]:getattr(d,'nf_owned_handoff_'+n).argtypes=a
d.nf_owned_display_availability_configure.argtypes=[Init,Poll]
f=d.nf_owned_handoff_draw_wait_commit_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
checks=[]
for mode in ['pause','epoch','close','timeout']:
 q=d.nf_owned_handoff_create(1);entered=threading.Event();calls=[];result=[]
 init=Init(lambda:0)
 def poll(ms):entered.set();time.sleep(ms/1000);return 0
 poll_cb=Poll(poll);draw=CB(lambda _:calls.append('draw') or 0);present=CB(lambda _:calls.append('present') or 1)
 assert d.nf_owned_display_availability_configure(init,poll_cb)==1
 def run():result.append(f(q,1,1,1,2,1,.5,0,draw,None,present,None,(U*8)(),(U*4)(),(U*7)()))
 t=threading.Thread(target=run);t.start();assert entered.wait(1);start=time.perf_counter()
 if mode=='pause':assert d.nf_owned_handoff_pause(q,1)==1
 elif mode=='epoch':assert d.nf_owned_handoff_epoch(q,2)==1
 elif mode=='close':d.nf_owned_handoff_close(q)
 t.join(3);assert not t.is_alive() and result==([-1] if mode=='timeout' else [0]) and not calls,(mode,result,calls)
 checks.append(dict(mode=mode,result=result[0],elapsed_ms=(time.perf_counter()-start)*1000));d.nf_owned_handoff_destroy(q)
out=dict(result='PASS_AVAILABILITY_RETIREMENT_AND_TOTAL_TIMEOUT',checks=checks,scope='Synthetic unavailable display: concurrent lifecycle retirement never draws/presents; two-second total timeout fails explicitly. No live display cadence proof.')
(p/'prototype-runs/availability-retirement.json').write_text(json.dumps(out,indent=2));print(out)
