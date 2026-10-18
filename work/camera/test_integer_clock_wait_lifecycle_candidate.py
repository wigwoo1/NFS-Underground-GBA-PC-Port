import ctypes as C,time,threading,json
from pathlib import Path
k=C.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=C.c_void_p;k.GetProcessHandleCount.argtypes=[C.c_void_p,C.c_void_p]
def handles():
 n=C.c_uint();assert k.GetProcessHandleCount(k.GetCurrentProcess(),C.byref(n));return n.value
results=[]
for name in ('owned-draw-commit-integer-clock-candidate.dll','owned-draw-commit-integer-clock-create-failure.dll','owned-draw-commit-integer-clock-set-failure.dll'):
 d=C.CDLL(str((Path(__file__).parent/name).resolve()));d.nf_owned_handoff_create.argtypes=[C.c_uint64];d.nf_owned_handoff_create.restype=C.c_void_p;d.nf_owned_handoff_destroy.argtypes=[C.c_void_p];d.nf_owned_handoff_close.argtypes=[C.c_void_p];d.nf_owned_handoff_pause.argtypes=[C.c_void_p,C.c_uint]
 f=d.nf_owned_handoff_wait_token;f.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64,C.c_void_p]
 q=d.nf_owned_handoff_create(1)
 try:
  # Warm runtime before handle accounting; repeated actual waits must release timers.
  out=(C.c_uint64*4)();assert f(q,1,1,time.perf_counter_ns()+1000000,out)==1;before=handles()
  for i in range(100):
   target=time.perf_counter_ns()+1000000;assert f(q,1,1,target,out)==1 and out[1]==target and out[2]>=target
  after=handles();assert after==before,(name,before,after)
  assert f(None,1,1,0,out)==-1 and f(q,0,1,0,out)==-1 and f(q,1,0,0,out)==-1 and f(q,1,1,0,None)==-1
  assert f(q,1,1,time.perf_counter_ns()+3000000000,out)==-1;assert f(q,2,1,0,out)==0
  started=threading.Event();done=[]
  def wait():
   a=(C.c_uint64*4)();started.set();rc=f(q,1,1,time.perf_counter_ns()+500000000,a);done.append((rc,list(a)))
  t=threading.Thread(target=wait);t.start();assert started.wait(1);time.sleep(.01);assert d.nf_owned_handoff_pause(q,1)==1;t.join(1);assert not t.is_alive() and done[0][0]==0
  assert d.nf_owned_handoff_pause(q,0)==1;assert f(q,1,1,0,out)==0 and f(q,1,3,0,out)==1
  d.nf_owned_handoff_close(q);assert f(q,1,3,0,out)==0
  results.append(dict(library=name,waits=100,no_early_return=True,handles_before=before,handles_after=after,cancellation=True,resume_new_generation=True,closed_owner_rejected=True))
 finally:d.nf_owned_handoff_destroy(q)
out=dict(result='PASS_HIGHRES_TIMER_FAILURE_FALLBACK_AND_LIFECYCLE',results=results,scope='Actual native success/create-failure/set-failure APIs, deadline and invalid argument guards, cancellation/resume/closed owner,100waits pervariant exact processhandle parity. No gameplay/fidelity/smooth60 claim.')
Path('work/camera/prototype-runs/integer-clock-wait-lifecycle-20261009.json').write_text(json.dumps(out,indent=2));print(out)
