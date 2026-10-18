"""Control-gate deadline refresh with actual native pause owner and game KEYINPUT."""
import ctypes as C,time,json
from pathlib import Path
from live_game_controls import LiveGameControls
from live_owned_gpu_worker import LiveOwnedGPUWorker
core=C.CDLL(str(Path('work/camera/sky-caller-probe.dll').resolve()));core.nf_init.argtypes=[C.c_char_p,C.c_char_p];core.nf_state.argtypes=[C.c_char_p,C.c_int];core.nf_read.argtypes=[C.c_uint,C.c_int];core.nf_read.restype=C.c_uint
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');assert core.nf_init(str(rom).encode(),b'') and core.nf_state(str(Path('work/race.state').resolve()).encode(),0)
def state(keys=0,paused=False,quit=False):return dict(keys=keys,paused=paused,quit=quit)
cases=[('release_after_deadline',[state(1),state(0)],0),('steering_after_deadline',[state(17),state(33)],33),('pause_after_deadline',[state(1),state(1,True),state(1,True),state(2),state(2)],2),('quit_after_deadline',[state(1),state(0,quit=True)],None),('quit_before_deadline',[state(1,quit=True)],None)]
checks=[]
try:
 for name,sequence,expected in cases:
  worker=LiveOwnedGPUWorker(2,draw_only=True,present=True,verify=False,expected_frames=None);worker.start_clock(time.perf_counter_ns(),100);initial_origin=worker.clock_origin;calls=[];states=iter(sequence)
  def advance(keys):
   core.nf_frame(keys);actual=core.nf_read(0x04000130,2)&1023;assert actual==((~keys)&1023);calls.append(dict(keys=keys,keyinput=actual))
  gate=LiveGameControls(worker,advance,lambda:100,snapshot=lambda:next(states))
  try:
   result=gate.step();assert result==(expected is not None)
   assert [x['keys'] for x in calls]==([] if expected is None else [expected])
   if name=='pause_after_deadline':
    assert len(worker.pause_events)==1 and worker.clock_origin>initial_origin
    assert gate.last_clock_origin==worker.clock_origin
   if expected is None:assert gate.quit and gate.steps==0
   checks.append(dict(case=name,actual_game_updates=calls,pause_events=len(worker.pause_events),deadline_origin_refreshed=gate.last_clock_origin==worker.clock_origin if expected is not None else None))
  finally:worker.close()
finally:core.nf_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/control-deadline-game-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Scripted snapshots through production LiveGameControls/actual native owner pause clock and actual original core KEYINPUT; no physical controller, focused window or live scene cadence proof'),indent=2));print('PASS',len(checks),'deadline/pause/quit cases')
