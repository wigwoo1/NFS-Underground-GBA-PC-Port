"""Opt-in bounded whole-worker input-poll diagnostic; no input behavior changes."""
import threading,time,json
from pathlib import Path
instances=[]
class InputPollLedger:
 def __init__(self,capacity=128):
  if not 1<=capacity<=1024:raise ValueError('Invalid poll capacity')
  self.capacity=capacity;self.owner=None;self.count=0;self.long_count=0;self.dropped=0;self.rows=[];self.max_ns=0;self.closed=False;self.totals={k:0 for k in ('total_ns','message_pump_ns','keyboard_ns','controller_ns','snapshot_ns')}
  instances.append(self)
 def observe(self,stage,message=None):
  owner=threading.get_native_id()
  if self.closed or self.owner is not None and self.owner!=owner:raise RuntimeError('Poll ledger ownership violation')
  if set(stage)!=set(self.totals) or any(type(v)is not int or v<0 for v in stage.values()):raise ValueError('Invalid poll stages')
  if sum(v for k,v in stage.items() if k!='total_ns')>stage['total_ns']+1:raise ValueError('Poll stage partition')
  self.owner=owner;self.count+=1;self.max_ns=max(self.max_ns,stage['total_ns'])
  for k,v in stage.items():self.totals[k]+=v
  if stage['total_ns']>10000000:
   self.long_count+=1
   if len(self.rows)<self.capacity:self.rows.append(dict(index=self.count,observed_ns=time.perf_counter_ns(),thread=owner,message_profile=None if message is None else dict(message),**stage))
   else:self.dropped+=1
 def stats(self):
  return dict(count=self.count,long_threshold_ns=10000000,long_count=self.long_count,dropped=self.dropped,capacity=self.capacity,max_ns=self.max_ns,totals=dict(self.totals),rows=list(self.rows),owner=self.owner,closed=self.closed)
def save(path):
 if not instances or not all(x.closed for x in instances):raise RuntimeError('Joined renderer ledgers required')
 Path(path).write_text(json.dumps(dict(result='COMPLETE_NATIVE_INPUT_POLL_LEDGER',workers=[x.stats() for x in instances],scope='All enabled worker polls counted; only>10ms polls retained, overflow explicit. Diagnostic only; no historic recurrence or visible60 claim.'),indent=2))
