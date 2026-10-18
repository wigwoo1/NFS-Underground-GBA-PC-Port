"""Lifecycle cancellation and deadline tests; stand-in callbacks, no GPU claim."""
import ctypes as C,json,time,threading
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;CB=C.CFUNCTYPE(C.c_int,P)
d=C.CDLL(str(Path('work/camera/owned-wait-commit-candidate.dll').resolve()))
d.nf_owned_handoff_create.argtypes=[U];d.nf_owned_handoff_create.restype=P
for name in ['destroy','close']:getattr(d,'nf_owned_handoff_'+name).argtypes=[P]
d.nf_owned_handoff_pause.argtypes=[P,C.c_uint];d.nf_owned_handoff_epoch.argtypes=[P,U]
f=d.nf_owned_handoff_wait_commit_sample;f.argtypes=[P,U,U,U,U,U,C.c_double,U,CB,P,P,P,P]
checks=[]
for action in ['deadline','pause','epoch','close']:
 q=d.nf_owned_handoff_create(7);out=(U*8)(*([123]*8));wait=(U*4)();stages=(U*7)();calls=[];results=[];errors=[]
 @CB
 def present(ctx):calls.append(time.perf_counter_ns());return 1
 deadline=time.perf_counter_ns()+150000000
 def run():
  try:results.append(f(q,7,1,10,14,20,.5,deadline,present,None,out,wait,stages))
  except BaseException as e:errors.append(repr(e))
 t=threading.Thread(target=run);t.start()
 try:
  limit=time.perf_counter()+2
  while not wait[0] and t.is_alive() and time.perf_counter()<limit:time.sleep(.001)
  assert wait[0] and t.is_alive(), 'Native waiting entry not observed'
  if action=='pause':assert d.nf_owned_handoff_pause(q,1)
  elif action=='epoch':assert d.nf_owned_handoff_epoch(q,8)
  elif action=='close':d.nf_owned_handoff_close(q)
  t.join(3);assert not t.is_alive() and not errors
  if action=='deadline':
   assert results==[1] and len(calls)==1 and calls[0]>=deadline and out[6]>=deadline
   assert wait[2]>=deadline and list(out)[:5]==[7,1,10,14,20]
   assert all(a<=b for a,b in zip(stages,stages[1:]))
  else:assert results==[0] and not calls and list(out)==[123]*8
  checks.append(dict(action=action,result=results[0],native_wait_ms=(wait[2]-wait[0])/1e6,callback_count=len(calls)))
 finally:
  t.join(3)
  assert not t.is_alive(), 'Do not destroy live native owner'
  d.nf_owned_handoff_destroy(q)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-wait-commit-concurrency-20261007');cp.mkdir(exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Observed native wait entry, concurrent native lifecycle cancellation and original deadline; stand-in callbacks, no live GPU or Python publication-lock concurrency proof.'),indent=2))
print(json.dumps(checks,indent=2))
