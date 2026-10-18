"""Force quit during an actual native copy; verify owner remains alive until drain."""
import ctypes as C,threading,time,runpy,json
from pathlib import Path
from live_game_controls import LiveGameControls
from owned_handoff_copy_service_candidate import HandoffCopyService
P=C.c_void_p;Hook=C.CFUNCTYPE(None)
d=C.CDLL(str(Path('work/camera/owned-handoff-request-authority-barrier-test.dll').resolve()));d.nf_test_copy_hook.argtypes=[P]
entered=threading.Event();release=threading.Event();closing=threading.Event();count=0;worker=None;forced=False;errors=[];owner_held=False
@Hook
def barrier():
 global count
 count+=1
 if count==40:
  entered.set()
  if not release.wait(10):errors.append('Copy shutdown barrier timeout')
original_step=LiveGameControls.step;original_wait=HandoffCopyService.wait_idle
def step(self):
 global worker,forced
 worker=self.worker
 if entered.is_set():forced=True;self.quit=True;return False
 return original_step(self)
def wait_idle(self,timeout=30):
 if entered.is_set() and not release.is_set():closing.set()
 return original_wait(self,timeout)
def coordinator():
 global owner_held
 try:
  assert entered.wait(15) and closing.wait(10)
  time.sleep(.03)
  assert worker.owner is not None and worker.copy_service.thread.is_alive() and worker.copy_service.pending>0
  owner_held=True;release.set()
 except BaseException as exc:errors.append(repr(exc));release.set()
LiveGameControls.step=step;HandoffCopyService.wait_idle=wait_idle;d.nf_test_copy_hook(C.cast(barrier,P));monitor=threading.Thread(target=coordinator);monitor.start()
try:
 runpy.run_path('work/camera/run_native_async_handoff_barrier_candidate.py',run_name='__main__')
 assert forced and owner_held and not errors,errors
 assert worker.owner is None and not worker.thread.is_alive() and not worker.copy_shutdown['thread_alive'] and worker.copy_shutdown['pending']==0
 c=worker.copy_shutdown['counts'];assert c['admitted']==c['published']+c['retired'] and c['failed']==0
 out=dict(result='PASS_ACTUAL_RENDERER_QUIT_WITH_INFLIGHT_COPY',copy=worker.copy_shutdown,owner_held_during_blocked_close=owner_held,scope='Forced early quit after40th copy, not a full smoke duration or game timing/cadence qualification. Actual native renderer shutdown ordering exercised.')
 Path('work/camera/prototype-runs/forced-async-shutdown-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:
 LiveGameControls.step=original_step;HandoffCopyService.wait_idle=original_wait;d.nf_test_copy_hook(None);release.set();monitor.join(15);assert not monitor.is_alive()
