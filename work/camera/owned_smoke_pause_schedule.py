"""Diagnostic pauses trigger on observation, so slow frames cannot skip pulses."""
class SmokePauseSchedule:
 def __init__(self,starts,duration=.2):
  self.starts=tuple(starts);self.duration=duration;self.index=0;self.active_until=None
  if duration<=0 or any(b<=a for a,b in zip(self.starts,self.starts[1:])):raise ValueError('Invalid smoke pause schedule')
 def paused(self,elapsed):
  if self.active_until is not None:
   if elapsed<self.active_until:return True
   self.active_until=None
  if self.index<len(self.starts) and elapsed>=self.starts[self.index]:
   self.index+=1;self.active_until=elapsed+self.duration;return True
  return False
