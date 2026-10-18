"""Isolated immutable object-chain views; bounded identity cache retains owned bytes."""
import struct,threading
from types import MappingProxyType
from owned_scene_bundle import chunks
local=threading.local();calls=0
def owned_object_chains(closed):
 global calls
 calls+=1
 cache=getattr(local,'cache',[])
 for owner,value in cache:
  if owner is closed:return value
 if type(closed.objects) is not bytes:raise ValueError('Object chains require immutable owned bytes')
 chains={}
 for h,raw in chunks(memoryview(closed.objects),'graph_objects'):
  chain=[]
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0];source=raw[132+i*168:296+i*168];chain.append((index,source))
  chains[h[3]]=tuple(chain)
 value=MappingProxyType(chains);cache.append((closed,value));local.cache=cache[-4:]
 return value
def install():
 import owned_ordinary_model_visits as target
 target.owned_object_chains=owned_object_chains
