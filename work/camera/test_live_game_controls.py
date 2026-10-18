from live_game_controls import LiveGameControls
from live_owned_gpu_worker import LiveOwnedGPUWorker
from pathlib import Path
import time,json
w=LiveOwnedGPUWorker(2,draw_only=True,present=True,verify=False,expected_frames=None)
calls=[];states=iter([dict(keys=0,paused=True,quit=False),dict(keys=17,paused=False,quit=False),dict(keys=17,paused=False,quit=False),dict(keys=0,paused=False,quit=True)])
w.start_clock(time.perf_counter_ns(),100)
g=LiveGameControls(w,lambda keys:calls.append(keys),lambda:100,snapshot=lambda:next(states))
try:
 assert g.step() and calls==[17]
 assert not g.step() and g.quit and calls==[17]
 assert len(w.pause_events)==1 and w.pause_events[0]['duration_ns']>=10000000
finally:w.close()
r=dict(result='PASS_GAME_CONTROL_GATE',routed_keys=calls,pause_clock_shift_ns=w.pause_events[0]['duration_ns'],quit_stops_updates=True,scope='Scripted producer gate using actual native handoff pause/clock. Physical game driving unverified.')
Path('work/camera/live-game-controls-tests.json').write_text(json.dumps(r,indent=2));print(r)
