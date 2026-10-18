"""Bounded scalar submission waits; no scene/frame ownership retained."""
import json
from owned_serialized_recent_rows_candidate import RecentRows
class SubmissionRows(RecentRows):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.long=[];self.long_total=0;self.long_dropped=0;self.wait_total=0;self.wait_max=0
 def append(self,row):
  wait=row['space_wait_ns'];self.wait_total+=wait;self.wait_max=max(self.wait_max,wait)
  if wait*16777216>280896*1000000000:
   selected={k:v for k,v in row.items() if k.endswith('_ns') or k in ('scene_identity','preparation_pair','replay','thread_id')}
   encoded=json.dumps(selected,separators=(',',':'),allow_nan=False);self.long_total+=1
   if len(encoded.encode())>4096 or len(self.long)>=4096:self.long_dropped+=1
   else:self.long.append(encoded)
  super().append(row)
 def stats(self):
  out=super().stats();out['whole_submission_space_wait']=dict(total_ns=self.wait_total,max_ns=self.wait_max,long_total=self.long_total,dropped=self.long_dropped,capacity=4096,records=[json.loads(x) for x in self.long],scope='All queue space wait totals; each wait>one original update retained if dropped=0. Association with game thread blocking, not exclusive cause of aggregate drift.')
  return out
