import os
"""Concurrent isolated expired-slot accounting and presentation lifecycle checks."""
import ctypes as C,json,time,threading
from pathlib import Path
d=C.CDLL(str((Path(__file__).parent/os.environ.get('NFSUG_RETIREMENT_TEST_DLL','owned-draw-commit-retirement-candidate.dll')).resolve()))
d.nf_owned_handoff_create.argtypes=[C.c_uint64];d.nf_owned_handoff_create.restype=C.c_void_p
for name in ('destroy','close'):getattr(d,'nf_owned_handoff_'+name).argtypes=[C.c_void_p]
cb=C.CFUNCTYPE(C.c_int,C.c_void_p)
commit=d.nf_owned_handoff_commit_sample;commit.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_double,cb,C.c_void_p,C.c_void_p]
retire=d.nf_owned_handoff_retire_expired;retire.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_void_p,C.c_size_t]
bind=d.nf_owned_handoff_bind_display_clock;bind.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64]
origin=time.perf_counter_ns()-1000000000;results=[]
for trial in range(20):
 q=d.nf_owned_handoff_create(2);assert bind(q,2,1,origin)==1;assert q
 entered=threading.Event();release=threading.Event();finished=[];calls=[];retired=[];barrier=threading.Barrier(3)
 @cb
 def present(ctx):
  calls.append(1);entered.set();assert release.wait(2);return 1
 def draw():
  out=(C.c_uint64*8)();finished.append((commit(q,2,1,100,104,0,.5,present,None,out),list(out)))
 def retirement():
  barrier.wait();out=(C.c_uint64*8)(*([123]*8));rc=retire(q,2,1,1,1,origin,out,64);retired.append((rc,list(out)))
 threads=[threading.Thread(target=retirement) for _ in range(2)];t=threading.Thread(target=draw)
 try:
  t.start();assert entered.wait(2)
  for v in threads:v.start()
  barrier.wait();time.sleep(.02);assert not retired and all(v.is_alive() for v in threads)
  release.set();t.join(2)
  for v in threads:v.join(2)
  assert not t.is_alive() and not any(v.is_alive() for v in threads)
  assert finished[0][0]==1 and finished[0][1][4]==0 and finished[0][1][7]==1
  assert sorted(rc for rc,_ in retired)==[-1,1] and calls==[1]
  for rc,row in retired:
   if rc==-1:assert row==[123]*8
   else:assert row[2:4]==[1,1] and row[6:]==[1,1]
  out=(C.c_uint64*8)();assert commit(q,2,1,100,104,2,.5,present,None,out)==1 and out[7]==2
  d.nf_owned_handoff_close(q);out=(C.c_uint64*8)(*([123]*8));assert retire(q,2,1,3,3,origin,out,64)==0 and list(out)==[123]*8
  results.append(dict(trial=trial,blocked_during_present=True,one_retirement_only=True,successful_serial=2,closed_no_write=True))
 finally:
  release.set();t.join(2)
  for v in threads:
   if v.ident is not None:v.join(2)
  assert not t.is_alive() and not any(v.is_alive() for v in threads)
  d.nf_owned_handoff_destroy(q)
close_trials=0
for trial in range(5):
 q=d.nf_owned_handoff_create(2);assert bind(q,2,1,origin)==1;entered=threading.Event();release=threading.Event();closed=threading.Event();completed=[]
 @cb
 def held_present(ctx):entered.set();assert release.wait(2);return 1
 def in_flight():
  out=(C.c_uint64*8)();completed.append(commit(q,2,1,100,104,0,.5,held_present,None,out))
 def close_owner():d.nf_owned_handoff_close(q);closed.set()
 t=threading.Thread(target=in_flight);closer=threading.Thread(target=close_owner)
 try:
  t.start();assert entered.wait(2);closer.start();time.sleep(.02);assert not closed.is_set() and closer.is_alive()
  release.set();t.join(2);closer.join(2);assert completed==[1] and closed.is_set() and not t.is_alive() and not closer.is_alive()
  out=(C.c_uint64*8)(*([123]*8));assert retire(q,2,1,1,1,origin,out,64)==0 and list(out)==[123]*8
  close_trials+=1
 finally:
  release.set();t.join(2)
  if closer.ident is not None:closer.join(2)
  assert not t.is_alive() and not closer.is_alive();d.nf_owned_handoff_destroy(q)
out=dict(library=d._name,close_during_present_trials=close_trials,result='PASS_CONCURRENT_EXPIRED_SLOT_SERIALIZATION',trials=len(results),results=results,scope='20 controlled races in isolated native DLL: retirement waits behind in-flight presentation, duplicate expired slot consumed exactly once, failed output unchanged, successful serial unaffected by retirement, post-close rejected. No live source-buffer/pause-race or 60fps qualification.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/expired-slot-accounting-component-20261010/concurrent-component.json').write_text(json.dumps(out,indent=2));print(out['result'],len(results),'trials')




