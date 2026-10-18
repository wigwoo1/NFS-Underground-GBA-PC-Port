"""Bounded update rows plus exact whole-run original-deadline totals."""
from owned_serialized_recent_rows_candidate import RecentRows
class ProducerDeadlineRows(RecentRows):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.count=0;self.total={};self.maximum={};self.over_period=0;self.over_two_periods=0
 def append(self,row):
  n=row['native_boundary'];a=row['started_ns'];b=row['completed_ns'];d=row['original_deadline_ns']
  assert len(n)==5 and a<=n[0]<=n[1]<=b
  parts=dict(start_residual_ns=a-d,pre_native_ns=n[0]-a,native_ns=n[1]-n[0],post_native_ns=b-n[1],completion_residual_ns=b-d)
  assert sum(parts[k] for k in ('start_residual_ns','pre_native_ns','native_ns','post_native_ns'))==parts['completion_residual_ns']
  super().append(row)
  self.count+=1
  for k,v in parts.items():self.total[k]=self.total.get(k,0)+v;self.maximum[k]=max(self.maximum.get(k,v),v)
  self.over_period+=parts['completion_residual_ns']*16777216>280896*1000000000
  self.over_two_periods+=parts['completion_residual_ns']*16777216>2*280896*1000000000
 def stats(self):
  out=super().stats();out['whole_run_original_deadlines']=dict(count=self.count,total_ns=self.total,max_ns=self.maximum,completion_over_one_update=self.over_period,completion_over_two_updates=self.over_two_periods,scope='Every native-boundary update, exact original deadline residual totals; bounded retained rows. No pixel/scanout or causal attribution.')
  return out
