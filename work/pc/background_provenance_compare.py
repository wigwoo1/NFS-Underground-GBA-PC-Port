"""Test-only comparison of observed, unselected completed-scene provenance.

Never normalizes renderer inputs or selected ownership. No runtime capture use.
"""
import struct

def auxiliary(data):
 offset=0;end=len(data)
 for index in [0,0,3]:
  if end-offset<128:raise ValueError('short container')
  at,n=struct.unpack_from('<QQ',data,offset+64+16*index)
  if at<128 or n>end-offset-at:raise ValueError('invalid nested range')
  offset+=at;end=offset+n
 if end-offset!=5312:raise ValueError('unexpected auxiliary size')
 records=[struct.unpack_from('<8Q',data,offset+64+i*64) for i in range(2)]
 return offset,records

def selected(data,owners):
 at,records=auxiliary(data);indices=[]
 for owner in owners:
  matches=[i for i,row in enumerate(records) if row[:5]==tuple(owner)]
  if len(matches)!=1:raise ValueError('ambiguous or absent selected owner')
  indices+=matches
 if len(set(indices))!=len(owners):raise ValueError('duplicate selected owner')
 return at,records,indices

class BackgroundProvenanceLedger:
 def __init__(self):self.old_seen={};self.new_seen={};self.recovered={}
 def observe(self,data,owners,side,step,baseline_missing=False):
  at,records,indices=selected(data,owners)
  target=self.old_seen if side=='baseline' else self.new_seen
  for i in indices:
   row=records[i];target.setdefault(row,step)
   if side=='candidate' and baseline_missing and not any(old[:5]==row[:5] for old in self.old_seen):self.recovered.setdefault(row,step)
 def compare(self,a,b,owners,step):
  if a==b:return None
  if len(a)!=len(b) or len(owners)!=1:raise ValueError('size or selected-owner count changed')
  at,ar,ai=selected(a,owners);bt,br,bi=selected(b,owners)
  if at!=bt or ai!=bi or ar[ai[0]]!=br[bi[0]]:raise ValueError('selected provenance changed')
  unused=1-ai[0];old,new=ar[unused],br[unused];current=ar[ai[0]]
  if old not in self.old_seen or new not in self.recovered:raise ValueError('unobserved historical record')
  if not(old[0]==new[0]==current[0] and old[1]<new[1]<current[1] and old[3]<=new[2] and new[3]<=current[2] and old[7]==new[7]==1):raise ValueError('history did not advance to a valid earlier recovered scene')
  start=at+64+unused*64;end=start+64
  if a[:start]!=b[:start] or a[end:]!=b[end:]:raise ValueError('data outside unselected record changed')
  return dict(step=step,record_index=unused,old=list(old),new=list(new),selected_owner=list(owners[0]),baseline_record_observed_at=self.old_seen[old],recovered_record_observed_at=self.recovered[new],changed_bytes=sum(x!=y for x,y in zip(a,b)))
