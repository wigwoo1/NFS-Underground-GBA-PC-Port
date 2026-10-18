from live_owned_gpu_worker import LiveOwnedGPUWorker
import json, threading
from pathlib import Path
w=LiveOwnedGPUWorker(2,draw_only=True,present=True,verify=False,expected_frames=None)
try:
 state=w.controls()
 assert state['keys']==0 and state['paused'] and not state['quit'],state
 failures=[]
 def wrong_thread():
  try:w.controls()
  except AssertionError:failures.append(True)
 t=threading.Thread(target=wrong_thread);t.start();t.join();assert failures==[True]
 w.set_paused(state['paused']);assert w.paused
 w.set_paused(False);assert not w.paused
finally:w.close()
r=dict(result='PASS_LIVE_INPUT_SNAPSHOT_BRIDGE',state=state,wrong_producer_thread_rejected=True,scope='Actual idle renderer polling and producer atomic snapshot; physical driving and game key routing unverified.')
Path('work/camera/live-owned-controls-tests.json').write_text(json.dumps(r,indent=2));print(r)
