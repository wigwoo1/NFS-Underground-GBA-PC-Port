"""Bounded immutable complete original-update diagnostics, no clock changes."""
import json
from owned_producer_caller_gap_candidate import ProducerDeadlineRows as Base
class ProducerDeadlineRows(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.complete_updates=[];self.complete_update_dropped=0
 def append(self,row):
  super().append(row)
  # Base enriches a private row with the actual preceding caller interval.
  encoded=self.rows[-1]
  assert type(encoded) is str
  if len(encoded.encode())>2048:raise ValueError('Complete update record exceeds bounded size')
  if len(self.complete_updates)<8192:self.complete_updates.append(encoded)
  else:self.complete_update_dropped+=1
 def stats(self):
  out=super().stats();out['complete_original_updates']=dict(total=self.total_records,dropped=self.complete_update_dropped,capacity=8192,max_record_bytes=2048,records=[json.loads(x) for x in self.complete_updates],scope='Every original update only when dropped==0; original deadline/native boundary/preceding caller retained. Diagnostics do not prove CPU attribution or visible cadence.')
  return out
