"""Real native input owner lifecycle while no frames are queued; no physical pad claim."""
import json,time,threading
from pathlib import Path
from owned_native_source_input_worker_candidate import NativeSourceWorker
worker=NativeSourceWorker();main=threading.get_ident()
try:
 first=worker.input_snapshot();initial=worker.input_polls
 deadline=time.monotonic()+2
 while worker.input_polls<initial+3 and time.monotonic()<deadline:time.sleep(.01)
 assert worker.input_polls>=initial+3,'Idle renderer stopped servicing input'
 assert worker.input_poll_thread==worker.thread.ident and worker.input_poll_thread!=main
 latest=worker.input_snapshot();assert len(latest)==4
 assert latest[1] in (0,1) and latest[2] in (0,1) and latest[3] in (0,1)
 if latest[1]:assert latest[0]==0,'Paused input must not move game'
 result=dict(result='PASS_IDLE_NATIVE_INPUT_OWNER',first=list(first),latest=list(latest),idle_poll_count=worker.input_polls-initial,owner_thread=worker.input_poll_thread,caller_thread=main,physical_controller_verified=False,scope='Actual native window/controller service idle polling, cross-thread immutable snapshot, paused key suppression and teardown; no keyboard injection, physical controller mapping or live gameplay verification')
finally:worker.close()
assert not worker.thread.is_alive()
try:worker.input_snapshot()
except RuntimeError:pass
else:raise AssertionError('Closed input still available')
result['clean_shutdown']=True
Path('work/camera/prototype-runs/native-input-owner-component.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
