"""Bounded immutable progressive handoff; component, not live renderer integration."""
import threading,time,math
from owned_segmented_frame_candidate import SegmentedFrame
class RetiredGeneration(RuntimeError):pass
def immutable_size(value):
 if type(value) is bytes:return len(value)
 if isinstance(value,SegmentedFrame):return len(value.prefix)+len(value.base)
 if type(value) is tuple:return sum(immutable_size(v) for v in value)
 if type(value) in (int,float,str) or value is None:return 64
 raise ValueError('Mutable publication payload')
class ProgressiveMailbox:
 def __init__(self,capacity=2,budget=64*1024*1024):
  if type(capacity) is not int or not 1<=capacity<=8 or type(budget) is not int or budget<=0:raise ValueError('Invalid mailbox bounds')
  self.capacity=capacity;self.budget=budget;self.cv=threading.Condition();self.generation=0;self.closed=False;self.pending=[];self.leased={};self.bytes=0;self.next_index=0;self.serial=0
 def _valid(self,generation):
  if self.closed or generation!=self.generation:raise RetiredGeneration('Publication retired')
 def publish(self,generation,index,payload,timeout=30):
  if not math.isfinite(timeout) or not 0<=timeout<=30:raise ValueError('Invalid wait')
  size=immutable_size(payload)
  if size>self.budget:raise ValueError('Publication exceeds budget')
  deadline=time.monotonic()+timeout
  with self.cv:
   self._valid(generation)
   if type(index) is not int or index!=self.next_index or not 0<=index<8:raise ValueError('Out of order sample')
   while len(self.pending)+len(self.leased)>=self.capacity or self.bytes+size>self.budget:
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('Mailbox full')
    self.cv.wait(remaining);self._valid(generation)
   # Recheck after waiting: concurrent producers cannot publish duplicate indices.
   if index!=self.next_index:raise ValueError('Duplicate sample')
   self.serial+=1;token=(generation,index,self.serial);self.pending.append((token,payload,size));self.bytes+=size;self.next_index+=1;self.cv.notify_all();return token
 def take(self,generation,timeout=30):
  if not math.isfinite(timeout) or not 0<=timeout<=30:raise ValueError('Invalid wait')
  deadline=time.monotonic()+timeout
  with self.cv:
   self._valid(generation)
   while not self.pending:
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('Mailbox empty')
    self.cv.wait(remaining);self._valid(generation)
   token,payload,size=self.pending.pop(0);self.leased[token]=(payload,size);return token,payload
 def acknowledge(self,token):
  with self.cv:
   if token not in self.leased:raise ValueError('Unknown or duplicate acknowledgement')
   _,size=self.leased.pop(token);self.bytes-=size;self.cv.notify_all()
 def retire(self):
  with self.cv:
   self.generation+=1;self.bytes-=sum(x[2] for x in self.pending);self.pending.clear();self.next_index=0;self.cv.notify_all();return self.generation
 def close(self):
  with self.cv:self.closed=True
  self.retire()
 def stats(self):
  with self.cv:return dict(generation=self.generation,pending=len(self.pending),leased=len(self.leased),retained_bytes=self.bytes,closed=self.closed)
