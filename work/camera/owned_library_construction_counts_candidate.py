"""Bounded library-wrapper construction counts; no pointer lifetime changes."""
import ctypes as C,threading,sys,time
from pathlib import Path
counts={};dropped=0;live=False
original=C.CDLL.__init__
def initialize(self,*args,**kwargs):
 global dropped
 caller=sys._getframe(1);key=(str(args[0]) if args else str(kwargs.get('name')),Path(caller.f_code.co_filename).name,caller.f_code.co_name,live,threading.get_ident());del caller
 begin=time.perf_counter_ns()
 original(self,*args,**kwargs)
 elapsed=time.perf_counter_ns()-begin
 if key not in counts:
  if len(counts)>=256:dropped+=1;return
  counts[key]=[0,0]
 counts[key][0]+=1;counts[key][1]+=elapsed
C.CDLL.__init__=initialize
import live_game_controls
step=live_game_controls.LiveGameControls.step
def observed_step(self):
 global live
 live=True
 return step(self)
live_game_controls.LiveGameControls.step=observed_step
