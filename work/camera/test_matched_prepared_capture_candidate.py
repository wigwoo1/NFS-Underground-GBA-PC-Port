import runpy,json,time,statistics
from pathlib import Path
import _owned_frame_capture_profile_candidate as extension
import _owned_frame_capture_release_candidate as unprepared
from owned_prepared_frame_service_candidate import PreparedFrames
original=extension.capture;count=0;trials=[];service=PreparedFrames()
def capture(*args):
 global count
 packet=original(*args);count+=1
 if count==40:
  for trial in range(12):
   row={}
   for kind in ((0,1) if trial%2==0 else (1,0)):
    # Readiness excluded from measurement: isolates ready-path producer cost.
    if kind:
     with service.cv:assert service.cv.wait_for(lambda:bool(service.ready) or service.error is not None,10)
    start=time.perf_counter_ns()
    output=service.capture(*args) if kind else unprepared.capture(*args)
    end=time.perf_counter_ns()
    assert output==packet
    row['prepared_ms' if kind else 'unprepared_ms']=(end-start)/1e6
    del output
   trials.append(row)
 return packet
extension.capture=capture
try:
 runpy.run_path('work/camera/run_native_async_private_capture_candidate.py',run_name='__main__')
 assert len(trials)==12
finally:extension.capture=original;shutdown=service.close()
result=dict(result='PASS_MATCHED_PREPARED_CAPTURE_COST_PARITY',trials=trials,medians={k:statistics.median(t[k] for t in trials) for k in trials[0]},shutdown=shutdown,scope='Same actual source frame,12 alternating ordered capture pairs, exact bytes. Ready-buffer waits excluded, resize and reader included. Background preparation competes for CPU; repeated source/cache effects and scheduling perturbed. Not whole-run improvement or60fps proof.')
assert shutdown['joined'] and shutdown['pending']==0
Path('work/camera/prototype-runs/matched-prepared-capture-20261009.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='trials'})
