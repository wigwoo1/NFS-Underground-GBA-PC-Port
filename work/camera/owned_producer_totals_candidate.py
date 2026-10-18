"""Whole-run duration totals with bounded producer rows."""
from owned_recent_rows_candidate import RecentRows
class DurationTotals:
 def __init__(self):self.count=0;self.total=0;self.maximum=0
 def append(self,value):
  if not isinstance(value,int) or value<0:raise ValueError('Invalid duration')
  self.count+=1;self.total+=value;self.maximum=max(self.maximum,value)
 def stats(self):return dict(count=self.count,total_ms=self.total/1e6,max_ms=self.maximum/1e6 if self.count else None,median_ms=None,scope='Whole-run exact count/total/max; median not retained.')
class ProducerRows(RecentRows):
 def __init__(self):super().__init__();self.duration=DurationTotals();self.stages={}
 def append(self,row):
  for value in [row['ns'],*row['stages'].values()]:
   if not isinstance(value,int) or value<0:raise ValueError('Invalid producer duration')
  super().append(row);self.duration.append(row['ns'])
  for key,value in row['stages'].items():self.stages.setdefault(key,DurationTotals()).append(value)
 def __iter__(self):return iter(self.rows)
