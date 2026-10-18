"""Actual-renderer atomic notification failure; fail visibly and join copy owner."""
import runpy,json,queue
from pathlib import Path
from live_game_controls import LiveGameControls
from owned_handoff_copy_settlement_candidate import CopySettlement
original_init=CopySettlement.__init__;original_step=LiveGameControls.step;worker=None;count=0;injected=False

def step(self):
 global worker
 worker=self.worker;return original_step(self)
def init(self,notify,release,retire,fail):
 global count
 count+=1;index=count
 def notification(receipt):
  global injected
  if index==40:injected=True;raise queue.Full('Forced atomic notification failure')
  return notify(receipt)
 original_init(self,notification,release,retire,fail)
CopySettlement.__init__=init;LiveGameControls.step=step
try:
 try:runpy.run_path('work/camera/run_native_async_handoff_candidate.py',run_name='__main__')
 except RuntimeError as exc:
  assert injected and 'Async copy settlement' in str(exc),str(exc)
 else:raise AssertionError('Renderer hid forced notification failure')
 assert worker is not None and worker.owner is None and not worker.thread.is_alive()
 assert not worker.copy_shutdown['thread_alive'] and worker.copy_shutdown['pending']==0 and worker.copy_shutdown['counts']['failed']==1
 out=dict(result='PASS_ACTUAL_RENDERER_NOTIFICATION_FAILURE_CLEANUP',copy=worker.copy_shutdown,errors=worker.errors,scope='Forced failure during live rendering, native publication retired before reservation release, visible runtime failure and joined shutdown. No timing/cadence proof.')
 Path('work/camera/prototype-runs/forced-async-notification-failure-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:CopySettlement.__init__=original_init;LiveGameControls.step=original_step
