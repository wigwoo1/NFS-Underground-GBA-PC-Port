"""Attach the preceding source submission and update completion to slow records."""
from owned_producer_slow_ledger_candidate import ProducerDeadlineRows as Base
last_submission=None
def submission(begin,end):
 global last_submission
 assert begin<=end;last_submission=(begin,end)
class ProducerDeadlineRows(Base):
 def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.previous=None
 def append(self,row):
  row=dict(row)
  if self.previous is not None:
   assert self.previous<=row['started_ns']
   span=last_submission
   assert span is not None and self.previous<=span[0]<=span[1]<=row['started_ns']
   row['preceding_caller']=dict(previous_completed_ns=self.previous,submit_begin_ns=span[0],submit_end_ns=span[1])
  super().append(row);self.previous=row['completed_ns']
