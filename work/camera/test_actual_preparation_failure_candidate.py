import runpy,json
from pathlib import Path
from live_game_controls import LiveGameControls
from owned_exact_prepared_service_candidate import native
original_prepare=native.prepare;original_step=LiveGameControls.step;worker=None;count=0;injected=False
def prepare(size):
 global count,injected
 count+=1
 if count==40:injected=True;raise MemoryError('Injected private preparation allocation failure')
 return original_prepare(size)
def step(self):
 global worker
 worker=self.worker;return original_step(self)
native.prepare=prepare;LiveGameControls.step=step
try:
 try:runpy.run_path('work/camera/run_native_exact_preparation_lifecycle_candidate.py',run_name='__main__')
 except RuntimeError as error:assert injected and 'Preparation failed' in str(error),repr(error)
 else:raise AssertionError('Preparation failure hidden')
 assert worker is not None and worker.owner is None and not worker.thread.is_alive()
 shutdown=worker.frame_preparation_shutdown
 assert shutdown['joined'] and shutdown['pending']==0 and shutdown['owner_alive_after_preparation_join'] and shutdown['owner_released_after_renderer_close']
 assert not worker.copy_shutdown['thread_alive'] and worker.copy_shutdown['pending']==0
 result=dict(result='PASS_ACTUAL_PREPARATION_FAILURE_CLEANUP',shutdown=shutdown,copy=worker.copy_shutdown,scope='Injected allocation failure on40th background preparation during actual game rendering, visibleRuntimeError and joinedshutdown. Expectedfailure, not runnable/timing milestone.')
 Path('work/camera/prototype-runs/actual-preparation-failure-20261009.json').write_text(json.dumps(result,indent=2));print(result)
finally:native.prepare=original_prepare;LiveGameControls.step=original_step
