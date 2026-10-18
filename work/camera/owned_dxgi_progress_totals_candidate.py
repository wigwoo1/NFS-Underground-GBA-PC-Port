"""Bounded DXGI progression counters, not physical pixel certification."""
class DisplayProgressTotals:
 def __init__(self):self.previous=None;self.queries=0;self.unavailable=0;self.uninitialized=0;self.repeated=0;self.discontinuities=0;self.advances=0;self.images=0;self.refreshes=0;self.multi_refresh_single_image=0;self.max_refresh_span=0;self.max_submission_lag=0
 def observe(self,key,s):
  if len(s)!=9:raise ValueError('Invalid statistics length')
  self.queries+=1
  if s[0]!=0 or s[1]!=0:self.unavailable+=1;self.previous=None;return
  if s[3]==0 or s[4]==0 or s[6]==0:self.uninitialized+=1;self.previous=None;return
  if s[8]<=0:raise ValueError('Invalid QPC frequency')
  self.max_submission_lag=max(self.max_submission_lag,s[2]-s[3])
  if self.previous is not None:
   prior,a=self.previous
   dp=s[3]-a[3];dr=s[4]-a[4]
   if key!=prior or dp<0 or dr<0 or s[6]<a[6] or s[8]!=a[8]:self.discontinuities+=1
   elif dp==0:self.repeated+=1;return
   else:
    self.advances+=1;self.images+=dp;self.refreshes+=dr;self.max_refresh_span=max(self.max_refresh_span,dr);self.multi_refresh_single_image+=dp==1 and dr>1
  self.previous=(key,list(s))
 def stats(self):return dict(queries=self.queries,unavailable=self.unavailable,uninitialized_reports=self.uninitialized,repeated_reports=self.repeated,excluded_discontinuities=self.discontinuities,observed_advances=self.advances,reported_image_advance=self.images,reported_refresh_advance=self.refreshes,single_image_advances_over_multiple_refreshes=self.multi_refresh_single_image,max_observed_refresh_span=self.max_refresh_span,max_submission_lag=self.max_submission_lag,scope='Whole observed DXGI reports. Query gaps may skip reports; pause/generation discontinuities excluded. Not an exact presented-pixel mapping or physical scanout certification.')
