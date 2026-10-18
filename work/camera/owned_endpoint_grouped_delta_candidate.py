"""Bounded thread-local endpoint corrections, immutable values, no point LRU nodes."""
import threading
from owned_portal_traversal import endpoint_delta as original
compute=original.__wrapped__
local=threading.local()
def endpoint_delta(x,z,raw,normal):
 if not hasattr(local,'owners'):
  local.owners=[];local.hits=local.misses=local.bypassed=0
 owners=local.owners
 entry=next((e for e in owners if (e[0] is raw and e[1] is normal) or (e[0]==raw and e[1]==normal)),None)
 if entry is None:
  entry=(raw,normal,{})
  owners.append(entry)
  if len(owners)>2:owners.pop(0)
 values=entry[2];key=(x,z)
 if key in values:
  local.hits+=1;return values[key]
 local.misses+=1;result=compute(x,z,raw,normal)
 if len(values)<2048:values[key]=result
 else:local.bypassed+=1
 return result
def stats():
 owners=getattr(local,'owners',[])
 return dict(endpoint_owners=len(owners),point_entries=sum(len(e[2]) for e in owners),hits=getattr(local,'hits',0),misses=getattr(local,'misses',0),bypassed=getattr(local,'bypassed',0),max_endpoint_owners=2,max_points_per_owner=2048)
def clear():
 if hasattr(local,'owners'):local.owners.clear()
 local.hits=local.misses=local.bypassed=0
