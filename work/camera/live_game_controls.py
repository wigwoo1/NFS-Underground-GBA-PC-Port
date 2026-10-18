"""Original-game-thread control gate; renderer continues polling while paused."""
import time
class LiveGameControls:
 def __init__(self,worker,frame,refresh,snapshot=None):
  self.worker=worker;self.frame=frame;self.refresh=refresh
  self.snapshot=snapshot or worker.controls;self.quit=False;self.steps=0;self.last_deadline_ns=None;self.last_clock_origin=None;self.last_clock_base=None;self.last_state=None;self.last_state_ns=None
 def step(self):
  while True:
   state=self.snapshot()
   if state['quit']:
    self.quit=True;return False
   self.worker.set_paused(state['paused'])
   if state['paused']:
    time.sleep(.01);continue
   if self.worker.clock_origin is not None:
    ticks=(self.refresh()-self.worker.clock_base+1)*280896
    self.last_clock_origin=self.worker.clock_origin;self.last_clock_base=self.worker.clock_base
    self.last_deadline_ns=self.last_clock_origin+(ticks*1000000000+16777215)//16777216
    self.worker.wait_until(self.last_deadline_ns)
    state=self.snapshot()
    if state['quit']:self.quit=True;return False
    if state['paused']:continue
   self.last_state=dict(state);self.last_state_ns=time.perf_counter_ns()
   self.frame(state['keys']);self.steps+=1;return True
