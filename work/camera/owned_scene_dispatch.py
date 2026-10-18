"""Derive ordinary draw dispatch from immutable callback-complete scene sources."""
import struct
from collections import defaultdict
from owned_scene_bundle import chunks
from owned_graph_packet import GraphPacket
from owned_object_filter import select_owned,depth_distance
from owned_object_dispatch import select

def draws(bundle):
 bundle.validate()
 graph=GraphPacket.decode(bundle.graph);state=graph.context[:256];camera=graph.context[256:304]
 callbacks=defaultdict(dict)
 for h,raw in chunks(bundle.callbacks,'callbacks'):
  if h[2]==0x03002090:callbacks[h[7]][struct.unpack_from('<H',raw,32)[0]]=raw[32:196]
 result=[]
 for h,raw in chunks(bundle.objects,'objects'):
  objects={struct.unpack_from('<I',raw,80+i*168)[0]:raw[84+i*168:248+i*168] for i in range(h[5])}
  completed=callbacks[h[4]]
  for index in select_owned(h[3],objects,camera,completed):
   source=completed.get(index,objects[index]);depth=depth_distance(source,camera)[0]
   result.append(dict(region=h[4],index=index,source=source,dispatch=select(source,state,depth)))
 return result
