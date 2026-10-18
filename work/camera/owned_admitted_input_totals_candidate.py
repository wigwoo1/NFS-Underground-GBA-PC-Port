"""Bounded counters for keys after successful original update completion."""
class AdmittedInputTotals:
 def __init__(self):self.counts=[0]*1024;self.total=0;self.transitions=0;self.previous=None;self.first_refresh=None;self.last_refresh=None
 def observe(self,refresh,keys):
  if not isinstance(keys,int) or not 0<=keys<1024:raise ValueError('Invalid original key mask')
  if self.last_refresh is not None and refresh<=self.last_refresh:raise ValueError('Original refresh did not advance')
  if self.previous is not None:self.transitions+=keys!=self.previous
  if self.first_refresh is None:self.first_refresh=refresh
  self.last_refresh=refresh;self.previous=keys;self.total+=1;self.counts[keys]+=1
 def stats(self):return dict(successful_original_updates=self.total,key_counts={str(i):n for i,n in enumerate(self.counts) if n},key_transitions=self.transitions,first_refresh=self.first_refresh,last_refresh=self.last_refresh,scope='Keys admitted after successful original callback completion; synthetic input is not physical controller evidence.')
