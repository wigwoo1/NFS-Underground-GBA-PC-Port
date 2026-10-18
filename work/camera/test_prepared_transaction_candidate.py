import ctypes as C,time,threading,json
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-batch-present-prepared-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P);Init=C.CFUNCTYPE(C.c_int);Poll=C.CFUNCTYPE(C.c_int,C.c_uint);Action=C.CFUNCTYPE(C.c_int,U,U,U);Final=C.CFUNCTYPE(C.c_int,U,U,U,P)
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
for n,a in [('destroy',[P]),('close',[P]),('pause',[P,C.c_uint]),('epoch',[P,U])]:getattr(d,'nf_owned_handoff_'+n).argtypes=a
d.nf_owned_display_availability_configure.argtypes=[Init,Poll];d.nf_owned_prepared_configure.argtypes=[Action,Action,Final]
f=d.nf_owned_handoff_draw_wait_commit_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,CB,P,P,P,P]
checks=[]
for mode in ['success','pause','epoch','close','prepare_error']:
 q=d.nf_owned_handoff_create(1);calls=[];entered=threading.Event();release=threading.Event();result=[];deadline=time.perf_counter_ns()+200000000
 init=Init(lambda:0);poll=Poll(lambda ms:1);draw=CB(lambda _:calls.append('draw') or 0);legacy=CB(lambda _:calls.append('legacy') or 1)
 def prepare(e,g,i):
  calls.append(['prepare',e,g,i]);entered.set()
  if mode not in ['success','prepare_error']:assert release.wait(1)
  return 99 if mode=='prepare_error' else 0
 prepare_cb=Action(prepare);abort=Action(lambda e,g,i:calls.append(['abort',e,g,i]) or 0)
 def final(e,g,i,ctx):calls.append(['present',e,g,i]);assert time.perf_counter_ns()>=deadline;return 1
 final_cb=Final(final)
 assert d.nf_owned_display_availability_configure(init,poll)==1 and d.nf_owned_prepared_configure(prepare_cb,abort,final_cb)==1
 def run():result.append(f(q,1,1,1,2,7,.5,deadline,draw,None,legacy,None,(U*8)(),(U*4)(),(U*7)()))
 t=threading.Thread(target=run);t.start();assert entered.wait(1)
 if mode=='pause':assert d.nf_owned_handoff_pause(q,1)==1
 elif mode=='epoch':assert d.nf_owned_handoff_epoch(q,2)==1
 elif mode=='close':d.nf_owned_handoff_close(q)
 release.set();t.join(2);assert not t.is_alive()
 expected=1 if mode=='success' else -1 if mode=='prepare_error' else 0
 assert result==[expected] and 'legacy' not in calls,(mode,result,calls)
 assert calls==(['draw',['prepare',1,1,7],['present',1,1,7]] if mode=='success' else ['draw',['prepare',1,1,7]] if mode=='prepare_error' else ['draw',['prepare',1,1,7],['abort',1,1,7]]),(mode,calls)
 checks.append(dict(mode=mode,result=expected,calls=calls));d.nf_owned_handoff_destroy(q)
out=dict(result='PASS_PREPARE_BEFORE_WAIT_AND_ABORT_ON_RETIREMENT',checks=checks,scope='Synthetic prepared transfer/native transaction order, concurrent pause/epoch/close during preparation, matched identity abort and original deadline guard; no GPU or live cadence proof.')
(p/'prototype-runs/prepared-transaction-tests.json').write_text(json.dumps(out,indent=2));print(out)
