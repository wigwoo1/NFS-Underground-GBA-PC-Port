"""Candidate display-only selection; no game update or scene ownership mutation."""
from owned_motion_clock import deadline

def select(slots,origin,now_ns,previous_index,protected_until=-1):
 slots=tuple(slots)
 if not slots:return slots,None
 for i,s in enumerate(slots):
  if s['deadline_ns']!=deadline(origin,s['index']):raise ValueError('Wrong presentation grid')
  if i and s['index']!=slots[i-1]['index']+1:raise ValueError('Nonconsecutive source interval')
  if not 0<=s['alpha']<=1:raise ValueError('Invalid scene fraction')
 if previous_index is None:return slots,None
 if slots[0]['index']<=previous_index:raise ValueError('Already committed slot in interval')
 if slots[0]['index']<=protected_until:return slots,None
 due=[i for i,s in enumerate(slots) if s['deadline_ns']<=now_ns]
 first=due[-1] if due else 0
 selected=slots[first:]
 if selected[0]['index']==previous_index+1:return selected,None
 skipped_last=selected[0]['index']-1
 if deadline(origin,skipped_last)>now_ns:raise ValueError('Cannot skip future display slot')
 return selected,dict(previous_index=previous_index,target_index=selected[0]['index'],skipped_count=selected[0]['index']-previous_index-1,last_skipped_deadline_ns=deadline(origin,skipped_last),observed_ns=now_ns)
