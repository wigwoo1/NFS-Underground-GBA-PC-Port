"""Fill actual copy reservations behind one blocked copy, then release pressure."""
import ctypes as C,threading,time,runpy,json
from pathlib import Path
from live_game_controls import LiveGameControls
P=C.c_void_p;Hook=C.CFUNCTYPE(None)
d=C.CDLL(str(Path('work/camera/owned-handoff-request-authority-barrier-test.dll').resolve()));d.nf_test_copy_hook.argtypes=[P]
entered=threading.Event();release=threading.Event();count=0;worker=None;errors=[];peak=0
@Hook
def barrier():
 global count
 count+=1
 if count==40:
  entered.set()
  if not release.wait(10):errors.append('Pressure barrier timeout')
original=LiveGameControls.step
def step(self):
 global worker
 worker=self.worker;return original(self)
def coordinator():
 global peak
 try:
  assert entered.wait(15);deadline=time.monotonic()+10
  while True:
   with worker.copy_service.lock:pending=worker.copy_service.pending
   peak=max(peak,pending);assert pending<=worker.copy_service.capacity
   if pending==worker.copy_service.capacity:break
   assert time.monotonic()<deadline;time.sleep(.001)
  release.set()
 except BaseException as exc:errors.append(repr(exc));release.set()
LiveGameControls.step=step;d.nf_test_copy_hook(C.cast(barrier,P));monitor=threading.Thread(target=coordinator);monitor.start()
try:
 runpy.run_path('work/camera/run_native_async_handoff_barrier_candidate.py',run_name='__main__')
 assert not errors and peak==worker.copy_service.capacity,errors
 assert worker.owner is None and not worker.copy_shutdown['thread_alive'] and worker.copy_shutdown['pending']==0
 c=worker.copy_shutdown['counts'];assert c['admitted']==c['published']+c['retired'] and c['failed']==0
 out=dict(result='PASS_ACTUAL_RENDERER_COPY_CAPACITY_PRESSURE',capacity=worker.copy_service.capacity,observed_peak=peak,copy=worker.copy_shutdown,scope='Test-only blockedcopy fills bounded reservations and resumes. Timing perturbed, no speed/cadence qualification.')
 Path('work/camera/prototype-runs/forced-async-capacity-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:LiveGameControls.step=original;d.nf_test_copy_hook(None);release.set();monitor.join(15);assert not monitor.is_alive()
