"""Input admission changes across original-clock waits; no hardware claim."""
import time,json
from pathlib import Path
from live_game_controls import LiveGameControls
class Worker:
 clock_origin=123456;clock_base=100
 def __init__(self,change):self.change=change;self.deadlines=[];self.pauses=[]
 def set_paused(self,p):self.pauses.append(p)
 def wait_until(self,d):self.deadlines.append(d);self.change()
checks=[]
for name,after in [('disconnect',dict(keys=0,paused=False,quit=False,controller_connected=False)),('new_keys',dict(keys=34,paused=False,quit=False,controller_connected=True)),('quit',dict(keys=0,paused=False,quit=True,controller_connected=False))]:
 state=dict(keys=17,paused=False,quit=False,controller_connected=True);calls=[]
 w=Worker(lambda:state.update(after));g=LiveGameControls(w,lambda k:calls.append(k),lambda:100,snapshot=lambda:state)
 admitted=g.step();assert w.deadlines==[123456+(280896*1000000000+16777215)//16777216]
 if after['quit']:assert not admitted and not calls and g.last_state is None
 else:
  assert admitted and calls==[after['keys']] and g.last_state==after and g.last_state is not state
  captured=dict(g.last_state);stamp=g.last_state_ns;state['keys']=1023;assert g.last_state==captured and stamp<=time.perf_counter_ns()
 checks.append(name)
# A pause appearing during wait must reject held keys and take a fresh state after resume.
states=iter([dict(keys=17,paused=False,quit=False),dict(keys=17,paused=True,quit=False),dict(keys=0,paused=False,quit=False),dict(keys=2,paused=False,quit=False)])
w=Worker(lambda:None);calls=[];g=LiveGameControls(w,calls.append,lambda:100,snapshot=lambda:next(states));assert g.step() and calls==[2] and len(w.deadlines)==2 and g.last_state['keys']==2;checks.append('pause_after_wait')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/control-admission-boundaries-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual LiveGameControls with injected timing worker; verifies post-wait admission, copied snapshot, pause/quit rejection. Not physical controller or game response verification.'),indent=2));print('PASS',checks)
