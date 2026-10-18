"""Bounded immutable scene chain; presentation authority is never retained."""
from collections import OrderedDict
class ResumeSceneChain:
 def __init__(self,capacity):
  if not 3<=capacity<=16:raise ValueError('Invalid retained scene capacity')
  self.capacity=capacity;self.items=OrderedDict();self.epoch=None
 def append(self,frame,scene):
  trace=getattr(type(self),"phase_trace",False);ticks=[__import__("time").perf_counter_ns()] if trace else None;frame_type=type(frame).__name__ if trace else None
  identity=scene.identity
  if self.epoch is not None and identity[0]!=self.epoch:raise ValueError('Scene chain epoch changed')
  if self.items and identity[1]<=next(reversed(self.items))[1]:raise ValueError('Nonsequential scene publication')
  if trace:ticks.append(__import__("time").perf_counter_ns())
  frame=bytes(frame)
  if trace:ticks.append(__import__("time").perf_counter_ns())
  scene.match(frame)
  if trace:ticks.append(__import__("time").perf_counter_ns())
  self.epoch=identity[0];self.items[identity]=(frame,scene)
  if trace:ticks.append(__import__("time").perf_counter_ns())
  while len(self.items)>self.capacity:self.items.popitem(last=False)
  if trace:
   ticks.append(__import__("time").perf_counter_ns());self.last_append_profile=dict(identity=identity,ticks=ticks,frame_type=frame_type,frame_bytes=len(frame))
 def suffix(self,older,newer):
  if older not in self.items or newer not in self.items:raise ValueError('Displayed interval no longer retained')
  keys=list(self.items);i=keys.index(older)
  if i+1>=len(keys) or keys[i+1]!=newer:raise ValueError('Displayed boundaries are not adjacent')
  return tuple(self.items[key] for key in keys[i:])
 def replay_plan(self,older,newer,last_index,origin,base,delay):
  from owned_motion_clock import scene_samples
  if not isinstance(last_index,int) or last_index<0:raise ValueError('Invalid committed display index')
  chain=self.suffix(older,newer);intervals=[];expected=last_index+1
  for i,(a,b) in enumerate(zip(chain,chain[1:])):
   slots=scene_samples(origin,base,a[1].identity[1],b[1].identity[1],delay)
   if i==0 and last_index not in [slot['index'] for slot in slots]:raise ValueError('Committed sample is outside retained interval')
   pending=tuple(slot for slot in slots if slot['index']>last_index)
   for slot in pending:
    if slot['index']!=expected:raise ValueError('Resume presentation grid has a gap')
    expected+=1
   intervals.append((a,b,pending))
  return tuple(intervals)
 def initial_replay_plan(self,origin,base,delay):
  from owned_motion_clock import scene_samples
  chain=tuple(self.items.values())
  if len(chain)<2:raise ValueError('Initial replay requires a retained source interval')
  intervals=[];expected=None
  for a,b in zip(chain,chain[1:]):
   slots=tuple(scene_samples(origin,base,a[1].identity[1],b[1].identity[1],delay))
   for slot in slots:
    if expected is not None and slot['index']!=expected:raise ValueError('Initial presentation grid has a gap')
    expected=slot['index']+1
   intervals.append((a,b,slots))
  if expected is None:raise ValueError('Initial replay has no presentation samples')
  return tuple(intervals)
 def clear(self):self.items.clear();self.epoch=None
