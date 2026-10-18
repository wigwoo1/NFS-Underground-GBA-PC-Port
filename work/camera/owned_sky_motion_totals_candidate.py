import math
class SkyMotionTotals:
 def __init__(self):self.previous=None;self.samples=0;self.transitions=0;self.stationary=0;self.source_holds=0;self.excluded=0;self.slow=0;self.api_slow=0;self.over_60_budget=0;self.api_over_60_budget=0;self.max_commit_gap=0;self.max_api_gap=0;self.commit_buckets=(0,)*6;self.api_buckets=(0,)*6
 def observe(self,row):
  if row['native_result']!=1:return
  old,new=row['sky_source_angles'];assert all(isinstance(v,int) and 0<=v<2**32 for v in (old,new));assert math.isfinite(row['alpha']) and 0<=row['alpha']<=1;delta=((new-old+8192)&16383)-8192;alpha=row['alpha']
  phase=(((new&16383) if alpha==1 else (old&16383)+delta*alpha)*240/4096)%240
  assert math.isclose(phase-math.floor(phase),row['sky_fraction'],abs_tol=1e-10)
  key=(row['epoch'],row['generation'],row['display_index']);stamp=row['native_committed_sample'][6];api_stamp=row['callback_timing']['present_end_ns']
  if self.previous is not None:
   prior,p,prior_delta,t,api_t=self.previous
   if key[:2]==prior[:2] and key[2]==prior[2]+1:
    assert stamp>=t
    held=abs((phase-p+120)%240-120)<1e-10
    self.transitions+=1;self.stationary+=held;self.source_holds+=held and delta==0 and prior_delta==0;self.slow+=stamp-t>25000000;self.api_slow+=api_stamp-api_t>25000000
    gap=stamp-t;api_gap=api_stamp-api_t
    self.over_60_budget+=gap*60>1000000000;self.api_over_60_budget+=api_gap*60>1000000000
    self.max_commit_gap=max(self.max_commit_gap,gap);self.max_api_gap=max(self.max_api_gap,api_gap)
    self.commit_buckets=self._bucket(self.commit_buckets,gap);self.api_buckets=self._bucket(self.api_buckets,api_gap)
   else:self.excluded+=1
  self.previous=(key,phase,delta,stamp,api_stamp);self.samples+=1
 @staticmethod
 def _bucket(counts,gap):
  # Immutable tuples keep shallow diagnostic snapshots independent.
  cutoffs=(16000000,17333334,20000000,25000000,33333334)
  index=sum(gap>cutoff for cutoff in cutoffs)
  return tuple(value+(i==index) for i,value in enumerate(counts))
 def stats(self):return dict(successful_samples=self.samples,adjacent_transitions=self.transitions,stationary_transitions=self.stationary,stationary_with_unchanged_source_angles=self.source_holds,excluded_identity_discontinuities=self.excluded,commit_intervals_over_25ms=self.slow,api_intervals_over_25ms=self.api_slow,commit_intervals_over_60fps_budget=self.over_60_budget,api_intervals_over_60fps_budget=self.api_over_60_budget,maximum_commit_gap_ns=self.max_commit_gap,maximum_api_gap_ns=self.max_api_gap,stationary_with_moving_source_angles=self.stationary-self.source_holds,interval_bucket_upper_ns=[16000000,17333334,20000000,25000000,33333334,None],commit_interval_buckets=list(self.commit_buckets),api_interval_buckets=list(self.api_buckets),scope='Whole-run captured phase and commit intervals; pause generation boundaries excluded; no pixels or scanout proof.')
