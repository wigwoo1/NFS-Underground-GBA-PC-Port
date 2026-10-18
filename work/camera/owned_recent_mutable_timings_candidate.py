"""Bounded references to fixed-schema mutable lifecycle timing rows."""
from collections import deque
class RecentMutableTimingRows:
 def __init__(self,capacity=60):self.rows=deque(maxlen=capacity);self.total_records=0
 def __len__(self):return len(self.rows)
 def append(self,row):
  if not isinstance(row,dict):raise ValueError('Expected lifecycle timing dictionary')
  self.rows.append(row);self.total_records+=1
 def snapshot(self):return list(self.rows)
 def stats(self):return dict(total_records=self.total_records,retained_records=len(self),dropped_records=self.total_records-len(self),capacity=self.rows.maxlen,scope='Recent mutable lifecycle timing references; snapshot only after worker joins.')
