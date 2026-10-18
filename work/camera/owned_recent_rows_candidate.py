"""Bounded recent rows with separate total count; list length is retained count."""
from collections import deque
import json
class RecentRows:
 def __init__(self,capacity=240,max_record_bytes=65536):
  if capacity<1:raise ValueError('Positive capacity required')
  self.rows=deque(maxlen=capacity);self.total_records=0;self.max_record_bytes=max_record_bytes
 def append(self,row):
  encoded=json.dumps(row,separators=(',',':'),allow_nan=False)
  if len(encoded.encode())>self.max_record_bytes:raise ValueError('Diagnostic row exceeds configured byte limit')
  self.rows.append(json.loads(encoded));self.total_records+=1
 def __len__(self):return len(self.rows)
 def snapshot(self):return list(self.rows)
 def stats(self):return dict(total_records=self.total_records,retained_records=len(self),dropped_records=self.total_records-len(self),capacity=self.rows.maxlen,scope='Recent diagnostics; total count preserved independently.')
