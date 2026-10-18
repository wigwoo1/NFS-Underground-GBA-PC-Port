"""Bounded DXGI progression counters, not physical pixel certification."""
from collections import deque,OrderedDict
class DisplayProgressTotals:
 def __init__(self):self.unmapped_reports=0;self.reported_owner_discontinuities=0;self.submissions=OrderedDict();self.spans=deque(maxlen=128);self.spans_dropped=0;self.previous=None;self.queries=0;self.unavailable=0;self.uninitialized=0;self.repeated=0;self.discontinuities=0;self.advances=0;self.images=0;self.refreshes=0;self.multi_refresh_single_image=0;self.max_refresh_span=0;self.max_submission_lag=0
 def observe(self,key,s,submission=None):
  if len(s)!=9:raise ValueError('Invalid statistics length')
  if submission is not None and s[1]==0:
   self.submissions[s[2]]=dict(submission)
   while len(self.submissions)>128:self.submissions.popitem(last=False)
  self.queries+=1
  if s[0]!=0 or s[1]!=0:self.unavailable+=1;self.previous=None;return
  if s[3]==0 or s[4]==0 or s[6]==0:self.uninitialized+=1;self.previous=None;return
  if s[8]<=0:raise ValueError('Invalid QPC frequency')
  self.max_submission_lag=max(self.max_submission_lag,s[2]-s[3])
  if submission is not None:
   owner=self.submissions.get(s[3])
   if owner is None:self.unmapped_reports+=1;self.previous=None;return
   if (owner['epoch'],owner['generation'])!=tuple(key):self.reported_owner_discontinuities+=1;self.previous=None;return
  if self.previous is not None:
   prior,a=self.previous
   dp=s[3]-a[3];dr=s[4]-a[4]
   if key!=prior or dp<0 or dr<0 or s[6]<a[6] or s[8]!=a[8]:self.discontinuities+=1
   elif dp==0:self.repeated+=1;return
   else:
    if dr>dp:
     if len(self.spans)==128:self.spans_dropped+=1
     self.spans.append(dict(key=list(key),image_advance=dp,refresh_advance=dr,start_qpc=a[6],end_qpc=s[6],qpc_frequency=s[8],older_present_count=a[3],newer_present_count=s[3],older_native_sample=self.submissions.get(a[3]),newer_native_sample=self.submissions.get(s[3])))
    self.advances+=1;self.images+=dp;self.refreshes+=dr;self.max_refresh_span=max(self.max_refresh_span,dr);self.multi_refresh_single_image+=dp==1 and dr>1
  self.previous=(key,list(s))
 def stats(self):return dict(unmapped_reports=self.unmapped_reports,reported_owner_discontinuities=self.reported_owner_discontinuities,excess_refresh_spans=list(self.spans),excess_refresh_spans_dropped=self.spans_dropped,queries=self.queries,unavailable=self.unavailable,uninitialized_reports=self.uninitialized,repeated_reports=self.repeated,excluded_discontinuities=self.discontinuities,observed_advances=self.advances,reported_image_advance=self.images,reported_refresh_advance=self.refreshes,single_image_advances_over_multiple_refreshes=self.multi_refresh_single_image,max_observed_refresh_span=self.max_refresh_span,max_submission_lag=self.max_submission_lag,scope='Whole observed DXGI reports. Query gaps may skip reports; pause/generation discontinuities excluded. Not an exact presented-pixel mapping or physical scanout certification.')
