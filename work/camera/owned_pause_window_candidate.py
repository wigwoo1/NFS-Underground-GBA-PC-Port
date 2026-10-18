"""Bounded pause event window with exact whole-run completed pause duration."""
from collections import deque
class PauseWindow:
 def __init__(self,capacity=64):self.rows=deque(maxlen=capacity);self.total_records=0;self.duration_ns=0;self.last_end=None
 def append(self,row):
  begin,end,duration=row['begin_ns'],row['end_ns'],row['duration_ns']
  if end<begin or duration!=end-begin or (self.last_end is not None and begin<self.last_end):raise ValueError('Invalid completed pause interval')
  self.rows.append(row);self.total_records+=1;self.duration_ns+=duration;self.last_end=end
 def __getitem__(self,index):return self.rows[index]
 def __len__(self):return len(self.rows)
 def snapshot(self):return list(self.rows)
 def stats(self):return dict(total_records=self.total_records,retained_records=len(self),dropped_records=self.total_records-len(self),total_completed_pause_ns=self.duration_ns,scope='Completed pause totals; recent mutable metadata only, open pause excluded.')
