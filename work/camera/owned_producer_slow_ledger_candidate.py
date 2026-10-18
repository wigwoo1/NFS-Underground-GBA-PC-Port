"""Bounded immutable ledger of updates completing over two original periods late."""
import json
from owned_producer_deadline_totals_candidate import ProducerDeadlineRows as Base
class ProducerDeadlineRows(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.slow=[];self.slow_dropped=0
 def append(self,row):
  slow=(row['completed_ns']-row['original_deadline_ns'])*16777216>2*280896*1000000000
  encoded=json.dumps(row,separators=(',',':'),allow_nan=False) if slow else None
  if encoded is not None and len(encoded.encode())>2048:raise ValueError('Slow producer record exceeds bounded size')
  super().append(row)
  if slow:
   if len(self.slow)<4096:self.slow.append(encoded)
   else:self.slow_dropped+=1
 def stats(self):
  out=super().stats();out['slow_original_updates']=dict(total=self.over_two_periods,dropped=self.slow_dropped,capacity=4096,max_record_bytes=2048,records=[json.loads(x) for x in self.slow],scope='Whole slow-update records only if dropped==0; overflow invalidates complete attribution.')
  return out
