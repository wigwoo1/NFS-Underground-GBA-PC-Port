"""Constant-space successful native API-return interval statistics."""
class PresentationIntervalTotals:
 def __init__(self):self.previous=None;self.count=0;self.excluded=0;self.total_ns=0;self.max_ns=0;self.over25=0;self.over33=0;self.over50=0;self.under8=0
 def observe(self,row):
  if row['native_result']!=1:return
  t=row['callback_timing'];at=t['present_end_ns']
  if not t['present_begin_ns']<=at<=row['transaction_end_ns']:raise ValueError('Invalid successful presentation times')
  key=(row['epoch'],row['generation'],row['display_index'])
  if self.previous is not None:
   prior,stamp=self.previous
   if key[:2]==prior[:2] and key[2]==prior[2]+1:
    delta=at-stamp
    if delta<0:raise ValueError('Presentation return time moved backwards')
    self.count+=1;self.total_ns+=delta;self.max_ns=max(self.max_ns,delta)
    self.over25+=delta>25000000;self.over33+=delta*3>100000000;self.over50+=delta>50000000;self.under8+=delta<8000000
   else:self.excluded+=1
  self.previous=(key,at)
 def stats(self):return dict(adjacent_successful_intervals=self.count,excluded_discontinuities=self.excluded,mean_ms=self.total_ns/self.count/1e6 if self.count else None,max_ms=self.max_ns/1e6,over_25ms=self.over25,over_33_333ms=self.over33,over_50ms=self.over50,under_8ms=self.under8,scope='Whole observed API return intervals; pause/reset boundaries excluded. No scanout or pixel motion claim; no retained quantile samples.')
