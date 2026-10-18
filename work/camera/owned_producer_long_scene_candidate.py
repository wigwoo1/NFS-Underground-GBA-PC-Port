"""Complete bounded ledger for scene preparation exceeding one original update."""
import json,os
from owned_producer_totals_candidate import ProducerRows as Base
class ProducerRows(Base):
 def __init__(self):super().__init__();self.long=[];self.long_total=0;self.long_dropped=0
 def append(self,row):
  if os.environ.get('NFSUG_SUPPLEMENT_FINE_TRACE')=='1':
   from owned_closed_supplements import supplement_trace
   detail=supplement_trace()
   if detail is not None and detail['refresh']==row['refresh']:
    row=dict(row,supplement_decode_trace=detail)
  slow=row['ns']*16777216>280896*1000000000
  encoded=json.dumps(row,separators=(',',':'),allow_nan=False) if slow else None
  if encoded is not None and len(encoded.encode())>16384:raise ValueError('Long producer record too large')
  super().append(row)
  if slow:
   self.long_total+=1
   if len(self.long)<1024:self.long.append(encoded)
   else:self.long_dropped+=1
 def stats(self):
  out=super().stats();out['long_scene_preparations']=dict(total=self.long_total,dropped=self.long_dropped,capacity=1024,max_record_bytes=16384,records=[json.loads(x) for x in self.long],scope='Every preparation>one original update if dropped==0; source timings do not prove scanout cadence.')
  return out
