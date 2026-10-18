"""Brief-lock ownership/publication bookkeeping; native batch runs outside lock."""
import threading
from owned_batch_commit_snapshot import resolve_pause_snapshot
class AdvancementBatchPublication:
 def __init__(self):self.lock=threading.RLock();self.active=None;self.last=None;self.published=[]
 def begin(self,epoch,generation,rows,owner):
  rows=tuple(dict(x) for x in rows)
  if not rows or len(rows)>8:raise ValueError('Invalid active batch')
  with self.lock:
   if self.active is not None:raise ValueError('Previous batch not published')
   for i,row in enumerate(rows):
    if row['epoch']!=epoch or row['generation']!=generation or (i and row['display_index']!=rows[i-1]['display_index']+1):raise ValueError('Invalid active batch identity')
   if self.last and rows[0]['display_index']<=self.last['display_index']:raise ValueError('Advancement batch moves backwards')
   if self.last and rows[0]['display_index']>self.last['display_index']+1:
    plan=rows[0].get('display_advance_plan');assert plan and plan['previous_index']==self.last['display_index'] and plan['target_index']==rows[0]['display_index'] and plan['last_skipped_deadline_ns']<=plan['observed_ns']
   token=object();self.active=(token,epoch,generation,rows,owner);return token
 def snapshot(self,sample,has_sample,epoch,generation):
  with self.lock:
   rows=self.active[3] if self.active else ()
   if has_sample and rows and sample[4]<rows[0]['display_index']-1:
    if any(r.get('epoch')!=epoch or r.get('generation')!=generation or (i and r['display_index']!=rows[i-1]['display_index']+1) for i,r in enumerate(rows)):raise ValueError('Invalid retained advancement batch')
    plan=rows[0].get('display_advance_plan')
    if not plan or plan['previous_index']!=sample[4] or plan['target_index']!=rows[0]['display_index'] or plan['skipped_count']!=rows[0]['display_index']-sample[4]-1 or plan['last_skipped_deadline_ns']>plan['observed_ns']:
     raise ValueError('Invalid pending advancement snapshot')
    state=resolve_pause_snapshot(sample,has_sample,epoch,generation,(),self.last)
    # Retain every selected row; the skipped display slots were never owners.
    state['pending_indices']=[r['display_index'] for r in rows]
    return state
   return resolve_pause_snapshot(sample,has_sample,epoch,generation,rows,self.last)
 def finish(self,token,committed_samples):
  samples=tuple(tuple(x) for x in committed_samples)
  with self.lock:
   if self.active is None or self.active[0] is not token:raise ValueError('Stale batch publication')
   _,epoch,generation,rows,owner=self.active
   if len(samples)>len(rows):raise ValueError('Invalid committed prefix length')
   output=[]
   for i,sample in enumerate(samples):
    state=resolve_pause_snapshot(sample,1,epoch,generation,rows,self.last)
    if sample[4]!=rows[i]['display_index']:raise ValueError('Committed prefix gap')
    output.append(dict(rows[i],**state['last_committed'],native_committed_sample=list(sample)))
   # Validate all prefix rows before publishing or releasing their owner.
   self.published.extend(output)
   if output:self.last=output[-1]
   self.active=None
   return tuple(output)
