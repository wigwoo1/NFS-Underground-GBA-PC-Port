"""Endpoint ordinary-model visit order from owned object chains, not draw slots."""
import struct
from owned_scene_bundle import chunks
from owned_object_filter import eligibility,depth_distance
from owned_object_dispatch import select

import threading
from types import MappingProxyType
_chain_local=threading.local()
def owned_object_chains(closed):
 cache=getattr(_chain_local,'cache',[])
 for owner,value in cache:
  if owner is closed:return value
 chains={}
 for h,raw in chunks(closed.objects,'graph_objects'):
  chain=[]
  for i in range(h[5]):
   index=struct.unpack_from('<I',raw,128+i*168)[0];source=raw[132+i*168:296+i*168];chain.append((index,source))
  chains[h[3]]=tuple(chain)
 value=MappingProxyType(chains);cache.append((closed,value))
 if len(cache)>4:cache.pop(0)
 _chain_local.cache=cache
 return value

def ordinary_model_visits(closed,queue,include_inactive_scenery=False):
 chains=owned_object_chains(closed)
 state=closed.graph.context[:256];camera=closed.graph.context[256:304];seen=set();out=[]
 for ordinal,region in reversed(list(enumerate(queue))):
  # Original model collection (03004D5C -> 030027F0/030054A0)
  # forwards empty clip intervals too; draw ownership precedes raster clipping.
  if region[5]&0x88:continue
  selected=[]
  for position,(index,source) in enumerate(chains.get(region[0],())):
   if index in seen:continue
   seen.add(index)
   if struct.unpack_from('<H',source,10)[0]&16:continue
   decision=eligibility(source)
   if decision=='callback':raise ValueError('Unresolved ordinary object callback')
   if decision!='project':continue
   depth,distance,_=depth_distance(source,camera)
   if depth<=0:continue
   dispatch=select(source,state,depth)
   allocated=source[136]!=255
   if include_inactive_scenery and dispatch['kind']=='hidden' and not allocated and 30<=struct.unpack_from('<h',source,54)[0]<=36:
    candidate=bytearray(source);candidate[136]=0
    dispatch=select(bytes(candidate),state,depth)
   if dispatch['kind']=='model':selected.append(dict(allocated=allocated,ordinal=ordinal,parent=region[0],object=index,source=bytes(source),depth=depth,distance=distance,position=position,dispatch=dispatch,bounds=tuple(region[1:5])))
  selected.sort(key=lambda item:(-item['distance'],-item['position']));out.extend(selected)
 return tuple(out)
