import threading,time,runpy,json
from pathlib import Path
from live_game_controls import LiveGameControls
from owned_exact_prepared_service_candidate import ExactPreparedFrames,native
entered=threading.Event();release=threading.Event();closing=threading.Event();count=0;worker=None;forced=False;owner_held=False;errors=[]
original_prepare=native.prepare;original_step=LiveGameControls.step;original_close=ExactPreparedFrames.close
def prepare(size):
 global count
 capsule=original_prepare(size);count+=1
 if count==40:
  entered.set()
  if not release.wait(10):errors.append('Preparation barrier timed out')
 return capsule
def step(self):
 global worker,forced
 worker=self.worker
 if entered.is_set():forced=True;self.quit=True;return False
 return original_step(self)
def close(self):
 if entered.is_set() and not release.is_set():closing.set()
 return original_close(self)
def coordinator():
 global owner_held
 try:
  assert entered.wait(15) and closing.wait(10)
  import owned_exact_preparation_worker_install_candidate as install
  assert worker.owner is not None and install.service.thread.is_alive()
  owner_held=True;release.set()
 except BaseException as exc:errors.append(repr(exc));release.set()
native.prepare=prepare;LiveGameControls.step=step;ExactPreparedFrames.close=close
monitor=threading.Thread(target=coordinator,daemon=False);monitor.start()
try:
 runpy.run_path('work/camera/run_native_exact_preparation_lifecycle_candidate.py',run_name='__main__')
 assert forced and owner_held and not errors,errors
 shutdown=worker.frame_preparation_shutdown
 assert shutdown['joined'] and shutdown['pending']==0 and shutdown['owner_alive_after_preparation_join'] and shutdown['owner_released_after_renderer_close']
 assert worker.owner is None and not worker.thread.is_alive() and not worker.copy_shutdown['thread_alive']
 result=dict(result='PASS_ACTUAL_RENDERER_INFLIGHT_PREPARATION_CLOSE',owner_held=owner_held,shutdown=shutdown,scope='Forcedearlyquit on40th prepared allocation heldbeforequeuepublication. Actualnativeworker closespreparer beforeownerfree. Not fullsmokeduration orclock/cadence proof.')
 Path('work/camera/prototype-runs/actual-preparation-close-20261009.json').write_text(json.dumps(result,indent=2));print(result)
finally:
 release.set();monitor.join(15);native.prepare=original_prepare;LiveGameControls.step=original_step;ExactPreparedFrames.close=original_close
 assert not monitor.is_alive()
