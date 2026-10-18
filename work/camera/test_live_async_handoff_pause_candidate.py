"""Forced actual-renderer in-flight retirement; diagnostic timing is perturbed."""
import ctypes as C,threading,time,runpy,json
from pathlib import Path
from live_game_controls import LiveGameControls
P=C.c_void_p;Hook=C.CFUNCTYPE(None)
d=C.CDLL(str(Path('work/camera/owned-handoff-request-authority-barrier-test.dll').resolve()));d.nf_test_copy_hook.argtypes=[P]
entered=threading.Event();release=threading.Event();worker_ready=threading.Event();count=0;worker=None;forced=False;errors=[]
@Hook
def barrier():
 global count
 count+=1
 if count==40:
  entered.set()
  if not release.wait(10):errors.append('Barrier release timeout')
def coordinator():
 try:
  assert entered.wait(15) and worker_ready.wait(5)
  deadline=time.monotonic()+10;generation=C.c_uint64()
  while worker.d.nf_owned_handoff_request_generation(worker.owner,worker.epoch,C.byref(generation)):
   assert time.monotonic()<deadline;time.sleep(.001)
  release.set()
 except BaseException as exc:errors.append(repr(exc));release.set()
original=LiveGameControls.step
def step(self):
 global worker,forced
 worker=self.worker;worker_ready.set()
 if entered.is_set() and not forced:
  forced=True;self.worker.set_paused(True)
  assert self.worker.copy_service.wait_idle(0) and self.worker.copy_counts['retired']>=1
  self.worker.set_paused(False)
 return original(self)
LiveGameControls.step=step;d.nf_test_copy_hook(C.cast(barrier,P));monitor=threading.Thread(target=coordinator);monitor.start()
try:
 runpy.run_path('work/camera/run_native_async_handoff_barrier_candidate.py',run_name='__main__')
 assert forced and not errors,errors
 assert worker.copy_shutdown['pending']==0 and not worker.copy_shutdown['thread_alive']
 assert worker.copy_shutdown['counts']['retired']>=1 and worker.copy_shutdown['counts']['failed']==0
 out=dict(result='PASS_ACTUAL_RENDERER_INFLIGHT_COPY_PAUSE',copy=worker.copy_shutdown,forced_copy_index=40,scope='Test-only after-copy barrier and external coordinator perturb timing; actual native renderer pause/drain/resume/replay/close exercised. No speed/cadence or live pixel fidelity proof.')
 Path('work/camera/prototype-runs/forced-async-pause-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:
 LiveGameControls.step=original;d.nf_test_copy_hook(None);release.set();monitor.join(15);assert not monitor.is_alive()
